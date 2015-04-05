#!/usr/bin/python
"""
The superscript should take as an input:
1) min date (yr + week)
2) max date (yr + week)
3) possibly some _argDict['seasonMode'] bits such as regular season, post season, etc.

All input parameters _argDict['seasonMode'] fields should be at the top

the superscript can make intermediate csvs but they should be temporary

the superscript should be able to get schedules, populate game db, 
populate player db with new players, and populate game player db

The superscript should continue when there is an error, but output the errors to a known location

This superscript should be entirely from nfl.com (other than line info).  Other superscripts can come from other locations

all print statements should be for _argDict['debug'], stdout should not be piped to any other script

It is better to duplicate work and have the script be independent than vice versa
"""
import argparse
import django
import sys,os
try:
    import urllib2 as url
except:
    import urllib3 as url
import re
import subprocess
sys.path.append( '%s/../' % os.path.dirname( os.path.abspath( __file__ ) ) )
from myproject import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings") 
from django import db
from teamstats.models import *
from django.db.models import *
from decimal import *
import sqlite3
django.setup()

# 
# Input params
#

_argDict = {}
_argDict['minyear'] =2014
_argDict['minweek'] =1
_argDict['maxyear'] =2014
_argDict['maxweek'] =15
_argDict['debug'] = False
_argDict['seasonMode'] = 'regularseason' # certain links follow a different format for regular/postseason
_argDict['playerMode'] = 'current' # hitoric player data is found on different pages than current player data.
_argDict['overwrite'] = False # Sometimes we want to overwrite everything, other times we dont :)
_argDict['updateGames'] = False
_argDict['updatePlayers'] = False
_argDict['stopOnFail'] = False
# below swicthes are for manual moves/additions
_argDict['playerid'] = 0 # this is only used when playerMode is 'cmdline'.  It allows me to add a specific player if they were overlooked for some reason
_argDict['movePlayer'] = False
_argDict['oldid'] = False
_argDict['migrate'] = ''
_argDict['newid'] = False

_gameDataSource = 'default' #we have various sources for game data, some are better for different time periods
_currentSeason = 2014
_mvOldPlayerIds = True # Sometimes nfl.com changes the player ids, causing an enormous headache.
                    # the situation is hard to deal with since its also possible for 2 players with different
                    # ids to have the same name.  When this is true we migrate player data from old id to new id when we find it

# end of Input params

# Global data structures

_gameLinks = []
_gameDictList = [] #basic game info
_gameDataDict = {} #extended info/stats

_playerLinks = []
_playerList = []

#Keep order consistent with array ing views.py
_fieldTypes=[
"grass",
"turf"
]
_positions = [
  'C',
  'CB',
  'DB',
  'DE',
  'DL',
  'DT',
  'FB',
  'FS',
  'G',
  'ILB',
  'K',
  'LB',
  'LS',
  'MLB',
  'NT',
  'OG',
  'OL',
  'OLB',
  'OT',
  'P',
  'QB',
  'RB',
  'SAF',
  'SS',
  'T',
  'TE',
  'WR',
  #following is generic defense, used for pregc stats where i dont know exct pos _yet_
  'DEF',
  #following is generic RBWR, used for pregc stats where i dont know exct pos _yet_
  'RBWR',
  #following is generic nostat, used for pregc stats where i dont know exct pos _yet_
  'NA',
  ]
_teams = [
  "cardinals",
  "falcons",
  "ravens",
  "bills",
  "panthers",
  "bears",
  "bengals",
  "browns",
  "cowboys",
  "broncos",
  "lions",
  "packers",
  "texans",
  "colts",
  "jaguars",
  "chiefs",
  "dolphins",
  "vikings",
  "patriots",
  "saints",
  "giants",
  "jets",
  "raiders",
  "eagles",
  "steelers",
  "chargers",
  "49ers",
  "seahawks",
  "rams",
  "buccaneers",
  "titans",
  "redskins",
]
_team_cities = [
  "Arizona",
  "Atlanta",
  "Baltimore",
  "Buffalo",
  "Carolina",
  "Chicago",
  "Cincinnati",
  "Cleveland",
  "Dallas",
  "Denver",
  "Detroit",
  "Green Bay",
  "Houston",
  "Indianapolis",
  "Jacksonville",
  "Kansas City",
  "Miami",
  "Minnesota",
  "New England",
  "New Orleans",
  "NY Giants",
  "NY Jets",
  "Oakland",
  "Philadelphia",
  "Pittsburgh",
  "San Diego",
  "San Francisco",
  "Seattle",
  "St. Louis",
  "Tampa Bay",
  "Tennessee",
  "Washington",
]

_team_city_dict = dict(zip(_team_cities, _teams))
 
_team_abbrevs = {
    "GB" : "packers",
    "SEA" : "seahawks",
    "WAS" : "redskins",
    "HOU" : "texans",
    "TEN" : "titans",
    "KC" : "chiefs",
    "NE" : "patriots",
    "MIA" : "dolphins",
    "OAK" : "raiders",
    "NYJ" : "jets",
    "JAC" : "jaguars",
    "PHI" : "eagles",
    "CLE" : "browns",
    "PIT" : "steelers",
    "MIN" : "vikings",
    "STL" : "rams",
    "BUF" : "bills",
    "CHI" : "bears",
    "CIN" : "bengals",
    "BAL" : "ravens",
    "NO" : "saints",
    "ATL" : "falcons",
    "CAR" : "panthers",
    "TB" : "buccaneers",
    "SF" : "49ers",
    "DAL" : "cowboys",
    "IND" : "colts",
    "DEN" : "broncos",
    "NYG" : "giants",
    "DET" : "lions",
    "SD" : "chargers",
    "ARI" : "cardinals",
}

_teamRecord = { val: {} for val in _teams }

# Convert column names in nfl.com to our own field names
_fieldDict = { 
         'Away Final Score' : 'away_team_score',
         'Home Final Score': 'home_team_score',
         'Away Total Net Yards': 'away_team_yards',
         'Home Total Net Yards': 'home_team_yards',
         'Away Net Yards Rushing': 'away_team_rushing_yards',
         'Home Net Yards Rushing': 'home_team_rushing_yards',
         'Away Net Yards Passing': 'away_team_passing_yards',
         'Home Net Yards Passing': 'home_team_passing_yards',
}

_decimalFields = ['away_team_spread', 'over_under', 'away_team_record', 'home_team_record',
                  'RecvAvg', 'RushAvg', 'Pct', 'Avg', 'Rate', 'RushAvg', 'Sck', 'Avg']

# Functions

#
# The folowing should be rarely used, but sometimes we have to start a db from scratch
# and accessing the raw sql could be  the best way
#
def migrateDb ( ):
    dbDict = {}
    dbDict['teamstats_games'] = Games
    dbDict['teamstats_players'] = Players
    dbDict['teamstats_coaches'] = Coaches
    dbDict['teamstats_defgamestats'] = DefGameStats
    dbDict['teamstats_gameextras'] = GameExtras
    dbDict['teamstats_gameplayers'] = GamePlayers
    dbDict['teamstats_gamestreaks'] = GameStreaks
    dbDict['teamstats_qbgamestats'] = QbGameStats
    dbDict['teamstats_rbwrgamestats'] = RbWrGameStats
    conn = sqlite3.connect( _argDict['migrate'] )
    c = conn.cursor()
    # must order table query because we cant wuery gameplayers before games, etc.
    tables = [ 'teamstats_games', 'teamstats_players', 'teamstats_gameplayers',
               'teamstats_coaches', 'teamstats_gameextras','teamstats_gamestreaks', 
               'teamstats_defgamestats', 'teamstats_qbgamestats', 'teamstats_rbwrgamestats' ]
    uniqueIds = [ ['gameid'], ['playerid'], ['gameid_id','playerid_id'],
                       ['firstname', 'lastname'], ['game_id'], ['game_id'], 
                       ['gameplayer_id'], ['gameplayer_id'], ['gameplayer_id'] ] 
    uniqueIdDict = dict( zip( tables, uniqueIds ) )
    # The following tables allow us to start the migration
    # in the middle of a table, or to skip certain tables.
    skipTables =  []
    startIndices =  [ 0, 0, 0, 0, 0, 0, 0, 0, 0 ]
    startIndexDict = dict( zip( tables, startIndices ) )
    # On webfaction server I kept getting booted for exceeding
    # memory limits.  To handle this I make multiple calls to
    # the script.  Each call writes up to writesPerCall rows
    writesPerCall = 100000

    for table in tables:
        if ( table in skipTables ):
            continue
        object = dbDict[table]
        fieldStr = ''
        fieldArray = []
        objCache = []
        index = 0
        rowNum = 0
        for fieldTuple in c.execute('PRAGMA table_info(%s)'%table).fetchall():
            field = fieldTuple[1]
            fieldArray.append(field)
            if field in [ '_state' ]:
                continue
            fieldStr += "%s," % field

        print ( " select %s from %s " % ( fieldStr[0:-1], table ) )
        for row in c.execute( "select %s from %s" % ( fieldStr[:-1], table ) ).fetchall()[startIndexDict[table]:]:
            # Determine if entry is already in table
            kwDict = {}
            i = 0
            # DEBUG
            if ( rowNum % 10000 == 1 ):
                print( 'rowNum = %d index = %d'%(rowNum, index) )
            rowNum += 1
            # END of DEBUG
            for field in fieldArray:
                if field in [ '_state' ]:
                    continue
                if ( field in uniqueIdDict[ table ] ):
                    kwDict[ field ] = row[i]
                i += 1
            if ( object.objects.filter( **kwDict ).count() != 0 ):
                continue
                    
            obj = object()
            i = 0
            for field in fieldArray:
                if field in [ '_state' ]:
                    continue
                if ( field in _decimalFields ):
                    rowStr = str( row[i] )
                    if( rowStr.find('.') == -1 ):
                        rowStr += ".0"
                    obj.__dict__[field] = Decimal( rowStr )
                else:
                    obj.__dict__[field] = row[i]
                i += 1
            objCache.append(obj) 
            index += 1
            if ( index % 30 == 0 and objCache != [] ):
                object.objects.bulk_create(objCache)
                objCache = []
            if ( index > writesPerCall ):
                break
        object.objects.bulk_create(objCache)
        if ( index > writesPerCall ):
            break

# If nfl.com changes the player id in the gamelog url, we change too
def movePlayer ( oldid, newid ):
    oldplayer = Players.objects.filter(playerid = oldid)[0]
    newplayer = Players()

    newplayer.playerid = newid
    newplayer.position = oldplayer.position
    newplayer.birthdate = oldplayer.birthdate
    newplayer.lastname = oldplayer.lastname
    newplayer.firstname = oldplayer.firstname
    newplayer.save()

    gameplayers = GamePlayers.objects.filter(playerid = oldid)
    if (gameplayers.count() > 0 ):
        gameMoved = False
        for game in gameplayers:
            game.playerid = newplayer
            game.save()
            gameMoved = True
        if (gameMoved):
            oldplayer.delete()
            print ( "%s %s  moved to new id" %(newplayer.firstname, newplayer.lastname) )

#
# If for some reason we have created two entries for a player, combine
def combineMultipleEntries( playerEntries, player ):
    currentEntry = Players.objects.filter(playerid = player['id'])[0]
    if ( currentEntry ):
        for entry in playerEntries:
            if ( entry.playerid != player['id'] ):
                gameplayers = GamePlayers.objects.filter(playerid = entry.playerid)
                gameMoved = False
                for game in gameplayers:
                    game.playerid = currentEntry
                    game.save()
                    gameMoved = True
                if (gameMoved):
                    entry.delete()
                    print ( "%s %s  combined multiple entries and moved to new id" %(currentEntry.firstname, currentEntry.lastname) )

            

def isDefense(position = ''):
    if(position in ['DB', 'DE', 'LB', 'DL', 'OLB', 'ILB', 'MLB', 'CB', 'DT', 'NT',  'SS', 'FS'  ]):
        return True
    return False

def getAllGameLinks():
    if ( _argDict['seasonMode'] == 'regularseason' ):
        wkPrefix = 'REG'
    elif ( _argDict['seasonMode'] == 'postseason' ):
        wkPrefix = 'POST'
    for yr in range(_argDict['minyear'],_argDict['maxyear']+1):
        for wk in range(_argDict['minweek'],_argDict['maxweek']+1):
            sb= url.urlopen('http://www.nfl.com/scores/%d/%s%d'%(yr, wkPrefix, wk))
            scoreboard = sb.readlines()
            getGameLinksFromScoreboard(scoreboard)
            getTeamRecordsFromScoreboard(scoreboard, yr, wk)

#
# scoreboard is a page of links for a given week on nfl.com
#
def getGameLinksFromScoreboard(scoreboard = []):
    for line in scoreboard:
        line_re = re.search("a href=\"(\S+)\"\s+class=\"game-center-link\"", line)
        if (line_re):
            _gameLinks.append(str(line_re.group(1)))

#
# This returns the record after the game.  We will save the record before the game in the db
#
def getTeamRecordsFromScoreboard(scoreboard = [], yr=1, wk=1):
    for line in scoreboard:
        line_re = re.search("team=(.*)\">\((\d+)-(\d+)-(\d+)", line)
        if (line_re):
            team = line_re.group(1)
            wins = int(line_re.group(2))
            losses = int(line_re.group(3))
            ties = int(line_re.group(4))
            print( 'wk %d team %s wins = %d'%(wk, _team_abbrevs[team], wins) )
            _teamRecord[_team_abbrevs[team]]['%d%d'%(yr, wk)] = { 'wins': 0, 'losses' : 0, 'ties' : 0 }
            if ( wins + losses + ties > 0 ) :
                _teamRecord[_team_abbrevs[team]]['%d%d'%(yr, wk)]['wins'] = wins
                _teamRecord[_team_abbrevs[team]]['%d%d'%(yr, wk)]['losses'] = losses
                _teamRecord[_team_abbrevs[team]]['%d%d'%(yr, wk)]['ties'] = ties

        

def getGameDictListFromGameLinks(): 
    #/gamecenter/2013090803/2013/REG1/dolphins@browns
    for game in _gameLinks:
        game_re = re.search("gamecenter.(\d+).(\d+).(REG|POST)(\d+).(\S+)@(\S+)", game)
        if (game_re):
            gameDict = {}
            gameDict['gameid'] = int(game_re.group(1))
            gameDict['year'] = int(game_re.group(2))
            gameDict['week'] = int(game_re.group(4))
            gameDict['away_team'] = str(game_re.group(5))
            gameDict['home_team'] = str(game_re.group(6))
            _gameDictList.append(gameDict)

def getGameExtras(gameid, season, week, home, away):
    schedule = url.urlopen('http://www.pro-football-reference.com/years/%d/games.htm'%season)
    print( 'looking for boxscore for %s at %s week %d'%(away, home, week) )
    in_row = False #When true, we are in a row that could contain the relevent boxscore
    row_index = 0
    home_team_wins = True
    box_score_found = False
    for line in schedule.readlines():
        if ( not in_row ):
            # Week
            line_re = re.search('csk="(\d+)"', line)
            if (line_re):
                tmp_week = int(line_re.group(1))

            # BoxScore link
            else:
                #<td align="right"><a href="/boxscores/201409070atl.htm"><span class="bold_text">@Falcons 37</span><br>Saints 34</a></td>
                line_re = re.search('a href="(/boxscores/\d+.*htm)">boxscore', line)
                if (line_re):
                    boxscore = str(line_re.group(1))
                    in_row = True
                    row_index = 0
                    home_team_wins = True
        else:
            if ( row_index == 0 ):
                line_re = re.search('>(.*)</a>', line)
                if(line_re):
                    winning_team = str(line_re.group(1)).lower()
                    row_index+=1
            elif ( row_index == 1 ):
                if(line.find('@') >= 0):
                    home_team_wins = False
                row_index+=1
            elif ( row_index == 2 ):
                in_row = False
                row_index = 0
                line_re = re.search('>(.*)</a>', line)
                if(line_re):
                    losing_team = str(line_re.group(1)).lower()
                    if (home_team_wins):
                        tmp_home_team = winning_team
                        tmp_away_team = losing_team
                    else:
                        tmp_home_team = losing_team
                        tmp_away_team = winning_team
                    if ( tmp_home_team.find(home) >= 0 and tmp_away_team.find(away) >= 0  and week == tmp_week ):
                        box_score_found = True
                        break
    if ( box_score_found ):
        print( 'boxscore found for %s at %s'%(away, home) )
        getDataFromBoxScore(gameid, boxscore)


def getDataFromBoxScore(gameid, boxscore):
    print( 'opening http://www.pro-football-reference.com/%s'%boxscore )
    page = url.urlopen('http://www.pro-football-reference.com/%s'%boxscore)                    
    surface = False
    weather = False
    temperature = -100
    for line in page.readlines():
        if(line.find('<b>Surface</b>') >= 0):
            surface = True
        elif(line.find('<b>Weather</b>') >= 0):
            weather = True
            print( 'weather found' )
        elif(surface):
            surface = False
            if (line.find('turf') >= 0 ):
                surfaceType = _fieldTypes.index('turf') 
            else:
                surfaceType = _fieldTypes.index('grass') 
        elif(weather):
            print ( line )
            weather = False
            line_re = re.search('(\d+)\s+degrees', line) 
            if (line_re):
                temperature=int(line_re.group(1))
                break
    _gameDataDict[gameid]['fieldtype'] = surfaceType
    _gameDataDict[gameid]['temperature']   = temperature
            
        
            
            

def getBetData(gameid, season, week, home, away):
    gameDataFuncs = {
                        'repole' : getBetDataFromRepole,
                        'wagetracker' : getBetDataFromWageTracker
                    }			
    if ( _gameDataSource != 'default' ):
        gameDataSource = _gameDataSource
    elif ( season < 2014 ): 
        gameDataSource = 'repole'
    else:
        gameDataSource = 'wagetracker'
    return gameDataFuncs[gameDataSource](gameid, week, home, away)

def getBetDataFromWageTracker(gameid, week, home, away):
    print( 'in getBetDataFromWageTracker home = %s away = %s'%(home, away) )
    #print('week,away_team,away_team_score,away_team_spread,away_team_ml,over,under,home_team,home_team_score,home_team_spread,home_team_ml,total') 
    week_with_preseason = week+5
    page = url.urlopen('http://www.wagertracker.com/Odds.aspx?week=%d&sport=NFL'%week_with_preseason)
    matches = 0
    for line in page.readlines():
        """
        <td colspan="2"><table class="stnd"><tr><td class="oddshead">Final</td><td class="oddsheadnum">Score</td><td class="oddsheadnum">Spread</td><td class="oddsheadnum">ML</td><td class="oddsheadnum">Over/Under</td></tr><tr><td class="scoreoddsteamwinning">Dallas</td><td class="scoreodds">24</td><td class="scoreodds">+3.5</td><td class="scoreodds">+166</td><td class="scoreodds"><SPAN class="scoreodds">-106</SPAN>/<SPAN class="scoreodds">-104</SPAN></td></tr><tr><td class="scoreoddsteam">NY Giants</td><td class="scoreodds">17</td><td class="scoreodds">-3.5</td><td class="scoreodds">-185</td><td class="scoreodds">Total: 45.5</td></tr><tr><td colspan=5><a href="oddshistory.aspx?sport=NFL&gameid=1304544">Odds History</a>&nbsp;</tr></tr></table></td>
        """
        if(line.count('table class=\"stnd\"') > 0):
            team_re = re.search(r'scoreoddsteam\S*\">(.*)<.td><td class=\"scoreodds\">(\d+)</td><td class=\"scoreodds\">(\S+)</td><td class="scoreodds">(.*)</td><td class="scoreodds"><SPAN class="scoreodds">(.*)</SPAN>/<SPAN class="scoreodds">(.*)</SPAN></td></tr><tr><td class="scoreoddsteam.*">(.*)</td><td class="scoreodds">(\d+)</td><td class="scoreodds">(.*)</td><td class="scoreodds">(.*)</td><td class="scoreodds">Total: (.*)</td></tr>',line)
            if(team_re != None):
                matches+=1
                away_team = str(team_re.group(1))
                away_team_spread = str(team_re.group(3))
                away_team_ml = team_re.group(4)
                home_team = str(team_re.group(7))
                total = str(team_re.group(11))
                if ( _team_city_dict[away_team] == away and _team_city_dict[home_team] == home ):
                    return ( away_team_spread, total )
    

    
def getBetDataFromRepole(gameid, week, home, away):
    yr = int(str(gameid)[0:4])
    month = int(str(gameid)[4:6])
    date = int(str(gameid)[6:8])

    # handle discrepencies between regseason and postseason formatting
    season = yr
    awayIndex = 1
    homeIndex = 3
    lineIndex = 5
    overUnderIndex = 6
    print( "%s %s %d"%(away, home, gameid) )
    if ( _argDict['seasonMode'] == 'regularseason' ):
        csvPrefix = 'nfl'
    elif ( _argDict['seasonMode'] == 'postseason' ):
        csvPrefix = 'post'
        season = yr - 1
        awayIndex += 1
        homeIndex += 1
        lineIndex += 1
        overUnderIndex += 1
    f = url.urlopen('http://www.repole.com/sun4cast/stats/%s%dlines.csv'%(csvPrefix, season) )

    #12/29/2013,Kansas City Chiefs,24,San Diego Chargers,27,14.5,45 
    for line in f:
        lineArray = line.split(',')
        dateArray = lineArray[0].split('/')
        if (len(dateArray) == 3):
            if ( int(dateArray[2]) == yr and int(dateArray[0]) == month and int(dateArray[1]) == date):
                # The following are format changes specific to the differences between repole.com and nfl.com name formats
                tmpAway = lineArray[awayIndex].split()[-1].lower()
                tmpHome = lineArray[homeIndex].split()[-1].lower()
                if( tmpAway == away and tmpHome == home ):
                    print( "game found!" )
                    return ( lineArray[lineIndex], lineArray[overUnderIndex] )
    print( "game not found!" )

def getCoaches( gameid ):
    game = _gameDataDict[gameid]
    if ( game['year'] > 1999 and game['week'] > 0 ):
      try:
          page = url.urlopen('http://www.nfl.com/widget/gc/2011/tabs/cat-post-rate?gameId=%d'%(gameid)).readlines()
      except:
          print( 'cant open http://www.nfl.com/widget/gc/2011/tabs/cat-post-rate?gameId=%d'%(gameid) )
          page = []
    bf = ['','','']
    coachnum = 0
    coacharray = ['away', 'home']
    for line in page:
        bf[0] = bf[1]
        bf[1] = bf[2]
        bf[2] = line
        if( bf[2].find('Head Coach') != -1):
            line_re = re.search('name">(\S+)\s+(.*)</h3', bf[1])
            if (line_re):
                firstname = str(line_re.group(1)).lower()
                lastname = str(line_re.group(2)).lower()
                coachQuery = Coaches.objects.filter(firstname=firstname, lastname=lastname)
                if (coachQuery.count() == 0 ):
                    coach = Coaches()
                    coach.lastname = lastname
                    coach.firstname = firstname
                    coach.save()
                else:
                    coach = coachQuery[0]
                _gameDataDict[gameid]['%s_coach'%coacharray[coachnum]] = coach
            coachnum+=1
            if(coachnum == 2):
                break
    while ( coachnum < 2 ):
        _gameDataDict[gameid]['%s_coach'%coacharray[coachnum]] = 0
        coachnum+=1
                     
def getGameDataDict():
    game_num = 0
    header_list = ['year', 'week','away_team','home_team']
    for game in _gameDictList:
        if ( not _argDict['overwrite'] ):
            if ( Games.objects.filter( gameid = game['gameid'] ).count() > 0 ):
                print( '%d exists, skipping'%game['gameid'] )
                continue
   
        game_num += 1
        _gameDataDict[game['gameid']] = {}
        _gameDataDict[game['gameid']]['week'] = game['week']
        _gameDataDict[game['gameid']]['away_team'] = game['away_team']
        _gameDataDict[game['gameid']]['home_team'] = game['home_team']
        _gameDataDict[game['gameid']]['year'] = game['year']
        try:
            (spread, over_under) = getBetData(game['gameid'],  game['year'], game['week'], game['home_team'],  game['away_team'] )
        except:
            continue
        _gameDataDict[game['gameid']]['away_team_spread'] = spread
        _gameDataDict[game['gameid']]['over_under'] = over_under
        try:
            page = url.urlopen('http://www.nfl.com/widget/gc/2011/tabs/cat-post-boxscore?gameId=%d'%game['gameid'])
            page_array = page.readlines()
        except:
            page_array = [] 
            print( "year %d week %d gameid %d not found"%(game['year'], game['week'], game['gameid']) )
        boxscoretable = 0#our table is the second boxscoretable.  We increment to 3 when our table is complete
        row_index = 0
        getCoaches( game['gameid'] )
        getGameExtras( game['gameid'], game['year'], game['week'], game['home_team'],  game['away_team'] )
        for line in page_array:
            
            if(line.count('gc-box-score-table') > 0):
                boxscoretable +=1
            elif(boxscoretable == 2):
                """
                This is the standard format: 
          		<tr class="thd2">
          			<td>Total First Downs</td>
          			<td>18</td>
          			<td class="td-spacer"></td>
          			<td>Total First Downs</td>
          			<td>15</td>
          		</tr>
                """
                standard_line = False
                if(line.count('class') >  0 or line.count('</tr>') > 0):
                    row_index = (row_index+1)%7
                    standard_line = True
                #away team column name
                elif(row_index == 1):
                    line_re = re.search(r'<td>(.*)</td>', line)
                    if(line_re):
                        key = line_re.group(1)
                        row_index = (row_index+1)%7
                        standard_line = True
                #away team data
                elif(row_index == 2):
                    line_re = re.search(r'<td>(.*)</td>', line)
                    if(line_re):
                        val = line_re.group(1)
                        if( _fieldDict.has_key('Away %s'%key) ):
                            _gameDataDict[game['gameid']][_fieldDict['Away %s'%key]] = val
                        if(game_num == 1):
                            header_list.append('Away %s'%key)
                            if(_argDict['debug']):
                                print ("Adding header Away %s"%key)
                        row_index = (row_index+1)%7
                        standard_line = True
                #2nd printing of column name (for home team)
                elif(row_index == 4):
                    row_index = (row_index+1)%7
                    standard_line = True
                #home team data
                elif(row_index == 5):
                    line_re = re.search(r'<td>(.*)</td>', line)
                    if(line_re):
                      val = line_re.group(1)
                      if( _fieldDict.has_key('Home %s'%key) ):
                          _gameDataDict[game['gameid']][_fieldDict['Home %s'%key]] = val
                      if(game_num == 1):
                        header_list.append('Home %s'%key)
                        if(_argDict['debug']):
                          print ("Adding header Home %s"%key)
                      row_index = (row_index+1)%7
                      standard_line = True
                if(not standard_line):
                    if(_argDict['debug']):
                        print( "non standard line at row_index %d :"%row_index )
                        print ( line )
                    if(line.count('</table>') > 0):
                        if(_argDict['debug']):
                            print( "boxscore table complete" )
                        boxscoretable+=1
                    elif(line.count('</td>') > 0):
                        row_index = (row_index+1)%7
                        standard_line = True
                    elif(line.count('<td>') == 0):
                        if(_argDict['debug']):
                            print( "nonstandard line contains data" )
                        #for now it appears that these non standard lines are always #s
                        line_re = re.search(r'(\d+)', line)
                        if(line_re):
                            val = line_re.group(1)
                        else:
                            val = line
                        if(row_index == 1):
                            #val = line
                            if( _fieldDict.has_key('Away %s'%key) ):
                                _gameDataDict[game['gameid']][_fieldDict['Away %s'%key]] = val
                            if(game_num == 1):
                              header_list.append('Away %s'%key)
                              if(_argDict['debug']):
                                print ("Adding header Away %s"%key)
                        elif(row_index == 5):
                            #val = line
                            if( _fieldDict.has_key('Home %s'%key) ):
                                _gameDataDict[game['gameid']][_fieldDict['Home %s'%key]] = val
                            if(game_num == 1):
                              header_list.append('Home %s'%key)
                              if(_argDict['debug']):
                                print ("Adding header Home %s"%key)

    #Can be used for DEBUG, TODO: create a standalone csv function
    #now go through the dictionary I just created and write a csv
    #header = 'gameid,'
    #for item in header_list:
    #  if(item == '' or item == ' '):
    #    header += '0,'
    #  else:
    #    header+="%s,"%item
    #_gameCsvList.append(header)
    #for game in _gameDictList:
    #    gameid = game['gameid']
    #    row = '%s,'%str(gameid)
    #    for item in header_list:
    #      #remove leading spaces
    #      data = str(_gameDataDict[gameid].get(item, 'unknown'))
    #      data = str(re.sub(r'^\s+', '', data))
    #      #remove trailing spaces
    #      data = str(re.sub(r'\s+$', '', data))
    #      data = data.replace('&nbsp;-&nbsp;', ':')
    #      row += '%s,'%data
    #    _gameCsvList.append(row)
      
#
# Get win percentage for each team
#
def getRecords ( gameEntry ): 
    #
    # The data from gamecenter is post game, which is not what we want
    # So we subtract a game
    #
    yr = int(str(gameEntry.gameid)[0:4])
    month = int(str(gameEntry.gameid)[4:6])
    
    # records are stored by season, not yr
    season = yr
    if ( month < 6 ):
        season -= 1
    print( '%d%d'%(yr,gameEntry.week) )
    away_games_played = max ( _teamRecord[_teams[gameEntry.away_team]]['%d%d'%(season,gameEntry.week)]['wins']   + 
                              _teamRecord[_teams[gameEntry.away_team]]['%d%d'%(season,gameEntry.week)]['losses'] + 
                              _teamRecord[_teams[gameEntry.away_team]]['%d%d'%(season,gameEntry.week)]['ties'] - 1, 1)
    home_games_played = max( _teamRecord[_teams[gameEntry.home_team]]['%d%d'%(season,gameEntry.week)]['wins']   + 
                             _teamRecord[_teams[gameEntry.home_team]]['%d%d'%(season,gameEntry.week)]['losses'] + 
                             _teamRecord[_teams[gameEntry.home_team]]['%d%d'%(season,gameEntry.week)]['ties'] - 1, 1)

    if ( gameEntry.away_team_score > gameEntry.home_team_score ):
        away_wins =  _teamRecord[_teams[gameEntry.away_team]]['%d%d'%(season,gameEntry.week)]['wins'] - 1
        home_wins =  _teamRecord[_teams[gameEntry.home_team]]['%d%d'%(season,gameEntry.week)]['wins']
    elif( gameEntry.away_team_score < gameEntry.home_team_score ): 
        away_wins =  _teamRecord[_teams[gameEntry.away_team]]['%d%d'%(season,gameEntry.week)]['wins']
        home_wins =  _teamRecord[_teams[gameEntry.home_team]]['%d%d'%(season,gameEntry.week)]['wins'] - 1
    else:
        away_wins =  _teamRecord[_teams[gameEntry.away_team]]['%d%d'%(season,gameEntry.week)]['wins'] - 1
        home_wins =  _teamRecord[_teams[gameEntry.home_team]]['%d%d'%(season,gameEntry.week)]['wins'] - 1
    
    gameEntry.away_team_record = (1.0 * away_wins)/away_games_played
    gameEntry.home_team_record = (1.0 * home_wins)/home_games_played

def updateGameTable():
    print( "in updateGameTable" )
    for gameid,game in _gameDataDict.items():
        print ( gameid )
        gameEntries = Games.objects.filter(gameid = gameid)
        if ( gameEntries.count() > 0  and not _argDict['overwrite']):
            print( "%d found, skipping"%gameid )
            continue
        elif ( gameEntries.count() > 0  and _argDict['overwrite']):
            print( "%d found"%gameid )
            gameEntry = gameEntries[0]
        else:
            print( "%d not found"%gameid )
            gameEntry = Games()
            gameEntry.gameid = gameid
        # Certain data is stored in a separate GameExtras table
        gameExtraQuery = GameExtras.objects.filter(game = gameEntry)
        if ( gameExtraQuery.count() == 0 ):
            gameExtra = GameExtras()
            gameExtra.game = gameEntry
        else:
            gameExtra = gameExtraQuery[0]

        yr = int(str(gameid)[0:4])
        month = int(str(gameid)[4:6])
        date = int(str(gameid)[6:8])
        fulldate = '%s-%s-%s'%(yr,month,date)
        gameEntry.date = fulldate
        if ( month > 6 ):
            gameEntry.season = yr
        else:
            gameEntry.season = yr - 1

        for key,val in game.items():
            if( gameEntry.__dict__.has_key(key) ):
                print( 'setting %s to %s'%(str(key),str(val)) )
                if ( key not in ['away_team', 'home_team'] ):
                    gameEntry.__dict__[key] = val
                else:
                    gameEntry.__dict__[key] = _teams.index(val)
            elif( gameExtra.__dict__.has_key(key) ):
                print( 'setting %s to %s'%(str(key),str(val)) )
                gameExtra.__dict__[key] = val
        getRecords( gameEntry )
        # FIXME!! find real values
        gameEntry.stadium = 0
        #gameEntry.fieldtype = 0
        print( "saving game" )
        gameEntry.save()
        gameExtra.save()
    

def getPlayers():
    if (_argDict['playerMode'] == 'current'):
        getCurrentRosterLinks()
        getCurrentPlayersFromRosterLinks()
    elif (_argDict['playerMode'] == 'historic'):
        getHistoricalPlayers()
    elif (_argDict['playerMode'] == 'cmdline'):
        getPlayerFromPlayerId(_argDict['playerid'])

def getPlayerFromPlayerId(playerid):
    player = Players.objects.filter(playerid=playerid)[0]
    _playerList.append({ 
                         'fullname' : '%s%s'%(player.firstname,player.lastname), 
                         'id' : playerid, 
                         'lastname' : player.lastname, 
                         'firstname' : player.firstname, 
                         'position' : _positions[player.position] 
                       })

def getHistoricalPlayers():
    #positions = ['quarterback', 'runningback', 'widereceiver', 'tightend', 'offensiveline', 'defensivelineman', 'linebacker', 'defensiveback','kicker','punter']
    positions = ['quarterback', 'runningback', 'widereceiver', 'tightend' ] #'offensiveline', 'defensivelineman', 'linebacker', 'defensiveback','kicker','punter']
    positionDict = {
                    'quarterback':'QB', 
                    'runningback':'RB', 
                    'widereceiver':'WR', 
                    'tightend':'TE', 
                    'offensiveline' : 'OL', 
                    'defensivelineman' : 'DL', 
                    'linebacker' : 'LB', 
                    'defensiveback' : 'DB',
                    'kicker':'K',
                    'punter':'P'
                  }
    for pos in positions:
        #page = url.urlopen('http://www.nfl.com/players/search?category=position&filter=%s&playerType=historical&conference=ALL'%pos, 'r')
        #for line in page.readlines():
        #    if(line.find('span class="linkNavigation floatRight"> <strong>') != -1):
        #        line_array = line.split('</a>') 
        #        for tag in line_array:
        #            link = tag.replace('>&nbsp|&nbsp<a href="', 'http://www.nfl.com')
        #            link = str(re.sub('title="Go to page \d+.>\d+', '', link))
        #            link = str(re.sub('.*strong', '', link))
        #            link = str(re.sub('.*a href=.', 'http://www.nfl.com', link))
        #            link = str(re.sub('&amp;', '&', link))
        #            link = str(re.sub('filter=%s.*'%pos, 'filter=%s'%pos, link))
        #            _playerLinks.append(link)
        lastpage=False
        for i in range(1, 100):
            print( 'grabbing historic %s'%pos )
            try:
                page = url.urlopen('http://www.nfl.com/players/search?category=position&playerType=historical&d-447263-p=%d&filter=%s&conferenceAbbr=null'%(i, pos) )
            except:
                print( 'cant open %s'%link )
                continue
            for line in page.readlines():
                if (line.find('No players found.') >= 0):
                    print ( line )
                    lastpage=True
                    break
                #<td style="width:200px" class="tbdy"><a href="/player/dukeabbruzzi/2508149/profile">Abbruzzi, Duke</a></td>
                line_re = re.search("href=\"\/player\/(\S+)/(\d+)/profile\">(\S+),\s+(\S+)</a>", line)
                if( line_re ):
                    fullname = str(line_re.group(1))
                    id = int(line_re.group(2))
                    lastname = str(line_re.group(3))
                    firstname = str(line_re.group(4))
                    position=positionDict[pos]
                    player = { 'fullname' : fullname, 'id' : id, 'lastname' : lastname, 'firstname' : firstname, 'position' : position }
                    _playerList.append(player) 
            if ( lastpage ):
                break
            

                
#
# for typical usage, we only need current players
# since we will be running regularly
def getCurrentRosterLinks():
    print( 'in getCurrentRosterLinks' )
    fh = url.urlopen('http://www.nfl.com/players/search?category=team&playerType=current')
    for line in fh.readlines():
        line_re = re.search("a href=\"(.*players.search.category=team.*;filter.*playerType=current)\"", line)
        if line_re:
            roster_link = re.subn('amp;','', str(line_re.group(1)))[0]
            print( 'adding %s to roster links'%roster_link )
            _playerLinks.append("http://www.nfl.com%s"%roster_link)

def getCurrentPlayersFromRosterLinks():
    print( 'In getCurrentPlayersFromRosterLinks' )
    for link in _playerLinks:
        print( 'opening %s'%link )
        fh = url.urlopen(link)
        for line in fh.readlines():
            # <td><a href="/player/kendallwright/2532977/profile">Wright, Kendall</a></td>
            line_re = re.search("<td class=\"tbdy\">(RB|FB|TE|LS|ILB|LB|DE|WR|SS|FS|DB|NT|C|P|G|T|DT|QB|MLB|OLB|K|CB)</td>", line)
            if ( line_re ):
                position = str(line_re.group(1))
            line_re = re.search("href=\"\/player\/(\S+)/(\d+)/profile\">(\S+),\s+(\S+)</a>", line)
            if ( line_re ):
                fullname = str(line_re.group(1))
                id = int(line_re.group(2))
                lastname = str(line_re.group(3))
                firstname = str(line_re.group(4))
                player = { 'fullname' : fullname, 'id' : id, 'lastname' : lastname, 'firstname' : firstname, 'position' : position }
                _playerList.append(player) 

def updatePlayers():
    print( "In updatePlayers" )
    for player in _playerList:
        if ( Players.objects.filter(playerid=player['id']).count() == 0):
            if ( Players.objects.filter(lastname = player['lastname'].lower(), firstname=player['firstname'].lower(), position=_positions.index(player['position'])).count() != 0 ):
                matchingPlayers = Players.objects.filter(lastname = player['lastname'].lower(), firstname=player['firstname'].lower(), position=_positions.index(player['position']))
                if ( not _mvOldPlayerIds ):
                    print( "Warning!!! %d players with same name/position (%s %s) exist.  Atleast one with diff. id (%d vs %d).  Skipping"% ( 
                        matchingPlayers.count(), player['firstname'].lower(), player['lastname'].lower(), matchingPlayers[0].playerid, player['id']
                    ) )
                    continue
                else:
                    movePlayer( matchingPlayers[0].playerid, player['id'] ) 
                    continue
            print( 'Adding %s %s to player db'%( player['firstname'].lower(), player['lastname'].lower() ) )
            playerInst = Players()
            playerInst.playerid = player['id']
            playerInst.lastname = player['lastname'].lower()
            playerInst.firstname = player['firstname'].lower()
            playerInst.position =  _positions.index(player['position'])
            # FIXME : Add Birthdate
            playerInst.birthdate = '1900-01-01'
            playerInst.save()
        playerEntries = Players.objects.filter(lastname=player['lastname'].lower(), firstname=player['firstname'].lower(), position=_positions.index(player['position']))
        if ( playerEntries.count() > 1 ):
            combineMultipleEntries(playerEntries, player)

def getStatsFromGamelogs():
    for player in _playerList:
        # Different _positions have different stats/data formatted differently
        position = player['position']
        hasStats = True
        if(position == 'RB' or position == 'FB'):
            fields = ['G','GS','RushAtt','RushYds','RushAvg','RushLng','RushTD','Rec','RecYds','RecAvg','RecLng','RecTD','FUM','Lost']
            gameStatInst = RbWrGameStats()
            gameStatClass = RbWrGameStats
        elif(position == 'WR' or position == 'TE'):
            fields = ['G','GS','Rec','RecYds','RecAvg','RecLng','RecTD','RushAtt','RushYds','RushAvg','RushLng','RushTD','FUM','Lost']
            gameStatInst = RbWrGameStats()
            gameStatClass = RbWrGameStats
        elif(position == 'QB'):
            fields = ['G','GS','Comp','Att','Pct','Yds','Avg','TD','Int','Sck','SckY','Rate','RushAtt','RushYds','RushAvg','RushTD','FUM','Lost']
            gameStatInst = QbGameStats()
            gameStatClass = QbGameStats
        elif(isDefense(position)):
            fields = ['G','GS','CombTck','Tck','AstTck','Sck','Sfty','PDef','Int','Yds','Avg','Lng','TD','FF']
            gameStatInst = DefGameStats()
            gameStatClass = DefGameStats
        else:
            print( "No stat collection for position %s"%position )
            hasStats = False

        #First find all seasons a player played in
        try:
            gamelog = url.urlopen('http://www.nfl.com/player/%s/%d/gamelogs/'%(player['fullname'],player['id']))
            gamelogarray = gamelog.readlines()
        except:
            print( 'cant open http://www.nfl.com/player/%s/%d/gamelogs/'%(player['fullname'],player['id']) )
            continue
        season_select = False
        past_seasons = []
        for line in gamelogarray:
            if(line.count('<strong>Game Log:') > 0):
              season_select = True
              print( 'season select begins!' )
            elif(season_select and line.count('<option value=') > 0):
              line_re = re.search(r'value=.(\d+).>',line)
              if(line_re):
                past_seasons.append(int(line_re.group(1)))
            elif(season_select and line.count('</select>') > 0):
              season_select = False
              print( 'past seasons:' )
              print ( past_seasons )

        seasonList = past_seasons
        seasonList.append(_currentSeason)
        # iterate over all seasons, looking for missing gameplayers
        for season in seasonList:
            if (season < _argDict['minyear'] or season > _argDict['maxyear']):
                continue
            try:
                gamelog = url.urlopen('http://www.nfl.com/player/%s/%d/gamelogs/?season=%d'%(player['fullname'], player['id'], season))
                gamelogarray = gamelog.readlines()
            except:
                print( 'cant open http://www.nfl.com/player/%s/%d/gamelogs/season=%d'%(player['fullname'],player['id'],season) )
                continue
            reg_season = False
            intable = False
            for line in gamelogarray:
                if(line.count('Regular Season') > 0 and _argDict['seasonMode'] == 'regularseason' or 
                     line.count('Postseason')>0 and _argDict['seasonMode'] == 'postseason'
                    ):
                  print( 'Season Sect begins!' )
                  reg_season = True
                elif(reg_season and line.count('gamecenter') > 0): 
                  intable = True
                  fieldIndex = 0
                  line_re = re.search(r'gamecenter.(\d+)',line)
                   # two links, one has video ('/watch') , the other has score
                  if(line_re and line.find('watch') < 0 ):
                    gameid = int(line_re.group(1))
                    gameInst = Games.objects.filter(gameid = gameid)
                    playerInst = Players.objects.filter(playerid = player['id'])
                    if ( playerInst.count() == 0 ):
                        if ( _argDict['debug'] ):
                            print( "player %d not in db, skipping"%player['id'] )
                        intable = False
                        continue
                    if ( gameInst.count() == 0 ):
                        if ( _argDict['debug'] ):
                            print( "Game %d not in db, skipping"%gameid )
                        intable = False
                        continue
                    gamePlayerQuery = GamePlayers.objects.filter(gameid = gameInst[0], playerid = playerInst[0] )
                    if( gamePlayerQuery.count() != 0 ):
                        gameStatQuery = gameStatClass.objects.filter( gameplayer = gamePlayerQuery[0] )
                        if (  not _argDict['overwrite'] and gameStatQuery.count() > 0 ):
                            if ( _argDict['debug'] ):
                                print( "Game %d player %d already in db, skipping"%( gameid, player['id'] ) )
                            intable = False
                            continue
                        else:
                            gamePlayerInst = gamePlayerQuery[0]
                            if ( gameStatQuery.count() > 0 ):
                                gameStatInst = gameStatQuery[0]
                            elif ( hasStats ):
                                print( "adding Game %d player %s to db"%( gameid, player['fullname'] ) )
                                gameStatInst = gameStatClass()
                                gameStatInst.gameplayer = gamePlayerInst
                    else:
                        gamePlayerInst = GamePlayers()
                        gamePlayerInst.gameid   = gameInst[0]
                        gamePlayerInst.playerid = playerInst[0]
                        gamePlayerInst.save()
                        print( "adding Game %d player %s to db"%( gameid, player['fullname'] ) )
                        gameStatInst = gameStatClass()
                        gameStatInst.gameplayer = gamePlayerInst
                    
                elif(reg_season and intable):
                  line_re = re.search(r'<td>(.*)</td>', line)
                  if(line_re):
                    if ( hasStats ):
                        if ( gameStatInst.__dict__.has_key(fields[fieldIndex]) ):
                            statString = re.sub('[a-zA-Z]', '', str(line_re.group(1)))
                            if ( statString in ['--'] ):
                                statString = '0'
                            if ( fields[fieldIndex] in _decimalFields ):
                                stat = Decimal(statString)
                            else:
                                stat = int(statString.split('.')[0])          
                            gameStatInst.__dict__[fields[fieldIndex]] = stat
                            fieldIndex += 1
                  elif(line.count('class="border-td"')>0):
                      intable = False
                      print( 'saving gamestat for player %s'%player['fullname'] )
                      if ( hasStats ):
                          if (not _argDict['stopOnFail']):
                              try: 
                                  gameStatInst.save()
                              except:
                                  print( 'failed to save gamestat for player %s'%player['fullname'] )
                          else:
                              gameStatInst.save()
                if(reg_season and line.count('TOTAL') > 0):
                    reg_season = False
                    if ( intable ):
                        intable = False
                        print( 'saving gamestat for player %s'%player['fullname'] )
                        gamePlayerInst.save()
                        if ( hasStats ):
                            if (not _argDict['stopOnFail']):
                                try: 
                                    gameStatInst.save()
                                except:
                                    print( 'failed to save gamestat for player %s' % player['fullname'] )
                            else:
                                gameStatInst.save()
        


def parseArgs(parser):
    args = parser.parse_args()
    for key,val in args.__dict__.items():
        print( "%s = %s"%(str(key), str(val)) )
        if ( val != None ):
            _argDict[key] = val
            
#
# Main
#
parser = argparse.ArgumentParser()
parser.add_argument("--minyear", type=int)
parser.add_argument("--maxyear", type=int)
parser.add_argument("--minweek", type=int)
parser.add_argument("--maxweek", type=int)
parser.add_argument("--seasonMode", type=str)
parser.add_argument("--playerMode", type=str)
parser.add_argument("--debug", action="store_true")
parser.add_argument("--overwrite", action="store_true")
parser.add_argument("--updateGames", action="store_true")
parser.add_argument("--updatePlayers", action="store_true")
parser.add_argument("--stopOnFail", action="store_true")
parser.add_argument("--movePlayer", action="store_true")
parser.add_argument("--playerid", type=int)
parser.add_argument("--oldid", type=int)
parser.add_argument("--newid", type=int)
parser.add_argument("--migrate", type=str)
parseArgs(parser)


# allow for migration of raw db to the db currenlty used
# Currently this only supports migrations from sqlite
if( _argDict['migrate'] != '' ):
    migrateDb()

# Manually move a player to a new id.
# We typically use the id from our parsing source,
# whether it be nfl.com, nflreference.  But this can change from
# underneath us, or we can change our source, in which case this
# utility comes  in handy.
if( _argDict['movePlayer'] ):
    movePlayer( _argDict['oldid'], _argDict['newid'] )

# game data
if ( _argDict['updateGames'] ):
    getAllGameLinks()
    getGameDictListFromGameLinks()
    getGameDataDict()
    updateGameTable()

# player data
if ( _argDict['updatePlayers'] ):
    getPlayers()
    updatePlayers()
    getStatsFromGamelogs()



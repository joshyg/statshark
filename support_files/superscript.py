#!/usr/bin/python
"""
The superscript should take as an input:
1) min date (yr + week)
2) max date (yr + week)
3) possibly some _seasonMode bits such as regular season, post season, etc.

All input parameters _seasonMode fields should be at the top

the superscript can make intermediate csvs but they should be temporary

the superscript should be able to get schedules, populate game db, 
populate player db with new players, and populate game player db

The superscript should continue when there is an error, but output the errors to a known location

This superscript should be entirely from nfl.com (other than line info).  Other superscripts can come from other locations

all print statements should be for debug, stdout should not be piped to any other script

It is better to duplicate work and have the script be independent than vice versa
"""
import django
import sys,os
import urllib2 as url
import re
import subprocess
sys.path.append('/home/joshyg/webapps/nflbacktest/myproject')
from myproject import settings
from django.core.management import setup_environ
setup_environ(settings)
from django import db
from teamstats.models import *
from django.db.models import *
from decimal import *



# 
# Input params
#

minyear=2013
minweek=17
maxyear=2013
maxweek=22
debug = False
_seasonMode = 'postseason' # certain links follow a different format for regular/postseason
_currentSeason = 2014
_overwrite = False # Sometimes we want to overwrite everything, other times we dont :)
_mvOldPlayerIds = True # Sometimes nfl.com changes the player ids, causing an enormous headache.
                    # the situation is hard to deal with since its also possible for 2 players with different
                    # ids to have the same name.  When this is true we migrate player data from old id to new id when we find it

_updateGames = True
_updatePlayers = True
# end of Input params

# Global data structures

_gameLinks = []
_gameDictList = [] #basic game info
_gameDataDict = {} #extended info/stats

_rosterLinks = []
_playerList = []

#Keep order consistent with array ing views.py
positions = [
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
teams = [
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
 
team_abbrevs = {
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

_teamRecord = { val: {} for val in teams }

# Convert column names in nfl.com to our own field names
fieldDict = { 
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

#functions

#
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
            print "%s %s  moved to new id"%(newplayer.firstname, newplayer.lastname)

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
                    print "%s %s  combined multiple entries and moved to new id"%(currentEntry.firstname, currentEntry.lastname)

            

def isDefense(position = ''):
    if(position in ['DB', 'DE', 'LB', 'DL', 'OLB', 'ILB', 'MLB', 'CB', 'DT', 'NT',  'SS', 'FS'  ]):
        return True
    return False

def getAllGameLinks():
    if ( _seasonMode == 'regularseason' ):
        wkPrefix = 'REG'
    elif ( _seasonMode == 'postseason' ):
        wkPrefix = 'POST'
    for yr in range(minyear,maxyear+1):
        for wk in range(minweek,maxweek+1):
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
            print 'wk %d team %s wins = %d'%(wk, team_abbrevs[team], wins)
            _teamRecord[team_abbrevs[team]]['%d%d'%(yr, wk)] = { 'wins': 0, 'losses' : 0, 'ties' : 0 }
            if ( wins + losses + ties > 0 ) :
                _teamRecord[team_abbrevs[team]]['%d%d'%(yr, wk)]['wins'] = wins
                _teamRecord[team_abbrevs[team]]['%d%d'%(yr, wk)]['losses'] = losses
                _teamRecord[team_abbrevs[team]]['%d%d'%(yr, wk)]['ties'] = ties

        

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

#
# This function is specifically looking for the spread in the csvs on repole.com
#
def getBetData(gameid, home, away):
    yr = int(str(gameid)[0:4])
    month = int(str(gameid)[4:6])
    date = int(str(gameid)[6:8])

    # handle discrepencies between regseason and postseason formatting
    season = yr
    awayIndex = 1
    homeIndex = 3
    lineIndex = 5
    overUnderIndex = 6
    print "%s %s %d"%(away, home, gameid)
    if ( _seasonMode == 'regularseason' ):
        csvPrefix = 'nfl'
    elif ( _seasonMode == 'postseason' ):
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
                    print "game found!"
                    return ( lineArray[lineIndex], lineArray[overUnderIndex] )
    print "game not found!"
                     
def getGameDataDict():
    game_num = 0
    header_list = ['year', 'week','away_team','home_team']
    for game in _gameDictList:
        if ( not _overwrite ):
            if ( Games.objects.filter( gameid = game['gameid'] ).count > 0 ):
                print '%d exists, skipping'%game['gameid']
                continue
   
        game_num += 1
        _gameDataDict[game['gameid']] = {}
        _gameDataDict[game['gameid']]['week'] = game['week']
        _gameDataDict[game['gameid']]['away_team'] = game['away_team']
        _gameDataDict[game['gameid']]['home_team'] = game['home_team']
        _gameDataDict[game['gameid']]['year'] = game['year']
        (spread, over_under) = getBetData(game['gameid'],  game['home_team'],  game['away_team'] )
        _gameDataDict[game['gameid']]['away_team_spread'] = spread
        _gameDataDict[game['gameid']]['over_under'] = over_under
        try:
            page = url.urlopen('http://www.nfl.com/widget/gc/2011/tabs/cat-post-boxscore?gameId=%d'%game['gameid'])
            page_array = page.readlines()
        except:
            page_array = [] 
            print "year %d week %d gameid %d not found"%(game['year'], game['week'], game['gameid'])
        boxscoretable = 0#our table is the second boxscoretable.  We increment to 3 when our table is complete
        row_index = 0
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
                        if( fieldDict.has_key('Away %s'%key) ):
                            _gameDataDict[game['gameid']][fieldDict['Away %s'%key]] = val
                        if(game_num == 1):
                            header_list.append('Away %s'%key)
                            if(debug):
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
                      if( fieldDict.has_key('Home %s'%key) ):
                          _gameDataDict[game['gameid']][fieldDict['Home %s'%key]] = val
                      if(game_num == 1):
                        header_list.append('Home %s'%key)
                        if(debug):
                          print ("Adding header Home %s"%key)
                      row_index = (row_index+1)%7
                      standard_line = True
                if(not standard_line):
                    if(debug):
                        print "non standard line at row_index %d :"%row_index
                        print line
                    if(line.count('</table>') > 0):
                        if(debug):
                            print "boxscore table complete"
                        boxscoretable+=1
                    elif(line.count('</td>') > 0):
                        row_index = (row_index+1)%7
                        standard_line = True
                    elif(line.count('<td>') == 0):
                        if(debug):
                            print "nonstandard line contains data"
                        #for now it appears that these non standard lines are always #s
                        line_re = re.search(r'(\d+)', line)
                        if(line_re):
                            val = line_re.group(1)
                        else:
                            val = line
                        if(row_index == 1):
                            #val = line
                            if( fieldDict.has_key('Away %s'%key) ):
                                _gameDataDict[game['gameid']][fieldDict['Away %s'%key]] = val
                            if(game_num == 1):
                              header_list.append('Away %s'%key)
                              if(debug):
                                print ("Adding header Away %s"%key)
                        elif(row_index == 5):
                            #val = line
                            if( fieldDict.has_key('Home %s'%key) ):
                                _gameDataDict[game['gameid']][fieldDict['Home %s'%key]] = val
                            if(game_num == 1):
                              header_list.append('Home %s'%key)
                              if(debug):
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
    print '%d%d'%(yr,gameEntry.week)
    away_games_played = max ( _teamRecord[teams[gameEntry.away_team]]['%d%d'%(season,gameEntry.week)]['wins']   + 
                              _teamRecord[teams[gameEntry.away_team]]['%d%d'%(season,gameEntry.week)]['losses'] + 
                              _teamRecord[teams[gameEntry.away_team]]['%d%d'%(season,gameEntry.week)]['ties'] - 1, 1)
    home_games_played = max( _teamRecord[teams[gameEntry.home_team]]['%d%d'%(season,gameEntry.week)]['wins']   + 
                             _teamRecord[teams[gameEntry.home_team]]['%d%d'%(season,gameEntry.week)]['losses'] + 
                             _teamRecord[teams[gameEntry.home_team]]['%d%d'%(season,gameEntry.week)]['ties'] - 1, 1)

    if ( gameEntry.away_team_score > gameEntry.home_team_score ):
        away_wins =  _teamRecord[teams[gameEntry.away_team]]['%d%d'%(season,gameEntry.week)]['wins'] - 1
        home_wins =  _teamRecord[teams[gameEntry.home_team]]['%d%d'%(season,gameEntry.week)]['wins']
    elif( gameEntry.away_team_score < gameEntry.home_team_score ): 
        away_wins =  _teamRecord[teams[gameEntry.away_team]]['%d%d'%(season,gameEntry.week)]['wins']
        home_wins =  _teamRecord[teams[gameEntry.home_team]]['%d%d'%(season,gameEntry.week)]['wins'] - 1
    else:
        away_wins =  _teamRecord[teams[gameEntry.away_team]]['%d%d'%(season,gameEntry.week)]['wins'] - 1
        home_wins =  _teamRecord[teams[gameEntry.home_team]]['%d%d'%(season,gameEntry.week)]['wins'] - 1
    
    gameEntry.away_team_record = (1.0 * away_wins)/away_games_played
    gameEntry.home_team_record = (1.0 * home_wins)/home_games_played

def updateGameTable():
    for gameid,game in _gameDataDict.iteritems():
        print gameid
        gameEntries = Games.objects.filter(gameid = gameid)
        if ( gameEntries.count() > 0  and not _overwrite):
            print "%d found, skipping"%gameid
            continue
        elif ( gameEntries.count() > 0  and _overwrite):
            print "%d found"%gameid
            gameEntry = gameEntries[0]
        else:
            print "%d not found"%gameid
            gameEntry = Games()
            gameEntry.gameid = gameid

        yr = int(str(gameid)[0:4])
        month = int(str(gameid)[4:6])
        date = int(str(gameid)[6:8])
        fulldate = '%s-%s-%s'%(yr,month,date)
        gameEntry.date = fulldate
        if ( month > 6 ):
            gameEntry.season = yr
        else:
            gameEntry.season = yr - 1

        for key,val in game.iteritems():
            if ( gameEntry.__dict__.has_key(key) ):
                print 'setting %s to %s'%(str(key),str(val))
                if ( key not in ['away_team', 'home_team'] ):
                    gameEntry.__dict__[key] = val
                else:
                    gameEntry.__dict__[key] = teams.index(val)
        getRecords( gameEntry )
        # FIXME!! find real values
        gameEntry.stadium = 0
        gameEntry.fieldtype = 0
        gameEntry.away_coach = 0
        gameEntry.home_coach = 0
        gameEntry.save()
    
#
# for typical usage, we only need current players
# since we will be running regularly
def getCurrentRosterLinks():
    print 'in getCurrentRosterLinks'
    fh = url.urlopen('http://www.nfl.com/players/search?category=team&playerType=current')
    for line in fh.readlines():
        line_re = re.search("a href=\"(.*players.search.category=team.*;filter.*playerType=current)\"", line)
        if line_re:
            roster_link = re.subn('amp;','', str(line_re.group(1)))[0]
            print 'adding %s to roster links'%roster_link
            _rosterLinks.append("http://www.nfl.com%s"%roster_link)

def getCurrentPlayersFromRosterLinks():
    print 'In getCurrentPlayersFromRosterLinks'
    for link in _rosterLinks:
        print 'opening %s'%link
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
    print "In updatePlayers"
    for player in _playerList:
        if ( Players.objects.filter(playerid=player['id']).count() == 0):
            if ( Players.objects.filter(lastname = player['lastname'].lower(), firstname=player['firstname'].lower(), position=positions.index(player['position'])).count() != 0 ):
                matchingPlayers = Players.objects.filter(lastname = player['lastname'].lower(), firstname=player['firstname'].lower(), position=positions.index(player['position']))
                if ( not _mvOldPlayerIds ):
                    print "Warning!!! %d players with same name/position (%s %s) exist.  Atleast one with diff. id (%d vs %d).  Skipping"% (
                        matchingPlayers.count(), player['firstname'].lower(), player['lastname'].lower(), matchingPlayers[0].playerid, player['id']
                    )
                    continue
                else:
                    movePlayer( matchingPlayers[0].playerid, player['id'] ) 
                    continue
            print 'Adding %s %s to player db'%( player['firstname'].lower(), player['lastname'].lower() )
            playerInst = Players()
            playerInst.playerid = player['id']
            playerInst.lastname = player['lastname'].lower()
            playerInst.firstname = player['firstname'].lower()
            playerInst.position =  positions.index(player['position'])
            # FIXME : Add Birthdate
            playerInst.birthdate = '1900-01-01'
            playerInst.save()
        playerEntries = Players.objects.filter(lastname=player['lastname'].lower(), firstname=player['firstname'].lower(), position=positions.index(player['position']))
        if ( playerEntries.count() > 1 ):
	    combineMultipleEntries(playerEntries, player)

def getStatsFromGamelogs():
    for player in _playerList:
        # Different positions have different stats/data formatted differently
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
            print "No stat collection for position %s"%position
            hasStats = False

        #First find all seasons a player played in
        try:
            gamelog = url.urlopen('http://www.nfl.com/player/%s/%d/gamelogs/'%(player['fullname'],player['id']))
            gamelogarray = gamelog.readlines()
        except:
            print 'cant open http://www.nfl.com/player/%s/%d/gamelogs/'%(player['fullname'],player['id'])
            continue
        season_select = False
        past_seasons = []
        for line in gamelogarray:
            if(line.count('<strong>Game Log:') > 0):
              season_select = True
              print 'season select begins!'
            elif(season_select and line.count('<option value=') > 0):
              line_re = re.search(r'value=.(\d+).>',line)
              if(line_re):
                past_seasons.append(int(line_re.group(1)))
            elif(season_select and line.count('</select>') > 0):
              season_select = False
              print 'past seasons:'
              print past_seasons

        seasonList = past_seasons
        seasonList.append(_currentSeason)
        # iterate over all seasons, looking for missing gameplayers
        for season in seasonList:
            if (season < minyear or season > maxyear):
                continue
            try:
                gamelog = url.urlopen('http://www.nfl.com/player/%s/%d/gamelogs/?season=%d'%(player['fullname'], player['id'], season))
                gamelogarray = gamelog.readlines()
            except:
                print 'cant open http://www.nfl.com/player/%s/%d/gamelogs/season=%d'%(player['fullname'],player['id'],season)
                continue
            reg_season = False
            intable = False
            for line in gamelogarray:
                if(line.count('Regular Season') > 0 and _seasonMode == 'regularseason' or 
                     line.count('Postseason')>0 and _seasonMode == 'postseason'
                    ):
                  print 'Season Sect begins!'
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
                        if ( debug ):
                            print "player %d not in db, skipping"%player['id']
                        intable = False
                        continue
                    if ( gameInst.count() == 0 ):
                        if ( debug ):
                            print "Game %d not in db, skipping"%gameid
                        intable = False
                        continue
                    gamePlayerQuery = GamePlayers.objects.filter(gameid = gameInst[0], playerid = playerInst[0] )
                    if( gamePlayerQuery.count() != 0 ):
                        if (  not _overwrite and gameStatClass.objects.filter( gameplayer = gamePlayerQuery[0] ) ):
                            if ( debug ):
                                print "Game %d player %d already in db, skipping"%( gameid, player['id'] )
                            intable = False
                            continue
                        else:
                            gamePlayerInst = GamePlayers.objects.filter(gameid = gameInst[0], playerid = playerInst[0])[0]
                    else:
                        gamePlayerInst = GamePlayers()
                        gamePlayerInst.gameid   = gameInst[0]
                        gamePlayerInst.playerid = playerInst[0]
                    if ( hasStats ):
                        print "adding Game %d player %s to db"%( gameid, player['fullname'] )
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
                      print 'saving gamestat for player %s'%player['fullname']
                      gamePlayerInst.save()
                      if ( hasStats ):
                          try: 
                              gameStatInst.save()
                          except:
                              print 'failed to save gamestat for player %s'%player['fullname']
                if(reg_season and line.count('TOTAL') > 0):
                    reg_season = False
                    if ( intable ):
                        intable = False
                        print 'saving gamestat for player %s'%player['fullname']
                        gamePlayerInst.save()
                        if ( hasStats ):
                            try: 
                                gameStatInst.save()
                            except:
                                print 'failed to save gamestat for player %s'%player['fullname']
        
            
#
# Main
#

# game data
if ( _updateGames ):
    getAllGameLinks()
    getGameDictListFromGameLinks()
    getGameDataDict()
    updateGameTable()

# player data
if ( _updatePlayers ):
    getCurrentRosterLinks()
    getCurrentPlayersFromRosterLinks()
    updatePlayers()
    getStatsFromGamelogs()

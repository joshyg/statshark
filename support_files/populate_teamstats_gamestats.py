#!/usr/bin/python
from teamstats.models import *
import csv
from decimal import Decimal

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
  'QB',#20
  'RB',
  'SAF',
  'SS',
  'T',
  'TE',
  'WR',
  #following is generic defense, used for pregc stats where i dont know exct pos _yet_
  'DEF',#27
  #following is generic RBWR, used for pregc stats where i dont know exct pos _yet_
  'RBWR',
  #following is generic nostat, used for pregc stats where i dont know exct pos _yet_
  'NA',
  ]
teams = [
"ARI",
"ATL",
"BAL",
"BUF",
"CAR",
"CHI",
"CIN",
"CLE",
"DAL",
"DEN",
"DET",
"GB",
"HOU",
"IND",
"JAC",
"KC",
"MIA",
"MIN",
"NE",
"NO",
"NYG",
"NYJ",
"OAK",
"PHI",
"PIT",
"SD",
"SF",
"SEA",
"STL",
"TB",
"TEN",
"WAS",
##following teams no longer exist
##initially i mismapped extinct teams, this was my mapping:
##"Los Angeles Rams",
##"Los Angeles Raiders",
##"Houston Oilers",
##"St Louis Cardinals"
##correct mapping:
"Los Angeles Rams",
"Los Angeles Raiders",
"Houston Oilers",
"Tennessee Oilers",
"St Louis Cardinals",
"Phoenix Cardinals",
"Baltimore Colts"
]

def get_opponent(tm,season):
  if(tm == "HOU" and season <=1998): 
    return teams.index("Houston Oilers")
  elif(tm == "TEN" and season < 1997): 
    return teams.index("Houston Oilers")
  elif(tm == "TEN" and (season == 1998 or season == 1997)): 
    return teams.index("Tennessee Oilers")
  elif(tm == "STL" and season <=1994): 
    return teams.index("Los Angeles Rams")
  elif(tm == "ARI" and season <=1987): 
    return teams.index("St Louis Cardinals")
  elif(tm == "ARI" and season <=1993): 
    return teams.index("Phoenix Cardinals")
  elif(tm == "OAK" and season <=1994 and season >= 1982): 
    return teams.index("Los Angeles Raiders")
  elif(tm == "IND" and season <= 1983): 
    return teams.index("Baltimore Colts")
  else:
    if(teams.count(tm) > 0):
      return teams.index(tm)
    else:
      return -1
#position_array = ['RB','FB','QB','WR','TE'] 
mode = 'prehistorical'
gamemode = 'postseason'
#prehistorical mode looks at data from prehistorical_gamestats csv
if(mode != 'prehistorical'):
  if(mode == 'current'):
    position_array = ['RB','FB','WR','TE', 'QB', 'D'] 
    #position_array = ['D'] 
  else:
    #position_array = ['RB','QB','WR','TE'] 
    position_array = ['DB','DL', 'LB'] 
  for pos in position_array:
    if(mode == 'current'): 
      if(gamemode == 'regularseason'):
        csv_fh = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csv_files/current_%s_gamestats_map.csv'%pos, 'r')
      else:
        csv_fh = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csv_files/current_%s_playoff_gamestats_2012_map.csv'%pos, 'r')

    else:
      if(gamemode == 'regularseason'):
        csv_fh = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csv_files/historical_%s_gamestats_map.csv'%pos, 'r')
      else:
        csv_fh = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csv_files/historical_%s_playoff_gamestats_map.csv'%pos, 'r')

    player_csv_dict = csv.DictReader(csv_fh)
    count = 0
    gamestatarray = []
    firstline = True
    for line in player_csv_dict:
      if( not (
            #linebacker was thrown in RB sect
            (pos != 'D' and line['lastname'] == 'Keasey' and line['firstname'] == 'Zak') or
            (pos != 'D' and line['lastname'] == 'Marshall' and line['firstname'] == 'Torrance') or
            (pos != 'D' and line['lastname'] == 'Saleh' and line['firstname'] == 'Tarek') or
            (pos != 'D' and line['lastname'] == 'Schable' and line['firstname'] == 'A.J.') or
            (pos != 'D' and line['lastname'] == 'Curry' and line['firstname'] == 'Ronald') or
            (pos != 'D' and line['lastname'] == 'Joseph' and line['firstname'] == 'Kerry') or
            (pos != 'D' and line['lastname'] == 'Randall' and line['firstname'] == 'Marcus') or
            (pos != 'D' and line['lastname'] == 'Floyd' and line['firstname'] == 'Marquis') or
            (pos != 'D' and line['lastname'] == 'Tate' and line['firstname'] == 'Robert') or
            #guess he did play some receiver...
            (pos != 'D' and line['lastname'] == 'Sanders' and line['firstname'] == 'Deion') or
            #this guy is a snapper
            (line['lastname'] == 'Massey' and line['firstname'] == 'Chris') or
            #punter
            (line['lastname'] == 'Tupa' and line['firstname'] == 'Tom') or
            #kicker
            (line['lastname'] == 'Carpenter' and line['firstname'] == 'Dan') or
            (pos != 'TE' and line['lastname'] == 'Fasano' and line['firstname'] == 'Anthony') or
            (pos != 'P' and line['lastname'] == 'Fields' and line['firstname'] == 'Brandon') or
            (pos != 'WR' and line['lastname'] == 'Hartline' and line['firstname'] == 'Brian') or
            (pos != 'FB' and line['lastname'] == 'Lane' and line['firstname'] == 'Jorvorskie') or
            (pos != 'WR' and line['lastname'] == 'Matthews' and line['firstname'] == 'Rishard') or
            #dl
            (pos != 'D' and line['lastname'] == 'Brightful' and line['firstname'] == 'Lamont') or
            (pos != 'D' and line['lastname'] == 'O\'Neal' and line['firstname'] == 'Deltha') or
            ( pos != 'D' and line['lastname'] == 'Vrabel' and line['firstname'] == 'Mike') or
            #WR grouped with Def
            (line['lastname'] == 'Binns' and line['firstname'] == 'Armon') or
            ( pos != 'RB' and line['lastname'] == 'Bush' and line['firstname'] == 'Reggie') or
            ( pos != 'RB' and line['lastname'] == 'Miller' and line['firstname'] == 'Lamar') or 
            ( pos != 'D' and line['lastname'] == 'Young' and line['firstname'] == 'Darrel') 
          )
      ):
        print 'grabbing player: %s %s for gameid %s playerid=%s'% (line['firstname'],line['lastname'],line['gameid'],line['playergameid'])
        #if (firstline):
        #  print line.keys()
        #  firstline = False
        count = (count +1)%20
        try:
          #playerid = Players.objects.get(pk=int(line['playerid'].replace('00-', '')))
          playerid = int(line['playergameid'])
        except:
          print 'playerid %s does not exist'%line['playerid']
        try:
          gameid = int(line['gameid'])
        except:
          print 'gameid %s does not exist'%line['gameid']
        gparray = GamePlayers.objects.filter(gameid_id=gameid, playerid_id=playerid)
        if(len(gparray) > 1):
          print 'multiple entries for gameid %d playerid %d.  This must be fixed!!'%(gameid,playerid)
        elif(len(gparray) == 0):
          print 'entry for gameid %d playerid %d is missing.  fixing, rerun to add stats'%(gameid,playerid)
          new_gp = GamePlayers(gameid_id=gameid, playerid_id=playerid)
          new_gp.save()
        else:
          gp = gparray[0].pk
          if((len(RbWrGameStats.objects.filter(gameplayer_id=gp)) > 0 or 
             len(QbGameStats.objects.filter(gameplayer_id=gp)) > 0 or 
             len(DefGameStats.objects.filter(gameplayer_id=gp)) > 0)
             ):
            print 'stat for this gameplayer exists!'
          elif(pos in ['D','DB', 'LB', 'DL'] and  
               positions[Players.objects.get(pk=playerid).position] in ['QB', 'WR', 'RB', 'FB', 'TE', 'K', 'P']):
            print 'misplaced stat!'
          elif(pos in ['RB', 'WR', 'TE', 'FB']):
            newgs = RbWrGameStats(gameplayer_id=gp)
            for key in line.keys():
              print key
              print line[key]
              if(key not in ['playergameid','gameid','playerstatid','lastname','firstname',None]):
                if(line[key] != '--' and line[key] != [''] and line[key] != None and  line[key] != ''): 
                  if(key not in ['RushAvg','RecAvg','Rate','Avg']):
                    #print '%s %s %s'%(line['gameid'],line['playerstatid'],key)
                    newgs.__setattr__(key,int(line[key].replace('T','')))
                  else:
                    newgs.__setattr__(key,Decimal(line[key].replace('T','')))
                else:
                  newgs.__setattr__(key, 0) 
            gamestatarray.append(newgs)
            if(count == 0): 
              RbWrGameStats.objects.bulk_create(gamestatarray)
              gamestatarray = []
          elif(pos == 'QB'): 
            #print 'creating QB!'
            newgs = QbGameStats(gameplayer_id=gp)
            for key in line.keys():
              #print key
              #print line[key]
              if(key not in ['playergameid','gameid','playerstatid','lastname','firstname',None]):
                if(line[key] != '--' and line[key] != [''] and line[key] != '' and line[key] != None): 
                  if(key not in ['Avg','RushAvg','RecAvg','Rate','Pct']):
                    #print key
                    #if(key == 'RushAtt'):
                    #  print '%s %s %s %s'%(line['gameid'],line['playerstatid'],key,line[key])
                    newgs.__setattr__(key,int(line[key].replace('T','')))
                    newgs.__setattr__(key,int(line[key].replace('T','')))
                  else:
                    newgs.__setattr__(key,Decimal(line[key].replace('T','')))
                      
                else:
                  newgs.__setattr__(key,0 )
            gamestatarray.append(newgs)
            if(count == 0): 
              print 'bulk creating'
              QbGameStats.objects.bulk_create(gamestatarray)
              gamestatarray = []
          else:
            #print 'creating QB!'
            newgs = DefGameStats(gameplayer_id=gp)
            for key in line.keys():
              print key
              print line[key]
              if(key not in ['playergameid','gameid','playerstatid','lastname','firstname',None]):
                if(line[key] != '--' and line[key] != [''] and line[key] != '' and line[key] != None): 
                  if(key not in ['Avg','Sck']):
                    #print key
                    #if(key == 'RushAtt'):
                    #  print '%s %s %s %s'%(line['gameid'],line['playerstatid'],key,line[key])
                    newgs.__setattr__(key,int(line[key].replace('T','')))
                    newgs.__setattr__(key,int(line[key].replace('T','')))
                  else:
                    newgs.__setattr__(key,Decimal(line[key].replace('T','')))
                      
                else:
                  newgs.__setattr__(key,0 )
            gamestatarray.append(newgs)
            if(count == 0): 
              print 'bulk creating'
              DefGameStats.objects.bulk_create(gamestatarray)
              gamestatarray = []
    if(pos in ['RB','WR','TE', 'FB']):
      RbWrGameStats.objects.bulk_create(gamestatarray)
    elif(pos == 'QB'):
      QbGameStats.objects.bulk_create(gamestatarray)
    else:
      DefGameStats.objects.bulk_create(gamestatarray)
else:
  #csv_fh = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csv_files/prehistorical_gamestats_rev5.csv', 'r')
  csv_fh = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csv_files/current_players_prehistorical.csv', 'r')
  err = open('current_players_prehistorical_gamestats_errs', 'w')
  count = 0
  qbgamestatarray = []
  rbwrgamestatarray = []
  defgamestatarray = []
  linenum = 0
  playerfound = False
  for line in csv_fh:
    linenum +=1 
    if(linenum >= 0):
      line_array = line.split(',')
      if(line_array.count('Result') > 0):
        line_array.remove('Result')
      if(line_array[0] == 'Player'):
        pos = 'nostats'
        playerfound = False
        playerid = int(line_array[1])
        lastname = line_array[2].lower()
        firstname = line_array[3].lower()
        season = int(line_array[4])
        #print 'grabbing %s %s'%(firstname, lastname)
        if(Players.objects.filter(playerid=playerid,lastname=lastname,firstname=firstname).exists()):
          player = Players.objects.get(playerid=playerid,lastname=lastname,firstname=firstname)
          playerfound = True
          print 'player %s %s, playerid %d'%(player.firstname,player.lastname,player.playerid)
        elif(Players.objects.filter(lastname=lastname,firstname=firstname).exists()):
          if(Players.objects.filter(lastname=lastname,firstname=firstname).count() == 1):
            player = Players.objects.get(lastname=lastname,firstname=firstname)
            playerfound = True
            print 'player %s %s, playerid %d'%(player.firstname,player.lastname,player.playerid)
          else:
            err.write('multiple players named %s %s, not enough info in tis file to determine which one this is\n'%(firstname, lastname))
        else:
          err.write('no player in db named %s %s\n'%(firstname, lastname))
      elif(line_array[0] == 'WK' and playerfound and len(line_array) >= 15):
        if(line_array[14] == 'Rate'):
          if(positions[player.position] == 'QB'):
            pos = 'QB' 
            params = ['G','GS','Comp','Att','Pct','Yds','Avg',
                     'TD','Int','Sck','SckY','Rate','RushAtt',
                     'RushYds','RushAvg','RushTD','FUM','Lost']
          else:
            err.write('%s %s playerid %d at position %s does not match db player of same name.  Must be duplicate name'%(firstname,lastname,playerid,positions[player.position]))
            pos = 'nostats'
        elif(line_array[5] == 'Rec'):
          if(positions[player.position] in ['WR','TE', 'RBWR']):
            pos = 'WR' 
            params = ['G','GS','Rec','RecYds','RecAvg','RecLng','RecTD',
                    'RushAtt','RushYds','RushAvg','RushLng','RushTD','FUM','Lost']
          else:
            err.write('%s %s playerid %d at position %s does not match db player of same name.  Must be duplicate name'%(firstname,lastname,playerid,positions[player.position]))
            pos = 'nostats'
        elif(line_array[5] == 'Att'):
          if(positions[player.position] in ['RB','FB', 'RBWR']):
            pos = 'RB' 
            params = ['G','GS','RushAtt','RushYds','RushAvg','RushLng','RushTD', 
                    'Rec','RecYds','RecAvg','RecLng','RecTD','FUM','Lost']
          else:
            err.write('%s %s playerid %d at position %s does not match db player of same name.  Must be duplicate name'%(firstname,lastname,playerid,positions[player.position]))
            pos = 'nostats'
        elif(line_array[5] == 'Comb'):
          if(positions[player.position] in ['D','DB', 'LB', 'DL', 'DEF', 'CB', 'DE','DL','DT','FS','ILB','LS','MLB','NT','OLB','SAF','SS']):
            pos = 'DEF' 
            params = ['G','GS','CombTck','Tck','AstTck','Sck','Sfty','PDef','Int','Yds','Avg','Lng','TD','FF']
          else:
            err.write('%s %s playerid %d at position %s does not match db player of same name.  Must be duplicate name'%(firstname,lastname,playerid,positions[player.position]))
            pos = 'nostats'
        else:
          pos = 'nostats'
      elif(line_array[1] != 'Bye' and playerfound):
        #print 'stat line, pos = %s'%pos
        if(pos != 'nostats'):
          gameplayerfound = False
          week = int(line_array[0])
          opponent = get_opponent(line_array[2],season)
          month_day = line_array[1].split('/')
          month = int(month_day[0])
          day = int(month_day[1])
          if(int(month_day[0]) <6):
            year = season+1
          else:
            year = season
          fulldate = "%s-%s-%s"%(year,month_day[0],month_day[1])
          homequery = Games.objects.filter(date=fulldate,away_team=opponent)
          awayquery = Games.objects.filter(date=fulldate,home_team=opponent)
          #sbquery = Games.objects.filter(date=fulldate,home_team=opponent)
          if(homequery.count() == 1 and awayquery.count() == 0):
            if(GamePlayers.objects.filter(playerid_id=player.playerid,gameid_id=homequery[0].gameid).exists()):
              count = (count +1)%30
              gameplayer = GamePlayers.objects.filter(playerid_id=player.playerid,gameid_id=homequery[0].gameid)[0]
              gameplayerfound=True
              print('adding gamestat for %s %s position %s'%(firstname, lastname, positions[player.position]))
          elif(homequery.count() == 0 and awayquery.count() == 1):
            if(GamePlayers.objects.filter(playerid_id=player.playerid,gameid_id=awayquery[0].gameid).exists()):
              count = (count +1)%30
              gameplayer = GamePlayers.objects.filter(playerid_id=player.playerid,gameid_id=awayquery[0].gameid)[0]
              gameplayerfound=True
              print('adding gamestat for %s %s position %s'%(firstname, lastname, positions[player.position]))
          elif(homequery.count() == 1 and awayquery.count() == 1):
            err.write('Appears as if team is home and away in the same week.  home gameid = %d away gameid = %d\n'%(homequery[0].gameid,awayquery[0].gameid))
            print('Appears as if team is home and away in the same week.  home gameid = %d away gameid = %d'%(homequery[0].gameid,awayquery[0].gameid))
          elif(homequery.count() > 1 or awayquery.count() > 1):
            err.write('Appears as if team is playing more than 1 game in the same week.  opponent = %s week = %d season = %d month = %d day = %d\n'%(line_array[2],week,season,month,day))
            print('Appears as if team is playing more than 1 game in the same week.  opponent = %s week = %d season = %d month = %d day = %d'%(line_array[2],week,season,month,day))
          elif(homequery.count() == 0 and awayquery.count() == 0):
            err.write('No matches for opponent in this week.  opponent = %s week = %d season = %d month = %d day = %d\n'%(teams[opponent],week,season,month,day))
            print('No matches for opponent in this week.  opponent = %s week = %d season = %d month = %d day = %d'%(teams[opponent],week,season,month,day))
          if(gameplayerfound):
            createstats = False
            if(positions[player.position] == "QB"):
              if(not QbGameStats.objects.filter(gameplayer=gameplayer).exists()):
                newgs = QbGameStats(gameplayer=gameplayer)
                createstats = True
            elif(positions[player.position] in ["RB","WR","TE","FB","RBWR"]):
              if(not RbWrGameStats.objects.filter(gameplayer=gameplayer).exists()):
                newgs = RbWrGameStats(gameplayer=gameplayer)
                createstats = True
            elif(positions[player.position] in ['D','DB', 'LB', 'DL', 'DEF', 'CB', 'DE','DL','DT','FS','ILB','LS','MLB','NT','OLB','SAF','SS']):
              if(not DefGameStats.objects.filter(gameplayer=gameplayer).exists()):
                newgs = DefGameStats(gameplayer=gameplayer)
                createstats = True
            else:
              err.write('player %s %s position %s doesnt fall into stat category\n'%(lastname,firstname,positions[player.position]))
            if(createstats):
              paramindex = 3
              for key in params:
                #print key
                if(line_array[paramindex] != '--' and line_array[paramindex] != [''] and line_array[paramindex] != '' and line_array[paramindex] != None): 
                  if(key not in ['Avg','RushAvg','RecAvg','Rate','Pct', 'Sck']):
                    newgs.__setattr__(key,int(line_array[paramindex].replace('T','')))
                    newgs.__setattr__(key,int(line_array[paramindex].replace('T','')))
                  else:
                    newgs.__setattr__(key,Decimal(line_array[paramindex].replace('T','')))
                      
                else:
                  newgs.__setattr__(key,0 )
                paramindex += 1 
              if(positions[player.position] == "QB"):
                qbgamestatarray.append(newgs)
              elif(positions[player.position] in ["RB","WR","TE","FB","RBWR"]):
                rbwrgamestatarray.append(newgs)
              elif(positions[player.position] in ['D','DB', 'LB', 'DL', 'DEF', 'CB', 'DE','DL','DT','FS','ILB','LS','MLB','NT','OLB','SAF','SS']):
                defgamestatarray.append(newgs)
              if(len(qbgamestatarray) >= 20 or len(rbwrgamestatarray) >= 20 or len(defgamestatarray) >= 20):
                if(qbgamestatarray != []):
                  QbGameStats.objects.bulk_create(qbgamestatarray) 
                if(rbwrgamestatarray != []):
                  RbWrGameStats.objects.bulk_create(rbwrgamestatarray) 
                if(defgamestatarray != []):
                  DefGameStats.objects.bulk_create(defgamestatarray) 
                qbgamestatarray = []
                rbwrgamestatarray = []
                defgamestatarray = []
              
  QbGameStats.objects.bulk_create(qbgamestatarray) 
  RbWrGameStats.objects.bulk_create(rbwrgamestatarray) 
  DefGameStats.objects.bulk_create(defgamestatarray) 
  err.close()

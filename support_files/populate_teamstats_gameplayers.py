#!/usr/bin/python
from teamstats.models import GamePlayers,Games,Players
import csv
import datetime
from datetime import date
import re

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

mode = 'pregc'
if(mode == 'gc'):  
  print "hi"
  #csv_fh = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csvs/game_player_db.csv', 'r')
  csv_fh = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csv_files/playoff_game_player_db.csv', 'r')
  player_csv_dict = csv.DictReader(csv_fh)
  count = 0
  gameplayerarray = []
  for line in player_csv_dict:
    count = (count +1)%30
    try:
      #playerid = Players.objects.get(pk=int(line['playerid'].replace('00-', '')))
      playerid = int(line['playerid'].replace('00-', ''))
    except:
      print 'playerid %s does not exist'%line['playerid']
    try:
      gameid = int(line['gameid'])
    except:
      print 'gameid %s does not exist'%line['gameid']
    away = int(line['away'])
    if(len(GamePlayers.objects.filter(gameid_id=gameid, playerid_id=playerid)) == 0):
      newgameplayer = GamePlayers(playerid_id=playerid,gameid_id=gameid,away=away) 
      gameplayerarray.append(newgameplayer)
      if(count == 0):
        GamePlayers.objects.bulk_create(gameplayerarray)
        gameplayerarray = []
  GamePlayers.objects.bulk_create(gameplayerarray)
else:
  #pregc
  csv_fh = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csv_files/current_players_prehistorical.csv', 'r')
  """
  Player,2508148,Abbott,Vince,1988
  WK,Game     Date,Opp,G,GS,Blk,Lng,FG Att,FGM,Pct,XPM,XP Att,Pct,Blk,KO,Avg,TB,Ret,Avg,
  1,09/04,OAK,1,--,0,33,2,2,100.0,1,1,100.0,0,--,--,--,--,--,
  """     
  err = open('current_players_prehistorical_errs', 'w')
  gameplayerarray = []
  count = 0
  grab_gameplayers = False
  linenum = 0
  singleplayer = False
  for line in csv_fh:
    linenum +=1 
    if(linenum >= 0):
      if(line.find('Player,') == 0):
        count = (count +1)%100
        line_array = line.split(',') 
        playerid = int(line_array[1])
        ln = line_array[2].lower()
        fn = line_array[3].lower()
        season = int(line_array[4])
        if(not singleplayer):
          playerquery = Players.objects.filter(lastname=ln,firstname=fn)
        else:
          #using player id for manual entry of duplicate player
          print 'singleplayer mode, playerid=%d'%playerid
          playerquery = Players.objects.filter(lastname=ln,firstname=fn, playerid=playerid)
        if(playerquery.exists()):
          if(playerquery.count()==1 or singleplayer):
            player = playerquery[0]
            playerid = player.playerid
            grab_gameplayers = True
            print('grabbing games for %s %s'%(fn, ln))
          else:
            err.write('multiple entries for %s %s\n'%(fn, ln))
            grab_gameplayers = False
        else:
          err.write('cant find %s %s in db\n'%(fn, ln))
          grab_gameplayers = False
      elif(re.search('^\d+,',line) and line.find(',Bye,') == -1 and grab_gameplayers):  
        #print line
        line_array = line.split(',')
        week = int(line_array[0])
        month_day_array = line_array[1].split('/')
        month = int(month_day_array[0])
        day = int(month_day_array[1])
        if(month < 6):
          year = season + 1
        else:
          year = season
        if(line_array[2] not in ['0','1']):
          opponent=get_opponent(line_array[2],season)
        elif(Games.objects.filter(date=date(year,month,day)).count() == 1):
          print "possibly poorly formatted superbowl game"
          #noticed some superbowl entries have no opponent, fortunately these have 1 game on that date!
          game = Games.objects.get(date=date(year,month,day))
          if(game.away_team == playerteam):
            opponent = game.home_team
          elif(game.home_team == playerteam):
            opponent = game.away_team
          else:
            opponent = -1
        else:
          opponent = -1
        if(opponent != -1):
          homequery = Games.objects.filter(date=date(year,month,day),away_team=opponent)
          awayquery = Games.objects.filter(date=date(year,month,day),home_team=opponent)
          if(homequery.count() == 1 and awayquery.count() == 0):
            playerteam = Games.objects.get(date=date(year,month,day),away_team=opponent).home_team
            if(not GamePlayers.objects.filter(playerid_id=playerid,gameid_id=homequery[0].gameid).exists()):
              count = (count +1)%30
              newgameplayer = GamePlayers(playerid_id=playerid,gameid_id=homequery[0].gameid,away=0) 
              gameplayerarray.append(newgameplayer)
              print('adding game for %s %s'%(fn, ln))
          elif(homequery.count() == 0 and awayquery.count() == 1):
            playerteam = Games.objects.get(date=date(year,month,day),home_team=opponent).away_team
            if(not GamePlayers.objects.filter(playerid_id=playerid,gameid_id=awayquery[0].gameid).exists()):
              count = (count +1)%30
              newgameplayer = GamePlayers(playerid_id=playerid,gameid_id=awayquery[0].gameid,away=1) 
              gameplayerarray.append(newgameplayer)
              print('adding game for %s %s'%(fn, ln))
          elif(homequery.count() == 1 and awayquery.count() == 1):
            err.write('Appears as if team is home and away in the same week.  home gameid = %d away gameid = %d\n'%(homequery[0].gameid,awayquery[0].gameid))
            print('Appears as if team is home and away in the same week.  home gameid = %d away gameid = %d'%(homequery[0].gameid,awayquery[0].gameid))
          elif(homequery.count() > 1 or awayquery.count() > 1):
            err.write('Appears as if team is playing more than 1 game in the same week.  opponent = %s week = %d season = %d month = %d day = %d\n'%(line_array[2],week,season,month,day))
            print('Appears as if team is playing more than 1 game in the same week.  opponent = %s week = %d season = %d month = %d day = %d'%(line_array[2],week,season,month,day))
          elif(homequery.count() == 0 and awayquery.count() == 0):
            err.write('No matches for opponent in this week.  opponent = %s week = %d season = %d month = %d day = %d\n'%(teams[opponent],week,season,month,day))
            print('No matches for opponent in this week.  opponent = %s week = %d season = %d month = %d day = %d'%(teams[opponent],week,season,month,day))
          if(count == 0):
            GamePlayers.objects.bulk_create(gameplayerarray)
            gameplayerarray = []
  GamePlayers.objects.bulk_create(gameplayerarray)
          
        
        


        #newgameplayer = GamePlayers(playerid_id=playerid,gameid_id=gameid,away=away) 
  

  

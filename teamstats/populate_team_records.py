#!/usr/bin/python
from teamstats.models import Games
from decimal import *
import sqlite3
teams = [
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
mode = 'sql'
if(mode == 'sql'):
  conn = sqlite3.connect('../teamstats.db')
  c = conn.cursor()
err = open('team_record_errs', 'w')
for team in teams:
  team_index = teams.index(team)
  for year in range(1966, 2001):
    wins = 0
    games_played = 0#tam doesnt play every week
    for week in range(1,18):
      if(len(Games.objects.filter(season=year,week=week,away_team=team_index))>0):
        game = Games.objects.filter(season=year,week=week,away_team=team_index)[0]
        games_played += 1
        if(games_played == 1):
          #getcontext().prec=1
          #game.away_team_record = Decimal(0.0) 
          print "game 1"
        else:
          getcontext().prec=3
          game.away_team_record = Decimal(str(Decimal(wins)/Decimal(games_played-1))) 
          #if(game.away_team_record < .0625):
          #  game.away_team_record = Decimal(0.0)
          #no need to save when record 0, we already have that in there
          print game.away_team_record
          print '%d/%d'%(wins,games_played-1)
          if(mode == 'django'):
            if(wins != 0):
              try:
                game.save()
              except:
                err.write('save failed on season %d week %d home_team %d wins %d games played %d\n'%(year,week,team_index, wins, games_played-1))
          else:
            try:
              c.execute('update teamstats_games set away_team_record=%.3f where gameid=%d'%(game.away_team_record,game.gameid))
            except:
              err.write('save failed on season %d week %d home_team %d wins %d games played %d\n'%(year,week,team_index, wins, games_played-1))
        if(game.away_team_score > game.home_team_score):
          wins += 1
      elif(len(Games.objects.filter(season=year,week=week,home_team=team_index))>0):
        game = Games.objects.filter(season=year,week=week,home_team=team_index)[0]
        games_played += 1
        if(games_played == 1):
          #getcontext().prec=1
          #game.home_team_record = Decimal(0.0) 
          print "game 1"
        else:
          getcontext().prec=3
          game.home_team_record = Decimal(str(Decimal(wins)/Decimal(games_played-1)))
          #if(game.home_team_record < .0625):
          #  game.home_team_record = Decimal(0.0)
          #no need to save when record 0, we already have that in there
          print game.home_team_record
          print '%d/%d'%(wins,games_played-1)
          if(mode == 'django'):
            if(wins != 0):
              try:
                game.save()
              except:
                err.write('save failed on season %d week %d away_team %d wins %d games played %d\n'%(year,week,team_index, wins, games_played-1))
          else:
            try:
              c.execute('update teamstats_games set home_team_record=%.3f where gameid=%d'%(game.home_team_record,game.gameid))
            except:
              err.write('save failed on season %d week %d home_team %d wins %d games played %d\n'%(year,week,team_index, wins, games_played-1))
        if(game.away_team_score < game.home_team_score):
          wins += 1
conn.commit()
conn.close()
         
         
          

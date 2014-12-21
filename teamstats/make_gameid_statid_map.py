from teamstats.models import GamePlayers,Players
import csv
mode = 'historical'
date = '1_3'
if(mode == 'current'):
  position_array = ['RB','FB','QB','TE','WR', 'D']
  game_stat_playerid_map = open('game_stat_playerid_map.csv', 'w')
  nonunique_playernames  = open('current_nonunique_playernames.csv', 'w')
  missing_playernames  = open('current_missing_playernames.csv', 'w')
else:
  position_array = ['RB','QB','TE','WR', 'DL', 'DB', 'LB']
  game_stat_playerid_map = open('historical_game_stat_playerid_map.csv', 'w')
  nonunique_playernames  = open('historical_nonunique_playernames_%s.csv'%date, 'w')
  missing_playernames  = open('historical_missing_playernames_%s.csv'%date, 'w')

game_stat_playerid_map.write('gameplayerid,statplayerid,lastname,firstname\n')
nonunique_playernames.write('lastname,firstname,count\n')
players_added = []
for position in position_array:
  #gamestat_csvdict = csv.DictReader(open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csv_files/current_%s_gamestats.csv'%position,'r'))
  gamestat_csvdict = csv.DictReader(open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csv_files/%s_%s_gamestats.csv'%(mode,position),'r'))
  for line in gamestat_csvdict:
    if line['playerstatid'] not in players_added:
      players_added.append(line['playerstatid'])
      players = Players.objects.filter(lastname=line['lastname'].lower(), firstname=line['firstname'].lower())
      if(len(players) == 1):
        game_stat_playerid_map.write('%s,%s,%s,%s\n'%(players[0].pk, line['playerstatid'],line['lastname'].lower(),line['firstname'].lower()))
      elif(len(players) >= 2):
        nonunique_playernames.write('%s,%s,%s\n'%(line['lastname'].lower(),line['firstname'].lower(),len(players)))
      else:
        print '%s %s not found in db'%(line['firstname'].lower(), line['lastname'].lower())
        missing_playernames.write('%s %s not found in db\n'%(line['firstname'].lower(), line['lastname'].lower()))
        
game_stat_playerid_map.close()
nonunique_playernames.close()
missing_playernames.close()

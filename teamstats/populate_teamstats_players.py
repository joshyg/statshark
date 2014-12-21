#!/usr/bin/python
from teamstats.models import Players
import csv

class populate_teamstats_players():
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
  
  mode = 'pregc'
  print "hi"
  if(mode == 'gc'):
    csv_fh = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csvs/players.csv', 'r')
    player_csv_dict = csv.DictReader(csv_fh)
    
    count = 0
    playerarray = []
    for line in player_csv_dict:
      count = (count +1)%100
      playerid = int(line['playerid'].replace('00-', ''))
      if(len(Players.objects.filter(playerid=playerid)) == 1):
        lastname = line['ln'].lower()
        firstname = line['fn'].lower()
        position = positions.index(line['pos'])
        bd_array = line['bdate'].split('/')
        if(len(bd_array[0]) == 1):
          bd_array[0] = '0'+ bd_array[0] 
        if(len(bd_array[1]) == 1):
          bd_array[1] = '0'+ bd_array[1] 
        if(bd_array[0] == 'null' or bd_array[1] == 'null' or bd_array[2] == 'null'):
          bd = '2014-01-01'#this is the dummy bday for unknowns
        else:
          bd = ('%s-%s-%s'%( bd_array[2], bd_array[0], bd_array[1]))
        if(len(Players.objects.filter(playerid=playerid)) == 0):
          newplayer = Players(playerid=playerid, lastname=lastname,firstname=firstname, position=position, birthdate=bd)
          playerarray.append(newplayer)
          if(count == 0):
            Players.objects.bulk_create(playerarray)
            playerarray = []
      elif(len(Players.objects.filter(playerid=playerid)) > 1):
        print '%s %s has multiple entries'%(firstname,lastname) 
    Players.objects.bulk_create(playerarray)
  else:
    print 'pregc players!'
    #csv_fh = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csv_files/prehistorical_gamestats.csv', 'r')
    csv_fh = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/csv_files/prehistorical_gamestats_rev5.csv', 'r')
    err = open('prehistorical_player_errs_rev5', 'w')
    grab_position = False
    playerarray = []
    count = 0
    bd = '2014-01-01'#this is the dummy bday for unknowns
    lastplayerid = 0
    for line in csv_fh:
      if(line.find('Player,') == 0):
        count = (count +1)%100
        line_array = line.split(',') 
        playerid = int(line_array[1])
        ln = line_array[2].lower()
        fn = line_array[3].lower()
        if(Players.objects.filter(playerid=playerid,lastname=ln,firstname=fn).exists() or
           lastplayerid == playerid
          ):
          pass
        elif(Players.objects.filter(lastname=ln,firstname=fn).exists()):
          duplicate = Players.objects.filter(lastname=ln,firstname=fn) 
          err.write('%s %s with id %d is already in db with id %d\n'%(fn,ln,playerid,duplicate[0].playerid)) 
        elif(Players.objects.filter(playerid=playerid)):
          duplicate = Players.objects.filter(playerid=playerid)
          err.write('id %d already taken  by %s %s.  Cant be used for %s %s\n'%(playerid, duplicate[0].firstname, duplicate[0].lastname,fn,ln)) 
          print 'id %d already taken  by %s %s.  Cant be used for %s %s\n'%(playerid, duplicate[0].firstname, duplicate[0].lastname,fn,ln) 
        else:
          print 'creating %s %s'%(fn,ln)
          newplayer = Players(playerid=playerid, lastname=ln,firstname=fn, birthdate=bd)
          grab_position = True
          lastplayerid= playerid
      elif(grab_position):
        if(line.find('SFTY') != -1):
          newplayer.position = positions.index('DEF') 
        elif(line.find('Rate') != -1):
          newplayer.position = positions.index('QB') 
        elif(line.find('G,GS,Att') != -1):
          newplayer.position = positions.index('RB') 
        elif(line.find('G,GS,Rec') != -1):
          newplayer.position = positions.index('WR') 
        elif(line.find('FGM') != -1):
          newplayer.position = positions.index('K') 
        elif(line.find('G,GS')!= -1):
          newplayer.position = positions.index('NA') 
        playerarray.append(newplayer)
        grab_position = False
      if(count == 0):
        Players.objects.bulk_create(playerarray)
        playerarray = []
    Players.objects.bulk_create(playerarray)
    err.close()
        
       

          
  
  

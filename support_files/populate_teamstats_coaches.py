#!/usr/bin/python
from teamstats.models import Coaches, Games
from coach_list import coach_list
"""
count = 0
coach_array = []
for item in coach_list:
  name = item.split(' ')
  firstname = name[0].lower()
  lastname = name[1].lower()
  if(len(name) > 2):
    for i in range(2,len(name)):
      lastname += ' '
      lastname += name[i].lower()
  if(Coaches.objects.filter(firstname=firstname, lastname=lastname).exists()):
    print '%s %s already exists'%(firstname, lastname)
  else:
    coach_array.append(Coaches(firstname=firstname, lastname=lastname))
    count = (count + 1)%20
    if(count == 0):
      Coaches.objects.bulk_create(coach_array)
      coach_array = []
Coaches.objects.bulk_create(coach_array)
"""
    
gamemode = 'regularseason'
if(gamemode == 'regularseason'):
  coach_csv = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/nfldotcom/coach_games.csv', 'r')
else:
  coach_csv = open('/home/joshyg/nflbacktest/svn_nflbacktest/nflbacktest/support_files/nfldotcom/playoffs/coach_games.csv', 'r')
away = True
for line in coach_csv.readlines():
  if(line.find('cant open') == -1 ):
    line_array = line.split(',')
    gameid = int(line_array[0])
    name = line_array[1].split(' ')
    firstname = name[0].lower()
    lastname = name[1].lower()
    if(len(name) > 2):
      for i in range(2,len(name)):
        lastname += ' '
        lastname += name[i].lower()
    lastname = lastname[0:len(lastname)-1]
    if(Games.objects.filter(gameid=gameid).exists()):
      g = Games.objects.get(gameid=gameid)
      #print 'grab coach %s %s!'%(firstname,lastname)
      if(firstname != 'unknown'):
        c = Coaches.objects.get(lastname=lastname,firstname=firstname)
      
        if(away):
          g.away_coach = c.pk 
          away = False
        else:
          g.home_coach = c.pk 
          away = True
      else:
        if(away):
          g.away_coach = -1
          away = False
        else:
          g.home_coach = -1
          away = True
      g.date = '2014-01-01'
      g.save()
    else:
      print '%d is missing'%gameid
        
    
  
  

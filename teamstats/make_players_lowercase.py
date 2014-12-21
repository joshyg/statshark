#!/usr/bin/python
from teamstats.models import Players
import csv

print "hi"
playerlist = Players.objects.all()
for player in playerlist:
  if(player.lastname != player.lastname.lower() or player.firstname != player.firstname.lower()):
    Players.objects.filter(pk=player.pk).update(lastname =  player.lastname.lower())
    Players.objects.filter(pk=player.pk).update(firstname =  player.firstname.lower())
       
      
    
  
  

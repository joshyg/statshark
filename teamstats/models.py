from django.db import models

# Create your models here.
class Games(models.Model):
    gameid = models.IntegerField(primary_key=True)
    date = models.DateField('date of game')
    away_team = models.IntegerField(db_index=True)
    home_team = models.IntegerField(db_index=True)
    away_team_spread = models.DecimalField(decimal_places=1, max_digits=4)
    over_under = models.DecimalField(decimal_places=1, max_digits=4)
    away_team_score = models.IntegerField()
    home_team_score = models.IntegerField()
    home_team_record = models.DecimalField(decimal_places=3, max_digits=4)
    away_team_record = models.DecimalField(decimal_places=3, max_digits=4)
    week =   models.IntegerField(db_index=True)
    season = models.IntegerField(db_index=True)
    away_team_yards = models.IntegerField()
    home_team_yards = models.IntegerField()
    away_team_rushing_yards = models.IntegerField()
    home_team_rushing_yards = models.IntegerField()
    away_team_passing_yards = models.IntegerField()#for now lets make this net, later we can add gross
    home_team_passing_yards = models.IntegerField()#for now lets make this net, later we can add gross
    stadium = models.IntegerField()
    fieldtype = models.IntegerField()
    away_coach = models.IntegerField()
    home_coach = models.IntegerField()

class GameExtras(models.Model):
    game = models.OneToOneField(Games,primary_key=True)
    temperature = models.IntegerField(default=-100)
    humidity = models.IntegerField(default=0)
    windspeed = models.IntegerField(default=0)
    precipitation = models.IntegerField(default=0)
    attendance = models.IntegerField(default=0)
    starttime = models.TimeField(default='00:00')
  
class GameStreaks(models.Model):
    game = models.OneToOneField(Games,primary_key=True)
    away_team_win_streak = models.IntegerField()  
    home_team_win_streak = models.IntegerField()  
    away_team_ats_streak = models.IntegerField()  
    home_team_ats_streak = models.IntegerField()  

class Players(models.Model):
    playerid = models.IntegerField(primary_key=True)
    games = models.ManyToManyField(Games, through='GamePlayers')
    position = models.IntegerField()
    birthdate = models.DateField()
    lastname = models.CharField(max_length = 20, db_index=True)
    firstname = models.CharField(max_length = 20, db_index=True)

class GamePlayers(models.Model):
    gameid = models.ForeignKey(Games)
    playerid = models.ForeignKey(Players)
    away = models.BooleanField()

#G,GS,Rec,RecYds,RecAvg,REcLng,RecTD,FUM,Lost,RushAtt,RushYds,RushAvg,RushLng,RushTD
class RbWrGameStats(models.Model):
  gameplayer = models.OneToOneField(GamePlayers)
  G=models.BooleanField()
  GS=models.BooleanField()
  Rec=models.IntegerField()
  RecYds=models.IntegerField()
  RecAvg=models.DecimalField(decimal_places=1, max_digits=4)
  RecLng=models.IntegerField()
  RecTD=models.IntegerField()
  FUM=models.IntegerField()
  Lost=models.IntegerField()
  RushAtt=models.IntegerField()
  RushYds=models.IntegerField()
  RushAvg=models.DecimalField(decimal_places=1, max_digits=4)
  RushLng=models.IntegerField()
  RushTD=models.IntegerField()
  
# playergameid,gameid,playerstatid,lastname,firstname,G,GS,Comp,Att,Pct,Yds,Avg,TD,Int,Sck,SckY,Rate,Att,Yds,Avg,TD,FUM,Lost
class QbGameStats(models.Model):
  gameplayer = models.OneToOneField(GamePlayers)
  G=models.BooleanField()
  GS=models.BooleanField()
  Comp=models.IntegerField()
  Att=models.IntegerField()
  Pct=models.DecimalField(decimal_places=1, max_digits=4)
  Yds=models.IntegerField()
  Avg=models.DecimalField(decimal_places=1, max_digits=4)
  TD=models.IntegerField()
  Int=models.IntegerField()
  Sck=models.IntegerField()
  SckY=models.IntegerField()
  Rate=models.DecimalField(decimal_places=1, max_digits=4)
  RushAtt=models.IntegerField()
  RushYds=models.IntegerField()
  RushAvg=models.DecimalField(decimal_places=1, max_digits=4)
  RushTD=models.IntegerField()
  FUM=models.IntegerField()
  Lost=models.IntegerField()

class DefGameStats(models.Model):
  gameplayer = models.OneToOneField(GamePlayers)
  G=models.BooleanField()
  GS=models.BooleanField()
  CombTck=models.IntegerField()
  Tck=models.IntegerField()
  AstTck=models.IntegerField()
  Sck=models.DecimalField(decimal_places=1, max_digits=3)
  Sfty=models.IntegerField()
  PDef=models.IntegerField()
  Int=models.IntegerField()
  Yds=models.IntegerField()
  Avg=models.DecimalField(decimal_places=1, max_digits=4)
  Lng=models.IntegerField()
  TD=models.IntegerField()
  FF=models.IntegerField()
 

class Coaches(models.Model):
  firstname = models.CharField(max_length=20, db_index=True)
  lastname = models.CharField(max_length=20, db_index=True)

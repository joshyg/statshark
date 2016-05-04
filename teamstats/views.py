# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.context_processors import csrf
from teamstats.models import *
import json
from django.http import HttpResponse
from decimal import Decimal
from django.db import models
from django.db.models import Q
import cairo, math, random
import math, random
import cairoplot
from django.conf import settings
import time,datetime
import sys

plotting = True
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
afc_east = [
  'New England',
  'Buffalo',
  'NY Jets',
  'Miami'
]
afc_north = [
  'Baltimore',
  'Pittsburgh',
  'Cincinnati',
  'Cleveland'
]
afc_south = [
  'Houston',
  'Indianapolis',
  'Tennessee',
  'Jacksonville'
]
afc_west = [
  'Denver',
  'San Diego',
  'Oakland',
  'Kansas City'
]
afc = [
  'New England',
  'Buffalo',
  'NY Jets',
  'Miami',
  'Baltimore',
  'Pittsburgh',
  'Cincinnati',
  'Cleveland',
  'Houston',
  'Indianapolis',
  'Tennessee',
  'Jacksonville',
  'Denver',
  'San Diego',
  'Oakland',
  'Kansas City'
]
nfc_east = [
  'NY Giants',
  'Washington',
  'Dallas',
  'Philadelphia'
]

nfc_north = [
  'Green Bay',
  'Chicago',
  'Minnesota',
  'Detroit'
]
nfc_south = [
  'Atlanta',
  'Tampa Bay',
  'New Orleans',
  'Carolina'
]
nfc_west = [
  'San Francisco',
  'Seattle',
  'Arizona',
  'St. Louis'
]
nfc = [
  'NY Giants',
  'Washington',
  'Dallas',
  'Philadelphia',
  'Green Bay',
  'Chicago',
  'Minnesota',
  'Detroit',
  'Atlanta',
  'Tampa Bay',
  'New Orleans',
  'Carolina',
  'San Francisco',
  'Seattle',
  'Arizona',
  'St. Louis'
]
groups = [
  afc,
  afc_east,
  afc_north,
  afc_south,
  afc_west,
  nfc,
  nfc_east,
  nfc_north,
  nfc_south,
  nfc_west,
]

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

field_types=[
"grass",
"turf"
]

condition_types=[
"None",
"group",
"team",
"favoredBy",
"isHome",
"isAway",
"season",
"week",
"over_under",
"WinPercentage",
"player",
"coach",
"underdogOf",
"fieldtype",
"temperature",
"wind",
"humidity",
"WinStreak",
]

comp_types=[
">",
"=",
"<"
]


class QueryTracker:
    def __init__( self ):
        self.gameset = []
        self.games_def = []
        self.result_array = []
        self.final_result_array = []
        self.team_a_conditions_exist = False
        self.team_b_conditions_exist = False
        self.team_a_conditions = []
        self.team_b_conditions = []
        self.num_team_a_conditions = 0
        self.num_team_b_conditions = 0
        self.num_game_conditions = 0
        self.team_a_dict = {}
        self.team_a_list = []
        self.queried_players = []
        self.player_game_list = []
        # results
        self.teama_spreadwins=0
        self.teamb_spreadwins=0
        self.teama_wins=0
        self.teamb_wins=0
        self.over_wins=0
        self.teama_points=0
        self.teamb_points=0
        self.numgames=0.0
        self.numgamesint=0
        self.push_goes_to_bookie=False
        #response dict
        self.response = {}
        self.response['result_table'] = []
        self.response['teama_summary'] = []
        self.response['teamb_summary'] = []
        self.response['player_table'] = []
        self.response['players_with_stats'] = []
        self.response['qbs_with_stats'] = []
        self.response['defs_with_stats'] = []
        self.response['rbwrs_with_stats'] = []
        self.response['qb_avgs'] = []
        self.response['def_avgs'] = []
        self.response['rbwr_avgs'] = []
        self.response['qb_charts'] = []
        self.response['playerdata_charts'] = []
        self.response['rbwr_charts'] = []
        self.response['def_charts'] = []

        self.filter_dict = {
            'season' : self.filter_by_season,
            'week' : self.filter_by_week,
            'fieldtype' : self.filter_by_fieldtype,
            'temperature' : self.filter_by_temperature,
            'wind' : self.filter_by_wind,
            'humidity' : self.filter_by_humidity,
            'over_under' : self.filter_by_over_under,
            'group' : self.filter_by_group,
            'team' : self.filter_by_team,
            'underdogOf' : self.filter_by_spread,
            'favoredBy' : self.filter_by_spread,
            'WinPercentage' : self.filter_by_win_percentage,
            'WinStreak' : self.filter_by_win_streak,
            'coach' : self.filter_by_coach,
            'player' : self.filter_by_player,
            'opposition_group' : self.filter_by_opposition_group,
            'opposition_team' : self.filter_by_opposition_team,
            'opposition_WinPercentage' : self.filter_by_opposition_win_percentage,
            'opposition_WinStreak' : self.filter_by_opposition_win_streak,
            'opposition_coach' : self.filter_by_opposition_coach,
        }
      

    def query_wrapper( self, condition_list, item_type, **kwargs ):
        print( "check for %s conditions" % item_type )
        for entry in condition_list:
            if( entry['type'] in [ item_type, item_type.replace('opposition_', '') ] ):
                self.filter_dict[item_type]( entry, **kwargs )

    def init_team_a_dict( self ):
        #Lets first see if team a is restricted to home or away
        ( self.use_home_team, self.use_away_team ) = get_home_away_conditions( self.team_a_conditions, self.team_b_conditions )
        #initial home/away filtering can occur now
        #the following dict will keep track of which team in a given game is "team a"
        if(not self.use_home_team):
            for game in self.games_def:
                self.team_a_dict[game.pk] = game.away_team
        elif(not self.use_away_team):
            for game in self.games_def:
                self.team_a_dict[game.pk] = game.home_team

    def get_conditions( self, request ):
        for i in range(self.num_team_a_conditions):
            table = 'a_%d'%(i)
            comptype = table+"_comptype"
            print "Condition type  = %s"%condition_types[int(get_request_param(request,table,0))]
            print "Condition value  = %s"%get_request_param(request,table+'_value', 1)
            #print "Condition_type = %s value = %s"%(condition_types[int(get_request_param(request,table,0))],get_request_param(request,table+'_value', 1))
            self.team_a_conditions.append({'type':condition_types[int(get_request_param(request,table,0))], 'value':get_request_param(request,table+'_value', 1), 'comptype':comp_types[int(get_request_param(request,comptype,1))]})
            print "condition added"
        #treat game conditions as team a conditions
        for i in range(self.num_game_conditions):
            table = 'g_%d'%(i)
            comptype = table+"_comptype"
            print "Condition type  = %s"%condition_types[int(get_request_param(request,table,0))]
            print "Condition value  = %s"%get_request_param(request,table+'_value', 1)
            #print "Condition_type = %s value = %s"%(condition_types[int(get_request_param(request,table,0))],get_request_param(request,table+'_value', 1))
            self.team_a_conditions.append({'type':condition_types[int(get_request_param(request,table,0))], 'value':get_request_param(request,table+'_value', 1), 'comptype':comp_types[int(get_request_param(request,comptype,1))]})
            print "condition added"
        for i in range(self.num_team_b_conditions):
            table = 'b_%d'%(i)
            comptype = table+"_comptype"
            print comptype
            print "Condition type  = %s"%condition_types[int(get_request_param(request,table,0))]
            print "Condition value  = %s"%get_request_param(request,table+'_value', 1)
            self.team_b_conditions.append({'type':condition_types[int(get_request_param(request,table))], 'value':get_request_param(request,table+'_value', 1), 'comptype':comp_types[int(get_request_param(request,comptype,1))]})
        #adjust spread condition so that favored by and underdog of can be treated the same
        for item in self.team_a_conditions:
            if(item['type'] == "favoredBy"):
                print 'spread must be reversed'
                item['value'] = Decimal(-1)*Decimal(item['value'])
                item['comptype'] = reverseCompType(item['comptype'])
                print 'spread reversed spread must be %s %s'%(item['comptype'], str(item['value']))
        print "request params gathered, team a conditions are:"
        for item in self.team_a_conditions:
            print item 

    def filter_by_season( self, item ):
        print "about to compute season conditions"
        self.team_a_conditions_exist = True
        print "about to filter on comptype"
        if(item['comptype'] == '='):
            self.result_array = self.result_array.filter(season=int(item['value']))
        elif(item['comptype'] == '<'):
            self.result_array = self.result_array.filter(season__lt=int(item['value']))
        elif(item['comptype'] == '>'):
            self.result_array = self.result_array.filter(season__gt=int(item['value']))
        print( "season conditions complete current size of queryset is %d" % ( self.result_array.count() ) )
    
    def filter_by_week( self, item ):
        print "about to compute week conditions"
        self.team_a_conditions_exist = True
        print "about to filter on comptype"
        if(item['comptype'] == '='):
            if(int(item['value']) < 21):
                self.result_array = self.result_array.filter(week=int(item['value']))
            else:
                #some years the SuperBowl is wk 22
                self.result_array = self.result_array.filter(week__gte=21)
            
        elif(item['comptype'] == '<'):
            self.result_array = self.result_array.filter(week__lt=int(item['value']))
        elif(item['comptype'] == '>'):
            self.result_array = self.result_array.filter(week__gt=int(item['value']))
    
    def filter_by_fieldtype( self, item ):
        print "about to compute fieldtype conditions"
        self.team_a_conditions_exist = True
        self.result_array = self.result_array.filter(fieldtype=item['value'])
    
    def filter_by_temperature( self, item ):
        print "about to compute temperature conditions"
        tmp_result_array = GameExtras.objects.filter(game__in=self.result_array).exclude(temperature=-100)
        print "tmp_result_array gathered, length = %d"%len(tmp_result_array)
        self.team_a_conditions_exist = True
        if(item['comptype'] == '='):
            tmp_result_array = tmp_result_array.filter(temperature=int(item['value']))
        elif(item['comptype'] == '<'):
            tmp_result_array = tmp_result_array.filter(temperature__lt=int(item['value']))
        elif(item['comptype'] == '>'):
            tmp_result_array = tmp_result_array.filter(temperature__gt=int(item['value']))
        self.result_array = Games.objects.filter(gameextras__in=tmp_result_array)
    
    def filter_by_wind( self, item ):
        print "about to compute wind conditions"
        tmp_result_array = GameExtras.objects.filter(game__in=self.result_array).exclude(windspeed=-100)
        print "tmp_result_array gathered, length = %d"%len(tmp_result_array)
        self.team_a_conditions_exist = True
        if(item['comptype'] == '='):
            tmp_result_array = tmp_result_array.filter(windspeed=int(item['value']))
        elif(item['comptype'] == '<'):
            tmp_result_array = tmp_result_array.filter(windspeed__lt=int(item['value']))
        elif(item['comptype'] == '>'):
            tmp_result_array = tmp_result_array.filter(windspeed__gt=int(item['value']))
        self.result_array = Games.objects.filter(gameextras__in=tmp_result_array)
    
    def filter_by_humidity( self, item ):
        print "about to compute humidity conditions"
        tmp_result_array = GameExtras.objects.filter(game__in=self.result_array).exclude(humidity=-100)
        print "tmp_result_array gathered, length = %d"%len(tmp_result_array)
        self.team_a_conditions_exist = True
        if(item['comptype'] == '='):
            tmp_result_array = tmp_result_array.filter(humidity=int(item['value']))
        elif(item['comptype'] == '<'):
            tmp_result_array = tmp_result_array.filter(humidity__lt=int(item['value']))
        elif(item['comptype'] == '>'):
            tmp_result_array = tmp_result_array.filter(humidity__gt=int(item['value']))
        self.result_array = Games.objects.filter(gameextras__in=tmp_result_array)
    
    def filter_by_over_under( self, item ):
        print "about to compute over_under conditions"
        self.result_array = self.result_array.filter(over_under__gt=0)
        team_a_conditions_exist = True
        print "about to filter on comptype"
        if(item['comptype'] == '='):
            self.result_array = self.result_array.filter(over_under=int(item['value']))
        elif(item['comptype'] == '<'):
            self.result_array = self.result_array.filter(over_under__lt=int(item['value']))
        elif(item['comptype'] == '>'):
            self.result_array = self.result_array.filter(over_under__gt=int(item['value']))
    
    def filter_by_group( self, item ):
        print ("Querying %s"% groups[int(item['value'])])
        self.team_a_conditions_exist = True
        team_a_index_list = []
        for team in groups[int(item['value'])]:
            team_index = teams.index(team)
            self.team_a_list.append(team)
            team_a_index_list.append(team_index)
        if(self.use_away_team and not self.use_home_team):
            self.result_array =  self.result_array.filter(away_team__in=team_a_index_list)
            for game in self.result_array:
                self.team_a_dict[game.pk] = game.away_team
        elif(self.use_home_team and not self.use_away_team):
            self.result_array =  self.result_array.filter(home_team__in=team_a_index_list)
            for game in self.result_array:
                self.team_a_dict[game.pk] = game.home_team
        elif(self.use_home_team and self.use_away_team): 
            self.result_array =  self.result_array.filter(Q(home_team__in=team_a_index_list)|Q(away_team__in=team_a_index_list))
            for game in self.result_array:
                if(game.home_team in team_a_index_list): 
                    self.team_a_dict[game.pk] = game.home_team
                else:
                    self.team_a_dict[game.pk] = game.away_team
    
    def filter_by_opposition_group( self, item ):
        print("team b has group conditions")
        tmp_result_array = self.result_array
        self.team_b_conditions_exist = True
        #print 'result size before group condition filtering is %d'%tmp_result_array.count()
        team_b_index_list = []
        team_a_index_list = []
        for t in self.team_a_list:
            team_a_index_list.append(self.team_a_list.index(t))
        for team in groups[int(item['value'])]:
            #explanation of following condition: Jets vs AFC east
            #in team a filter we get jets vs SF.  Now we want to remove SF
            #but since jets are in AFC east, they will not be removed (without this condition)  
            team_index = teams.index(team)
            print "searching for team b = %s, index %d"%(team,team_index)
            if(self.team_a_list.count(team) == 0):
                team_index = teams.index(team)
                team_b_index_list.append(team_index)
        if(self.use_away_team and not self.use_home_team):
            print 'using away'
            for t in teams:
                if(teams.index(t) not in team_b_index_list and teams.index(t) not in team_a_index_list):
                    print 'excluding %s %d from final results size of results now = %d'%(t,teams.index(t),tmp_result_array.count())
                    tmp_result_array =  tmp_result_array.exclude(Q(away_team=int(teams.index(t))))
            self.result_array = tmp_result_array
            for game in self.result_array:
                self.team_a_dict[game.pk] = game.home_team
        elif(self.use_home_team and not self.use_away_team):
            print 'using home'
            print team_b_index_list
            for t in teams:
                if(teams.index(t) not in team_b_index_list and teams.index(t) not in team_a_index_list):
                    tmp_result_array =  tmp_result_array.exclude(home_team=teams.index(t))
            self.result_array = tmp_result_array
            for game in self.result_array:
                self.team_a_dict[game.pk] = game.away_team
        elif(self.use_home_team and self.use_away_team): 
            print 'using home and away, length of team list is %d'%(len(team_b_index_list))
            for game in tmp_result_array:
                if(self.team_a_dict[game.pk] == game.away_team and (game.home_team not in team_b_index_list) or
                     self.team_a_dict[game.pk] == game.home_team and (game.away_team not in team_b_index_list)):
                  print 'excluding!'
                  tmp_result_array =  tmp_result_array.exclude(gameid=game.pk)
            self.result_array = tmp_result_array  
        print 'team b group condition check is complete'
    
    def filter_by_team( self, item ):
        print "about to compute  team conditions"
        self.team_a_list.append(teams[int(item['value'])])
        self.team_a_conditions_exist = True
        print "self.result_array gathered, length = %d"%self.result_array.count()
        if(self.use_away_team and not self.use_home_team):
            self.result_array = self.result_array.filter(away_team=int(item['value']))
            for game in self.result_array:
                self.team_a_dict[game.pk] = game.away_team
        elif(self.use_home_team and not self.use_away_team):
            self.result_array = self.result_array.filter(home_team=int(item['value']))
            for game in self.result_array:
                self.team_a_dict[game.pk] = game.home_team
        elif(self.use_home_team and self.use_away_team):
            self.result_array = self.result_array.filter(Q(home_team=int(item['value'])) | Q(away_team=int(item['value'])))
            for game in self.result_array:
                if(int(item['value']) == game.home_team):
                    self.team_a_dict[game.pk] = game.home_team
                else:
                    self.team_a_dict[game.pk] = game.away_team
    
    def filter_by_opposition_team( self, item ):
        print "about to filter team b by team"
        self.team_b_conditions_exist = True
        if(self.use_away_team and not self.use_home_team):
            self.result_array = self.result_array.filter(away_team=int(item['value']))
            for game in self.result_array:
                self.team_a_dict[game.pk] = game.home_team
        elif(self.use_home_team and not self.use_away_team):
            self.result_array = self.result_array.filter(home_team=int(item['value']))
            for game in self.result_array:
                self.team_a_dict[game.pk] = game.away_team
        elif(self.use_home_team and self.use_away_team):
            self.result_array = self.result_array.filter(Q(home_team=int(item['value'])) | Q(away_team=int(item['value'])))
            for game in self.result_array:
                if(int(item['value']) == game.home_team):
                    self.team_a_dict[game.pk] = game.away_team
                else:
                    self.team_a_dict[game.pk] = game.home_team
        print "done filtering team b by team, length of result array is %d"%(self.result_array.count())
    
    def filter_by_spread( self, item ):
        print "about to compute spread conditions."
        tmp_team_a_list = self.result_array.filter(away_team_spread__gt=-100)
        self.team_a_conditions_exist = True
        threshold = Decimal(item['value'])
        #print "tmp_team_a_list gathered, length = %d"%len(tmp_team_a_list)
        if(self.use_away_team and self.use_home_team):
            print 'using home and away'
            #gather games that might satisfy our results if the satisfying teams are in our dict
            if(item['comptype'] == '='):
                tmp_result_array = tmp_team_a_list.filter(Q(away_team_spread=threshold) | Q(away_team_spread=-1*threshold))
            elif(item['comptype'] == '<'):
                tmp_result_array = tmp_team_a_list.filter(Q(away_team_spread__lt=threshold)|Q(away_team_spread__gt=-1*threshold))
            elif(item['comptype'] == '>'):
                tmp_result_array = tmp_team_a_list.filter(Q(away_team_spread__gt=threshold)|Q(away_team_spread__lt=-1*threshold))
        elif(self.use_away_team):
            print 'using just away'
            if(item['comptype'] == '='):
                tmp_result_array = tmp_team_a_list.filter(away_team_spread=threshold)
            elif(item['comptype'] == '<'):
                tmp_result_array = tmp_team_a_list.filter(away_team_spread__lt=threshold)
            elif(item['comptype'] == '>'):
                tmp_result_array = tmp_team_a_list.filter(away_team_spread__gt=threshold)
        else:
            print 'using just home'
            if(item['comptype'] == '='):
                tmp_result_array = tmp_team_a_list.filter(away_team_spread=-1*threshold)
            elif(item['comptype'] == '<'):
                tmp_result_array = tmp_team_a_list.filter(away_team_spread__gt=-1*threshold)
            elif(item['comptype'] == '>'):
                tmp_result_array = tmp_team_a_list.filter(away_team_spread__lt=-1*threshold)
       
        print 'gather comparrison arrays to determine team_a_dict'
        #gather the results where the away team satisfies 
        if(item['comptype'] == '='):
            tmp_result_array_away = tmp_team_a_list.filter(away_team_spread=threshold)
        elif(item['comptype'] == '<'):
            tmp_result_array_away = tmp_team_a_list.filter(away_team_spread__lt=threshold)
        elif(item['comptype'] == '>'):
            tmp_result_array_away = tmp_team_a_list.filter(away_team_spread__gt=threshold)
        #gather the results where the home team satisfies 
        if(item['comptype'] == '='):
            tmp_result_array_home = tmp_team_a_list.filter(away_team_spread=-1*threshold)
        elif(item['comptype'] == '<'):
            tmp_result_array_home = tmp_team_a_list.filter(away_team_spread__gt=-1*threshold)
        elif(item['comptype'] == '>'):
            tmp_result_array_home = tmp_team_a_list.filter(away_team_spread__lt=-1*threshold)
        #iterate over team a dict, determine which team is team a, and if a game was included where satisfying team is not team a, exclude them
        print 'generate exclusion_list'
        exclusion_pk_list = []
        for game in tmp_result_array:
            game_pk = game.pk
            if(not self.team_a_dict.has_key(game_pk)):
                if(tmp_result_array_away.filter(gameid=game_pk).exists()):
                    self.team_a_dict[game_pk] = game.away_team
                else:
                    self.team_a_dict[game_pk] = game.home_team
            elif(self.team_a_dict[game_pk] == game.away_team):
                if(tmp_result_array_away.filter(gameid=game_pk).exists()):
                    self.team_a_dict[game_pk] = game.away_team
                else:
                    exclusion_pk_list.append(game_pk)
            elif(self.team_a_dict[game_pk] == game.home_team):
                if(tmp_result_array_home.filter(gameid=game_pk).exists()):
                    self.team_a_dict[game_pk] = game.home_team
                else:
                     exclusion_pk_list.append(game_pk)
        print 'exclusion_list computed.  length = %d'%(len(exclusion_pk_list))
        if(exclusion_pk_list != []):
            self.result_array = self.exclude_games( tmp_result_array, exclusion_pk_list )
        else:
            self.result_array = tmp_result_array
        print 'spread conditions computed.'
    
    def filter_by_win_percentage( self, item ):
        print "about to compute WinPercentage conditions"
        tmp_result_array = result_array
        win_record  = get_record( item['value'] )
        self.team_a_conditions_exist = True
        if(self.use_away_team and self.use_home_team):
          #a note on the team a dict for win%:
          # as a stand alone feature, the win% only makes sense if both teams are assigned miutually exclusive
          #constraints.  Like a +500 team versus a minus 500.   So, if home and away are being used
          # I only assign to the team_a_dict in the team_b constraints
          if(item['comptype'] == '='):
              self.result_array = tmp_result_array.filter(Q(away_team_record=win_record) | Q(home_team_record=win_record))
              result_array_away = tmp_result_array.filter(away_team_record=win_record)
              result_array_home = tmp_result_array.filter(home_team_record=win_record)
          elif(item['comptype'] == '<'):
              self.result_array = tmp_result_array.filter(Q(away_team_record__lt=win_record)|Q(home_team_record__lt=win_record))
              result_array_away = tmp_result_array.filter(away_team_record__lt=win_record)
              result_array_home = tmp_result_array.filter(home_team_record__lt=win_record)
          elif(item['comptype'] == '>'):
              self.result_array = tmp_result_array.filter(Q(away_team_record__gt=win_record)|Q(home_team_record__gt=win_record))
              result_array_away = tmp_result_array.filter(away_team_record__gt=win_record)
              result_array_home = tmp_result_array.filter(home_team_record__gt=win_record)
          #we dont assign team_A_dict in this condition, but if its already assigned, take it into consideration
          print 'result_array count = %d'%result_array.count()
          exclusion_list = []
          for game in self.result_array:
              if(self.team_a_dict.has_key(game.pk)):
                  if((not result_array_away.filter(gameid=game.pk).exists()) and self.team_a_dict[game.pk] == game.away_team or
                     (not result_array_home.filter(gameid=game.pk).exists()) and self.team_a_dict[game.pk] == game.home_team):
                       print 'adding to exclusion list'
                       exclusion_list.append(game.pk)
          self.result_array = self.result_array.exclude(gameid__in=exclusion_list)
          print 'result_array count = %d'%self.result_array.count()
              
        elif(self.use_away_team):
          if(item['comptype'] == '='):
              self.result_array = tmp_result_array.filter(away_team_record=win_record)
          elif(item['comptype'] == '<'):
              self.result_array = tmp_result_array.filter(away_team_record__lt=win_record)
          elif(item['comptype'] == '>'):
              self.result_array = tmp_result_array.filter(away_team_record__gt=win_record)
          for game in self.result_array:
              if(not team_a_dict.has_key(game.pk)):
                  self.team_a_dict[game.pk] = game.away_team
        else:
            if(item['comptype'] == '='):
                self.result_array = tmp_result_array.filter(home_team_record=win_record)
            elif(item['comptype'] == '<'):
                self.result_array = tmp_result_array.filter(home_team_record__lt=win_record)
            elif(item['comptype'] == '>'):
                self.result_array = tmp_result_array.filter(home_team_record__gt=win_record)
            for game in self.result_array:
                if(not self.team_a_dict.has_key(game.pk)):
                    self.team_a_dict[game.pk] = game.home_team
    
    def filter_by_opposition_win_percentage( self, item ):
        print( "about to compute WinPercentage conditions size of result_array = %d" % ( self.result_array.count() ) )
        tmp_result_array = self.result_array
        self.team_b_conditions_exist = True
        win_record  = get_record( item['value'] )
        if(tmp_result_array.count() > 0):
              if(self.use_away_team and self.use_home_team):
                  #a note on the team a dict for win%:
                  # as a stand alone feature, the win% only makes sense if both teams are assigned miutually exclusive
                  #constraints.  Like a +500 team versus a minus 500.   So, if home and away are being used
                  # I only assign to the team_a_dict in the team_b constraints
                  if(item['comptype'] == '='):
                      self.result_array = tmp_result_array.filter(Q(away_team_record=win_record) | Q(home_team_record=win_record))
                      self.result_array_away = tmp_result_array.filter(away_team_record=win_record)
                      self.result_array_home = tmp_result_array.filter(home_team_record=win_record)
                  elif(item['comptype'] == '<'):
                      self.result_array = tmp_result_array.filter(Q(away_team_record__lt=win_record)|Q(home_team_record__lt=win_record))
                      self.result_array_away = tmp_result_array.filter(away_team_record__lt=win_record)
                      self.result_array_home = tmp_result_array.filter(home_team_record__lt=win_record)
                  elif(item['comptype'] == '>'):
                      self.result_array = tmp_result_array.filter(Q(away_team_record__gt=win_record)|Q(home_team_record__gt=win_record))
                      self.result_array_away = tmp_result_array.filter(away_team_record__gt=win_record)
                      self.result_array_home = tmp_result_array.filter(home_team_record__gt=win_record)
                  #imagine team a is the viking, we want them against teams that have < 500 record.  
                  #make sure to exclude games where only the vikings have < 500 record
                  exclusion_list = []
                  for game in self.result_array:
                      if(self.team_a_dict.has_key(game.pk)):
                          if((not self.result_array_away.filter(gameid=game.pk).exists()) and self.team_a_dict[game.pk] == game.home_team or
                             (not self.result_array_home.filter(gameid=game.pk).exists()) and self.team_a_dict[game.pk] == game.away_team):
                              print 'adding to exclusion list'
                              exclusion_list.append(game.pk)
                  self.result_array = self.result_array.exclude(gameid__in=exclusion_list)
                  for game in self.result_array:
                      if(not self.team_a_dict.has_key(game.pk)):
                          if(self.result_array_away.filter(gameid=game.pk).exists()):
                              self.team_a_dict[game.pk] = game.home_team
                          else:
                              self.team_a_dict[game.pk] = game.away_team
                      
              elif(self.use_away_team):
                  if(item['comptype'] == '='):
                      self.result_array = tmp_result_array.filter(away_team_record=win_record)
                  elif(item['comptype'] == '<'):
                      self.result_array = tmp_result_array.filter(away_team_record__lt=win_record)
                  elif(item['comptype'] == '>'):
                      self.result_array = tmp_result_array.filter(away_team_record__gt=win_record)
                  for game in self.result_array:
                      if(not self.team_a_dict.has_key(game.pk)):
                          self.team_a_dict[game.pk] = game.home_team
              else:
                    if(item['comptype'] == '='):
                        self.result_array = tmp_result_array.filter(home_team_record=win_record)
                    elif(item['comptype'] == '<'):
                        self.result_array = tmp_result_array.filter(home_team_record__lt=win_record)
                    elif(item['comptype'] == '>'):
                        self.result_array = tmp_result_array.filter(home_team_record__gt=win_record)
                    for game in self.result_array:
                        if(not self.team_a_dict.has_key(game.pk)):
                            self.team_a_dict[game.pk] = game.away_team
              print "added team_b record conditions" 
    
    def filter_by_win_streak( self, item ):
        print "about to compute WinStreak conditions"
        tmp_result_array = GameStreaks.objects.filter(game__in=self.result_array)
        self.team_a_conditions_exist = True
        if(self.use_away_team and self.use_home_team):
            #a note on the team a dict for win%:
            # as a stand alone feature, the win% only makes sense if both teams are assigned miutually exclusive
            #constraints.  Like a +500 team versus a minus 500.   So, if home and away are being used
            # I only assign to the team_a_dict in the team_b constraints
            if(item['comptype'] == '='):
                self.result_array = tmp_result_array.filter(Q(away_team_win_streak=item['value']) | Q(home_team_win_streak=item['value']))
                result_array_away = tmp_result_array.filter(away_team_win_streak=item['value'])
                result_array_home = tmp_result_array.filter(home_team_win_streak=item['value'])
            elif(item['comptype'] == '<'):
                self.result_array = tmp_result_array.filter(Q(away_team_win_streak__lt=item['value'])|Q(home_team_win_streak__lt=item['value']))
                result_array_away = tmp_result_array.filter(away_team_win_streak__lt=item['value'])
                result_array_home = tmp_result_array.filter(home_team_win_streak__lt=item['value'])
            elif(item['comptype'] == '>'):
                self.result_array = tmp_result_array.filter(Q(away_team_win_streak__gt=item['value'])|Q(home_team_win_streak__gt=item['value']))
                result_array_away = tmp_result_array.filter(away_team_win_streak__gt=item['value'])
                result_array_home = tmp_result_array.filter(home_team_win_streak__gt=item['value'])
            #we dont assign team_A_dict in this condition, but if its already assigned, take it into consideration
            print 'result_array count = %d'%self.result_array.count()
            self.result_array = Games.objects.filter(gamestreaks__in=result_array)
            result_array_away = Games.objects.filter(gamestreaks__in=result_array_away)
            result_array_home = Games.objects.filter(gamestreaks__in=result_array_home)
            exclusion_list = []
            for game in self.result_array:
                if(self.team_a_dict.has_key(game.pk)):
                    if((not result_array_away.filter(gameid=game.pk).exists()) and self.team_a_dict[game.pk] == game.away_team or
                       (not result_array_home.filter(gameid=game.pk).exists()) and self.team_a_dict[game.pk] == game.home_team):
                         print 'adding to exclusion list'
                         exclusion_list.append(game.pk)
            self.result_array = self.result_array.exclude(gameid__in=exclusion_list)
            print 'result_array count = %d'%self.result_array.count()
              
        elif(self.use_away_team):
            if(item['comptype'] == '='):
                self.result_array = tmp_result_array.filter(away_team_win_streak=item['value'])
            elif(item['comptype'] == '<'):
                self.result_array = tmp_result_array.filter(away_team_win_streak__lt=item['value'])
            elif(item['comptype'] == '>'):
                self.result_array = tmp_result_array.filter(away_team_win_streak__gt=item['value'])
            self.result_array = Games.objects.filter(gamestreaks__in=self.result_array)
            for game in self.result_array:
                if(not self.team_a_dict.has_key(game.pk)):
                    self.team_a_dict[game.pk] = game.away_team
        else:
            if(item['comptype'] == '='):
                self.result_array = tmp_result_array.filter(home_team_win_streak=item['value'])
            elif(item['comptype'] == '<'):
                self.result_array = tmp_result_array.filter(home_team_win_streak__lt=item['value'])
            elif(item['comptype'] == '>'):
                self.result_array = tmp_result_array.filter(home_team_win_streak__gt=item['value'])
            self.result_array = Games.objects.filter(gamestreaks__in=self.result_array)
            for game in self.result_array:
                if(not self.team_a_dict.has_key(game.pk)):
                    self.team_a_dict[game.pk] = game.home_team
    
    def filter_by_opposition_win_streak( self, item ):
        print "about to compute WinStreak conditions"
        tmp_result_array = self.result_array
        self.team_b_conditions_exist = True
        
        print "tmp_result_array gathered"
        if(tmp_result_array != []):
            if(self.use_away_team and self.use_home_team):
                #a note on the team a dict for win%:
                # as a stand alone feature, the win% only makes sense if both teams are assigned miutually exclusive
                #constraints.  Like a +500 team versus a minus 500.   So, if home and away are being used
                # I only assign to the team_a_dict in the team_b constraints
                if(item['comptype'] == '='):
                    self.result_array = tmp_result_array.filter(Q(gamestreaks__away_team_win_streak=item['value']) | Q(gamestreaks__home_team_win_streak=item['value']))
                    self.result_array_away = tmp_result_array.filter(away_team_win_streak=item['value'])
                    self.result_array_home = tmp_result_array.filter(home_team_win_streak=item['value'])
                elif(item['comptype'] == '<'):
                    self.result_array = tmp_result_array.filter(Q(gamestreaks__away_team_win_streak__lt=item['value'])|Q(gamestreaks__home_team_win_streak__lt=item['value']))
                    self.result_array_away = tmp_result_array.filter(away_team_win_streak__lt=item['value'])
                    self.result_array_home = tmp_result_array.filter(home_team_win_streak__lt=item['value'])
                elif(item['comptype'] == '>'):
                    self.result_array = tmp_result_array.filter(Q(gamestreaks__away_team_win_streak__gt=item['value'])|Q(gamestreaks__home_team_win_streak__gt=item['value']))
                    self.result_array_away = tmp_result_array.filter(gamestreaks__away_team_win_streak__gt=item['value'])
                    self.result_array_home = tmp_result_array.filter(gamestreaks__home_team_win_streak__gt=item['value'])
                print 'self.result_array_team_b count = %d'%self.result_array.count()
                #imagine team a is the viking, we want them against teams that have < 500 win_streak.  
                #make sure to exclude games where only the vikings have < 500 win_streak
                exclusion_list = []
                for game in self.result_array:
                    if(self.team_a_dict.has_key(game.pk)):
                        if((not self.result_array_away.filter(gameid=game.pk).exists()) and self.team_a_dict[game.pk] == game.home_team or
                           (not self.result_array_home.filter(gameid=game.pk).exists()) and self.team_a_dict[game.pk] == game.away_team):
                             print 'adding to exclusion list'
                             exclusion_list.append(game.pk)
                #print 'self.result_array_team_b count = %d'%self.result_array.count()
                self.result_array = self.result_array.exclude(gameid__in=exclusion_list)
                #print 'self.result_array_team_b count = %d'%self.result_array.count()
                for game in self.result_array:
                    if(not self.team_a_dict.has_key(game.pk)):
                        if(self.result_array_away.filter(gameid=game.pk).exists()):
                            self.team_a_dict[game.pk] = game.home_team
                        else:
                            self.team_a_dict[game.pk] = game.away_team
                  
            elif(self.use_away_team):
                if(item['comptype'] == '='):
                    self.result_array = tmp_result_array.filter(gamestreaks__away_team_win_streak=item['value'])
                elif(item['comptype'] == '<'):
                    self.result_array = tmp_result_array.filter(gamestreaks__away_team_win_streak__lt=item['value'])
                elif(item['comptype'] == '>'):
                    self.result_array = tmp_result_array.filter(gamestreaks__away_team_win_streak__gt=item['value'])
                for game in self.result_array:
                    if(not self.team_a_dict.has_key(game.pk)):
                        self.team_a_dict[game.pk] = game.home_team
            else:
                if(item['comptype'] == '='):
                    self.result_array = tmp_result_array.filter(gamestreaks__home_team_win_streak=item['value'])
                elif(item['comptype'] == '<'):
                    self.result_array = tmp_result_array.filter(gamestreaks__home_team_win_streak__lt=item['value'])
                elif(item['comptype'] == '>'):
                    self.result_array = tmp_result_array.filter(gamestreaks__home_team_win_streak__gt=item['value'])
                for game in self.result_array:
                    if(not self.team_a_dict.has_key(game.pk)):
                        self.team_a_dict[game.pk] = game.away_team
        print "added team_b win_streak conditions" 
    
    def filter_by_coach( self, item ):
        print "about to compute coach conditions"
        self.result_array = self.result_array.distinct()
        print "self.result_array gathered"
        self.team_a_conditions_exist = True
        coach_name_array = item['value'].split()
        print 'coach_name_array has length %d'%len(coach_name_array)
        firstname = coach_name_array[0].lower()
        if(len(coach_name_array) > 2):
            lastname = ''
            for i in range(1,len(coach_name_array)):
                lastname += coach_name_array[i].lower()
                if(i != len(coach_name_array) -1):
                    lastname += ' ' 
        else:
            lastname = coach_name_array[1].lower()
        #logic below will have to be adjusted for multiple coachs with the same name
        print 'gathered coach name, now lets query'
        if (Coaches.objects.filter(lastname=lastname, firstname=firstname).exists()):
            print 'coach exists!'
            coach = Coaches.objects.filter(lastname=lastname, firstname=firstname)[0]
            print 'coach id = %d'%int(coach.pk)
            if(self.use_away_team and not self.use_home_team):
                print 'using away'
                self.result_array = self.result_array.filter(away_coach=int(coach.pk)) 
                for game in self.result_array:
                    if(not team_a_dict.has_key(game.pk)):
                        self.team_a_dict[game.pk]= game.away_team
            elif(self.use_home_team and not self.use_away_team):
                print 'using home'
                self.result_array = self.result_array.filter(home_coach=int(coach.pk)) 
                for game in self.result_array:
                    if(not self.team_a_dict.has_key(game.pk)):
                        self.team_a_dict[game.pk]= game.home_team
            elif(self.use_away_team and self.use_home_team):
                self.result_array = self.result_array.filter(Q(home_coach=int(coach.pk))|Q(away_coach=int(coach.pk))) 
                print 'using home and away'
                for game in self.result_array:
                    if(not self.team_a_dict.has_key(game.pk)):
                        if(game.away_coach == coach.pk):
                            self.team_a_dict[game.pk]= game.away_team
                        else:
                            self.team_a_dict[game.pk]= game.home_team
    
    def filter_by_opposition_coach( self, item ):
        print "about to compute coach conditions"
        self.result_array = self.result_array.distinct()
        print "tmp_team_a_list gathered"
        self.team_b_conditions_exist = True
        coach_name_array = item['value'].split()
        print 'coach_name_array has length %d'%len(coach_name_array)
        firstname = coach_name_array[0].lower()
        if(len(coach_name_array) > 2):
            lastname = ''
            for i in range(1,len(coach_name_array)):
                lastname += coach_name_array[i].lower()
                if(i != len(coach_name_array) -1):
                    lastname += ' ' 
        else:
            lastname = coach_name_array[1].lower()
        #logic below will have to be adjusted for multiple coachs with the same name
        if (Coaches.objects.filter(lastname=lastname, firstname=firstname).exists()):
            print 'coach exists!'
            coach = Coaches.objects.filter(lastname=lastname, firstname=firstname)[0]
            if(self.use_away_team and not self.use_home_team):
                self.result_array = self.result_array.filter(away_coach=coach.pk) 
                for game in self.result_array:
                    if(not team_a_dict.has_key(game.pk)):
                        self.team_a_dict[game.pk]= game.home_team
            elif(not self.use_away_team and self.use_home_team):
                self.result_array = self.result_array.filter(home_coach=coach.pk) 
                for game in self.result_array:
                    if(not team_a_dict.has_key(game.pk)):
                        self.team_a_dict[game.pk]= game.away_team
            elif(self.use_away_team and self.use_home_team):
                self.result_array = self.result_array.filter(Q(home_coach=coach.pk)|Q(away_coach=coach.pk)) 
                for game in self.result_array:
                    if(not team_a_dict.has_key(game.pk)):
                        if(game.away_coach == coach.pk):
                            self.team_a_dict[game.pk]= game.home_team
                        else:
                            self.team_a_dict[game.pk]= game.away_team

    def get_player_filter( self, name_str ) :
        player_name_array = name_str.split()
        print 'player_name_array has length %d'%len(player_name_array)
        firstname = player_name_array[0].lower()
        if(len(player_name_array) > 2):
          lastname = ''
          for i in range(1,len(player_name_array)):
            lastname += player_name_array[i].lower()
            if(i != len(player_name_array) -1):
              lastname += ' ' 
        else:
          lastname = player_name_array[1].lower()
        #logic below will have to be adjusted for multiple players with the same name
        player_filter = Players.objects.filter(lastname=lastname, firstname=firstname)
        if(not player_filter.exists()):
          player_filter_nickname = get_nickname(lastname,firstname) 
          if(player_filter_nickname != None):
            player_filter = player_filter_nickname
            lastname=player_filter[0].lastname
            firstname=player_filter[0].firstname
        return player_filter
    
    def get_player_game_list( self, player_filter ):
        print 'player exists!'
        if(player_filter.count() == 1):
          self.player = player_filter[0]
          nonunique = False
        else:
          self.player = resolve_nonunique_players(lastname,firstname)
          nonunique = True
        self.queried_players.append(self.player)
        self.player_game_list = self.player.games.only('gameid').all()
        print 'player game list gathered size = %d'%(self.player_game_list.count())
    
    def get_active_status( self, game ):
        player_game = game.gameplayers_set.filter(playerid=self.player)[0]
        #print 'game contain player position = %s'%positions[position]
        if(positions[self.player.position] in ['RB','FB','WR','TE','RBWR']):
          #print 'player %s %s is not QB'%(player_game.playerid.firstname, player_game.playerid.lastname)
          if(RbWrGameStats.objects.filter(gameplayer=player_game).exists()):
            isactive = player_game.rbwrgamestats.G
          else:
            isactive = False
        elif(positions[self.player.position] == 'QB'):
          #print 'player %s %s is QB'%(player_game.playerid.firstname, player_game.playerid.lastname)
          if(QbGameStats.objects.filter(gameplayer=player_game).exists()):
            isactive = player_game.qbgamestats.G and (player_game.qbgamestats.GS or player_game.gameid.date < datetime.date(1993,1,1))
          else:
            isactive = False
        else:
          #print 'player %s %s is not QB or rb/wr'%(player_game.playerid.firstname, player_game.playerid.lastname)
          isactive = True
        return isactive
    
    def exclude_games(self,  game_list, exclusion_list ):
        if(len(exclusion_list) > 0):
            count = 0
            tmp_exclusion_list = []
            for i in exclusion_list:
                count = (count + 1)%50
                tmp_exclusion_list.append(i)
                if(count == 0):
                    game_list = game_list.exclude(gameid__in=tmp_exclusion_list)
                    tmp_exclusion_list = []
                    # force the query to be evaluated.  Attempt to prevent too many SQL variables error
                    for item in game_list.all():
                        pass
                    print 'game list size = %d' % ( len(game_list) )
            game_list = game_list.exclude(gameid__in=tmp_exclusion_list)
        return game_list

    def filter_by_player( self, item, team ):
        print "about to compute player conditions team = %s use_away_team = %d use_home_team = %d" % ( team, self.use_away_team, self.use_home_team )
        tmp_result_array = self.result_array.distinct()
        print "tmp_result_array gathered"
        #print "tmp_result_array gathered, length = %d"%(tmp_result_array.count())
        self.team_a_conditions_exist = True
        player_filter = self.get_player_filter( item['value'] )
        if (player_filter.exists()):
            self.get_player_game_list( player_filter )
        else:
            print 'no such player %s %s'%(player_name_array[0], player_name_array[1])
            self.player_game_list = []
            tmp_result_array = []
        exclusion_list = []
        # The following is done to get around sqlite 'too many SQL variables bug
        # It prevents having very large exclude queries, which seems to lead to the bug.
        player_game_pk_list = []
        for gm in self.player_game_list:
            player_game_pk_list.append(gm.pk)
        tmp_result_array = tmp_result_array.filter(pk__in=player_game_pk_list)
        for game in tmp_result_array:
            #cond 1: player played in game
            if(self.player_game_list.filter(pk=game.pk).exists()):
                isactive = self.get_active_status(game)
                if(isactive):
                    #if team_a_dict not assigned it means we have yet to constrain this game.  go ahead and add it to list
                    # otherwise, make sure the team hes on is the team we are looking for
                    away = GamePlayers.objects.get(gameid=game.pk, playerid=self.player.pk).away
                    if(away and team == 'a' or ( not away ) and team == 'b' ):
                        team_a_away = True
                        if(not self.team_a_dict.has_key(game.pk)):
                            self.team_a_dict[game.pk] = game.away_team
                    else:
                        team_a_away = False
                        if(not self.team_a_dict.has_key(game.pk)):
                            self.team_a_dict[game.pk] = game.home_team
                    if( (      team_a_away  and self.team_a_dict[game.pk] != game.away_team ) or
                        (  not team_a_away  and self.team_a_dict[game.pk] == game.away_team ) ):
                        exclusion_list.append(game.pk)
                else:
                    print 'player was not active'
                    exclusion_list.append(game.pk)
            else:
                exclusion_list.append(game.pk)
        #print 'begin player based exclusion tmp_result_array size = %d exclusion_list size = %d'%(tmp_result_array.count(), len(exclusion_list))
        tmp_result_array = self.exclude_games( tmp_result_array, exclusion_list )
        self.result_array = tmp_result_array
        print 'end player based exclusion tmp_result_array size = %d'%(len(self.result_array))

    def get_game_data( self ):
        iteration = 0
        self.numgames = float(len(self.final_result_array))
        self.numgamesint = len(self.final_result_array)
        gameset = Games.objects.only('gameid','date','away_team','home_team','away_team_spread','over_under',
                                     'over_under','away_team_score','home_team_score','week','season')
        while((1000*iteration) <= self.numgamesint):
            self.result_array = gameset.filter(pk__in=self.final_result_array[1000*(iteration):1000*(iteration+1)-1])
            iteration += 1
            print 'iterate over result array'
            for item in self.result_array:
                if(self.team_a_dict.get(item.pk,-1) == item.away_team):
                    self.teama_points += item.away_team_score
                    self.teamb_points += item.home_team_score
                else:
                    self.teamb_points += item.away_team_score
                    self.teama_points += item.home_team_score
                #away team wins
                if(((item.away_team_score + item.away_team_spread)  - item.home_team_score) > 0): 
                    if(self.team_a_dict.get(item.pk,-1) == item.away_team):
                        self.teama_spreadwins += 1
                    else:
                        self.teamb_spreadwins += 1
                #home team wins
                elif(((item.away_team_score + item.away_team_spread)  - item.home_team_score) < 0): 
                    if(self.team_a_dict.get(item.pk,-1) == item.away_team):
                        self.teamb_spreadwins += 1
                    else:
                        self.teama_spreadwins += 1
                #draw
                elif(self.push_goes_to_bookie):
                    pass
                if((item.away_team_score  - item.home_team_score) > 0): 
                    if(self.team_a_dict.get(item.pk,-1) == item.away_team):
                        self.teama_wins += 1
                    else:
                        self.teamb_wins += 1
                #home team wins
                elif((item.away_team_score  - item.home_team_score) < 0): 
                    if(self.team_a_dict.get(item.pk,-1) == item.away_team):
                        self.teamb_wins += 1
                    else:
                        self.teama_wins += 1
                #the over covers
                if((item.away_team_score  + item.home_team_score) > item.over_under): 
                    self.over_wins +=1
            
                self.response['result_table'] += [item.season,item.week,item.away_team, item.away_team_score, item.home_team, item.home_team_score,str(item.away_team_spread),str(item.over_under), self.team_a_dict.get(item.pk,-1)]
        #aggregate data/summaries
        print 'calculating summaries, self.numgames = %d'%self.numgames
        #preventdiv by 0
        if(self.numgames == 0):
            self.numgames = 1
        self.response['teama_summary'] = ['%.2f'%(float(self.teama_spreadwins)/self.numgames), '%.2f'%(float(self.teama_wins)/self.numgames), '%.2f'%(self.over_wins/self.numgames), '%.2f'%(self.teama_points/self.numgames), '%.2f'%(self.teamb_points/self.numgames)]
        self.response['teamb_summary'] = ['%.2f'%(float(self.teamb_spreadwins)/self.numgames), '%.2f'%(float(self.teamb_wins)/self.numgames), '%.2f'%(self.over_wins/self.numgames), '%.2f'%(self.teamb_points/self.numgames), '%.2f'%(self.teama_points/self.numgames)]

    def get_summary_hist( self ):
          print 'about to do summary hist'
          int_ats = int(100*float(self.teama_spreadwins)/self.numgames) 
          int_wp = int(100*float(self.teama_wins)/self.numgames) 
          int_ou = int(100*float(self.over_wins)/self.numgames)  
          plotdata = [int_ats,int_wp,int_ou]
          color_array = get_color_array([int_ats,int_wp,int_ou])
          print 'color array:'
          print color_array
          timestamp = str(time.time())
          self.response['teamsumchart'] = 'teamsum_'+timestamp+'.png'
          teamsumchart_fullpath = settings.STATIC_ROOT+'teamsum_'+timestamp+'.png'
          print 'about to use cairoplot'
          if(plotting):
              cairoplot.vertical_bar_plot (  teamsumchart_fullpath, plotdata, 550, 400, border = 50, grid = True, rounded_corners = True,display_values = True, x_labels=['ATS', 'Win%', 'Over Covers'], colors=color_array)

    def get_player_data( self ):
        print 'collecting player stats'
        self.queried_players = uniq(self.queried_players)
        player_sums = []
        #A NOTE ON THE FOLLOWING:  We broke down the result array above for large game sets (> 1000)
        #no player gameset will be greater than a few hundred, so its not needed here, so we go back to 
        #full result array
        self.result_array = Games.objects.filter(pk__in=self.final_result_array).only('date','gameid')
        for playa in self.queried_players:
            print 'collecting stats for playa %s %s'%(playa.firstname,playa.lastname)
            #determine if this player has stats, currently only offensive position players
            positionstr = positions[playa.position] 
            if(positionstr in ['RB','FB','WR','TE','QB','RBWR'] or
                 positionstr in ['CB','DB','DE','DL', 'DT','FS', 'ILB', 'LB', 'LS', 'MLB', 'NT', 'OLB', 'SAF','SS','DEF']):
                rush_array = []
                pass_array = []
                totalyds_array = []
                date_array = []
                print 'about to gather playa stats for each game' 
                firstgame = True
                player_has_stats = False
                for item in self.result_array:
                    #on the first game for ech player determine if we have any stats for them
                    if(firstgame):
                        print 'firstgame'
                        player_sums = []
                        firstgame = False
                        #this is just a tes.  Is server side json un able to handle the mixed array sizes?
                        self.response['player_table'].extend(['hdr', playa.lastname, playa.firstname,playa.position])
                        #print 'first game is gameid %d playerid %d'%(item.pk, playa.pk)
                        #gp = GamePlayers.objects.filter(gameid=item.pk, playerid=playa.pk)[0]
                        player_game_list = GamePlayers.objects.filter(playerid=playa.pk)
                        #player_game_list = GamePlayers.objects.filter(playerid=playa.pk).filter(gameid__in=self.result_array)
                        print 'grab numstats'
                        #seems __in is a big perf loss, just set numstats to True for now
                        numstats = True
                        if(numstats):
                            print 'playr has stats'
                            player_has_stats = True
                            games_active = 0
                            #first filter fr playerid
                            if(positionstr in ['RB','FB','WR','TE','RBWR']):
                                print 'initialize player sums'
                                player_sums = [0,0,0,0,0,0]
                                self.response['rbwrs_with_stats'].append('%s %s'%(playa.firstname,playa.lastname))
                                self.response['players_with_stats'].append('%s %s'%(playa.firstname,playa.lastname))
                                #gpstatarray = RbWrGameStats.objects.filter(gameplayer__in=player_game_list).defer('FUM','Lost','RushAtt','RecLng','RecTD')
                            elif(positionstr == 'QB'):
                                player_sums = [0,0,0,0,0]
                                self.response['qbs_with_stats'].append('%s %s'%(playa.firstname,playa.lastname))
                                self.response['players_with_stats'].append('%s %s'%(playa.firstname,playa.lastname))
                                #gpstatarray = QbGameStats.objects.filter(gameplayer__in=player_game_list).defer('Pct','Avg','Int','Sck','SckY','RushAtt','RushYds','RushAvg','RushTD','FUM','Lost')
                            elif(positionstr in ['CB','DB','DE','DL', 'DT','FS', 'ILB', 'LB', 'LS', 'MLB', 'NT', 'OLB', 'SAF','SS','DEF']):
                                print 'player is on def'
                                player_sums = [0,0,0]
                                self.response['defs_with_stats'].append('%s %s'%(playa.firstname,playa.lastname))
                                #gpstatarray = DefGameStats.objects.filter(gameplayer__in=player_game_list)
                    if(player_has_stats): 
                        #print 'grab gp object'
                        gp = player_game_list.get(gameid=item.pk)
                        if(positionstr in ['RB','FB','WR','TE','RBWR']):
                            #print 'grab wr/rb stats'
                            #gpstatsarray = RbWrGameStats.objects.filter(gameplayer_id = gp.pk)
                            #try removing gpstatarray.  its generated by __in which is costly
                            #if(gpstatarray.filter(gameplayer_id = gp.pk).exists()):
                            #  gpstats = gpstatarray.filter(gameplayer_id = gp.pk)[0]
                            if(RbWrGameStats.objects.filter(gameplayer_id = gp.pk).exists()):
                                gpstats = RbWrGameStats.objects.filter(gameplayer_id = gp.pk)[0]
                            #print 'RbWrstat retrieved'
                            self.response['player_table'].extend([str(gpstats.RushYds),str(gpstats.RushTD), str(gpstats.RecYds),str(gpstats.RecTD)])
                            #we sum up the stats for each game in the avg array.  at the end we will divide byt total number of games
                            statnum = 0
                            #only add stat if the player was actuve (G=True means active.  For QBs we may later want to do GS (started)
                            if(gpstats.G):
                                games_active += 1
                                for stat in [gpstats.RushYds,gpstats.RushAvg,gpstats.RushTD, gpstats.RecYds,gpstats.RecAvg,gpstats.RecTD]:
                                    player_sums[statnum] += stat
                                    statnum += 1
                                rush_array.append(gpstats.RushYds)
                                pass_array.append(gpstats.RecYds)
                                totalyds_array.append(gpstats.RecYds+gpstats.RushYds)
                                date_array.append(str(item.date))
                        elif(positionstr == 'QB'):
                            #gpstatsarray = QbGameStats.objects.filter(gameplayer_id = gp.pk)
                            if(QbGameStats.objects.filter(gameplayer_id = gp.pk).exists()):
                                gpstats = QbGameStats.objects.filter(gameplayer_id = gp.pk)[0]
                            #print 'Qbstat retrieved'
                            self.response['player_table'].extend([str(gpstats.Comp), str(gpstats.Att), str(gpstats.Yds),str(gpstats.TD),str(gpstats.Rate)])
                            #we sum up the stats for each game in the avg array.  at the end we will divide byt total number of games
                            statnum = 0
                            #For QBs only add stat if the player started (GS=True means started) 
                            if(gpstats.GS):
                                games_active += 1
                                for stat in [gpstats.Comp, gpstats.Att, gpstats.Yds,gpstats.TD,gpstats.Rate]:
                                    player_sums[statnum] += stat
                                    statnum += 1
                                rush_array.append(gpstats.RushYds)
                                pass_array.append(gpstats.Yds)
                                total_yds = gpstats.Yds+gpstats.RushYds
                                totalyds_array.append(total_yds)
                                date_array.append(str(item.date))
                        elif(positionstr in ['CB','DB','DE','DL', 'DT','FS', 'ILB', 'LB', 'LS', 'MLB', 'NT', 'OLB', 'SAF','SS','DEF']):
                              #gpstatsarray = DefGameStats.objects.filter(gameplayer_id = gp.pk)
                              print 'collect def stats'
                              if(DefGameStats.objects.filter(gameplayer_id = gp.pk).exists()):
                                  gpstats = DefGameStats.objects.filter(gameplayer_id = gp.pk)[0]
                              print 'collected def stats'
                              #print 'Defstat retrieved'
                              self.response['player_table'].extend([str(gpstats.Tck), str(gpstats.Sck), str(gpstats.Int)])
                              #we sum up the stats for each game in the avg array.  at the end we will divide byt total number of games
                              statnum = 0
                              #For Def only add stat if the player started (GS=True means started) 
                              #might change this later
                              if(gpstats.GS):
                                  print 'player active'
                                  games_active += 1
                                  for stat in [gpstats.Tck, gpstats.Sck, gpstats.Int]:
                                      player_sums[statnum] += stat
                                      statnum += 1
                ##we are done with a particular player, calculate the stat avgs based on sums 
                player_avgs = []
                print 'calculating avgs'
                for stat in player_sums:
                    ##for now ill print 0 if 0 games active, maybe later ill change this
                    if(games_active != 0):
                        player_avgs.append('%.1f'%(stat/games_active))
                    else:
                        player_avgs.append(0)
                if(positions[playa.position] == 'QB'):
                    self.response['qb_avgs'].append(player_avgs) 
                elif(positions[playa.position] in ['WR','RB','FB','TE','RBWR']):
                    self.response['rbwr_avgs'].append(player_avgs) 
                else:
                    self.response['def_avgs'].append(player_avgs) 
          
                if(pass_array != []):
                    ##now create histograms
                    #total yds
                    totalyds_hist = get_hist(totalyds_array)
                    timestamp = str(time.time())
                    if(positions[playa.position] == 'QB'):
                        self.response['qb_charts'].append('totalydshist_'+timestamp+'.png')
                    else:
                        self.response['rbwr_charts'].append('totalydshist_'+timestamp+'.png')
                    histchart_fullpath = settings.STATIC_ROOT+'totalydshist_'+timestamp+'.png'
                    print 'creating passhist'
                    if(plotting):
                        cairoplot.vertical_bar_plot (  histchart_fullpath, totalyds_hist[1], 550, 400, border = 50, grid = True, rounded_corners = True,display_values = True,x_labels=totalyds_hist[0])
                    print 'totalydshist created'
        print 'player stats collected'
      
#counting sort, mightbe faster when sorting by yr
def count_sort (array):
    year_array = [0 for i in range(1966,2020)]
    #print "year array created"
    for gm in array:
        year_array[gm['year'] - 1966] += 1
    lte = 0
    #print "calculate lte year array"
    for i in range(0,len(year_array)):
        year_array[i] += lte
        lte = year_array[i]
    out_array = [0 for i in range(len(array))]
    j = len(array) - 1
    #print "populate output array"
    while(j >= 0):
        out_array[year_array[array[j]['year'] - 1966] - 1] = array[j]
        year_array[array[j]['year'] - 1966] -= 1
        j -= 1
    return out_array

def get_hist(input_array = []):
    print 'in get_hist'
    flength = float(len(input_array))
    sumval = 0
    sumvalsq = 0
    for i in input_array:
        sumval += i
        sumvalsq += i*i
    mean = float(sumval)/flength
    variance = (float(sumvalsq)/flength) - (mean*mean)
    print 'about to calc sqrt, variance = %f'%variance
    stdev = math.sqrt(variance)
    output_array = [[],[]]
    print 'mean/stdev calculated'
    #output array is 2d: keys in row 0, values in row 1
    #simpler than a dictionary cause dictionary doesnt preserve order
    for i in range(7):
        bucket = '%d'% (int(mean-(3.5-i)*stdev))
        output_array[0].append(bucket)
        output_array[1].append(0)
    for val in input_array:
        i = 0
        while(i < 7):
            upperbound = mean-(3-i)*stdev
            lowerbound = mean-(3-i+1)*stdev
            if((val <  upperbound or i == 6) and (val >= lowerbound or i == 0)):
                output_array[1][i] += 1
                i = 6
            i += 1 
    print 'leaving get_hist'
    return output_array

  
    
def get_color_array(input_array):
    output_array=[]
    for i in input_array:
        if(i >= 55):
            output_array.append((0,1,0))
        elif(i >= 45):
            output_array.append((1,1,0))
        else:
            output_array.append((1,.2,0))
    return output_array

def uniq(input):
    output = []
    for x in input:
        if x not in output:
            output.append(x)
    return output

"""
The below method will return what I believe 
is the most popular player with a nonunique name
"""
def resolve_nonunique_players(lastname, firstname, player_filter):
    if(lastname == 'peterson' and firstname == 'adrian'):
        return Players.objects.get(pk=25394) 
    elif(lastname == 'smith' and firstname == 'alex'):
        return Players.objects.get(pk=23436) 
    elif(lastname == 'brown' and firstname == 'antonio'):
        return Players.objects.get(pk=27793) 
    elif(lastname == 'johnson' and firstname == 'chris'):
        return Players.objects.get(pk=26164) 
    elif(lastname == 'johnson' and firstname == 'steve'):
        return Players.objects.get(pk=768) 
    elif(lastname == 'newton' and firstname == 'cam'):
        return Players.objects.get(pk=27939) 
    elif(lastname == 'williams' and firstname == 'mike'):
        return Players.objects.get(pk=27702) 
    else:
        # Unless specified, we should return the player with the most amount of games played
        index = 0
        max_games = 0
        return_index = 0
        for player in player_filter:
            num_games = Gameplayers.objects.filter(player = player_filter[0]).count()
            if ( num_games > max_games ):
                max_games = num_games
                return_index = index
            index += 1
        return player_filter[return_index]

"""
The below method will try to keep track of popular nicknames.
If the list gets too big will have to create a db
"""
def get_nickname(lastname,firstname):
    if(lastname=='thomas' and firstname=='dez'):
        return Players.objects.filter(lastname='thomas',firstname='demaryius')
    elif(lastname=='ochocinco' and firstname=='chad'):
        return Players.objects.filter(lastname='johnson',firstname='chad')
    else:
        return None

def filter_objlist(input_list, key, value, comptype='='):
    print "in filter_objlist, key = %s comptype = %s value = %s"%(key, comptype, str(value))
    output = []
    for x in input_list:
        if(comptype == '='):
            if(x.__getattribute__(key) == value):
                output.append(x)
        elif(comptype == '>'):
            if(float(x.__getattribute__(key)) > value):
                output.append(x)
        elif(comptype == '<'):
            if(float(x.__getattribute__(key)) < value):
                output.append(x)
    return output

"""
this helper method allows us to get a param whether it is POST or GET
"""
def get_request_param(request, param, default=0):
    post_val = request.POST.get(param, default)
    if(post_val != default):
        print 'Post data sent, param = %s' % param
        return post_val
    else:
        get_val = request.GET.get(param, default)
        print 'GET data sent, param = %s' % param
        return get_val

def reverseCompType(comptype):
    if(comptype == '>'):
        return '<'
    elif(comptype == '<'):
        return '>'
    return comptype  

def get_defer_fields(team_a,team_b):
    print 'in get_defer_fields'
    defer_fields = ['away_team','home_team','away_team_spread','over_under',
                    'away_team_score','home_team_score','away_team_record',
                    'home_team_record','season','away_team_yards',
                    'home_team_yards','home_team_rushing_yards','away_team_rushing_yards',
                    'home_team_passing_yards','away_team_passing_yards','stadium','fieldtype',
                    'away_coach','home_coach']
    #conditions = team_a
    #conditions.extend(team_b)
    print 'iterate over conditions'
    for list in [team_a, team_b]:
        for item in list:
            print item['type']
            if(item['type'] in ['favoredBy', 'underdogOf']):
                if(defer_fields.count('away_team_spread') > 0):
                    defer_fields.remove('away_team_spread')
                if(defer_fields.count('away_team') > 0):
                    defer_fields.remove('away_team')
                if(defer_fields.count('home_team') > 0):
                    defer_fields.remove('home_team')
            elif(item['type'] == 'season'):
                if(defer_fields.count('season') > 0):
                    defer_fields.remove('season')
            elif(item['type'] in ['group','team']):
                if(defer_fields.count('away_team') > 0):
                    defer_fields.remove('away_team')
                if(defer_fields.count('home_team') > 0):
                    defer_fields.remove('home_team')
            elif(item['type'] in ['isHome','isAway']):
                if(defer_fields.count('away_team') > 0):
                    defer_fields.remove('away_team')
                if(defer_fields.count('home_team') > 0):
                    defer_fields.remove('home_team')
            elif(item['type'] == "WinPercentage"):
                if(defer_fields.count('home_team_record') > 0):
                    defer_fields.remove('home_team_record')
                if(defer_fields.count('away_team_record') > 0):
                    defer_fields.remove('away_team_record')
            elif(item['type'] == 'over_under'):
                if(defer_fields.count('over_under') > 0):
                    defer_fields.remove('over_under')
    return defer_fields
      

def get_home_away_conditions( team_a_conditions, team_b_conditions ):
    use_home_team = True
    use_away_team = True
    for item in team_a_conditions:
        if(item['type'] == 'isHome'):
            use_away_team = False
        elif(item['type'] == 'isAway'):
            use_home_team = False
    #remember that team b having to be away is the same as team a having to be home
    for item in team_b_conditions:
        if(item['type'] == 'isHome'):
            use_home_team = False
        elif(item['type'] == 'isAway'):
            use_away_team = False
    return ( use_home_team, use_away_team )

# Different people will give win percentage in different ways.
# Some will give .5, others 50, others 500.  Of course there is now
# only one way to give 1%, which is .01, but noone should care about this.
def get_record( input ):
    if ( Decimal( input ) <= Decimal( '1' ) ):
        return Decimal(input)
    elif( Decimal( input ) <= Decimal( '100' ) ):
        return Decimal(input)/100
    elif( Decimal( input ) <= Decimal( '1000' ) ):
        return Decimal(input)/1000
    return Decimal( input )
    



           
      
def main(request={}):
    csrf_request = {}
    response = render_to_response('main.html',  csrf_request,context_instance=RequestContext(request))
    return response

def about(request={}):
    csrf_request = {}
    response = render_to_response('about.html',  csrf_request,context_instance=RequestContext(request))
    return response

def submit(request):
    query_tracker = QueryTracker()
    query_tracker.num_team_a_conditions = int(get_request_param(request,'num_team_a_conditions',0))
    query_tracker.num_team_b_conditions = int(get_request_param(request,'num_team_b_conditions',0))
    query_tracker.num_game_conditions = int(get_request_param(request,'num_game_conditions',0))
    query_tracker.queried_players = []
  
    query_tracker.get_conditions( request )
  
    #determine defer fields based on conditions
    defer_fields = get_defer_fields(query_tracker.team_a_conditions, query_tracker.team_b_conditions)
    query_tracker.games_def = Games.objects.all()
    for param in defer_fields:
        query_tracker.games_def = query_tracker.games_def.defer(param) 
  
    print "after deferment, team a conditions are:"
    for item in query_tracker.team_a_conditions:
        print item 
  
    query_tracker.init_team_a_dict()
  
    # Now that we've filtered home vs away  we can query based on other conditions
    # The first conditions should be those that dont add/subtract to teama list such 
    # as year, week, etc.  These are simpler and in most use cases  they will severely
    # reduce the data set.  Due to sqlite's  'too many SQL variables' bug
    # the exclude function will fail if the number of chains is too hi.  My add hoc 
    # solution is to initially split the data set into 4 (based on weeks) and then sum 
    # the querySets before we send them to be analyzed. 
    query_tracker.final_result_array = []
    final_result_date_array = []
    num_buckets = 7
    bucket_size = 24/num_buckets
    for i in range(num_buckets):
        ( query_tracker.use_home_team, query_tracker.use_away_team ) = get_home_away_conditions( query_tracker.team_a_conditions, query_tracker.team_b_conditions )
        query_tracker.gameset = query_tracker.games_def.filter(week__in=range( bucket_size*i+1, bucket_size*i+1+bucket_size ))
        if(query_tracker.gameset.exists()):
            query_tracker.result_array = query_tracker.gameset
            query_tracker.team_a_conditions_exist = False
            # the following lists the "team_a" teams.  It will be used later in team b logic
            query_tracker.team_a_list = []
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "season" )
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "week" )
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "fieldtype" )
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "temperature" )
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "wind" )
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "humidity" )
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "over_under" )
            
            # beginning of conditions that effect team_a_dict
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "group" )
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "team" )
      
            # we do spread calculations after we have done all team/group filtering
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "favoredBy" )
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "underdogOf" )
          
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "WinPercentage" )
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "WinStrak" )
      
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "coach" )
      
            # Ideally  want to do player queries last, as they are most computationally involved
            # and so perf will benefit from smaller data set
            query_tracker.query_wrapper( query_tracker.team_a_conditions, "player", team="a" )
          
            # uniquify a before its passed to b 
            if(query_tracker.result_array != []):
                query_tracker.result_array = query_tracker.result_array.distinct()
                print "uniquified team a query_tracker.results, num query_tracker.results = %d"%query_tracker.result_array.count() 
      
            # two things can lead to a 0 length array at this point:
            # one is no conditions yet.  The other is we already have no matches
            if(not query_tracker.team_a_conditions_exist):
              query_tracker.result_array = query_tracker.gameset 
            
            print 'beginning of team b conditions'
            # For team b, we will further limit what we obtained from team a conditions
            # note that while team a conditions are required, team b conditions are not
            # if no team b conditions, the results are the team a results 
            # Lets first see if team b is restricted to home or away
            query_tracker.team_b_conditions_exist = False
            ( query_tracker.use_home_team, query_tracker.use_away_team ) = get_home_away_conditions( query_tracker.team_b_conditions, query_tracker.team_a_conditions )
      
            # Now that we've done that we can query based on other conditions
            # remember that this time we are querying team a results
            print 'searching for team b group conditions'
            query_tracker.query_wrapper( query_tracker.team_b_conditions, "opposition_group" )
            query_tracker.query_wrapper( query_tracker.team_b_conditions, "opposition_team" )
            query_tracker.query_wrapper( query_tracker.team_b_conditions, "opposition_WinPercentage" )
            query_tracker.query_wrapper( query_tracker.team_b_conditions, "opposition_WinStrak" )
            query_tracker.query_wrapper( query_tracker.team_b_conditions, "opposition_coach" )
      
            # Ideally  want to do player queries last, as they are most computationally
            # involved and so perf will benefit from smaller data set
            query_tracker.query_wrapper( query_tracker.team_b_conditions, "player", team="b" )
            print 'done searching for team b conditions'
      
            # end of parsing team b conditions
            if(not query_tracker.team_b_conditions_exist):
                print "no team b conditions!"
            elif(query_tracker.result_array != []):
                print 'begin final uniquification'
                query_tracker.result_array = query_tracker.result_array.distinct()
                print "after final uniquification, length of result array is %d"%(query_tracker.result_array.count())
            for i in query_tracker.result_array:
                final_result_date_array.append({'pk':i.pk, 'year':i.date.year})
  
    print 'beginning of post collection calculations'
    # data collected, now calculate winnings/team data
    # put total results back in result array.
    final_result_date_array = count_sort(final_result_date_array)
    for item in final_result_date_array:
        query_tracker.final_result_array.append(item['pk'])
  
    query_tracker.get_game_data()
    query_tracker.get_summary_hist()
    #gather player data
    query_tracker.get_player_data()
  
    if(len(query_tracker.final_result_array) > 0):
        query_tracker.response['results_exist'] = 1
    else:
        query_tracker.response['results_exist'] = 0
  
    print 'Converting to json'
    json_str = json.dumps(query_tracker.response)
    if ( sys.version_info > (2, 7) ):
        return HttpResponse(json_str, content_type='application/json')
    else:
        return HttpResponse(json_str, mimetype='application/json')



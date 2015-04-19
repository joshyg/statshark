# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.context_processors import csrf
from teamstats.models import Games,Players,GamePlayers,QbGameStats,RbWrGameStats,Coaches,DefGameStats,GameExtras,GameStreaks
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
        self.team_a_conditions_exist = False
        self.team_a_conditions = []
        self.team_b_conditions = []
        self.num_team_a_conditions = 0
        self.num_team_b_conditions = 0
        self.num_game_conditions = 0
        self.team_a_dict = {}
        self.team_a_list = []
        self.queried_players = []
        self.player_game_list = []

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

query_tracker = QueryTracker()


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

def filter_by_season( item ):
    print "about to compute season conditions"
    #if at this point the results array is empty, it means we havent filtered 
    #by season/week/other team neutral conditions yet
    if(len(query_tracker.result_array) == 0 and not query_tracker.team_a_conditions_exist):
        tmp_team_a_list = query_tracker.gameset
    else:
        tmp_team_a_list = query_tracker.result_array
        query_tracker.result_array = []
    #print "tmp_team_a_list gathered, length = %d"%len(tmp_team_a_list)
    query_tracker.team_a_conditions_exist = True
    print "about to filter on comptype"
    if(item['comptype'] == '='):
        tmp_team_a_list = tmp_team_a_list.filter(season=int(item['value']))
    elif(item['comptype'] == '<'):
        tmp_team_a_list = tmp_team_a_list.filter(season__lt=int(item['value']))
    elif(item['comptype'] == '>'):
        tmp_team_a_list = tmp_team_a_list.filter(season__gt=int(item['value']))
    query_tracker.result_array = tmp_team_a_list  

def filter_by_week( item ):
    print "about to compute week conditions"
    #if at this point the results array is empty, it means we havent filtered 
    #by week/week/oter team neutral conditions yet
    if(len(query_tracker.result_array) == 0 and not query_tracker.team_a_conditions_exist):
        print "first condition"
        tmp_team_a_list = query_tracker.gameset 
    else:
        tmp_team_a_list = query_tracker.result_array
        query_tracker.result_array = []
    print "tmp_team_a_list gathered, length = %d"%len(tmp_team_a_list)
    query_tracker.team_a_conditions_exist = True
    print "about to filter on comptype"
    if(item['comptype'] == '='):
        if(int(item['value']) < 21):
            tmp_team_a_list = tmp_team_a_list.filter(week=int(item['value']))
        else:
            #some years the SuperBowl is wk 22
            tmp_team_a_list = tmp_team_a_list.filter(week__gte=21)
        
    elif(item['comptype'] == '<'):
        tmp_team_a_list = tmp_team_a_list.filter(week__lt=int(item['value']))
    elif(item['comptype'] == '>'):
        tmp_team_a_list = tmp_team_a_list.filter(week__gt=int(item['value']))
    query_tracker.result_array = tmp_team_a_list  

def filter_by_fieldtype( item ):
    print "about to compute fieldtype conditions"
    #if at this point the results array is empty, it means we havent filtered 
    #by week/week/oter team neutral conditions yet
    if(len(query_tracker.result_array) == 0 and not query_tracker.team_a_conditions_exist):
      print "first condition"
      tmp_team_a_list = query_tracker.gameset 
    else:
      tmp_team_a_list = query_tracker.result_array
      query_tracker.result_array = []
    print "tmp_team_a_list gathered, length = %d"%len(tmp_team_a_list)
    query_tracker.team_a_conditions_exist = True
    tmp_team_a_list = tmp_team_a_list.filter(fieldtype=item['value'])
    query_tracker.result_array = tmp_team_a_list  

def filter_by_temperature( item ):
    print "about to compute temperature conditions"
    #if at this point the results array is empty, it means we havent filtered 
    #by week/week/oter team neutral conditions yet
    if(len(query_tracker.result_array) == 0 and not query_tracker.team_a_conditions_exist):
        print "first condition"
        tmp_team_a_list = GameExtras.objects.filter(game__in=query_tracker.gameset).exclude(temperature=-100)
    else:
        tmp_team_a_list = GameExtras.objects.filter(game__in=query_tracker.result_array).exclude(temperature=-100)
        query_tracker.result_array = []
    print "tmp_team_a_list gathered, length = %d"%len(tmp_team_a_list)
    query_tracker.team_a_conditions_exist = True
    if(item['comptype'] == '='):
        tmp_team_a_list = tmp_team_a_list.filter(temperature=int(item['value']))
    elif(item['comptype'] == '<'):
        tmp_team_a_list = tmp_team_a_list.filter(temperature__lt=int(item['value']))
    elif(item['comptype'] == '>'):
        tmp_team_a_list = tmp_team_a_list.filter(temperature__gt=int(item['value']))
    query_tracker.result_array = Games.objects.filter(gameextras__in=tmp_team_a_list)

def filter_by_wind( item ):
    print "about to compute wind conditions"
    #if at this point the results array is empty, it means we havent filtered 
    #by week/week/oter team neutral conditions yet
    if(len(query_tracker.result_array) == 0 and not query_tracker.team_a_conditions_exist):
        print "first condition"
        tmp_team_a_list = GameExtras.objects.filter(game__in=query_tracker.gameset).exclude(windspeed=-100) 
    else:
        tmp_team_a_list = GameExtras.objects.filter(game__in=query_tracker.result_array).exclude(windspeed=-100)
        query_tracker.result_array = []
    print "tmp_team_a_list gathered, length = %d"%len(tmp_team_a_list)
    query_tracker.team_a_conditions_exist = True
    if(item['comptype'] == '='):
        tmp_team_a_list = tmp_team_a_list.filter(windspeed=int(item['value']))
    elif(item['comptype'] == '<'):
        tmp_team_a_list = tmp_team_a_list.filter(windspeed__lt=int(item['value']))
    elif(item['comptype'] == '>'):
        tmp_team_a_list = tmp_team_a_list.filter(windspeed__gt=int(item['value']))
    query_tracker.result_array = Games.objects.filter(gameextras__in=tmp_team_a_list)

def filter_by_humidity( item ):
    print "about to compute humidity conditions"
    #if at this point the results array is empty, it means we havent filtered 
    #by week/week/oter team neutral conditions yet
    if(len(query_tracker.result_array) == 0 and not query_tracker.team_a_conditions_exist):
        print "first condition"
        tmp_team_a_list = GameExtras.objects.filter(game__in=query_tracker.gameset).exclude(humidity=-100) 
    else:
        tmp_team_a_list = GameExtras.objects.filter(game__in=query_tracker.result_array).exclude(humidity=-100)
        query_tracker.result_array = []
    print "tmp_team_a_list gathered, length = %d"%len(tmp_team_a_list)
    query_tracker.team_a_conditions_exist = True
    if(item['comptype'] == '='):
        tmp_team_a_list = tmp_team_a_list.filter(humidity=int(item['value']))
    elif(item['comptype'] == '<'):
        tmp_team_a_list = tmp_team_a_list.filter(humidity__lt=int(item['value']))
    elif(item['comptype'] == '>'):
        tmp_team_a_list = tmp_team_a_list.filter(humidity__gt=int(item['value']))
    query_tracker.result_array = Games.objects.filter(gameextras__in=tmp_team_a_list)

def filter_by_over_under( item ):
    print "about to compute over_under conditions"
    #if at this point the results array is empty, it means we havent filtered 
    #by over_under/week/oter team neutral conditions yet
    if(len(query_tracker.result_array) == 0 and not query_tracker.team_a_conditions_exist):
        tmp_team_a_list = query_tracker.gameset.filter(over_under__gt=0) 
    else:
        tmp_team_a_list = query_tracker.result_array.filter(over_under__gt=0)
        query_tracker.result_array = []
    team_a_conditions_exist = True
    print "about to filter on comptype"
    if(item['comptype'] == '='):
        tmp_team_a_list = tmp_team_a_list.filter(over_under=int(item['value']))
    elif(item['comptype'] == '<'):
        tmp_team_a_list = tmp_team_a_list.filter(over_under__lt=int(item['value']))
    elif(item['comptype'] == '>'):
        tmp_team_a_list = tmp_team_a_list.filter(over_under__gt=int(item['value']))
    query_tracker.result_array = tmp_team_a_list  

def filter_by_group( item ):
    print ("Querying %s"% groups[int(item['value'])])
    #if at this point the results array is empty, it means we havent filtered 
    #by season/week/other team neutral conditions yet
    if(not query_tracker.team_a_conditions_exist):
        tmp_team_a_list = query_tracker.gameset 
    else:
        tmp_team_a_list = query_tracker.result_array
        query_tracker.result_array = []
    print "tmp_team_a_list gathered, length = %d"%len(tmp_team_a_list)
    query_tracker.team_a_conditions_exist = True
    team_a_index_list = []
    for team in groups[int(item['value'])]:
        team_index = teams.index(team)
        query_tracker.team_a_list.append(team)
        team_a_index_list.append(team_index)
    if(query_tracker.use_away_team and not query_tracker.use_home_team):
        query_tracker.result_array =  tmp_team_a_list.filter(away_team__in=team_a_index_list)
        for game in query_tracker.result_array:
            query_tracker.team_a_dict[game.pk] = game.away_team
    elif(query_tracker.use_home_team and not query_tracker.use_away_team):
        print 'size result_array before team filter: %d'%(tmp_team_a_list.count())
        query_tracker.result_array =  tmp_team_a_list.filter(home_team__in=team_a_index_list)
        print 'size result_array after team filter: %d'%(result_array.count())
        for game in query_tracker.result_array:
            query_tracker.team_a_dict[game.pk] = game.home_team
    elif(query_tracker.use_home_team and query_tracker.use_away_team): 
        query_tracker.result_array =  tmp_team_a_list.filter(Q(home_team__in=team_a_index_list)|Q(away_team__in=team_a_index_list))
        for game in result_array:
            if(game.home_team in team_a_index_list): 
                query_tracker.team_a_dict[game.pk] = game.home_team
            else:
                query_tracker.team_a_dict[game.pk] = game.away_team

def filter_by_opposition_group( item ):
    print("team b has group conditions")
    if(not query_tracker.team_b_conditions_exist):
      tmp_result_array = query_tracker.result_array
    else:
      tmp_result_array = []
    query_tracker.team_b_conditions_exist = True
    #print 'result size before group condition filtering is %d'%tmp_result_array.count()
    team_b_index_list = []
    team_a_index_list = []
    for t in query_tracker.team_a_list:
      team_a_index_list.append(query_tracker.team_a_list.index(t))
    for team in groups[int(item['value'])]:
      #explanation of following condition: Jets vs AFC east
      #in team a filter we get jets vs SF.  Now we want to remove SF
      #but since jets are in AFC east, they will not be removed (without this condition)  
      team_index = teams.index(team)
      print "searching for team b = %s, index %d"%(team,team_index)
      if(query_tracker.team_a_list.count(team) == 0):
        team_index = teams.index(team)
        team_b_index_list.append(team_index)
    if(query_tracker.use_away_team and not query_tracker.use_home_team):
      print 'using away'
      for t in teams:
        if(teams.index(t) not in team_b_index_list and teams.index(t) not in team_a_index_list):
          print 'excluding %s %d from final results size of results now = %d'%(t,teams.index(t),tmp_result_array.count())
          tmp_result_array =  tmp_result_array.exclude(Q(away_team=int(teams.index(t))))
      query_tracker.result_array = tmp_result_array
      for game in query_tracker.result_array:
        query_tracker.team_a_dict[game.pk] = game.home_team
    elif(query_tracker.use_home_team and not query_tracker.use_away_team):
      print 'using home'
      print team_b_index_list
      for t in teams:
        if(teams.index(t) not in team_b_index_list and teams.index(t) not in team_a_index_list):
          tmp_result_array =  tmp_result_array.exclude(home_team=teams.index(t))
      query_tracker.result_array = tmp_result_array
      for game in query_tracker.result_array:
        result_query.team_a_dict[game.pk] = game.away_team
    elif(query_tracker.use_home_team and query_tracker.use_away_team): 
      print 'using home and away, length of team list is %d'%(len(team_b_index_list))
      for game in tmp_result_array:
        if(result_query.team_a_dict[game.pk] == game.away_team and (game.home_team not in team_b_index_list) or
           result_query.team_a_dict[game.pk] == game.home_team and (game.away_team not in team_b_index_list)):
          print 'excluding!'
          tmp_result_array =  tmp_result_array.exclude(gameid=game.pk)
      query_tracker.result_array = tmp_result_array  
    print 'team b group condition check is complete'

def filter_by_team( item ):
    print "about to compute  team conditions"
    query_tracker.team_a_list.append(teams[int(item['value'])])
    #if at this point the results array is empty, it means we havent filtered 
    #by season/week/other team neutral conditions yet
    if(len(query_tracker.result_array) == 0 and not query_tracker.team_a_conditions_exist):
        tmp_result_array = query_tracker.gameset 
    else:
        tmp_result_array = query_tracker.result_array
    query_tracker.team_a_conditions_exist = True
    print "tmp_result_array gathered, length = %d"%len(tmp_result_array)
    print 'calculate for away team'
    if(query_tracker.use_away_team and not query_tracker.use_home_team):
        query_tracker.result_array = tmp_result_array.filter(away_team=int(item['value']))
        for game in query_tracker.result_array:
            query_tracker.team_a_dict[game.pk] = game.away_team
    elif(query_tracker.use_home_team and not query_tracker.use_away_team):
        query_tracker.result_array = tmp_result_array.filter(home_team=int(item['value']))
        for game in query_tracker.result_array:
            query_tracker.team_a_dict[game.pk] = game.home_team
    elif(query_tracker.use_home_team and query_tracker.use_away_team):
        query_tracker.result_array = tmp_result_array.filter(Q(home_team=int(item['value'])) | Q(away_team=int(item['value'])))
        for game in query_tracker.result_array:
            if(int(item['value']) == game.home_team):
                query_tracker.team_a_dict[game.pk] = game.home_team
            else:
                query_tracker.team_a_dict[game.pk] = game.away_team

def filter_by_opposition_team( item ):
    print "about to filter team b by team"
    if(not query_tracker.team_b_conditions_exist):
        tmp_team_b_list = query_tracker.result_array
    else:
        tmp_team_b_list = query_tracker.result_array
    query_tracker.team_b_conditions_exist = True
    if(query_tracker.use_away_team and not query_tracker.use_home_team):
        query_tracker.result_array = tmp_team_b_list.filter(away_team=int(item['value']))
        for game in query_tracker.result_array:
            query_tracker.team_a_dict[game.pk] = game.home_team
    elif(query_tracker.use_home_team and not query_tracker.use_away_team):
        query_tracker.result_array = tmp_team_b_list.filter(home_team=int(item['value']))
        for game in query_tracker.result_array:
            query_tracker.team_a_dict[game.pk] = game.away_team
    elif(query_tracker.use_home_team and query_tracker.use_away_team):
        query_tracker.result_array = tmp_team_b_list.filter(Q(home_team=int(item['value'])) | Q(away_team=int(item['value'])))
        for game in query_tracker.result_array:
            if(int(item['value']) == game.home_team):
                query_tracker.team_a_dict[game.pk] = game.away_team
            else:
                query_tracker.team_a_dict[game.pk] = game.home_team
    print "done filtering team b by team, length of result array is %d"%(query_tracker.result_array.count())

def filter_by_spread( item ):
    print "about to compute spread conditions"
    #if at this point the results array is empty, it means we havent filtered 
    #by team/conf yet and so we have to  take everything
    if(len(query_tracker.result_array) == 0 and not query_tracker.team_a_conditions_exist):
        #-100 indicates we dont have spread info, which is true of games < 1978
        tmp_team_a_list = query_tracker.gameset.filter(away_team_spread__gt=-100) 
    else:
        tmp_team_a_list = query_tracker.result_array.filter(away_team_spread__gt=-100)
        query_tracker.result_array = []
    query_tracker.team_a_conditions_exist = True
    #print "tmp_team_a_list gathered, length = %d"%len(tmp_team_a_list)
    if(query_tracker.use_away_team and query_tracker.use_home_team):
        print 'using home and away'
        #gather games that might satisfy our results if the satisfying teams are in our dict
        if(item['comptype'] == '='):
            tmp_result_array = tmp_team_a_list.filter(Q(away_team_spread=Decimal(item['value'])) | Q(away_team_spread=-1*Decimal(item['value'])))
        elif(item['comptype'] == '<'):
            tmp_result_array = tmp_team_a_list.filter(Q(away_team_spread__lt=Decimal(item['value']))|Q(away_team_spread__gt=-1*Decimal(item['value'])))
        elif(item['comptype'] == '>'):
            tmp_result_array = tmp_team_a_list.filter(Q(away_team_spread__gt=Decimal(item['value']))|Q(away_team_spread__lt=-1*Decimal(item['value'])))
    elif(query_tracker.use_away_team):
        print 'using just away'
        if(item['comptype'] == '='):
            tmp_result_array = tmp_team_a_list.filter(away_team_spread=Decimal(item['value']))
        elif(item['comptype'] == '<'):
            tmp_result_array = tmp_team_a_list.filter(away_team_spread__lt=Decimal(item['value']))
        elif(item['comptype'] == '>'):
            tmp_result_array = tmp_team_a_list.filter(away_team_spread__gt=Decimal(item['value']))
    else:
        print 'using just home'
        if(item['comptype'] == '='):
            tmp_result_array = tmp_team_a_list.filter(away_team_spread=-1*Decimal(item['value']))
        elif(item['comptype'] == '<'):
            tmp_result_array = tmp_team_a_list.filter(away_team_spread__gt=-1*Decimal(item['value']))
        elif(item['comptype'] == '>'):
            tmp_result_array = tmp_team_a_list.filter(away_team_spread__lt=-1*Decimal(item['value']))
   
    print 'gather comparrison arrays to determine team_a_dict'
    #gather the results where the away team satisfies 
    if(item['comptype'] == '='):
        tmp_result_array_away = tmp_team_a_list.filter(away_team_spread=Decimal(item['value']))
    elif(item['comptype'] == '<'):
        tmp_result_array_away = tmp_team_a_list.filter(away_team_spread__lt=Decimal(item['value']))
    elif(item['comptype'] == '>'):
        tmp_result_array_away = tmp_team_a_list.filter(away_team_spread__gt=Decimal(item['value']))
    #gather the results where the home team satisfies 
    if(item['comptype'] == '='):
        tmp_result_array_home = tmp_team_a_list.filter(away_team_spread=-1*Decimal(item['value']))
    elif(item['comptype'] == '<'):
        tmp_result_array_home = tmp_team_a_list.filter(away_team_spread__gt=-1*Decimal(item['value']))
    elif(item['comptype'] == '>'):
        tmp_result_array_home = tmp_team_a_list.filter(away_team_spread__lt=-1*Decimal(item['value']))
    #iterate over team a dict, determine which team is team a, and if a game was included where satisfying team is not team a, exclude them
    print 'generate exclusion_list'
    exclusion_pk_list = []
    for game in tmp_result_array:
        game_pk = game.pk
        if(not query_tracker.team_a_dict.has_key(game_pk)):
            if(tmp_result_array_away.filter(gameid=game_pk).exists()):
                query_tracker.team_a_dict[game_pk] = game.away_team
            else:
                query_tracker.team_a_dict[game_pk] = game.home_team
        elif(query_tracker.team_a_dict[game_pk] == game.away_team):
            if(tmp_result_array_away.filter(gameid=game_pk).exists()):
                query_tracker.team_a_dict[game_pk] = game.away_team
            else:
                exclusion_pk_list.append(game_pk)
        elif(query_tracker.team_a_dict[game_pk] == game.home_team):
            if(tmp_result_array_home.filter(gameid=game_pk).exists()):
                query_tracker.query_tracker.team_a_dict[game_pk] = game.home_team
            else:
                 exclusion_pk_list.append(game_pk)
    #testing exclude
    print 'exclusion_list computed.  length = %d'%(len(exclusion_pk_list))
    if(exclusion_pk_list != []):
        for key in exclusion_pk_list:
            tmp_result_array = tmp_result_array.exclude(gameid=key)
        query_tracker.result_array = tmp_result_array
    else:
        query_tracker.result_array = tmp_result_array
    print 'spread conditions computed.  length = %d'%(result_array.count())

def filter_by_win_percentage( item ):
    print "about to compute WinPercentage conditions"
    #if at this point the results array is empty, it means we havent filtered 
    #by team/conf/spread yet and so we have to  take everything
    if(len(query_tracker.result_array) == 0 and not query_tracker.team_a_conditions_exist):
      tmp_team_a_list = query_tracker.gameset 
    else:
      tmp_team_a_list = result_array
      query_tracker.result_array = []
    query_tracker.team_a_conditions_exist = True
    if(query_tracker.use_away_team and query_tracker.use_home_team):
      #a note on the team a dict for win%:
      # as a stand alone feature, the win% only makes sense if both teams are assigned miutually exclusive
      #constraints.  Like a +500 team versus a minus 500.   So, if home and away are being used
      # I only assign to the team_a_dict in the team_b constraints
      if(item['comptype'] == '='):
        query_tracker.result_array = tmp_team_a_list.filter(Q(away_team_record=Decimal(item['value'])) | Q(home_team_record=Decimal(item['value'])))
        result_array_away = tmp_team_a_list.filter(away_team_record=Decimal(item['value']))
        result_array_home = tmp_team_a_list.filter(home_team_record=Decimal(item['value']))
      elif(item['comptype'] == '<'):
        query_tracker.result_array = tmp_team_a_list.filter(Q(away_team_record__lt=Decimal(item['value']))|Q(home_team_record__lt=Decimal(item['value'])))
        result_array_away = tmp_team_a_list.filter(away_team_record__lt=Decimal(item['value']))
        result_array_home = tmp_team_a_list.filter(home_team_record__lt=Decimal(item['value']))
      elif(item['comptype'] == '>'):
        query_tracker.result_array = tmp_team_a_list.filter(Q(away_team_record__gt=Decimal(item['value']))|Q(home_team_record__gt=Decimal(item['value'])))
        result_array_away = tmp_team_a_list.filter(away_team_record__gt=Decimal(item['value']))
        result_array_home = tmp_team_a_list.filter(home_team_record__gt=Decimal(item['value']))
      #we dont assign team_A_dict in this condition, but if its already assigned, take it into consideration
      print 'result_array count = %d'%result_array.count()
      exclusion_list = []
      for game in query_tracker.result_array:
        if(query_tracker.team_a_dict.has_key(game.pk)):
          if((not result_array_away.filter(gameid=game.pk).exists()) and query_tracker.team_a_dict[game.pk] == game.away_team or
             (not result_array_home.filter(gameid=game.pk).exists()) and query_tracker.team_a_dict[game.pk] == game.home_team):
             print 'adding to exclusion list'
             exclusion_list.append(game.pk)
      for gameid in exclusion_list:
        query_tracker.result_array = query_tracker.result_array.exclude(gameid=gameid) 
      print 'result_array count = %d'%query_tracker.result_array.count()
          
    elif(query_tracker.use_away_team):
      if(item['comptype'] == '='):
        query_tracker.result_array = tmp_team_a_list.filter(away_team_record=Decimal(item['value']))
      elif(item['comptype'] == '<'):
        query_tracker.result_array = tmp_team_a_list.filter(away_team_record__lt=Decimal(item['value']))
      elif(item['comptype'] == '>'):
        query_tracker.result_array = tmp_team_a_list.filter(away_team_record__gt=Decimal(item['value']))
      for game in query_tracker.result_array:
        if(not team_a_dict.has_key(game.pk)):
          query_tracker.team_a_dict[game.pk] = game.away_team
    else:
      if(item['comptype'] == '='):
        query_tracker.result_array = tmp_team_a_list.filter(home_team_record=Decimal(item['value']))
      elif(item['comptype'] == '<'):
        query_tracker.result_array = tmp_team_a_list.filter(home_team_record__lt=Decimal(item['value']))
      elif(item['comptype'] == '>'):
        query_tracker.result_array = tmp_team_a_list.filter(home_team_record__gt=Decimal(item['value']))
      for game in query_tracker.result_array:
        if(not query_tracker.team_a_dict.has_key(game.pk)):
          query_tracker.team_a_dict[game.pk] = game.home_team

def filter_by_opposition_win_percentage( item ):
    print "about to compute WinPercentage conditions"
    tmp_team_b_list = query_tracker.result_array
    query_tracker.result_array = []
    query_tracker.team_b_conditions_exist = True
    
    print "tmp_team_b_list gathered"
    if(tmp_team_b_list != []):
      if(query_tracker.use_away_team and query_tracker.use_home_team):
        #a note on the team a dict for win%:
        # as a stand alone feature, the win% only makes sense if both teams are assigned miutually exclusive
        #constraints.  Like a +500 team versus a minus 500.   So, if home and away are being used
        # I only assign to the team_a_dict in the team_b constraints
        if(item['comptype'] == '='):
          query_tracker.result_array = tmp_team_b_list.filter(Q(away_team_record=Decimal(item['value'])) | Q(home_team_record=Decimal(item['value'])))
          query_tracker.result_array_away = tmp_team_b_list.filter(away_team_record=Decimal(item['value']))
          query_tracker.result_array_home = tmp_team_b_list.filter(home_team_record=Decimal(item['value']))
        elif(item['comptype'] == '<'):
          query_tracker.result_array = tmp_team_b_list.filter(Q(away_team_record__lt=Decimal(item['value']))|Q(home_team_record__lt=Decimal(item['value'])))
          query_tracker.result_array_away = tmp_team_b_list.filter(away_team_record__lt=Decimal(item['value']))
          query_tracker.result_array_home = tmp_team_b_list.filter(home_team_record__lt=Decimal(item['value']))
        elif(item['comptype'] == '>'):
          query_tracker.result_array = tmp_team_b_list.filter(Q(away_team_record__gt=Decimal(item['value']))|Q(home_team_record__gt=Decimal(item['value'])))
          query_tracker.result_array_away = tmp_team_b_list.filter(away_team_record__gt=Decimal(item['value']))
          query_tracker.result_array_home = tmp_team_b_list.filter(home_team_record__gt=Decimal(item['value']))
        print 'query_tracker.result_array_team_b count = %d'%query_tracker.result_array.count()
        #imagine team a is the viking, we want them against teams that have < 500 record.  
        #make sure to exclude games where only the vikings have < 500 record
        exclusion_list = []
        for game in query_tracker.result_array:
          if(query_tracker.team_a_dict.has_key(game.pk)):
            if((not query_tracker.result_array_away.filter(gameid=game.pk).exists()) and query_tracker.team_a_dict[game.pk] == game.home_team or
               (not query_tracker.result_array_home.filter(gameid=game.pk).exists()) and query_tracker.team_a_dict[game.pk] == game.away_team):
               print 'adding to exclusion list'
               exclusion_list.append(game.pk)
          #print 'query_tracker.result_array_team_b count = %d'%query_tracker.result_array.count()
        for gameid in exclusion_list:
          query_tracker.result_array = query_tracker.result_array.exclude(gameid=gameid) 
        #print 'query_tracker.result_array_team_b count = %d'%query_tracker.result_array.count()
        for game in query_tracker.result_array:
          if(not query_tracker.team_a_dict.has_key(game.pk)):
            if(query_tracker.result_array_away.filter(gameid=game.pk).exists()):
              query_tracker.team_a_dict[game.pk] = game.home_team
            else:
              query_tracker.team_a_dict[game.pk] = game.away_team
            
      elif(query_tracker.use_away_team):
        if(item['comptype'] == '='):
          query_tracker.result_array = tmp_team_b_list.filter(away_team_record=Decimal(item['value']))
        elif(item['comptype'] == '<'):
          query_tracker.result_array = tmp_team_b_list.filter(away_team_record__lt=Decimal(item['value']))
        elif(item['comptype'] == '>'):
          query_tracker.result_array = tmp_team_b_list.filter(away_team_record__gt=Decimal(item['value']))
        for game in query_tracker.result_array:
          if(not query_tracker.team_a_dict.has_key(game.pk)):
            query_tracker.team_a_dict[game.pk] = game.home_team
      else:
        if(item['comptype'] == '='):
          query_tracker.result_array = tmp_team_b_list.filter(home_team_record=Decimal(item['value']))
        elif(item['comptype'] == '<'):
          query_tracker.result_array = tmp_team_b_list.filter(home_team_record__lt=Decimal(item['value']))
        elif(item['comptype'] == '>'):
          query_tracker.result_array = tmp_team_b_list.filter(home_team_record__gt=Decimal(item['value']))
        for game in query_tracker.result_array:
          if(not query_tracker.team_a_dict.has_key(game.pk)):
            query_tracker.team_a_dict[game.pk] = game.away_team
      print "added team_b record conditions" 

def filter_by_win_streak( item ):
    print "about to compute WinStreak conditions"
    #if at this point the results array is empty, it means we havent filtered 
    #by team/conf/spread yet and so we have to  take everything
    if(len(query_tracker.result_array) == 0 and not query_tracker.team_a_conditions_exist):
        tmp_team_a_list = GameStreaks.objects.filter(game__in=query_tracker.gameset)
    else:
        tmp_team_a_list = GameStreaks.objects.filter(game__in=query_tracker.result_array)
        query_tracker.result_array = []
    query_tracker.team_a_conditions_exist = True
    if(query_tracker.use_away_team and query_tracker.use_home_team):
        #a note on the team a dict for win%:
        # as a stand alone feature, the win% only makes sense if both teams are assigned miutually exclusive
        #constraints.  Like a +500 team versus a minus 500.   So, if home and away are being used
        # I only assign to the team_a_dict in the team_b constraints
        if(item['comptype'] == '='):
            query_tracker.result_array = tmp_team_a_list.filter(Q(away_team_win_streak=item['value']) | Q(home_team_win_streak=item['value']))
            result_array_away = tmp_team_a_list.filter(away_team_win_streak=item['value'])
            result_array_home = tmp_team_a_list.filter(home_team_win_streak=item['value'])
        elif(item['comptype'] == '<'):
            query_tracker.result_array = tmp_team_a_list.filter(Q(away_team_win_streak__lt=item['value'])|Q(home_team_win_streak__lt=item['value']))
            result_array_away = tmp_team_a_list.filter(away_team_win_streak__lt=item['value'])
            result_array_home = tmp_team_a_list.filter(home_team_win_streak__lt=item['value'])
        elif(item['comptype'] == '>'):
            query_tracker.result_array = tmp_team_a_list.filter(Q(away_team_win_streak__gt=item['value'])|Q(home_team_win_streak__gt=item['value']))
            result_array_away = tmp_team_a_list.filter(away_team_win_streak__gt=item['value'])
            result_array_home = tmp_team_a_list.filter(home_team_win_streak__gt=item['value'])
        #we dont assign team_A_dict in this condition, but if its already assigned, take it into consideration
        print 'result_array count = %d'%query_tracker.result_array.count()
        query_tracker.result_array = Games.objects.filter(gamestreaks__in=result_array)
        result_array_away = Games.objects.filter(gamestreaks__in=result_array_away)
        result_array_home = Games.objects.filter(gamestreaks__in=result_array_home)
        exclusion_list = []
        for game in query_tracker.result_array:
            if(query_tracker.team_a_dict.has_key(game.pk)):
                if((not result_array_away.filter(gameid=game.pk).exists()) and query_tracker.team_a_dict[game.pk] == game.away_team or
                   (not result_array_home.filter(gameid=game.pk).exists()) and query_tracker.team_a_dict[game.pk] == game.home_team):
                     print 'adding to exclusion list'
                     exclusion_list.append(game.pk)
        for gameid in exclusion_list:
            query_tracker.result_array = query_tracker.result_array.exclude(gameid=gameid) 
        print 'result_array count = %d'%query_tracker.result_array.count()
          
    elif(query_tracker.use_away_team):
        if(item['comptype'] == '='):
            query_tracker.result_array = tmp_team_a_list.filter(away_team_win_streak=item['value'])
        elif(item['comptype'] == '<'):
            query_tracker.result_array = tmp_team_a_list.filter(away_team_win_streak__lt=item['value'])
        elif(item['comptype'] == '>'):
            query_tracker.result_array = tmp_team_a_list.filter(away_team_win_streak__gt=item['value'])
        query_tracker.result_array = Games.objects.filter(gamestreaks__in=query_tracker.result_array)
        for game in query_tracker.result_array:
            if(not query_tracker.team_a_dict.has_key(game.pk)):
                query_tracker.team_a_dict[game.pk] = game.away_team
    else:
        if(item['comptype'] == '='):
            query_tracker.result_array = tmp_team_a_list.filter(home_team_win_streak=item['value'])
        elif(item['comptype'] == '<'):
            query_tracker.result_array = tmp_team_a_list.filter(home_team_win_streak__lt=item['value'])
        elif(item['comptype'] == '>'):
            query_tracker.result_array = tmp_team_a_list.filter(home_team_win_streak__gt=item['value'])
        query_tracker.result_array = Games.objects.filter(gamestreaks__in=query_tracker.result_array)
        for game in query_tracker.result_array:
            if(not query_tracker.team_a_dict.has_key(game.pk)):
                query_tracker.team_a_dict[game.pk] = game.home_team

def filter_by_opposition_win_streak( item ):
    print "about to compute WinStreak conditions"
    if(len(query_tracker.result_array) != 0):
        tmp_team_b_list = GameStreaks.objects.filter(game__in=query_tracker.result_array)
        query_tracker.result_array = []
    else:
        tmp_team_b_list = []
    query_tracker.team_b_conditions_exist = True
    
    print "tmp_team_b_list gathered"
    if(tmp_team_b_list != []):
        if(query_tracker.use_away_team and query_tracker.use_home_team):
            #a note on the team a dict for win%:
            # as a stand alone feature, the win% only makes sense if both teams are assigned miutually exclusive
            #constraints.  Like a +500 team versus a minus 500.   So, if home and away are being used
            # I only assign to the team_a_dict in the team_b constraints
            if(item['comptype'] == '='):
                query_tracker.result_array = tmp_team_b_list.filter(Q(away_team_win_streak=item['value']) | Q(home_team_win_streak=item['value']))
                query_tracker.result_array_away = tmp_team_b_list.filter(away_team_win_streak=item['value'])
                query_tracker.result_array_home = tmp_team_b_list.filter(home_team_win_streak=item['value'])
            elif(item['comptype'] == '<'):
                query_tracker.result_array = tmp_team_b_list.filter(Q(away_team_win_streak__lt=item['value'])|Q(home_team_win_streak__lt=item['value']))
                query_tracker.result_array_away = tmp_team_b_list.filter(away_team_win_streak__lt=item['value'])
                query_tracker.result_array_home = tmp_team_b_list.filter(home_team_win_streak__lt=item['value'])
            elif(item['comptype'] == '>'):
                query_tracker.result_array = tmp_team_b_list.filter(Q(away_team_win_streak__gt=item['value'])|Q(home_team_win_streak__gt=item['value']))
                query_tracker.result_array_away = tmp_team_b_list.filter(away_team_win_streak__gt=item['value'])
                query_tracker.result_array_home = tmp_team_b_list.filter(home_team_win_streak__gt=item['value'])
            print 'query_tracker.result_array_team_b count = %d'%query_tracker.result_array.count()
            #imagine team a is the viking, we want them against teams that have < 500 win_streak.  
            #make sure to exclude games where only the vikings have < 500 win_streak
            query_tracker.result_array = Games.objects.filter(gamestreaks__in=query_tracker.result_array)
            exclusion_list = []
            for game in query_tracker.result_array:
                if(query_tracker.team_a_dict.has_key(game.pk)):
                    if((not query_tracker.result_array_away.filter(gameid=game.pk).exists()) and query_tracker.team_a_dict[game.pk] == game.home_team or
                       (not query_tracker.result_array_home.filter(gameid=game.pk).exists()) and query_tracker.team_a_dict[game.pk] == game.away_team):
                         print 'adding to exclusion list'
                         exclusion_list.append(game.pk)
            #print 'query_tracker.result_array_team_b count = %d'%query_tracker.result_array.count()
            for gameid in exclusion_list:
                query_tracker.result_array = query_tracker.result_array.exclude(gameid=gameid) 
            #print 'query_tracker.result_array_team_b count = %d'%query_tracker.result_array.count()
            for game in query_tracker.result_array:
                if(not query_tracker.team_a_dict.has_key(game.pk)):
                    if(query_tracker.result_array_away.filter(gameid=game.pk).exists()):
                        query_tracker.team_a_dict[game.pk] = game.home_team
                    else:
                        query_tracker.team_a_dict[game.pk] = game.away_team
              
        elif(query_tracker.use_away_team):
            if(item['comptype'] == '='):
                query_tracker.result_array = tmp_team_b_list.filter(away_team_win_streak=item['value'])
            elif(item['comptype'] == '<'):
                query_tracker.result_array = tmp_team_b_list.filter(away_team_win_streak__lt=item['value'])
            elif(item['comptype'] == '>'):
                query_tracker.result_array = tmp_team_b_list.filter(away_team_win_streak__gt=item['value'])
            query_tracker.result_array = Games.objects.filter(gamestreaks__in=query_tracker.result_array)
            for game in query_tracker.result_array:
                if(not query_tracker.team_a_dict.has_key(game.pk)):
                    query_tracker.team_a_dict[game.pk] = game.home_team
        else:
            if(item['comptype'] == '='):
                query_tracker.result_array = tmp_team_b_list.filter(home_team_win_streak=item['value'])
            elif(item['comptype'] == '<'):
                query_tracker.result_array = tmp_team_b_list.filter(home_team_win_streak__lt=item['value'])
            elif(item['comptype'] == '>'):
                query_tracker.result_array = tmp_team_b_list.filter(home_team_win_streak__gt=item['value'])
            query_tracker.result_array = Games.objects.filter(gamestreaks__in=query_tracker.result_array)
            for game in query_tracker.result_array:
                if(not query_tracker.team_a_dict.has_key(game.pk)):
                    query_tracker.team_a_dict[game.pk] = game.away_team
    print "added team_b win_streak conditions" 

def filter_by_coach( item ):
    print "about to compute coach conditions"
    #if at this point the results array is empty, it means either:
    # a) we havent filtered by team/conf/spread yet and so we have to  take everything
    # b) we have weeded everything out
    #if b is true then team_a_conditions_exist is already True
    if(not query_tracker.team_a_conditions_exist):
        tmp_team_a_list = query_tracker.gameset
        query_tracker.result_array = []
    else:
        tmp_team_a_list = result_array
        query_tracker.result_array = []
    tmp_team_a_list = tmp_team_a_list.distinct()
    print "tmp_team_a_list gathered"
    #print "tmp_team_a_list gathered, length = %d"%(tmp_team_a_list.count())
    query_tracker.team_a_conditions_exist = True
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
        if(query_tracker.use_away_team and not query_tracker.use_home_team):
            print 'using away'
            query_tracker.result_array = tmp_team_a_list.filter(away_coach=int(coach.pk)) 
            for game in query_tracker.result_array:
                if(not team_a_dict.has_key(game.pk)):
                    query_tracker.team_a_dict[game.pk]= game.away_team
        elif(query_tracker.use_home_team and not query_tracker.use_away_team):
            print 'using home'
            query_tracker.result_array = tmp_team_a_list.filter(home_coach=int(coach.pk)) 
            for game in query_tracker.result_array:
                if(not query_tracker.team_a_dict.has_key(game.pk)):
                    query_tracker.team_a_dict[game.pk]= game.home_team
        elif(query_tracker.use_away_team and query_tracker.use_home_team):
            query_tracker.result_array = tmp_team_a_list.filter(Q(home_coach=int(coach.pk))|Q(away_coach=int(coach.pk))) 
            print 'using home and away'
            for game in query_tracker.result_array:
                if(not query_tracker.team_a_dict.has_key(game.pk)):
                    if(game.away_coach == coach.pk):
                        query_tracker.team_a_dict[game.pk]= game.away_team
                    else:
                        query_tracker.team_a_dict[game.pk]= game.home_team

def filter_by_opposition_coach( item ):
    print "about to compute coach conditions"
    #if at this point the results array is empty, it means either:
    # a) we havent filtered by team/conf/spread yet and so we have to  take everything
    # b) we have weeded everything out
    #if be is true then team_a_conditions_exist is already True
    if(query_tracker.team_b_conditions_exist):
        tmp_team_b_list = query_tracker.result_array
        query_tracker.result_array = []
    else:
        query_tracker.result_array = []
        tmp_team_b_list = query_tracker.result_array
    tmp_team_b_list = tmp_team_b_list.distinct()
    print "tmp_team_a_list gathered"
    query_tracker.team_b_conditions_exist = True
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
        if(query_tracker.use_away_team and not query_tracker.use_home_team):
            query_tracker.result_array = tmp_team_b_list.filter(away_coach=coach.pk) 
            for game in query_tracker.result_array:
                if(not team_a_dict.has_key(game.pk)):
                    query_tracker.team_a_dict[game.pk]= game.home_team
        elif(not query_tracker.use_away_team and query_tracker.use_home_team):
            query_tracker.result_array = tmp_team_b_list.filter(home_coach=coach.pk) 
            for game in query_tracker.result_array:
                if(not team_a_dict.has_key(game.pk)):
                    query_tracker.team_a_dict[game.pk]= game.away_team
        elif(query_tracker.use_away_team and query_tracker.use_home_team):
            query_tracker.result_array = tmp_team_b_list.filter(Q(home_coach=coach.pk)|Q(away_coach=coach.pk)) 
            for game in query_tracker.result_array:
                if(not team_a_dict.has_key(game.pk)):
                    if(game.away_coach == coach.pk):
                        query_tracker.team_a_dict[game.pk]= game.home_team
                    else:
                        query_tracker.team_a_dict[game.pk]= game.away_team

def get_player_filter( name_str ) :
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

def get_player_game_list( player_filter ):
    print 'player exists!'
    if(player_filter.count() == 1):
      query_tracker.player = player_filter[0]
      nonunique = False
    else:
      query_tracker.player = resolve_nonunique_players(lastname,firstname)
      nonunique = True
    position = player.position
    positionstr = positions[position]
    query_tracker.queried_players.append(player)
    query_tracker.player_game_list = query_tracker.player.games.only('gameid').all()
    print 'player game list gathered size = %d position = %s'%(player_game_list.count(),positions[position])

def get_active_status(game):
    player_game = game.gameplayers_set.filter(playerid=query_tracker.player)[0]
    #print 'game contain player position = %s'%positions[position]
    if(positions[query_tracker.player.position] in ['RB','FB','WR','TE','RBWR']):
      #print 'player %s %s is not QB'%(player_game.playerid.firstname, player_game.playerid.lastname)
      if(RbWrGameStats.objects.filter(gameplayer=player_game).exists()):
        isactive = player_game.rbwrgamestats.G
      else:
        isactive = False
    elif(positions[query_tracker.player.position] == 'QB'):
      #print 'player %s %s is QB'%(player_game.playerid.firstname, player_game.playerid.lastname)
      if(QbGameStats.objects.filter(gameplayer=player_game).exists()):
        isactive = player_game.qbgamestats.G and (player_game.qbgamestats.GS or player_game.gameid.date < datetime.date(1993,1,1))
      else:
        isactive = False
    else:
      #print 'player %s %s is not QB or rb/wr'%(player_game.playerid.firstname, player_game.playerid.lastname)
      isactive = True
    return isactive

def exclude_games( game_list, exclude_list ):
    if(len(exclusion_list) > 0):
        count = 0
        tmp_exclusion_list = []
        for i in exclusion_list:
            count = (count + 1)%500
            tmp_exclusion_list.append(i)
            if(count == 0):
                tmp = game_list.exclude(gameid__in=tmp_exclusion_list)
                tmp_exclusion_list = []
        game_list = game_list.exclude(gameid__in=tmp_exclusion_list)
    return game_list

def filter_by_player( item, team ):
    print "about to compute player conditions"
    #if at this point the results array is empty, it means either:
    # a) we havent filtered by team/conf/spread yet and so we have to  take everything
    # b) we have weeded everything out
    #if be is true then team_a_conditions_exist is already True
    if(not query_tracker.team_a_conditions_exist and not query_tracker.team_b_conditions_exist):
        tmp_result_array = query_tracker.gameset
    else:
        tmp_result_array = query_tracker.result_array
        query_tracker.result_array = []
    tmp_result_array = tmp_result_array.distinct()
    print "tmp_result_array gathered"
    #print "tmp_result_array gathered, length = %d"%(tmp_result_array.count())
    query_tracker.team_a_conditions_exist = True
    player_filter = get_player_filter( item['value'] )
    if (player_filter.exists()):
        get_player_game_list( player_filter )
    else:
        print 'no such player %s %s'%(player_name_array[0], player_name_array[1])
        query_tracker.player_game_list = []
        tmp_result_array = []
    exclusion_list = []
    ##performance experiment, not required for functionality
    player_game_pk_list = []
    for gm in query_tracker.player_game_list:
        player_game_pk_list.append(gm.pk)
    tmp_result_array = tmp_result_array.filter(pk__in=player_game_pk_list)
    ##end of experiment
    for game in tmp_result_array:
        #cond 1: player played in game
        if(query_tracker.player_game_list.filter(pk=game.pk).exists()):
            isactive = get_active_status(game)
            if(isactive):
                #if team_a_dict not assigned it means we have yet to constrain this game.  go ahead and add it to list
                if(not query_tracker.team_a_dict.has_key(game.pk)):
                    query_tracker.result_array.append(game)
                    away = GamePlayers.objects.get(gameid=game.pk, playerid=query_tracker.player.pk).away
                    if(away and team == 'a' or home and team == 'b' ):
                        query_tracker.team_a_dict[game.pk]= game.away_team
                    else:
                        query_tracker.team_a_dict[game.pk]= game.home_team
                #otherwise, make sure the team hes on is team a
                else:
                    away = GamePlayers.objects.get(gameid=game.pk, playerid=query_tracker.player.pk).away
                    if(away and team == 'a' or home and team == 'b' ):
                        team = game.away_team
                    else:
                        team = game.home_team
                    if(query_tracker.team_a_dict[game.pk] == team):
                        query_tracker.result_array.append(game)
                        #print 'appending pk array'
                    else:
                        exclusion_list.append(game.pk)
            else:
                print 'player was not active'
                exclusion_list.append(game.pk)
        else:
            exclusion_list.append(game.pk)
    #print 'begin player based exclusion tmp_result_array size = %d exclusion_list size = %d'%(tmp_result_array.count(), len(exclusion_list))
    tmp_result_array = exclude_games( tmp_result_array, exclude_list )
    query_tracker.result_array = tmp_result_array
    print 'end player based exclusion tmp_result_array size = %d'%(len(query_tracker.result_array))
           
      
def main(request={}):
    csrf_request = {}
    response = render_to_response('main.html',  csrf_request,context_instance=RequestContext(request))
    return response

def about(request={}):
    csrf_request = {}
    response = render_to_response('about.html',  csrf_request,context_instance=RequestContext(request))
    return response

def submit(request):
  print ("num team a conditions was %d num team b conditions was %d num game conditions was %d"%(int(get_request_param(request,'num_team_a_conditions', 0)),int(get_request_param(request,'num_team_b_conditions',0)),int(get_request_param(request,'num_game_conditions',0))))
  response = {}
  query_tracker.num_team_a_conditions = int(get_request_param(request,'num_team_a_conditions',0))
  query_tracker.num_team_b_conditions = int(get_request_param(request,'num_team_b_conditions',0))
  query_tracker.num_game_conditions = int(get_request_param(request,'num_game_conditions',0))
  query_tracker.queried_players = []

  query_tracker.get_conditions( request )

  #determine defer fields based on conditions
  defer_fields = get_defer_fields(query_tracker.team_a_conditions, query_tracker.team_b_conditions)
  query_tracker.games_def = Games.objects.all()
  for param in defer_fields:
      #print 'defer %s'%param
      query_tracker.games_def = query_tracker.games_def.defer(param) 

  print "after deferment, team a conditions are:"
  for item in query_tracker.team_a_conditions:
      print item 

  query_tracker.init_team_a_dict()

  #Now that we've filtered home vs away  we can query based on other conditions
  #The first conditions should be those that dont add/subtract to teama list
  #such as year, week, etc.  These are simpler and in most usage 
  #they will severely reduce the data set
  #For the life of me i dont know why, but for certain queries the exclude function will fail if the number of chains is too hi
  #My add hoc solution is to initially split the data set into 4 (based on weeks) and then sum the querySets before we send 
  #them to be analyzed 
  final_result_array = []
  final_result_date_array = []
  for i in range(6):
    query_tracker.gameset = query_tracker.games_def.filter(week__in=range(4*i+1,4*i+5))
    if(query_tracker.gameset.exists()):
      query_tracker.result_array = []
      query_tracker.team_a_conditions_exist = False
      #TODO: following is redundant (we shouldnt have to do this each iteration)
      #but necessaqry for now since in temab section we reuse the vairables
      #the following lists the "team_a" teams.  
      #It will be used later in team b logic
      query_tracker.team_a_list = []
      print "check for season conditions"
      for item in query_tracker.team_a_conditions:
        if(item['type'] == "season"):
          filter_by_season( item )
      print "check for week conditions"
      for item in query_tracker.team_a_conditions:
        if(item['type'] == 'week'):
          filter_by_week( item )
      print "check for fieldtype conditions"
      for item in query_tracker.team_a_conditions:
        if(item['type'] == "fieldtype"):
          filter_by_fieldtype( item )
      print "check for temperature conditions"
      for item in query_tracker.team_a_conditions:
        if(item['type'] == "temperature"):
          filter_by_temperature( item )
      print "check for wind conditions"
      for item in query_tracker.team_a_conditions:
        if(item['type'] == "wind"):
          filter_by_wind( item )
      print "check for humidity conditions"
      for item in query_tracker.team_a_conditions:
        if(item['type'] == "humidity"):
          filter_by_humidity( item )
      print "check for over_under conditions"
      for item in query_tracker.team_a_conditions:
        if(item['type'] == "over_under"):
          filter_by_over_under( item )
      
      #beginning of conditions that effect team_a_dict
      print "check for group conditions"
      for item in query_tracker.team_a_conditions:
        print item 
        if(item['type'] == 'group'):
          filter_by_group( item )
        elif(item['type'] == 'team'):
          filter_by_team( item )

      #we do spread calculations after we have done all team/group filtering
      print "check for spread conditions"
      for item in query_tracker.team_a_conditions:
        if(item['type'] == "favoredBy" or item['type'] == "underdogOf"):
          filter_by_spread( item )
    
      print "check for WinPercentage conditions"
      for item in query_tracker.team_a_conditions:
        if(item['type'] == "WinPercentage"):
          filter_by_win_percentage( item )
      print "check for WinStreak conditions"
      for item in query_tracker.team_a_conditions:
        if(item['type'] == "WinStreak"):
          filter_by_win_streak( item )

      print "check for coach conditions"
      for item in query_tracker.team_a_conditions:
        if(item['type'] == "coach"):
          filter_by_coach( item )

      #Ideally  want to do player queries last, as they are most computationally involved
      #and so perf will benefit from smaller data set
      print "check for player conditions"
      for item in query_tracker.team_a_conditions:
        if(item['type'] == "player"):
          filter_by_player( item, 'a' )
    
      #uniquify a before its passed to b 
      #result_array = uniq(result_array)
      if(query_tracker.result_array != []):
        query_tracker.result_array = query_tracker.result_array.distinct()
        print "uniquified team a query_tracker.results, num query_tracker.results = %d"%query_tracker.result_array.count() 
        #print "current length is %d"%result_array.count()

      #two things can lead to a 0 lngth array at this point:
      # one is no conditions yet.  The other is we already have no matches
      #if(len(result_array) == 0):
      if(not query_tracker.team_a_conditions_exist):
        query_tracker.result_array = query_tracker.gameset 
      
      print 'beginning of team b conditions'
      #For team b, we will further limit what we obtained from team a conditions
      #note that while team a conditions are required, team b conditions are not
      # if no team b conditions, the results are the team a results 
      #Lets first see if team b is restricted to home or away
      query_tracker.team_b_conditions_exist = False
      ( query_tracker.use_home_team, query_tracker.use_away_team ) = get_home_away_conditions( query_tracker.team_b_conditions, query_tracker.team_a_conditions )
      #Now that we've done that we can query based on other conditions
      #remember that this time we are querying team a results
      print 'searching for team b group conditions'
      for item in query_tracker.team_b_conditions:
        if(item['type'] == 'group'):
          filter_by_opposition_group( item )
      for item in query_tracker.team_b_conditions:
        if(item['type'] == 'team'):
          filter_by_opposition_team( item )
      print 'searching for team b win pct conditions'
      for item in query_tracker.team_b_conditions:
        if(item['type'] == "WinPercentage"):
          filter_by_opposition_win_percentage( item )
      print 'searching for team b streak conditions'
      for item in query_tracker.team_b_conditions:
        if(item['type'] == "WinStreak"):
          filter_by_opposition_win_streak( item )
      print "check for coach conditions"
      for item in query_tracker.team_b_conditions:
        if(item['type'] == "coach"):
          filter_by_opposition_coach( item )

      #Ideally  want to do player queries last, as they are most computationally involved
      #and so perf will benefit from smaller data set
      print 'searching for team b player conditions'
      for item in query_tracker.team_b_conditions:
        if(item['type'] == "player"):
            filter_by_player( item, 'b' )
      print 'done searching for team b conditions'
      #end of parsing team be conditions
      if(not query_tracker.team_b_conditions_exist):
        print "no team b conditions!"
      elif(query_tracker.result_array != []):
        print 'begin final uniquification'
        query_tracker.result_array = query_tracker.result_array.distinct()
        print "after final uniquification, length of result array is %d"%(query_tracker.result_array.count())
      #end of for loop iteration.  
      #final_result_array.extend(query_tracker.result_array)    
      for i in query_tracker.result_array:
        #final_result_array.append(i.pk)
        final_result_date_array.append({'pk':i.pk, 'year':i.date.year})
  print 'beginning of post collection calculations'
  #data collected, now calculate winnings/team data
  # aggregate team data: ats %, win %, avg points scored, avg points allowed, avg total
  response['result_table'] = []
  response['teama_summary'] = []
  response['teamb_summary'] = []
  winnings = 0
  teama_spreadwins=0
  teamb_spreadwins=0
  teama_wins=0
  teamb_wins=0
  over_wins=0
  teama_points = 0
  teamb_points = 0
  #eventually make this user defined field
  push_goes_to_bookie = False
  #put total results back in result array.
  #final_result_date_array.sort(key=lambda gm: gm['year'])
  final_result_date_array = count_sort(final_result_date_array)
  print 'dates sorted'
  for item in final_result_date_array:
    final_result_array.append(item['pk'])
  #print 'convert numgames to float, numgames = %d'%(len(final_result_date_array))
  numgames = float(len(final_result_array))
  numgamesint = len(final_result_array)
  query_tracker.queried_players = uniq(query_tracker.queried_players)
  iteration = 0
  gameset = Games.objects.only('gameid','date','away_team','home_team','away_team_spread','over_under',
                               'over_under','away_team_score','home_team_score','week','season')
  while((1000*iteration) <= numgamesint):
    #why ordering when we already sorted?
    #query_tracker.result_array = gameset.filter(pk__in=final_result_array[1000*(iteration):1000*(iteration+1)-1]).order_by('date')
    query_tracker.result_array = gameset.filter(pk__in=final_result_array[1000*(iteration):1000*(iteration+1)-1])
    iteration += 1
    print 'iterate over result array'
    for item in query_tracker.result_array:
    #the method below might be necessary for large data sets
    #for entry in final_result_date_array:
    #  print 'grab game'
    #  item = Games.objects.get(pk=entry['pk'])
      tmp_winnings = 0
      if(query_tracker.team_a_dict.get(item.pk,-1) == item.away_team):
        teama_points += item.away_team_score
        teamb_points += item.home_team_score
      else:
        teamb_points += item.away_team_score
        teama_points += item.home_team_score
      #calculate spread wins
      #away team wins
      if(((item.away_team_score + item.away_team_spread)  - item.home_team_score) > 0): 
        if(query_tracker.team_a_dict.get(item.pk,-1) == item.away_team):
          #tmp_winnings = 100 
          #winnings += 100
          teama_spreadwins += 1
        else:
          #tmp_winnings = -100 
          #winnings -= 100
          teamb_spreadwins += 1
      #home team wins
      elif(((item.away_team_score + item.away_team_spread)  - item.home_team_score) < 0): 
        if(query_tracker.team_a_dict.get(item.pk,-1) == item.away_team):
          #tmp_winnings = -100 
          #winnings -= 100 
          teamb_spreadwins += 1
        else:
          teama_spreadwins += 1
          #tmp_winnings = 100 
          #winnings += 100
      #draw
      elif(push_goes_to_bookie):
        pass
        #tmp_winnings = -100 
        #winnings -= 100 
      #print 'calculating win %'
      #calculate regular wins
      if((item.away_team_score  - item.home_team_score) > 0): 
        if(query_tracker.team_a_dict.get(item.pk,-1) == item.away_team):
          teama_wins += 1
        else:
          teamb_wins += 1
      #home team wins
      elif((item.away_team_score  - item.home_team_score) < 0): 
        if(query_tracker.team_a_dict.get(item.pk,-1) == item.away_team):
          teamb_wins += 1
        else:
          teama_wins += 1
      #print 'calculating over cover %'
      #the over covers
      if((item.away_team_score  + item.home_team_score) > item.over_under): 
        over_wins +=1
  
      #print('%s        %d     %s        %d    %.1f          %s    %d'%(teams[item.away_team], item.away_team_score, teams[item.home_team], item.home_team_score,item.away_team_spread, teams[team_a_dict[item.pk]], tmp_winnings))
      #print 'put data in rsp array'
      response['result_table'] += [item.season,item.week,item.away_team, item.away_team_score, item.home_team, item.home_team_score,str(item.away_team_spread),str(item.over_under), query_tracker.team_a_dict.get(item.pk,-1)]
  #aggregate datae/summaries
  print 'calculating summaries, numgames = %d'%numgames
  #preventdiv by 0, notings gonna getprinted anyway
  if(numgames == 0):
    numgames = 1
  response['teama_summary'] = ['%.2f'%(float(teama_spreadwins)/numgames), '%.2f'%(float(teama_wins)/numgames), '%.2f'%(over_wins/numgames), '%.2f'%(teama_points/numgames), '%.2f'%(teamb_points/numgames)]
  response['teamb_summary'] = ['%.2f'%(float(teamb_spreadwins)/numgames), '%.2f'%(float(teamb_wins)/numgames), '%.2f'%(over_wins/numgames), '%.2f'%(teamb_points/numgames), '%.2f'%(teama_points/numgames)]
  response['winnings'] = winnings
  #plotdata = { 'teste00' : [response['teama_summary'][0]], 'teste01' : [response['teama_summary'][1]], 'teste02' : [response['teama_summary'][2]]}
  print 'about to do summary hist'
  int_ats = int(100*float(teama_spreadwins)/numgames) 
  int_wp = int(100*float(teama_wins)/numgames) 
  int_ou = int(100*float(over_wins)/numgames)  
  #plotdata = { 'ATS' : [int_ats], 'Win%' : [int_wp], 'Over Covers' : [int_ou]}
  plotdata = [int_ats,int_wp,int_ou]
  color_array = get_color_array([int_ats,int_wp,int_ou])
  print 'color array:'
  print color_array
  timestamp = str(time.time())
  response['teamsumchart'] = 'teamsum_'+timestamp+'.png'
  #teamsumchart_fullpath = settings.MY_PROJECT_ROOT+'templates/source/teamsum_'+timestamp+'.svg'
  teamsumchart_fullpath = settings.STATIC_ROOT+'teamsum_'+timestamp+'.png'
  print 'about to use cairoplot'
  if(plotting):
    cairoplot.vertical_bar_plot (  teamsumchart_fullpath, plotdata, 550, 400, border = 50, grid = True, rounded_corners = True,display_values = True, x_labels=['ATS', 'Win%', 'Over Covers'], colors=color_array)

  #gather player data
  print 'collecting player stats'
  response['player_table'] = []
  response['players_with_stats'] = []
  response['qbs_with_stats'] = []
  response['defs_with_stats'] = []
  response['rbwrs_with_stats'] = []
  response['qb_avgs'] = []
  response['def_avgs'] = []
  response['rbwr_avgs'] = []
  response['qb_charts'] = []
  response['playerdata_charts'] = []
  response['rbwr_charts'] = []
  response['def_charts'] = []
  player_sums = []
  #A NOTE ON THE FOLLOWING:  We broke down the result array above for large game sets (> 1000)
  #no player gameset will be greater than a few hundred, so its not needed here, so we go back to 
  #full result array
  query_tracker.result_array = Games.objects.filter(pk__in=final_result_array).only('date','gameid')
  for playa in query_tracker.queried_players:
    print 'collecting stats for playa %s %s'%(playa.firstname,playa.lastname)
    #determine if this player has stats, currently only offensive position players
    positionstr = positions[playa.position] 
    if(positionstr in ['RB','FB','WR','TE','QB','RBWR'] or
       positionstr in ['CB','DB','DE','DL', 'DT','FS', 'ILB', 'LB', 'LS', 'MLB', 'NT', 'OLB', 'SAF','SS','DEF']):
      rush_array = []
      pass_array = []
      totalyds_array = []
      date_array = []
      #print 'about to gather playa stats for each game num results is %d'%(query_tracker.result_array.count())
      print 'about to gather playa stats for each game' 
      firstgame = True
      player_has_stats = False
      #old, generated from __in
      for item in query_tracker.result_array:
        #on the first game for ech player determine if we have any stats for them
        if(firstgame):
          print 'firstgame'
          player_sums = []
          firstgame = False
          #this is just a tes.  Is server side json un able to handle the mixed array sizes?
          response['player_table'].extend(['hdr', playa.lastname, playa.firstname,playa.position])
          #print 'first game is gameid %d playerid %d'%(item.pk, playa.pk)
          #gp = GamePlayers.objects.filter(gameid=item.pk, playerid=playa.pk)[0]
          player_game_list = GamePlayers.objects.filter(playerid=playa.pk)
          #player_game_list = GamePlayers.objects.filter(playerid=playa.pk).filter(gameid__in=query_tracker.result_array)
          print 'grab numstats'
          #seems __in is a big perf loss, just set numstats to Tru for now
          numstats = True
          """
          if(positionstr in ['RB','FB','WR','TE','RBWR']):
            #numstats = RbWrGameStats.objects.filter(gameplayer_id = gp.pk).count()
            gpstatarray = RbWrGameStats.objects.filter(gameplayer__in=player_game_list).defer('FUM','Lost','RushAtt','RecLng','RecTD')
            numstats = gpstatarray.exists()
          elif(positionstr == 'QB'):
            #numstats = QbGameStats.objects.filter(gameplayer_id = gp.pk).count()
            #gpstatarray = QbGameStats.objects.filter(gameplayer__in=player_game_list).defer('Pct','Avg','Int','Sck','SckY','RushAtt','RushAvg','RushTD','FUM','Lost')
            #numstats = gpstatarray.exists()
          elif(positionstr in ['CB','DB','DE','DL', 'DT','FS', 'ILB', 'LB', 'LS', 'MLB', 'NT', 'OLB', 'SAF','SS','DEF']):
            #numstats = DefGameStats.objects.filter(gameplayer_id = gp.pk).count()
            gpstatarray = DefGameStats.objects.filter(gameplayer__in=player_game_list)
            numstats = gpstatarray.exists() 
          else:
            numstats = False
          """
          if(numstats):
            print 'playr has stats'
            player_has_stats = True
            games_active = 0
            #first filter fr playerid
            if(positionstr in ['RB','FB','WR','TE','RBWR']):
              print 'initialize player sums'
              player_sums = [0,0,0,0,0,0]
              response['rbwrs_with_stats'].append('%s %s'%(playa.firstname,playa.lastname))
              response['players_with_stats'].append('%s %s'%(playa.firstname,playa.lastname))
              #gpstatarray = RbWrGameStats.objects.filter(gameplayer__in=player_game_list).defer('FUM','Lost','RushAtt','RecLng','RecTD')
            elif(positionstr == 'QB'):
              player_sums = [0,0,0,0,0]
              response['qbs_with_stats'].append('%s %s'%(playa.firstname,playa.lastname))
              response['players_with_stats'].append('%s %s'%(playa.firstname,playa.lastname))
              #gpstatarray = QbGameStats.objects.filter(gameplayer__in=player_game_list).defer('Pct','Avg','Int','Sck','SckY','RushAtt','RushYds','RushAvg','RushTD','FUM','Lost')
            elif(positionstr in ['CB','DB','DE','DL', 'DT','FS', 'ILB', 'LB', 'LS', 'MLB', 'NT', 'OLB', 'SAF','SS','DEF']):
              print 'player is on def'
              player_sums = [0,0,0]
              response['defs_with_stats'].append('%s %s'%(playa.firstname,playa.lastname))
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
            response['player_table'].extend([str(gpstats.RushYds),str(gpstats.RushTD), str(gpstats.RecYds),str(gpstats.RecTD)])
            #we sum up the stats for each game in the avg array.  at the end we will divide byt total number of games
            statnum = 0
            #only add stat if the player was actuve (G=True means active.  For QBs we may later want to do GS (started)
            if(gpstats.G):
              #print 'player is active'
              games_active += 1
              for stat in [gpstats.RushYds,gpstats.RushAvg,gpstats.RushTD, gpstats.RecYds,gpstats.RecAvg,gpstats.RecTD]:
                player_sums[statnum] += stat
                statnum += 1
              rush_array.append(gpstats.RushYds)
              pass_array.append(gpstats.RecYds)
              totalyds_array.append(gpstats.RecYds+gpstats.RushYds)
              date_array.append(str(item.date))
              #print 'stats collected for this game'
          elif(positionstr == 'QB'):
            #gpstatsarray = QbGameStats.objects.filter(gameplayer_id = gp.pk)
            if(QbGameStats.objects.filter(gameplayer_id = gp.pk).exists()):
              gpstats = QbGameStats.objects.filter(gameplayer_id = gp.pk)[0]
            #print 'Qbstat retrieved'
            response['player_table'].extend([str(gpstats.Comp), str(gpstats.Att), str(gpstats.Yds),str(gpstats.TD),str(gpstats.Rate)])
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
            #print 'stats added to response games_active = %d'%games_active
          elif(positionstr in ['CB','DB','DE','DL', 'DT','FS', 'ILB', 'LB', 'LS', 'MLB', 'NT', 'OLB', 'SAF','SS','DEF']):
            #gpstatsarray = DefGameStats.objects.filter(gameplayer_id = gp.pk)
            print 'collect def stats'
            if(DefGameStats.objects.filter(gameplayer_id = gp.pk).exists()):
              gpstats = DefGameStats.objects.filter(gameplayer_id = gp.pk)[0]
            print 'collected def stats'
            #print 'Defstat retrieved'
            response['player_table'].extend([str(gpstats.Tck), str(gpstats.Sck), str(gpstats.Int)])
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
                #this is where we would add to any histogram forming array
                #pass_array.append(gpstats.Yds)
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
        response['qb_avgs'].append(player_avgs) 
      elif(positions[playa.position] in ['WR','RB','FB','TE','RBWR']):
        response['rbwr_avgs'].append(player_avgs) 
      else:
        response['def_avgs'].append(player_avgs) 

      if(pass_array != []):
        """
        ##the following is bad for performance and not that useful
        ##create linear plot of total yds
          if(plotting):
            timestamp = str(time.time())
            lineplot_fullpath = settings.STATIC_ROOT+'totalydsline_'+timestamp+'.png'
            print 'create line plot'
            cairoplot.dot_line_plot( lineplot_fullpath, totalyds_array, 550, 400, x_labels = date_array,
                               axis = True, grid = True, series_legend = True )
            response['playerdata_charts'].append('totalydsline_'+timestamp+'.png')
        """
        ##now create histograms
        #total yds
        totalyds_hist = get_hist(totalyds_array)
        timestamp = str(time.time())
        if(positions[playa.position] == 'QB'):
          response['qb_charts'].append('totalydshist_'+timestamp+'.png')
        else:
          response['rbwr_charts'].append('totalydshist_'+timestamp+'.png')
        #histchart_fullpath = settings.MY_PROJECT_ROOT+'templates/source/passhist_'+timestamp+'.svg'
        histchart_fullpath = settings.STATIC_ROOT+'totalydshist_'+timestamp+'.png'
        print 'creating passhist'
        if(plotting):
          cairoplot.vertical_bar_plot (  histchart_fullpath, totalyds_hist[1], 550, 400, border = 50, grid = True, rounded_corners = True,display_values = True,x_labels=totalyds_hist[0])
        print 'totalydshist created'
      """
      gonna do just aggregate hist for now
      #rec
      if(pass_array != []):
        pass_hist = get_hist(pass_array)
        timestamp = str(time.time())
        if(positions[playa.position] == 'QB'):
          response['qb_charts'].append('passhist_'+timestamp+'.png')
        else:
          response['rbwr_charts'].append('passhist_'+timestamp+'.png')
        #histchart_fullpath = settings.MY_PROJECT_ROOT+'templates/source/passhist_'+timestamp+'.svg'
        histchart_fullpath = settings.STATIC_ROOT+'passhist_'+timestamp+'.png'
        print 'creating passhist'
        if(plotting):
          cairoplot.vertical_bar_plot (  histchart_fullpath, pass_hist[1], 550, 400, border = 50, grid = True, rounded_corners = True,display_values = True,x_labels=pass_hist[0])
        print 'passhist created'
      #rush
      if(rush_array != []):
        rush_hist = get_hist(rush_array)
        timestamp = str(time.time())
        if(positions[playa.position] == 'QB'):
          response['qb_charts'].append('rushhist_'+timestamp+'.png')
        else:
          response['rbwr_charts'].append('rushhist_'+timestamp+'.png')
        #histchart_fullpath = settings.MY_PROJECT_ROOT+'templates/source/rushhist_'+timestamp+'.svg'
        histchart_fullpath = settings.STATIC_ROOT+'rushhist_'+timestamp+'.png'
        if(plotting):
          cairoplot.vertical_bar_plot (  histchart_fullpath, rush_hist[1], 550, 400, border = 50, grid = True, rounded_corners = True,display_values = True, x_labels = rush_hist[0])
      """  
  print 'player stats collected'
  #for line in response['player_table']:
  #  print line
  if(len(final_result_array) > 0):
    response['results_exist'] = 1
  else:
    response['results_exist'] = 0

  #response['player_table'] = []
  #print response['player_table']
  print 'about to converrt to json'
  json_str = json.dumps(response)
  #print 'json_str:'
  #print json_str
  print 'converted  to json Boy!'
  if ( sys.version_info > (2, 7) ):
    return HttpResponse(json_str, content_type='application/json')
  else:
    return HttpResponse(json_str, mimetype='application/json')



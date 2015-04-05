var positions = [
  'C','CB','DB','DE','DL','DT','FB','FS','G','ILB','K','LB','LS','MLB','NT','OG','OL','OLB','OT','P','QB','RB','SAF','SS','T','TE','WR'
  ];
var teams = [
  "Arizona",  "Atlanta",  "Baltimore",  "Buffalo",  "Carolina",  "Chicago",  "Cincinnati",  "Cleveland",  "Dallas",  "Denver",  "Detroit",
  "Green Bay",  "Houston",  "Indianapolis",  "Jacksonville",  "Kansas City",  "Miami",  "Minnesota",  "New England",  "New Orleans",  "NY Giants",
  "NY Jets",  "Oakland",  "Philadelphia",  "Pittsburgh",  "San Diego",  "San Francisco",  "Seattle",  "St. Louis",  "Tampa Bay",  "Tennessee",  "Washington",
  //old teams
  "Los Angeles Rams",
  "Los Angeles Raiders",
  "Houston Oilers",
  "Tennessee Oilers",
  "St Louis Cardinals",
  "Phoenix Cardinals",
  "Baltimore Colts"
];
function toTitleCase(str)
{
    return str.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
}
function get_week(season,week) {
  if(week <= 17 || season == 1993 && week == 18) {
    return week;
  }
  else {
    if (season == '1993'){
      week = week - 1;
    }
    if(week == 18) {
      return 'WC';
    }
    else if(week == 19) {
      return 'DIV';
    }
    else if(week == 20) {
      return 'CONF';
    }
    else if(week >= 21) {
      return 'SB';
    }
    return week;
  }
}
    
var game_columns = 9;
function setdisplay(tab) {
  if(tab == 1) {
    document.getElementById('summary').style.display = 'block';
    document.getElementById('player_results').style.display = 'none';
    document.getElementById('game_results').style.display = 'none';
  }
  else if(tab == 2)  {
    document.getElementById('summary').style.display = 'none';
    document.getElementById('player_results').style.display = 'block';
    document.getElementById('game_results').style.display = 'none';
  }
  else if(tab == 3)  {
    document.getElementById('summary').style.display = 'none';
    document.getElementById('player_results').style.display = 'none';
    document.getElementById('game_results').style.display = 'block';
  }
  else if(tab == 4)  {
    document.getElementById('TeamSum').style.display = 'block';
    document.getElementById('PlayerSum').style.display = 'none';
  }
  else if(tab == 5)  {
    document.getElementById('TeamSum').style.display = 'none';
    document.getElementById('PlayerSum').style.display = 'block';
  }
  else if(tab == 6)  {
    document.getElementById('PlayerCharts').style.display = 'block';
    document.getElementById('PlayerTables').style.display = 'none';
  }
  else if(tab == 7)  {
    document.getElementById('PlayerCharts').style.display = 'none';
    document.getElementById('PlayerTables').style.display = 'block';
  }
}
 
function GetSelectValue(sel){
  var val = sel.options[sel.selectedIndex].value;
  if(val == 1) {
    DisplayConfList(sel.name);
  }
  else if(val == 2) {
    DisplayTeamList(sel.name);
  }
  else if(val == 3 || val == 12) {
    DisplayNumberComp(sel.name, val);
  }
  else if(val == 4 || val == 5) {
    DisplayHomeAway(sel.name);
  }
  else if(val == 6 || val == 8 || val == 9 || val == 17) {
    DisplayNumberComp(sel.name, val);
  }
  else if(val == 7) {
    DisplayWeekComp(sel.name);
  }
  else if(val == 10 || val == 11) {
    DisplayPlayer(sel.name);
  }
  else if(val == 13) {
    DisplayFieldType(sel.name);
  }
  else if(val == 14 || val == 15 || val == 16) {
    DisplayNumberComp(sel.name);
  }
}

function DisplayPlayer(table) {
  str = "<input type=\"text\" class=\"input-block-level\" name=\""+table+"_value\">";
  document.getElementById("conditions_"+table+"_right").innerHTML = str;
  document.getElementById("conditions_"+table+"_far_right").innerHTML = "";
}
function DisplayNumberComp(table,compval) {
  str = "<select name=\""+table+"_comptype\">";
  str += "<option value=0>Greater Than</option>";
  str += "<option value=1>Equal To</option>";
  str += "<option value=2>Less Than</option>";
  str +="</select>";
  document.getElementById("conditions_"+table+"_right").innerHTML = str;
  str = "<input type=\"text\" class=\"input-block-level\" name=\""+table+"_value\">";
  document.getElementById("conditions_"+table+"_far_right").innerHTML = str;
}
function DisplayWeekComp(table,compval) {
  str = "<select name=\""+table+"_comptype\">";
  str += "<option value=0>Greater Than</option>";
  str += "<option value=1>Equal To</option>";
  str += "<option value=2>Less Than</option>";
  str +="</select>";
  document.getElementById("conditions_"+table+"_right").innerHTML = str;
  str = "<select name=\""+table+"_value\">";
  str += "<option value=0>0</option>";
  str += "<option value=1>1</option>";
  str += "<option value=2>2</option>";
  str += "<option value=3>3</option>";
  str += "<option value=4>4</option>";
  str += "<option value=5>5</option>";
  str += "<option value=6>6</option>";
  str += "<option value=7>7</option>";
  str += "<option value=8>8</option>";
  str += "<option value=9>9</option>";
  str += "<option value=10>10</option>";
  str += "<option value=11>11</option>";
  str += "<option value=12>12</option>";
  str += "<option value=13>13</option>";
  str += "<option value=14>14</option>";
  str += "<option value=15>15</option>";
  str += "<option value=16>16</option>";
  str += "<option value=17>17</option>";
  str += "<option value=18>Wild Card</option>";
  str += "<option value=19>Divisional</option>";
  str += "<option value=20>Conference</option>";
  str += "<option value=21>Superbowl</option>";
  str +="</select>";
  document.getElementById("conditions_"+table+"_far_right").innerHTML = str;
}


function DisplayConfList(table) {
  str = "<select name=\""+table+"_value\">";
  str += "<option value=0>AFC</option>";
  str += "<option value=1>AFC East</option>";
  str += "<option value=2>AFC North</option>";
  str += "<option value=3>AFC South</option>";
  str += "<option value=4>AFC West</option>";
  str += "<option value=5>NFC</option>";
  str += "<option value=6>NFC East</option>";
  str += "<option value=7>NFC North</option>";
  str += "<option value=8>NFC South</option>";
  str += "<option value=9>NFC West</option>";
  str +="</select>";
  //document.getElementById('debug').innerHTML="conditions_"+table+"_right";
  document.getElementById("conditions_"+table+"_right").innerHTML = str;
  document.getElementById("conditions_"+table+"_far_right").innerHTML = "";
}
function DisplayFieldType(table) {
  str = "<select name=\""+table+"_value\">";
  str += "<option value=0>Grass</option>";
  str += "<option value=1>Turf</option>";
  str +="</select>";
  //document.getElementById('debug').innerHTML="conditions_"+table+"_right";
  document.getElementById("conditions_"+table+"_right").innerHTML = str;
  document.getElementById("conditions_"+table+"_far_right").innerHTML = "";
}
//Following function just erases right and far_right fields
function DisplayHomeAway(table) {
  document.getElementById("conditions_"+table+"_right").innerHTML = "";
  document.getElementById("conditions_"+table+"_far_right").innerHTML = "";

}
function DisplayTeamList(table) {
  str = "<select name=\""+table+"_value\">";
  str += "<option value=0>Arizona</option>";
  str += "<option value=1>Atlanta</option>";
  str += "<option value=2>Baltimore</option>";
  str += "<option value=3>Buffalo</option>";
  str += "<option value=4>Carolina</option>";
  str += "<option value=5>Chicago</option>";
  str += "<option value=6>Cincinnati</option>";
  str += "<option value=7>Cleveland</option>";
  str += "<option value=8>Dallas</option>";
  str += "<option value=9>Denver</option>";
  str += "<option value=10>Detroit</option>";
  str += "<option value=11>Green Bay</option>";
  str += "<option value=12>Houston</option>";
  str += "<option value=13>Indianapolis</option>";
  str += "<option value=14>Jacksonville</option>";
  str += "<option value=15>Kansas City</option>";
  str += "<option value=16>Miami</option>";
  str += "<option value=17>Minnesota</option>";
  str += "<option value=18>New England</option>";
  str += "<option value=19>New Orleans</option>";
  str += "<option value=20>NY Giants</option>";
  str += "<option value=21>NY Jets</option>";
  str += "<option value=22>Oakland</option>";
  str += "<option value=23>Philadelphia</option>";
  str += "<option value=24>Pittsburgh</option>";
  str += "<option value=25>San Diego</option>";
  str += "<option value=26>San Francisco</option>";
  str += "<option value=27>Seattle</option>";
  str += "<option value=28>St. Louis</option>";
  str += "<option value=29>Tampa Bay</option>";
  str += "<option value=30>Tennessee</option>";
  str += "<option value=31>Washington</option>";
  str += "</select>";
  document.getElementById("conditions_"+table+"_right").innerHTML = str;
  document.getElementById("conditions_"+table+"_far_right").innerHTML = '';
}
var condition_number_a = 0;
var condition_number_b = 0;
var condition_number_g = 0;

function AddCondition(team) {
  var condition_number;
  if(team == 'a') {
    condition_number_a += 1;
    condition_number = condition_number_a;
    document.forms['conditions']['num_team_a_conditions'].value = condition_number+1;
  }
  else if (team == 'b'){
    condition_number_b += 1;
    condition_number = condition_number_b;
    document.forms['conditions']['num_team_b_conditions'].value = condition_number+1;
  }   
  else if (team == 'g'){
    condition_number_g += 1;
    condition_number = condition_number_g;
    document.forms['conditions']['num_game_conditions'].value = condition_number+1;
  }   
  next_condition_number = condition_number + 1;
  if(team != 'g') {
    str = "<table id=\"team_"+team+"_"+condition_number+"\">";
  }
  else {
    str = "<table id=\"g_"+condition_number+"\">";
  }
  str += "<tr>";
  str += "<td>";
  str += "<select name=\""+team+"_"+condition_number+"\" onchange=\"GetSelectValue(this)\">";
  str += "<option value=0 selected>Choose Condition</option>";
  if(team != 'g') {
    str += "<option value=1> Is In...</option>";
    str += "<option value=2>Is Equal to...</option>";
  }
  //for now I will only let team a.  I think this is less confusing
  if(team == 'a'){
    str += "<option value=3>Favored By</option>";
    str += "<option value=12>Underdog Of</option>";
  }
  if(team != 'g') {
    str += "<option value=4>Is Home</option>";
    str += "<option value=5>Is Away</option>";
  }
  if(team == 'g'){
    str += "<option value=6>Season Is</option>";
    str += "<option value=7>Week</option>";
    str += "<option value=8>Over/Under</option>";
    str += "<option value=13>Field Type</option>";
    str += "<option value=14>Temperature</option>";
    str += "<option value=15>Wind Speed (mph)</option>";
    str += "<option value=16>Relative Humidity (%)</option>";
  }
  if(team != 'g') {
    str += "<option value=9>Has Winning Percentage Of...</option>";
    str += "<option value=17>Has Winning Streak Of...</option>";
    str += "<option value=10>Has Player...</option>";
    str += "<option value=11>Has Coach...</option>";
  }
  str += "</select>";
  str += "</td><td>";
  str += "<span id=\"conditions_"+team+"_"+condition_number+"_right\"></span>";
  str += "</td><td>";
  str += "<span id=\"conditions_"+team+"_"+condition_number+"_far_right\"></span>";
  str += "</td><td>";
  str += "<a onclick=\" AddCondition(\'"+team+"\')\" href=\"javascript:void(0);\">Add</a> ";
  str += "<a onclick=\" DeleteCondition(\'"+team+"\',\'"+condition_number+"\')\" href=\"javascript:void(0);\">Delete</a><br>";
  str += "</td>";
  str += "</tr>";
  str += "</table>";
  str += "</span>";
  str += "<span id = \"conditions_"+team+"_"+next_condition_number+"\"></span><br>";
  //document.getElementById('debug').innerHTML = 'conditions_'+team+'_'+condition_number;
  document.getElementById('conditions_'+team+'_'+condition_number).innerHTML=str;
}

function DeleteCondition(team, condition_number) {
  var next_condition_number = condition_number + 1;
  if(team != 'g') {
    document.getElementById('team_'+team+'_'+condition_number).innerHTML='';
  }
  else {
    document.getElementById('g_'+condition_number).innerHTML='';
  }
  document.forms['conditions'][team+'_'+condition_number].value=0;
}

function ShowMainForm() {
  document.getElementById('main_form').style.display = 'block';
  document.getElementById('return_to_form').style.display = 'none';
}

function InitPage( static_url ) {
  document.getElementById('main_form').style.display = 'block';
  document.getElementById('return_to_form').style.display = 'none';
  document.getElementById('return_to_form').style.display = 'none';
  STATIC_URL = static_url
}
  
function ajax_submit(){
    var xmlhttproll = new XMLHttpRequest();
    //response received function
    xmlhttproll.onreadystatechange=function(){
      if (xmlhttproll.readyState==4 && xmlhttproll.status==200){
        //a good response has occured
        document.getElementById('summary').style.display = 'block';
        document.getElementById('player_results').style.display = 'none';
        document.getElementById('game_results').style.display = 'none';
        document.getElementById('main_form').style.display = 'none';
        document.getElementById('return_to_form').style.display = 'block';
        serverdata = eval( '(' + xmlhttproll.responseText + ')');
        summary_string = '';
        player_string = '';
        game_string = '';
        num_sum_charts = 1;
        //following can be used to quickly turn plotting off and on
        plotting = 1;
        if(parseInt(serverdata.results_exist) == 1) {
          //team summaries
          summary_string += '<ul class="nav nav-pills">';
          summary_string += '<li class="active" ><a href="#TeamSum" data-toggle="tab" onclick="setdisplay(4)">Team Stats</a></li>';
          summary_string += '<li><a href="#PlayerSum" data-toggle="tab" onclick="setdisplay(5)">Player Stats</a></li>';
          summary_string += '</ul>';
          summary_string += '<div class="tab-content">';
          summary_string += '<div class="tab-pane active" id="TeamSum">';
          //summary_string += '<br>Team Data<br>';
          if(plotting == 1) {
            //summary_string += '<img src=\"/static/'+serverdata.teamsumchart+'\" alt=\"\" >'
            summary_string += '<img src=\"'+STATIC_URL+serverdata.teamsumchart+'\" >'
          }

          summary_string += '<table id=\"player_stats\"><thead><tr><th>ATS</th><th>Win%</th><th>Over Covers</th><th>Avg Pts Scored</th><th>Avg Pts Allowed</th><th>Avg Total Points</th></tr></thead>';
       
          summary_string += '<tr>';
          for (i in serverdata.teama_summary) {
            summary_string += '<td>'+serverdata.teama_summary[i]+'</td>';
          }
          var totalpoints = parseFloat(serverdata.teama_summary[serverdata.teama_summary.length-2]) +  parseFloat(serverdata.teama_summary[serverdata.teama_summary.length-1]);
          summary_string += '<td>'+totalpoints.toFixed(2)+'</td>';
          summary_string += '</tr>';
          summary_string += '</table>';
          summary_string += '</div>';
          summary_string += '<div class="tab-pane" id="PlayerSum">';
          //qb avgs
          for (player in serverdata.qbs_with_stats) {
            summary_string += toTitleCase(serverdata.qbs_with_stats[player])+': '
            if(plotting == 1) {
              summary_string += 'Total Yards<br>';
              summary_string += '<img src="/static/'+serverdata.qb_charts[num_sum_charts*player]+'" alt="missing chart?" >';
              //summary_string += '<br><br>Pass Data<br>';
              //summary_string += '<img src="/static/'+serverdata.qb_charts[2*player]+'" alt="missing chart?" >';
              //summary_string += '<br><br>Rush Data<br>';
              //summary_string += '<img src="/static/'+serverdata.qb_charts[2*player+1]+'\" alt=\"missing chart?\" >';
            }
            summary_string += '<table id=\"player_stats\"><thead><tr><th>Comp/Game</th><th>Att/Game</th><th>Yds/Game</th><th>TD/Game</th><th>Rating</th></tr></thead>';
            summary_string += '<tr>';
            for (stat in serverdata.qb_avgs[player]) {
              summary_string += '<td>'+serverdata.qb_avgs[player][stat]+'</td>';
            }
            summary_string += '</tr>';
            summary_string += '</table>'
          }
          //rbwr avgs
          for (player in serverdata.rbwrs_with_stats) {
            summary_string += toTitleCase(serverdata.rbwrs_with_stats[player])+': '
            if(plotting == 1) {
              summary_string += 'Total Yards<br>';
              summary_string += '<img src="/static/'+serverdata.rbwr_charts[num_sum_charts*player]+'" alt="missing chart?" >';
              //summary_string += '<br>Reception Data<br>';
              //summary_string += '<img src="/static/'+serverdata.rbwr_charts[2*player]+'" alt="missing chart?" >';
              //summary_string += '<br><br>Rush Data<br>';
              //summary_string += '<img src="/static/'+serverdata.rbwr_charts[2*player+1]+'" alt="missing chart?" >';
            }
            summary_string += '<table id=\"player_stats\"><thead><tr><th>RushYds/Game</th><th>Yds/Rush</th><th>RushTD/Game</th><th>RecYds</th><th>Yds/Rec</th><th>RecTD/Game</th></tr></thead>';
            summary_string += '<tr>';
            for (stat in serverdata.rbwr_avgs[player]) {
              summary_string += '<td>'+serverdata.rbwr_avgs[player][stat]+'</td>';
            }
            summary_string += '</tr>';
            summary_string += '</table>';
          }
          //def avgs
          for (player in serverdata.defs_with_stats) {
            summary_string += '<br><br>'+toTitleCase(serverdata.defs_with_stats[player])+'<br>'
            summary_string += '<table id=\"player_stats\"><thead><tr><th>Tackles/Game</th><th>Sacks/Game</th><th>Int/Game</th></tr></thead>';
            summary_string += '<tr>';
            for (stat in serverdata.def_avgs[player]) {
              summary_string += '<td>'+serverdata.def_avgs[player][stat]+'</td>';
            }
            summary_string += '</tr>';
            summary_string += '</table>';
            //if(plotting == 1) {
            //}
          }
          summary_string += '</div></div>';//tab-pane and tab-content
          //document.getElementById('summary').innerHTML = summary_string;
          //Full player data
          var index = 0;
          var column_index;
          var row_index;
          var lastname = '';
          var firstname = '';
          var position = '';
          var numcolumns = 0;
          var season = 0;
          var show_full_player_table = 1;
          var firstplayer = 1;
          player_string += '<ul class="nav nav-pills">';
          player_string += '<li class="active" ><a href="#PlayerTables" data-toggle="tab" onclick="setdisplay(7)">Tables</a></li>';
          player_string += '<li ><a href="#PlayerCharts" data-toggle="tab" onclick="setdisplay(6)">Charts</a></li>';
          player_string += '</ul>';
          player_string += '<div class="tab-content">';
          player_string += '<div class="tab-pane" id="PlayerCharts">';
          /*This chart takes too long too generate at the back end and is not very useful
            Maybe ill replace it later with a javascript front end guy 
          for (player in serverdata.players_with_stats) {
                  player_string += toTitleCase(serverdata.players_with_stats[player])+': Yards/Game<br>'
                  player_string += '<img src="/static/'+serverdata.playerdata_charts[player]+'" alt="missing chart?" >';
                  player_string += '<br>';
          }
          */
          player_string += '</div>';//PlayerCharts
          player_string += '<div class="tab-pane active" id="PlayerTables">';
          if(show_full_player_table == 1) {
            while(index < serverdata.player_table.length && serverdata.player_table[index+4] != undefined) {
              if(serverdata.player_table[index] == 'hdr') {
                row_index = 0
                index += 1;
                lastname = toTitleCase(serverdata.player_table[index]);
                index += 1;
                firstname = toTitleCase(serverdata.player_table[index]);
                index += 1;
                position = positions[serverdata.player_table[index]];
                if(position == 'QB'){
                  if(firstplayer != 1) {
                    player_string += '</table>';
                  }
                  player_string += 'Full Stats for '+firstname+' '+lastname;
                  player_string += '<table id=\"player_stats\"><thead><tr><th>Season</th><th>Week</th><th>Away</th><th>Score</th><th>Home</th><th>Score</th><th>Comp</th><th>Att</th><th>Yards</th><th>TD</th><th>Rating</th></tr></thead>';
                  //following is subject to change, based on how much data im showing for each position
                  numcolumns = 11;
                }
                else if(position == 'RB' || position ==  'FB' || position == 'WR' || position ==  'TE') {
                  if(firstplayer != 1) {
                    player_string += '</table>';
                  }
                  player_string += 'Full Stats for '+firstname+' '+lastname;
                  player_string += '<table id=\"player_stats\"><thead><tr><th>Season</th><th>Week</th><th>Away</th><th>Score</th><th>Home</th><th>Score</th><th>RushYds</th><th>RushTD</th><th>RecYds</th><th>RecTD</th></tr></thead>';
                  //following is subject to change, based on how much data im showing for each position
                  numcolumns = 10;
                }
                else {//defensive player with stats
                  if(firstplayer != 1) {
                    player_string += '</table>';
                  }
                  player_string += 'Full Stats for '+firstname+' '+lastname;
                  player_string += '<table id=\"player_stats\"><thead><tr><th>Season</th><th>Week</th><th>Away</th><th>Score</th><th>Home</th><th>Score</th><th>Tackles</th><th>Sacks</th><th>Ints</th></tr></thead>';
                  //following is subject to change, based on how much data im showing for each position
                  numcolumns = 9;
                }
                firstplayer = 0;
              }
              player_string += '<tr>';
              for(column_index = 0; column_index < numcolumns; column_index+=1) {      
                if(column_index< 6 && serverdata.result_table[row_index*game_columns + column_index] != undefined) {
                  if(column_index == 1)  {
                    player_string += '<td>'+get_week(season,serverdata.result_table[row_index*game_columns + column_index])+'</td>';
                  }
                  else if(column_index == 2 || column_index == 4) {
                    player_string += '<td>'+teams[serverdata.result_table[row_index*game_columns + column_index]]+'</td>';
                  }
                  else {
                    player_string += '<td>'+serverdata.result_table[row_index*game_columns + column_index]+'</td>';
                    if(column_index == 0) {
                      season = serverdata.result_table[row_index*game_columns + column_index];
                    }
                  }
                }
                else {
                  index +=1;
                  if(serverdata.player_table[index] != 'hdr') {
                    player_string += '<td>'+serverdata.player_table[index]+'</td>';
                  }
                  else {
                    column_index = numcolumns;
                  }
                }
              }
              player_string += '</tr>';
              row_index += 1;
              if(index == serverdata.player_table.length-1) {
                player_string += '</table>';
              }
            }
          }
          player_string += '</div>';//playertables
          player_string += '</div>';
          //document.getElementById('player_results').innerHTML = player_string;
          
          game_string += '<table id=\"gradient-style\"><thead><tr><th>Year</th><th>Week</th><th>Away</th><th>Score</th><th>Home</th><th>Score</th><th>Spread</th><th>Over/Under</th><th>Team A</th></tr></thead>';
          var row_index = 0;
          var column_index;
          while(row_index < serverdata.result_table.length && serverdata.result_table[row_index*game_columns] != undefined) {
            game_string += '<tr>';
            for(column_index = 0; column_index < game_columns; column_index+=1) {      
              if(column_index == 1) {
                game_string += '<td>'+get_week(season, serverdata.result_table[row_index*game_columns + column_index])+'</td>';
              }
              else if(column_index == 2 || column_index == 4 || column_index == 8) {
                game_string += '<td>'+teams[serverdata.result_table[row_index*game_columns + column_index]]+'</td>';
              }
              else{
                game_string += '<td>'+serverdata.result_table[row_index*game_columns + column_index]+'</td>';
                if(column_index == 0) {
                  season = serverdata.result_table[row_index*game_columns + column_index];
                }
              }
            }
            game_string += '</tr>';
            row_index +=1;
          }
          game_string += '</table>';
        }
        else {
          game_string += 'No games match query';
          summary_string += 'No games match query';
          player_string += 'No games match query';
        }
        document.getElementById('game_results').innerHTML = game_string;
        document.getElementById('summary').innerHTML = summary_string;
        document.getElementById('player_results').innerHTML = player_string;
      }
    }
    //submit response function not sure what the true parameter is all about
    var i = 0;
    var str = 'num_team_a_conditions='+(condition_number_a+1)+'&num_team_b_conditions='+(condition_number_b+1)+'&num_game_conditions='+(condition_number_g+1)+'&';
    while(i < condition_number_a+1) {
      if(document.forms['conditions']['a_'+i] != undefined) {
        if(document.forms['conditions']['a_'+i].value != 0) {
          str += 'a_'+i+'='+document.forms['conditions']['a_'+i].value+'&';
          if(document.forms['conditions']['a_'+i+'_value'] != undefined){
            str += 'a_'+i+'_value='+document.forms['conditions']['a_'+i+'_value'].value+'&';
          }
         
          
          //Adding comptype to GET req
        }
        else {
          str += 'a_'+i+'='+document.forms['conditions']['a_'+i].value+'&';
          str += 'a_'+i+'_value=0&';
        }
      }
      else {
          str += 'a_'+i+'=0&';
          str += 'a_'+i+'_value=0&';
      }
      if(document.forms['conditions']['a_'+i+'_comptype'] != undefined){
        str += 'a_'+i+'_comptype='+document.forms['conditions']['a_'+i+'_comptype'].value+'&';
      }
      i+=1;
    }
    i = 0;
    while(i < condition_number_b+1) {
      if(document.forms['conditions']['b_'+i] != undefined) {
        if(document.forms['conditions']['b_'+i].value != 0) {
          str += 'b_'+i+'='+document.forms['conditions']['b_'+i].value+'&';
          if(document.forms['conditions']['b_'+i+'_value'] != undefined){
            str += 'b_'+i+'_value='+document.forms['conditions']['b_'+i+'_value'].value+'&';
          }
        }
        else {
          str += 'b_'+i+'='+document.forms['conditions']['b_'+i].value+'&';
          str += 'b_'+i+'_value=0&';
        }
      }
      else {
          str += 'b_'+i+'=0&';
          str += 'b_'+i+'_value=0&';
      }
      if(document.forms['conditions']['b_'+i+'_comptype'] != undefined){
        str += 'b_'+i+'_comptype='+document.forms['conditions']['b_'+i+'_comptype'].value+'&';
      }
      i+=1;
    }
    i = 0;
    while(i < condition_number_g+1) {
      if(document.forms['conditions']['g_'+i] != undefined) {
        if(document.forms['conditions']['g_'+i].value != 0) {
          str += 'g_'+i+'='+document.forms['conditions']['g_'+i].value+'&';
          if(document.forms['conditions']['g_'+i+'_value'] != undefined){
            str += 'g_'+i+'_value='+document.forms['conditions']['g_'+i+'_value'].value+'&';
          }
        }
        else {
          str += 'g_'+i+'='+document.forms['conditions']['g_'+i].value+'&';
          str += 'g_'+i+'_value=0&';
        }
      }
      else {
          str += 'g_'+i+'=0&';
          str += 'g_'+i+'_value=0&';
      }
      if(document.forms['conditions']['g_'+i+'_comptype'] != undefined){
        str += 'g_'+i+'_comptype='+document.forms['conditions']['g_'+i+'_comptype'].value+'&';
      }
      i+=1;
    }
    xmlhttproll.open('GET', '/submit/?'+str, true);
    xmlhttproll.send();

}

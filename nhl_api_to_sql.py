import os
import sys
import getopt
import json
import requests
import math
import psycopg2
import pandas as pd
from sqlalchemy import create_engine

def main(argv):
    teams = requests.get("https://statsapi.web.nhl.com/api/v1/teams")
    teams = teams.json()
    teams_by_id = {}
    for team in teams['teams']:
        teams_by_id[team['id']] = team['name']
    schedule = requests.get("https://statsapi.web.nhl.com/api/v1/schedule?startDate=2018-10-03&endDate=2019-04-06")
    schedule = schedule.json()
    shots_df = pd.DataFrame(columns=["gameID","teamID","opponentID","playerName","playerID","result","Xcoord","Ycoord","period","time","shooterTeamGoals","opponentGoals", "goalie"])
    for date in schedule['dates']:
        for game in date['games']:
            game_id = game['gamePk']
            shots_df = shots_df.append(get_shots_info(game_id), ignore_index=True)
    append_to_db(shots_df)
    print(shots_df)

def append_to_db(shots_df):
    engine = create_engine('postgresql://samoz:samoz@localhost:5432/nhl_stats_201819')
    shots_df.to_sql('shots',engine,if_exists='append')

def get_shots_info(game_id):
    game = requests.get("https://statsapi.web.nhl.com/api/v1/game/"+str(game_id)+"/feed/live")
    game = game.json()
    playTypes = ["Blocked Shot","Shot","Goal","Missed Shot"]
    all_shots = []
    for play in game['liveData']['plays']['allPlays']:
        if play['result']['event'] in playTypes:
            all_shots.append(play)
    away_team_id = game['gameData']['teams']['away']['id']
    home_team_id = game['gameData']['teams']['home']['id']
    shots_df = pd.DataFrame(columns=["gameID","teamID","opponentID","playerName","playerID","result","Xcoord","Ycoord","period","time","shooterTeamGoals","opponentGoals", "goalie"])
    for shot in all_shots:
        # print(json.dumps(shot,indent=2))
        # print(num)
        dict_to_append = { }
        dict_to_append['gameID'] = game_id
        for player in shot['players']:
            if (player['playerType']=='Shooter' or player['playerType']=='Scorer'):
                dict_to_append['playerName'] = player['player']['fullName']
                dict_to_append['playerID'] = player['player']['id']
            if (player['playerType']=='Goalie'):
                dict_to_append['goalie'] = player['player']['fullName']
        if ('event' in shot['result']):
            dict_to_append['result'] = shot['result']['event']
        if ('x' in shot['coordinates'] and 'y' in shot['coordinates']):
            dict_to_append['Xcoord'] = shot['coordinates']['x']
            dict_to_append['Ycoord'] = shot['coordinates']['y']
        if ('period' in shot['about']):
            dict_to_append['period'] = shot['about']['period']
        if ('periodTime' in shot['about']):
            dict_to_append['time'] = shot['about']['periodTime']
        if ('goals' in shot['about'] and 'id' in shot['team'] and shot['team']['id'] == home_team_id):
            dict_to_append['shooterTeamGoals'] = shot['about']['goals']['home']
            dict_to_append['opponentGoals'] = shot['about']['goals']['away']
            dict_to_append['opponentID'] = away_team_id
            dict_to_append['teamID'] = home_team_id
        elif ('goals' in shot['about']):
            dict_to_append['shooterTeamGoals'] = shot['about']['goals']['away']
            dict_to_append['opponentGoals'] = shot['about']['goals']['home']
            dict_to_append['opponentID'] = home_team_id
            dict_to_append['teamID'] = away_team_id
        # print(pd.DataFrame(dict_to_append, columns=dict_to_append.keys(),index=[0]))
        shots_df = shots_df.append(dict_to_append, ignore_index=True)
        # print(shots_df)
    return shots_df

if __name__ == "__main__":
    main(sys.argv[1:])

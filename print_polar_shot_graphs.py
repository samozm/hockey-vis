import os
import sys
import getopt
import json
import requests
import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def print_graphs(game_id,teams_by_id,schedule,directory):
    game = requests.get("https://statsapi.web.nhl.com/api/v1/game/"+str(game_id)+"/feed/live")
    game = game.json()
    home = game['gameData']['teams']['home']['id']
    away = game['gameData']['teams']['away']['id']
    playTypes = ["Blocked Shot","Shot","Goal"]
    all_shots = []
    for play in game['liveData']['plays']['allPlays']:
        if play['result']['event'] in playTypes:
            all_shots.append(play)
    home_shots = pd.DataFrame(columns=["r","theta"])
    home_blocked_shots = pd.DataFrame(columns=["r","theta"])
    home_goals = pd.DataFrame(columns=["r","theta"])
    away_shots = pd.DataFrame(columns=["r","theta"])
    away_blocked_shots = pd.DataFrame(columns=["r","theta"])
    away_goals = pd.DataFrame(columns=["r","theta"])
    for shot in all_shots:
        if shot['result']['event']=="Shot":
            if shot['team']['id'] == home:
                home_shots = home_shots.append(pd.DataFrame(flip2pol(shot['coordinates'].copy()),index=[0]))
            else:
                away_shots = away_shots.append(pd.DataFrame(flip2pol(shot['coordinates'].copy()),index=[0]))
        elif shot['result']['event']=="Blocked Shot":
            if shot['team']['id'] == home:
                home_blocked_shots = home_blocked_shots.append(pd.DataFrame(flip2pol(shot['coordinates'].copy()),index=[0]))
            else:
                away_blocked_shots = away_blocked_shots.append(pd.DataFrame(flip2pol(shot['coordinates'].copy()),index=[0]))
        else: 
            if shot['team']['id'] == home:
                home_goals = home_goals.append(pd.DataFrame(flip2pol(shot['coordinates'].copy()),index=[0]))
            else:
                away_goals = away_goals.append(pd.DataFrame(flip2pol(shot['coordinates'].copy()),index=[0]))
    plot_graphs(home_shots,home_blocked_shots,home_goals,teams_by_id[home],schedule['dates'][0]['date'],directory)
    plot_graphs(away_shots,away_blocked_shots,away_goals,teams_by_id[away],schedule['dates'][0]['date'],directory)

def plot_graphs(shots,blocked_shots,goals,team_name,date,directory):
    fig = plt.figure()
    plot = fig.add_subplot(111, projection='polar')
    plot.plot(shots['theta'],shots['r'],"o",c="yellow",label="Shots on Goal")
    plot.plot(blocked_shots['theta'],blocked_shots['r'],"o",c="red",label="Blocked Shots")
    plot.plot(goals['theta'],goals['r'],"o",c="green",label="Goals")
    plot.set_xlim([-(math.pi/2),(math.pi/2)])
    plot.set_ylim([0,100])
    crease_cr=pd.DataFrame(toPol(0,4),index=[0])
    crease_cr=crease_cr.append(pd.DataFrame(toPol(4,4),index=[0]))
    crease_cr=crease_cr.append(pd.DataFrame(toPol(4,-4),index=[0]))
    crease_cr=crease_cr.append(pd.DataFrame(toPol(0,-4),index=[0]))
    plot.plot(crease_cr['theta'],crease_cr['r'],c='blue',label="Crease")
    #plot.gca().add_artist(plt.Circle((96,0),4,color="b"))
    #plot.gca().add_artist(plt.Rectangle((96,-4),8,8,color="b"))
    plt.title(team_name + " Shots")
    plt.legend(bbox_to_anchor=(1.3,1))
    plt.savefig(directory + "/" + team_name + " Shots " + date + '.png')
    plt.close(fig)

# get all coordinates as positive and change them to polar coordinates
def flip2pol(coordinates):
    if (coordinates['x'] < 0):
        coordinates['x']*=(-1)
    coordinates['x'] = 100 - coordinates['x']
    return toPol(coordinates['x'],coordinates['y'])

def toPol(x,y):
    r = np.sqrt((x**2) + (y**2))
    if(x!=0):
        theta = np.arctan(y / x)
    else:
        if(y > 0):
            theta = math.pi/2
        else:
            theta = -math.pi/2
    return {'r':r,'theta':theta}

def get_teams():
    teams = requests.get("https://statsapi.web.nhl.com/api/v1/teams")
    teams = teams.json()
    teams_by_id = {}
    for team in teams['teams']:
        teams_by_id[team['id']] = team['name']
    return teams_by_id

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hd:",["date="])
    except getopt.GetoptError:
        print('test.py -d <date>, <date> should be in form YYYY-MM-DD')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -d <date>, <date> should be in form YYYY-MM-DD')
            return
        elif opt in ('-d','--date'):
            date=arg
    teams_by_id = get_teams()
    if (date):
        schedule = requests.get("https://statsapi.web.nhl.com/api/v1/schedule?date="+str(date))
    else:
        schedule = requests.get("https://statsapi.web.nhl.com/api/v1/schedule")
    schedule = schedule.json()
    directory = schedule['dates'][0]['date']
    if not os.path.exists(directory):
        os.mkdir(directory)
    for date in schedule['dates']:
        for gm in date['games']:
            print_graphs(gm['gamePk'],teams_by_id,schedule,directory)
    plt.close('all')

if __name__ == "__main__":
    main(sys.argv[1:])

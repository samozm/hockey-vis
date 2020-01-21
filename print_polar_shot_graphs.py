import os
import sys
import getopt
import json
import requests
import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def get_shots(game_id,teams_by_id):
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
                home_shots = home_shots.append(pd.DataFrame(flip2pol(shot['coordinates'].copy(),True),index=[0]))
            else:
                away_shots = away_shots.append(pd.DataFrame(flip2pol(shot['coordinates'].copy(), False),index=[0]))
        elif shot['result']['event']=="Blocked Shot":
            if shot['team']['id'] == home:
                home_blocked_shots = home_blocked_shots.append(pd.DataFrame(flip2pol(shot['coordinates'].copy(), True),index=[0]))
            else:
                away_blocked_shots = away_blocked_shots.append(pd.DataFrame(flip2pol(shot['coordinates'].copy(), False),index=[0]))
        else: 
            if shot['team']['id'] == home:
                home_goals = home_goals.append(pd.DataFrame(flip2pol(shot['coordinates'].copy(),True),index=[0]))
            else:
                away_goals = away_goals.append(pd.DataFrame(flip2pol(shot['coordinates'].copy(),False),index=[0]))
    return home,home_goals,home_blocked_shots,home_shots,away,away_goals,away_blocked_shots,away_shots

def print_graphs(home_name,home_goals,home_blocked_shots,home_shots,away_name,away_goals,away_blocked_shots,away_shots,schedule,directory,heatmap):
    fig = plt.figure(figsize=(12,12))
    if (heatmap):
        plot = fig.add_axes([0.15,0.3,0.3,0.45])
        plot_heat(plot,home_shots,home_blocked_shots,home_goals,home_name,schedule['dates'][0]['date'],directory, True)
    else:
        plot = fig.add_axes([0.05,0.1,0.45,0.9],polar=True)
        plot_graphs(plot,home_shots,home_blocked_shots,home_goals,home_name,schedule['dates'][0]['date'],directory, True) 
    plot = fig.add_axes([0.45,0.3,0.15,1])
    plot_table(plot,home_goals,home_name,away_goals,away_name)
    if (heatmap):
        plot = fig.add_axes([0.55,0.3,0.3,0.45])
        plot_heat(plot,away_shots,away_blocked_shots,away_goals,away_name,schedule['dates'][0]['date'],directory, False)
    else:
        plot = fig.add_axes([0.5,0.1,0.45,0.9],polar=True)
        plot_graphs(plot,away_shots,away_blocked_shots,away_goals,away_name,schedule['dates'][0]['date'],directory, False)
    fig.suptitle(home_name + " vs " + away_name)
    if(heatmap):
        plt.show()
        #plt.savefig(directory + "/" + home_name + away_name + "Heatmap" + schedule['dates'][0]['date'] + '.png')
    else:
        fig.legend(loc=(0.4,0.4))
        plt.savefig(directory + "/" + home_name + away_name + "Shots" + schedule['dates'][0]['date'] + '.png')
    plt.close()

def plot_table(plot,home_goals,home_team,away_goals,away_team):
    score = [['{:d}'.format(len(home_goals)),'{:d}'.format(len(away_goals))]]
    plot.text(-0.03,0.6,len(home_goals))
    plot.text(0.8,0.6,len(away_goals))
    plot.spines['right'].set_visible(False)
    plot.spines['top'].set_visible(False)
    plot.spines['left'].set_visible(False)
    plot.spines['bottom'].set_visible(False)
    plot.get_xaxis().set_visible(False)
    plot.get_yaxis().set_visible(False)

def plot_graphs(plot,shots,blocked_shots,goals,team_name,date,directory,home_team):
    if (home_team):
        plot.plot(shots['theta'],shots['r'],"o",c="yellow",label="Shots on Goal")
        plot.plot(blocked_shots['theta'],blocked_shots['r'],"o",c="red",label="Blocked Shots")
        plot.plot(goals['theta'],goals['r'],"o",c="green",label="Goals")
        plot.set_thetamin(-90)
        plot.set_thetamax(90)
        plot.set_thetagrids([45,0,-45],labels=('',''))
        crease_cr=pd.DataFrame(toPol(0,4),index=[0])
        crease_cr=crease_cr.append(pd.DataFrame(toPol(4.5,4),index=[0]))
        crease_cr=crease_cr.append(pd.DataFrame(toPol(4.5,-4),index=[0]))
        crease_cr=crease_cr.append(pd.DataFrame(toPol(0,-4),index=[0]))
        theta = np.arange(-90,90,0.1)

    else:
        plot.plot(shots['theta'],shots['r'],"o",c="yellow")
        plot.plot(blocked_shots['theta'],blocked_shots['r'],"o",c="red")
        plot.plot(goals['theta'],goals['r'],"o",c="green")
        plot.set_thetamin(90)
        plot.set_thetamax(270)
        plot.set_thetagrids([135,180,225],labels=('',''))
        crease_cr=pd.DataFrame(toPol(0,-4),index=[0])
        crease_cr=crease_cr.append(pd.DataFrame(toPol(-4.5,-4),index=[0]))
        crease_cr=crease_cr.append(pd.DataFrame(toPol(-4.5,4),index=[0]))
        crease_cr=crease_cr.append(pd.DataFrame(toPol(0,4),index=[0]))
        theta = np.arange(90,270,0.1)

    plot.set_rmin(0)
    plot.set_rmax(100)
    plot.plot(crease_cr['theta'],crease_cr['r'],c='red')
    r = [6]*(1800)
    plot.plot(theta,r,c='red')
    
def plot_heat(plot,shots,blocked_shots,goals,team_name,date,directory,home_team):
    all_shots = shots.append(blocked_shots).append(goals)
    all_shots = pd.DataFrame.from_dict(all_shots.apply(fromPol,axis=1))
    all_shots.drop(columns=['r','theta'])
    if (home_team):
        plot.set_xlim(0,50)
    else:
        plot.set_xlim(-50,0)
    plot.set_ylim(-50,50)
    plot.hist2d(all_shots['x'],all_shots['y'],bins=50,cmap='bwr')

# get all coordinates as positive and change them to polar coordinates
def flip2pol(coordinates, home):
    if (coordinates['x'] < 0):
        coordinates['x']*=(-1)
    if (home):
        coordinates['x'] = 100 - coordinates['x']
    else: 
        coordinates['x'] = -(100 - coordinates['x'])
    return toPol(coordinates['x'],coordinates['y'])

def toPol(x,y):
    r = np.sqrt((x**2) + (y**2))
    theta = np.arctan2(y, x)
    return {'r':r,'theta':theta}

def fromPol(col):
    r = col['r']
    theta = col['theta']
    col['x'] = r * np.cos(theta)
    col['y'] = r * np.sin(theta)
    return col

def get_teams():
    teams = requests.get("https://statsapi.web.nhl.com/api/v1/teams")
    teams = teams.json()
    teams_by_id = {}
    for team in teams['teams']:
        teams_by_id[team['id']] = team['name']
    return teams_by_id

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hmd:",["map","date="])
    except getopt.GetoptError:
        print('test.py -d <date>, <date> should be in form YYYY-MM-DD')
        sys.exit(2)
    heatmap = False
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -d <date>, <date> should be in form YYYY-MM-DD, -m --map optional arg to print a heatmap')
            return
        elif opt in ('-d','--date'):
            date=arg
        elif opt in ('-m','--map'):
            heatmap = True
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
            home_id,home_goals,home_blocked_shots,home_shots,away_id,away_goals,away_blocked_shots,away_shots = get_shots(gm['gamePk'],teams_by_id)
            home_name = teams_by_id[home_id]
            away_name = teams_by_id[away_id]
            print_graphs(home_name,home_goals,home_blocked_shots,home_shots,away_name,away_goals,away_blocked_shots,away_shots,schedule,directory,heatmap)
    plt.close('all')

if __name__ == "__main__":
    main(sys.argv[1:])

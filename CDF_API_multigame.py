# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 10:57:13 2020

@author: joshu
"""

import pickle
import pandas as pd
import numpy as np
import time
import datetime
from fractions import Fraction
import webbrowser
import scipy.io
import requests
import json
import glob


lvh_pkl = 'C:/Users/joshu/Documents/py_projects/joe_model/CDF_API/lvh_prob_final.pkl'
with open(lvh_pkl, 'rb') as file:
    lvh_prob_dict = pickle.load(file)
    
lvh_count_pkl = 'C:/Users/joshu/Documents/py_projects/joe_model/CDF_API/lvh_count_final.pkl'
with open(lvh_count_pkl, 'rb') as file:
    lvh_count_dict = pickle.load(file)

#hvl means better team is losing (negative score diff)    
hvl_pkl = 'C:/Users/joshu/Documents/py_projects/joe_model/CDF_API/hvl_prob_final.pkl'
with open(hvl_pkl, 'rb') as file:
    hvl_prob_dict = pickle.load(file)

hvl_count_pkl = 'C:/Users/joshu/Documents/py_projects/joe_model/CDF_API/hvl_count_final.pkl'
with open(hvl_count_pkl, 'rb') as file:
    hvl_count_dict = pickle.load(file)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def get_EV(bet1):

    while True:
        print(datetime.datetime.now())
        # bet1 = 100
        #pull game info
        print("pulling game stats")
####YOU HAVE TO CHANGE MONTH IN LINK AT THE END OF EACH MONTH####
        game_info = requests.get('https://nba.cheapdatafeeds.com/api/json/scores/v1/basketball/nba?month=01&year=2021&seasonType=Regular&api-key=051e498ade189575df68ffc7044b34d6')
        game_info_dict = game_info.json()
        
        #make empty dataframe to append the data to
        game_df = pd.DataFrame(columns = ['GameID', 'Home_Team', 'Away_Team','Home_Points', 'Away_Points',
                                          'current_quarter', 'Time_elapsed'])
        
        #get game stats and append to game_df
        for key in game_info_dict['games'].keys():
            if game_info_dict['games'][key]['status'] == 'Live':
                GameID = game_info_dict['games'][key]['gameUID']
                Home_team = game_info_dict['games'][key]['homeTeam']
                Away_team = game_info_dict['games'][key]['awayTeam']
                Home_points = game_info_dict['games'][key]['scoreHomeTotal']
                Away_points = game_info_dict['games'][key]['scoreAwayTotal']
                try:    
                    current_quarter = game_info_dict['games'][key]['currentPeriod']
                except:
                    print('in intermission')
                    continue
                    
            
                
                #get time and convert it to correct format
                try:
                    Time = game_info_dict['games'][key]['currentPeriodTimeRemaining']
                except:
                    print('period has not started')
                    continue
                Time_conv = time.strptime(Time, "%M:%S")
                Time_remaining = datetime.timedelta(minutes=Time_conv.tm_min,seconds=Time_conv.tm_sec).total_seconds()
                if Time_remaining is not None:
                    
                    quarter_time_elapsed = 720 - Time_remaining
                    if current_quarter == '1':
                        time_elapsed = 720-Time_remaining
                        game_df = game_df.append({'GameID':GameID, 'Home_Team':Home_team, 'Away_Team':Away_team,
                                              'Home_Points':Home_points, 'Away_Points':Away_points,
                                                  'current_quarter':current_quarter, 'Time_elapsed':time_elapsed},
                                             ignore_index=True)
                    elif current_quarter == '2':
                        time_elapsed = quarter_time_elapsed + 720
                        game_df = game_df.append({'GameID':GameID, 'Home_Team':Home_team, 'Away_Team':Away_team,
                                              'Home_Points':Home_points, 'Away_Points':Away_points,
                                                  'current_quarter':current_quarter, 'Time_elapsed':time_elapsed},
                                             ignore_index=True)
                    elif current_quarter == '3':
                        time_elapsed = quarter_time_elapsed + 1440
                        game_df = game_df.append({'GameID':GameID, 'Home_Team':Home_team, 'Away_Team':Away_team,
                                              'Home_Points':Home_points, 'Away_Points':Away_points,
                                                  'current_quarter':current_quarter, 'Time_elapsed':time_elapsed},
                                             ignore_index=True)
                    else:
                        time_elapsed = quarter_time_elapsed + 2160
                        game_df = game_df.append({'GameID':GameID, 'Home_Team':Home_team, 'Away_Team':Away_team,
                                              'Home_Points':Home_points, 'Away_Points':Away_points,
                                                  'current_quarter':current_quarter, 'Time_elapsed':time_elapsed},
                                             ignore_index=True)
                else:
                    print('game is not listed as live')
                        
                
        #pull game odds 
        print("pulling Bovada game odds")
        game_odds = requests.get('https://bovada-basketball-nba.cheapdatafeeds.com/api/json/odds/v2/basketball/nba?api-key=051e498ade189575df68ffc7044b34d6')
        go_dict = game_odds.json()
        
        odds_df = pd.DataFrame(columns = ['GameID', 'Home_fractional', 'Away_fractional'])
        
        for key_2 in go_dict['games'].keys():
            if go_dict['games'][key_2]['isLive'] == '1':
                if 'gameMoneylineHomePrice' in go_dict['games'][key_2].keys():
                    Home_ML = int(go_dict['games'][key_2]['gameMoneylineHomePrice'])
                    if Home_ML > 0:
                        Home_fractional = Home_ML / 100
                    else:
                        Home_fractional = (-100)/ Home_ML
                    Away_ML = int(go_dict['games'][key_2]['gameMoneylineAwayPrice'])
                    if Away_ML > 0:
                        Away_fractional = Away_ML / 100
                    else:
                        Away_fractional = (-100) / Away_ML
                else:
                    print("no money line listed for game {} vs {}".format(go_dict['games'][key_2]['homeTeam'], go_dict['games'][key_2]['awayTeam']))
                    
            GameID = go_dict['games'][key_2]['gameUID']
            odds_df = odds_df.append({'GameID':GameID, 'Home_fractional':Home_fractional,
                                      'Away_fractional':Away_fractional}, ignore_index=True)
                
        live_df = game_df.merge(odds_df, on=['GameID'])
        live_df = live_df.set_index('GameID')

        #filter out rows in which time_sec > real time elapsed
        print("reading in daily file")

        daily_file = pd.read_csv('C:/Users/joshu/Documents/py_projects/joe_model/CDF_API/daily_file.csv')
        
        median_df = pd.DataFrame(columns=['Home_Points', 'Away_Points', 'Home_fractional', 'Away_fractional',
                              'lower tier team', 'higher tier team', 'timeB', 'score',
                              'EV_low_tier', 'EV_higher_tier', 'future_time_block', 'lvh_prob', 'hvl_prob',
                              'lvh_kelly', 'hvl_kelly'])
        
        for game in live_df.index:
        
            daily_file_filtered = daily_file[daily_file['time_sec'] > live_df['Time_elapsed'].loc[game]]
            #filter out teams that don't relate to current looped index
            df_filt_oneT = daily_file_filtered.loc[(daily_file_filtered['lower tier team'] == live_df['Home_Team'].loc[game]) | (daily_file_filtered['higher tier team'] == live_df['Home_Team'].loc[game]),:]
                
            #merge the filtered daily file and the live_df
            if live_df['Home_Team'].loc[game] == df_filt_oneT['lower tier team'].iloc[0]:
                final_df = live_df.merge(df_filt_oneT,
                                     left_on=['Home_Team'],
                                     right_on = ['lower tier team'])
            else:
                final_df = live_df.merge(df_filt_oneT,
                                     left_on=['Home_Team'],
                                     right_on = ['higher tier team'])
            
            #get current score differential
            if final_df['lower tier team'][0] == final_df['Home_Team'][0]:
                score_diff = (int(final_df['Home_Points'][0]) - int(final_df['Away_Points'][0]))
            else:
                score_diff = (int(final_df['Away_Points'][0])-int(final_df['Home_Points'][0]))
                
            if final_df['higher tier team'][0] == final_df['Home_Team'][0]:
                high_score_diff = (int(final_df['Home_Points'][0]) - int(final_df['Away_Points'][0]))
            else:
                high_score_diff = (int(final_df['Away_Points'][0])-int(final_df['Home_Points'][0]))
                
            
            
            
            
            tier_matchup = str(final_df['lower tier'][0]) + ',' + str(final_df['higher tier'][0])
            ev_out_df = pd.DataFrame(columns=['index', 'EV_low_tier', 'EV_higher_tier', 'future_time_block', 'lvh_prob', 'hvl_prob', 'lvh_kelly', 'hvl_kelly'])
    
    
            
            
            for ind in final_df.index: 
                if final_df['Time_elapsed'].iloc[ind] <=180:
                    time_block = 1
                elif 180 < final_df['Time_elapsed'].iloc[ind] <= 360:
                    time_block = 2
                elif 360 < final_df['Time_elapsed'].iloc[ind] <= 540:
                    time_block = 3
                elif 540 < final_df['Time_elapsed'].iloc[ind] <= 720:
                    time_block = 4
                elif 720 < final_df['Time_elapsed'].iloc[ind] <= 900:
                    time_block = 5
                elif 900 < final_df['Time_elapsed'].iloc[ind] <= 1080:
                    time_block = 6
                elif 1080 < final_df['Time_elapsed'].iloc[ind] <= 1260:
                    time_block = 7
                elif 1260 < final_df['Time_elapsed'].iloc[ind] <= 1440:
                    time_block = 8
                elif 1440 < final_df['Time_elapsed'].iloc[ind] <= 1620:
                    time_block = 9
                elif 1620 < final_df['Time_elapsed'].iloc[ind] <= 1800:
                    time_block = 10
                elif 1800 < final_df['Time_elapsed'].iloc[ind] <= 1980:
                    time_block = 11
                elif 1980 < final_df['Time_elapsed'].iloc[ind] <= 2160:
                    time_block = 12
                elif 2160 < final_df['Time_elapsed'].iloc[ind] <= 2340:
                    time_block = 13
                elif 2340 < final_df['Time_elapsed'].iloc[ind] <= 2520:
                    time_block = 14
                elif 2520 < final_df['Time_elapsed'].iloc[ind] <= 2700:
                    time_block = 15
                else:
                    time_block = 16
    
            
    
                if final_df['time_sec'].iloc[ind] <=180:
                    future_time = 1
                elif 180 < final_df['time_sec'].iloc[ind] <= 360:
                    future_time = 2
                elif 360 < final_df['time_sec'].iloc[ind] <= 540:
                    future_time = 3
                elif 540 < final_df['time_sec'].iloc[ind] <= 720:
                    future_time = 4
                elif 720 < final_df['time_sec'].iloc[ind] <= 900:
                    future_time = 5
                elif 900 < final_df['time_sec'].iloc[ind] <= 1080:
                    future_time = 6
                elif 1080 < final_df['time_sec'].iloc[ind] <= 1260:
                    future_time = 7
                elif 1260 < final_df['time_sec'].iloc[ind] <= 1440:
                    future_time = 8
                elif 1440 < final_df['time_sec'].iloc[ind] <= 1620:
                    future_time = 9
                elif 1620 < final_df['time_sec'].iloc[ind] <= 1800:
                    future_time = 10
                elif 1800 < final_df['time_sec'].iloc[ind] <= 1980:
                    future_time = 11
                elif 1980 < final_df['time_sec'].iloc[ind] <= 2160:
                    future_time = 12
                elif 2160 < final_df['time_sec'].iloc[ind] <= 2340:
                    future_time = 13
                elif 2340 < final_df['time_sec'].iloc[ind] <= 2520:
                    future_time = 14
                elif 2520 < final_df['time_sec'].iloc[ind] <= 2700:
                    future_time = 15
                else:
                    future_time = 16
                
                
                # for ind in final_df.index:
                time_score = str(time_block) + ',' + str(score_diff)
                future_score = final_df['score'].iloc[ind]
                if lvh_count_dict[tier_matchup][time_score][str(future_time)][str(future_score)][0] > 49:
                    lvh_prob_win_dist = lvh_prob_dict[tier_matchup][time_score][str(future_time)]
                    lvh_prob_win = lvh_prob_win_dist.loc[:,str(future_score):].sum(axis=1)[0]
                else:
                    lvh_prob_win = 0
    
                lvh_prob_lose = 1-lvh_prob_win
        
                # #EV for lower tier team
                oddsB = final_df['oddsB higher tier'].iloc[ind]
                if final_df['Home_Team'].iloc[ind] == final_df['lower tier team'].iloc[ind]:
                    oddsA = float(Fraction(final_df['Home_fractional'].iloc[ind]))
                    bet2 = bet1*((oddsA+1)/(oddsB+1))
                    EV_low = ((((bet1*oddsA)-bet2)*.5)+(((bet2*oddsB)-bet1)*.5))*lvh_prob_win-(bet1*lvh_prob_lose)
                    try:
                        lvh_kelly = (0.02/(((1+0.02)/lvh_prob_win)-1))*2000
                    except:
                        lvh_kelly = 0
    
                else:
                    oddsA = float(Fraction(final_df['Away_fractional'].iloc[ind]))
                    bet2 = bet1*((oddsA+1)/(oddsB+1))
                    EV_low = ((((bet1*oddsA)-bet2)*.5)+(((bet2*oddsB)-bet1)*.5))*lvh_prob_win-(bet1*lvh_prob_lose)
                    try:
                        lvh_kelly = (0.02/(((1+0.02)/lvh_prob_win)-1))*2000
                    except:
                        lvh_kelly = 0
                        
                if EV_low < 0:
                    lvh_kelly = 0
    
            
            
                    
                    
    
                # EV higher tier team    
                time_score = str(time_block) + ',' + str(high_score_diff)
                high_future_score = final_df['score'].iloc[ind]
                if hvl_count_dict[tier_matchup][time_score][str(future_time)][str(high_future_score)][0] > 49:
                    hvl_prob_win_dist = hvl_prob_dict[tier_matchup][time_score][str(future_time)]
                    hvl_prob_win = hvl_prob_win_dist.loc[:,str(high_future_score):].sum(axis=1)[0]
                else:
                    hvl_prob_win = 0
    
                hvl_prob_lose = 1-hvl_prob_win
        
                # EV_high_list = []
                oddsB = final_df['oddsB lower tier'].iloc[ind]
                if final_df['Home_Team'].iloc[ind] == final_df['higher tier team'].iloc[ind]:
                    oddsA = float(Fraction(final_df['Home_fractional'].iloc[ind]))
                    bet2 = bet1*((oddsA+1)/(oddsB+1))
                    EV_high = ((((bet1*oddsA)-bet2)*.5)+(((bet2*oddsB)-bet1)*.5))*hvl_prob_win-(bet1*hvl_prob_lose)
                    try:    
                        hvl_kelly = (0.02/(((1+0.02)/hvl_prob_win)-1))*2000
                    except:
                        hvl_kelly = 0
    
                else:
                    oddsA = float(Fraction(final_df['Away_fractional'].iloc[ind]))
                    bet2 = bet1*((oddsA+1)/(oddsB+1))
                    EV_high = ((((bet1*oddsA)-bet2)*.5)+(((bet2*oddsB)-bet1)*.5))*hvl_prob_win-(bet1*hvl_prob_lose)
                    try:    
                        hvl_kelly = (0.02/(((1+0.02)/hvl_prob_win)-1))*2000
                    except:
                        hvl_kelly = 0
                        
                if EV_high < 0:
                    hvl_kelly = 0
            
                ev_data = [{'index': ind, 'EV_low_tier': EV_low, 'EV_higher_tier': EV_high,
                            'future_time_block': future_time,'lvh_prob': lvh_prob_win,
                            'hvl_prob':hvl_prob_win, 'lvh_kelly':lvh_kelly, 'hvl_kelly':hvl_kelly}]
                ev_out_df = ev_out_df.append(ev_data, ignore_index=True, sort=False)
                

     
            EV_final_full = final_df.merge(ev_out_df, left_index=True, right_on='index')
             
            #THIS IS THE FINAL DF
            EV_df_over20 = EV_final_full[(EV_final_full['EV_low_tier'].between(20,100)) | (EV_final_full['EV_higher_tier'].between(20,100))]
            relevant_feats = ['Home_Points', 'Away_Points', 'Home_fractional', 'Away_fractional',
                              'lower tier team', 'higher tier team', 'timeB', 'score',
                              'EV_low_tier', 'EV_higher_tier', 'future_time_block', 'lvh_prob', 'hvl_prob',
                              'lvh_kelly', 'hvl_kelly']
            EV_df_over20 = EV_df_over20[relevant_feats]



        

    
            if len(EV_df_over20.index) > 1:
                continue
            else:
                print('EVs over 20 found')
                try:
                    EV_low_idx = EV_df_over20.loc[EV_df_over20['EV_low_tier'] == np.median(EV_df_over20['EV_low_tier'])].index[0]
                    if EV_df_over20['EV_low_tier'].loc[EV_low_idx] > 0:
                        median_df = median_df.append(EV_df_over20.loc[EV_low_idx],ignore_index=True, sort=False)
                except:
                    EV_low_sort = EV_df_over20.iloc[(EV_df_over20['EV_low_tier']-np.median(EV_df_over20['EV_low_tier'])).abs().argsort()[:2]]
                    EV_low_median = EV_low_sort.iloc[0]
                    if EV_low_median['EV_low_tier'] > 0:
                        median_df = median_df.append(EV_low_median,ignore_index=True, sort=False)
                
                try:
                    EV_high_idx = EV_df_over20.loc[EV_df_over20['EV_higher_tier'] == np.median(EV_df_over20['EV_higher_tier'])].index[0]
                    if EV_df_over20['EV_higher_tier'].loc[EV_low_idx] > 0:
                        median_df = median_df.append(EV_df_over20.loc[EV_high_idx],ignore_index=True, sort=False)
                except:
                    EV_high_sort = EV_df_over20.iloc[(EV_df_over20['EV_higher_tier']-np.median(EV_df_over20['EV_higher_tier'])).abs().argsort()[:2]]
                    EV_high_median = EV_high_sort.iloc[0]
                    if EV_df_over20['EV_higher_tier'].loc[EV_low_idx] > 0:
                        median_df = median_df.append(EV_high_median,ignore_index=True, sort=False)
            
    
        if len(median_df.index) > 1:
            #Save EV df to html and then have it open in browser
            print("saving final dataframe to html and opening in browser")
            median_df.to_html('C:/Users/joshu/Documents/py_projects/joe_model/CDF_API/EV_over20.html')
            webbrowser.open('C:/Users/joshu/Documents/py_projects/joe_model/CDF_API/EV_over20.html')
            



                
            
        time.sleep(65)







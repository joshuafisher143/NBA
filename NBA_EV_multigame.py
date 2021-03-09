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

    
lvh_count_pkl = lvh_count_path
with open(lvh_count_pkl, 'rb') as file:
    lvh_count_dict = pickle.load(file)

hvl_count_pkl = hvl_count_path
with open(hvl_count_pkl, 'rb') as file:
    hvl_count_dict = pickle.load(file)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def get_EV(bet1,bank_roll):

    while True:
        print(datetime.datetime.now())
        #pull game info
        print("pulling game stats")
####YOU HAVE TO CHANGE MONTH IN LINK AT THE END OF EACH MONTH####
        game_info = requests.get(api-key)
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
                # print('{}:{} and {}:{}'.format(Home_team, Home_points, Away_team, Away_points))
                try:    
                    current_quarter = game_info_dict['games'][key]['currentPeriod']
                except:
                    print('{} vs {} in intermission or timeout'.format(Home_team, Away_team))
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
        game_odds = requests.get(api-key)
        go_dict = game_odds.json()
        
        odds_df = pd.DataFrame(columns = ['GameID', 'Home_fractional', 'Away_fractional'])
        
        for key_2 in go_dict['games'].keys():
            try:
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
                        Home_fractional = 0
                        Away_fractional = 0
                        
                GameID = go_dict['games'][key_2]['gameUID']
                odds_df = odds_df[(odds_df['Home_fractional'] > 0) & (odds_df['Away_fractional'] > 0)]
                odds_df = odds_df.append({'GameID':GameID, 'Home_fractional':Home_fractional,
                                          'Away_fractional':Away_fractional}, ignore_index=True)
            except:
                continue
                
        live_df = game_df.merge(odds_df, on=['GameID'])
        live_df = live_df.set_index('GameID')

        #filter out rows in which time_sec > real time elapsed
        print("reading in daily file")

        daily_file = pd.read_csv(daily_file_path)
        
        median_df = pd.DataFrame(columns=['lower tier team', 'higher tier team','lower tier points', 'higher tier points',
                                          'lower tier fractional', 'higher tier fractional','timeB', 'score',
                              'EV_low_tier', 'EV_higher_tier', 'oddsB lower tier ML', 'oddsB higher tier ML', 'lvh_prob', 'hvl_prob',
                              'lvh_kelly', 'hvl_kelly'])
        
        for game in live_df.index:
        
            daily_file_filtered = daily_file[daily_file['time_sec'] > live_df['Time_elapsed'].loc[game]]
            #filter out teams that don't relate to current looped index
            df_filt_oneT = daily_file_filtered.loc[(daily_file_filtered['lower tier team'] == live_df['Home_Team'].loc[game]) | (daily_file_filtered['higher tier team'] == live_df['Home_Team'].loc[game]),:]
            if len(df_filt_oneT) < 1:
                continue
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
            ev_out_df = pd.DataFrame(columns=['index', 'EV_low_tier', 'EV_higher_tier', 'future_time_block', 'oddsB lower tier ML', 'oddsB higher tier ML', 'lvh_prob', 'hvl_prob', 'lvh_kelly', 'hvl_kelly'])
    
    
            
            
            for ind in final_df.index: 
                time_block = int(abs(final_df['Time_elapsed'].iloc[ind]-1)/180) + 1
                future_time = int(abs(final_df['time_sec'].iloc[ind]-1)/180) + 1

                
                
                # for ind in final_df.index:
                time_score = str(time_block) + ',' + str(score_diff)
                future_score = final_df['score'].iloc[ind]
                if lvh_count_dict[tier_matchup][time_score][str(future_time)][str(future_score)][0] > 49:
                    lvh_prob_win_dist = lvh_count_dict[tier_matchup][time_score][str(future_time)].copy()
                    lvh_prob_win_dist.loc[:,'-60':'59'] = lvh_prob_win_dist.div(lvh_prob_win_dist.sum(axis=1)[0], axis=0)
                    if score_diff < future_score:
                        lvh_prob_win = lvh_prob_win_dist.loc[:,str(future_score):].sum(axis=1)[0]
                    else:
                        lvh_prob_win = lvh_prob_win_dist.loc[:,:str(future_score)].sum(axis=1)[0]
                else:
                    lvh_prob_win = 0
    
                lvh_prob_lose = 1-lvh_prob_win
        
                # #EV for lower tier team
                oddsB_low = final_df['oddsB lower tier'].iloc[ind]
                if final_df['Home_Team'].iloc[ind] == final_df['lower tier team'].iloc[ind]:
                    oddsA_low = float(Fraction(final_df['Home_fractional'].iloc[ind]))
                    bet2 = bet1*((oddsA_low+1)/(oddsB_low+1))
                    EV_low = ((((bet1*oddsA_low)-bet2)*.5)+(((bet2*oddsB_low)-bet1)*.5))*lvh_prob_win-(bet1*lvh_prob_lose)
                    try:
                        lvh_kelly = (0.02/(((1+0.02)/lvh_prob_win)-1))*bank_roll
                    except:
                        lvh_kelly = 0
    
                else:
                    oddsA_low = float(Fraction(final_df['Away_fractional'].iloc[ind]))
                    bet2 = bet1*((oddsA_low+1)/(oddsB_low+1))
                    EV_low = ((((bet1*oddsA_low)-bet2)*.5)+(((bet2*oddsB_low)-bet1)*.5))*lvh_prob_win-(bet1*lvh_prob_lose)
                    try:
                        lvh_kelly = (0.02/(((1+0.02)/lvh_prob_win)-1))*bank_roll
                    except:
                        lvh_kelly = 0
                        
                if EV_low < 0:
                    lvh_kelly = 0
    
            
            
                    
                    
    
                # EV higher tier team    
                time_score = str(time_block) + ',' + str(high_score_diff)
                high_future_score = final_df['score'].iloc[ind]
                if hvl_count_dict[tier_matchup][time_score][str(future_time)][str(high_future_score)][0] > 49:
                    hvl_prob_win_dist = hvl_count_dict[tier_matchup][time_score][str(future_time)].copy()
                    hvl_prob_win_dist.loc[:,'-60':'59'] = hvl_prob_win_dist.div(hvl_prob_win_dist.sum(axis=1)[0], axis=0)
                    if high_score_diff < high_future_score:
                        hvl_prob_win = hvl_prob_win_dist.loc[:,str(high_future_score):].sum(axis=1)[0]
                    else:
                        hvl_prob_win = hvl_prob_win_dist.loc[:,:str(high_future_score)].sum(axis=1)[0]
                else:
                    hvl_prob_win = 0
    
                hvl_prob_lose = 1-hvl_prob_win
        
                # EV_high_list = []
                oddsB_high = final_df['oddsB higher tier'].iloc[ind]
                if final_df['Home_Team'].iloc[ind] == final_df['higher tier team'].iloc[ind]:
                    oddsA_high = float(Fraction(final_df['Home_fractional'].iloc[ind]))
                    bet2 = bet1*((oddsA_high+1)/(oddsB_high+1))
                    EV_high = ((((bet1*oddsA_high)-bet2)*.5)+(((bet2*oddsB_high)-bet1)*.5))*hvl_prob_win-(bet1*hvl_prob_lose)
                    try:    
                        hvl_kelly = (0.02/(((1+0.02)/hvl_prob_win)-1))*bank_roll
                    except:
                        hvl_kelly = 0
    
                else:
                    oddsA_high = float(Fraction(final_df['Away_fractional'].iloc[ind]))
                    bet2 = bet1*((oddsA_high+1)/(oddsB_high+1))
                    EV_high = ((((bet1*oddsA_high)-bet2)*.5)+(((bet2*oddsB_high)-bet1)*.5))*hvl_prob_win-(bet1*hvl_prob_lose)
                    try:    
                        hvl_kelly = (0.02/(((1+0.02)/hvl_prob_win)-1))*bank_roll
                    except:
                        hvl_kelly = 0
                        
                if EV_high < 0:
                    hvl_kelly = 0
                    
                if oddsB_low > 1:
                    oddsB_low_ML = oddsB_low*100
                else:
                    oddsB_low_ML = (-100)/oddsB_low
                    
                if oddsB_high > 1:
                    oddsB_high_ML = oddsB_high*100
                else:
                    oddsB_high_ML = (-100)/oddsB_high
            
                ev_data = [{'index': ind, 'EV_low_tier': EV_low, 'EV_higher_tier': EV_high,
                            'future_time_block': future_time,'lvh_prob': lvh_prob_win, 'oddsB lower tier ML':oddsB_low_ML, 'oddsB higher tier ML':oddsB_high_ML,
                            'hvl_prob':hvl_prob_win, 'lvh_kelly':lvh_kelly, 'hvl_kelly':hvl_kelly}]
                ev_out_df = ev_out_df.append(ev_data, ignore_index=True, sort=False)


     
            EV_final_full = final_df.merge(ev_out_df, left_index=True, right_on='index')
            
            
            if EV_final_full['Home_Team'].iloc[0] == EV_final_full['lower tier team'].iloc[0]:
                EV_final_full = EV_final_full.rename(columns={'Home_Points':'lower tier points', 'Away_Points': 'higher tier points',
                                              'Home_fractional':'lower tier fractional', 'Away_fractional':'higher tier fractional'})
            else:
                EV_final_full = EV_final_full.rename(columns={'Home_Points':'higher tier points', 'Away_Points': 'lower tier points',
                                              'Home_fractional':'higher tier fractional', 'Away_fractional':'lower tier fractional'})
            #THIS IS THE FINAL DF
            EV_df_over20 = EV_final_full[(EV_final_full['EV_low_tier'].between(20,100)) | (EV_final_full['EV_higher_tier'].between(20,100))]
            relevant_feats = ['lower tier points', 'higher tier points', 'lower tier fractional', 'higher tier fractional',
                              'lower tier team', 'higher tier team', 'timeB', 'score',
                              'EV_low_tier', 'EV_higher_tier', 'oddsB lower tier ML', 'oddsB higher tier ML', 'lvh_prob', 'hvl_prob',
                              'lvh_kelly', 'hvl_kelly']
            EV_df_over20 = EV_df_over20[relevant_feats]



        

    
            if len(EV_df_over20.index) < 1:
                print('no EVs over 20 found in {} vs {}'.format(EV_final_full['lower tier team'].iloc[0], EV_final_full['higher tier team'].iloc[0]))
                continue
            else:
                print('EVs over 20 found in {} vs {}'.format(EV_final_full['lower tier team'].iloc[0], EV_final_full['higher tier team'].iloc[0]))
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
                    if EV_df_over20['EV_higher_tier'].loc[EV_high_idx] > 0:
                        median_df = median_df.append(EV_df_over20.loc[EV_high_idx],ignore_index=True, sort=False)
                except:
                    EV_high_sort = EV_df_over20.iloc[(EV_df_over20['EV_higher_tier']-np.median(EV_df_over20['EV_higher_tier'])).abs().argsort()[:2]]
                    EV_high_median = EV_high_sort.iloc[0]
                    if EV_high_median['EV_higher_tier'] > 0:
                        median_df = median_df.append(EV_high_median,ignore_index=True, sort=False)
            
    
        if len(median_df.index) > 0:
            #Save EV df to html and then have it open in browser
            print("saving final dataframe to html and opening in browser")
            median_df.to_html(output_html_path)
            webbrowser.open(output_html_path)
            



                
        print('iteration has ended')    
        time.sleep(65)







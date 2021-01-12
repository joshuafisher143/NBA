# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 18:10:59 2020

@author: joshu
"""
import pandas as pd
import numpy as np
import itertools
import pickle


tier_arr = dict.fromkeys(['1,6','2,4','2,5','2,6','3,4','3,5','4,4'])

tiers = list(np.arange(1,17,1))
scores = list(np.arange(-60,60,1))

tiers_score = list(itertools.product(tiers,scores))

string_list = [','.join(map(str,item)) for item in tiers_score]


tiers_score_dict = dict.fromkeys(string_list)

for key in tier_arr.keys():
    tier_arr[key] = tiers_score_dict.copy()
    
time2_dict = dict.fromkeys(list(map(str,np.arange(1,17,1))))

for key in tier_arr.keys():
    for key2 in tiers_score_dict.keys():
        tier_arr[key][key2] = time2_dict.copy()

scorediff2 = pd.DataFrame(np.zeros([1,120]), columns=list(map(str,np.arange(-60,60,1))))

for key in tier_arr.keys():
    for key2 in tiers_score_dict.keys():
        for key3 in time2_dict.keys(): 
            tier_arr[key][key2][key3] = scorediff2.copy()


df2 = pd.read_csv('C:/Users/joshu/Documents/py_projects/joe_model/CDF_API/data/18-19.csv', index_col='game_id')

df2['scorediff'] = df2['scorediff'] * -1


#remove missing values
df2 = df2.replace('Error', np.nan)
df2 = df2.dropna()

#convert columns from object to int
df2['Time block'] = df2['Time block'].astype(int)
df2['hometier'] = df2['hometier'].astype(int)
df2['awaytier'] = df2['awaytier'].astype(int)

# #take away apostrophe from beginning of game id
# df2.index = df2.index.map(lambda x: x.lstrip("'"))


#make dict using game id as keys
games = df2.index.unique()
game_dict = dict.fromkeys(games)

#fill dict values with other columns
for key in game_dict.keys():
    for ind in df2.index:
        if ind == key:
            game_dict[key] = df2.loc[ind,df2.columns !='game_id']



game_count = 0
#fill matchup scenarios
for game_key in game_dict.keys():
    #find low tier and high tier nums
    home_tier = int(np.amin(game_dict[game_key]['hometier']))
    away_tier = int(np.amax(game_dict[game_key]['awaytier']))
    if home_tier < away_tier:
        low_tier = home_tier
        high_tier = away_tier
    else:
        low_tier = away_tier
        high_tier = home_tier
    matchup = str(low_tier) + ',' + str(high_tier)
    
    for block in list(np.arange(1,17,1)):
        block_rows = game_dict[game_key].loc[game_dict[game_key]['Time block'] == block]
    
        unique_vals = block_rows['scorediff'].unique()
        
        for block_future in list(np.arange(2,17,1)):
            fblock_rows = game_dict[game_key].loc[game_dict[game_key]['Time block'] == block_future]
            funique_vals = fblock_rows['scorediff'].unique()
        
            for val in unique_vals:
                for fval in funique_vals:            
                    tier_arr[matchup][str(block) + ',' + str(val)][str(block_future)][str(fval)] +=1
    game_count += 1
    print(str(game_count)+'/'+str(len(game_dict)))
            

pkl_fname = 'C:/Users/joshu/Documents/py_projects/joe_model/CDF_API/tier_array_lvh.pkl'
with open(pkl_fname, 'wb') as file:
    pickle.dump(tier_arr,file)    


    
 
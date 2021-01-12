# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 13:31:43 2020

@author: joshu
"""
import pickle
import pandas as pd

pkl_fname = 'C:/Users/joshu/Documents/py_projects/joe_model/CDF_API/hvl_count_final.pkl'
with open(pkl_fname, 'rb') as file:
    tier_arr = pickle.load(file)
    
pkl_fname = 'C:/Users/joshu/Documents/py_projects/joe_model/CDF_API/hvl_count_final.pkl'
with open(pkl_fname, 'rb') as file:
    tier_arr_count = pickle.load(file)
    
    


for key in tier_arr.keys():
    for key2 in tier_arr[key].keys():
        for key3 in tier_arr[key][key2].keys():
            #calculate probabilities by dividing each cells cumulative sum by total sum
            tier_arr[key][key2][key3].loc[:,'-60':'59'] = tier_arr[key][key2][key3].cumsum(axis=1).div(tier_arr_count[key][key2][key3].sum(axis=1)[0], axis=0)


for key in tier_arr.keys():
    for key2 in tier_arr[key].keys():
        for key3 in tier_arr[key][key2].keys():
            for col in tier_arr[key][key2][key3].columns:
                if tier_arr_count[key][key2][key3][col].iloc[0] < 50:
                    tier_arr[key][key2][key3][col] = 0
                



            

pkl_fname = 'C:/Users/joshu/Documents/py_projects/joe_model/CDF_API/hvl_prob_final2.pkl'
with open(pkl_fname, 'wb') as file:
    pickle.dump(tier_arr,file)



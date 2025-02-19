import numpy as np
import pandas as pd
import scipy.stats as ss
import xlrd
import os
import sklearn

#os.chdir("C:\\Users\\student.DESKTOP-UT02KBN\\Desktop\\Stone_presixdio\\Data\\FFIEC CDR Call Bulk All Schedules 03312020")
#%%

names =[]
def find_ffiec(col_name):
    for f_name in os.listdir():
        f = open(f_name, 'r')
        if col_name in f.readline():
            data = pd.read_csv(f_name, 
                               delimiter='\t',
                               skiprows=0,
                               na_values=' '
                               )
            data.fillna(0, inplace=True)
            names.append(data[col_name][0])
            return( data[col_name].drop(labels=0).astype(int))
            
data_series = ("RCON1590",
                "RCON3386",
                "RCON5577",
                "RCON5584",
                "RCON5585",
                "RCON5586",
                "RCON5587",
                "RCON5588",
                "RCON5589",
                )
#data = zip(*[find_ffiec(i) for i in data_series])
data_dict = {i:find_ffiec(i) for i in data_series}
data_names = {i:j for i,j in zip(data_series, names)}
    #%%
#all domestic
#5584 subset of 5578?
tot_num = data_dict['RCON5577'].sum()#Wrong?
num_less100 = data_dict['RCON5584'].sum()
num_less250 = data_dict['RCON5586'].sum()
num_less500 = data_dict['RCON5588'].sum()
num_more500 = tot_num - (num_less100 + num_less250 + num_less500)
#%
tot_ag = data_dict['RCON1590'].sum()

amnt_less100 = data_dict['RCON5585'].sum()
amnt_less250 = data_dict['RCON5587'].sum()
amnt_less500 = data_dict['RCON5589'].sum()
amnt_more500 = tot_ag - amnt_less100 - amnt_less250 - amnt_less500

plt.scatter([amnt_less100,amnt_less250, amnt_less500], list(range(3)) )

[i/tot_ag for i in (amnt_less100 , amnt_less250, amnt_less500)]
#all 6%? did/didn't include residential improvements
#%%

#%%
#Total revenue vs. subcomponents, read in
    

#What predicts each subcomponent: pred both number of requested and margin for each type requested (eg. small vs. Large)? 
#or just sized weighted margin for subcategory?


#%% #Predicting revenue for each of the companies, by reading in revenue from model

program_Cos = ['Express Grain (KCO)']
fatoil_Cos = ['Western Dubuque', 'Hero', 'Kolmar', 'Sinclair', 'Mendota', 'Verbio']
energy_Cos = ['SGR Energy', 'Hiper Gas', 'Petromax']
cocoa_Cos = ['Hershey']
Cos =  [program_Cos, fatoil_Cos, energy_Cos, cocoa_Cos]

sheet_names = ['Rev Build_ Programs', 'Rev Build_ Fats&Oils', 
               'Rev Build_ Energy', 'Rev Build_ Cocoa Trading']
hist_ixs = [slice(12, 21), slice(12, 21), slice(12, 21), slice(12, 21)]

model_file_dir = 'C:\\Users\\student.DESKTOP-UT02KBN\\Desktop\\Stone_Presidio'
os.chdir(model_file_dir)
model_file_name = '20200520 02 FCStone Presidio Model WIP.xlsx'
model_bk = xlrd.open_workbook(model_file + "\\" + model_file_name)
#print(model_bk.sheet_names())    
#model_pybk = pyxlsb.open_workbook(model_file + "\\" + model_file_name)
#print(model_pybk.sheets)
for sheet_name, h_ix, sector_Cos in zip(sheet_names, hist_ixs, Cos):
    b = model_bk.sheet_by_name(sheet_name)
    co = sector_Cos[0]
    co_ix = b.col_values(0).index(co)    
    historical_rev = b.row_values(co_ix)[h_ix]
    
    try:
        gross_ix =  b.col_values(0, 
                                start_rowx = 0, 
                                end_rowx = 200).index('Gross Revenue')
        cos_ix =  b.col_values(0, 
                                start_rowx = 0, 
                                end_rowx = 200).index('Cost of Sales')
        margin = [1-j/i for i,j in zip(b.row_values(gross_ix)[h_ix],
                                     b.row_values(cos_ix)[h_ix])]#COS is line below gross revenue
    except:
        print(b.col_values(0, start_rowx = 0, end_rowx = 200), "\n\n\n\n")
        margin = None
    print(margin)
#for co in fatoil_Cos: 




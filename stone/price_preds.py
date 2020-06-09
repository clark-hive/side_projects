import numpy as np
import pandas as pd
import scipy.stats as ss
import xlrd
import os
import sklearn
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

#%%import Data from Com pricing spreadsheet

#com_dict = {name:pd.read_excel("16.16 Historical Commodity Price Data.xlsx", name )
#            for name in xl_bk.sheet_names()}
os.chdir("C:\\Users\\student.DESKTOP-UT02KBN\\Desktop\\Stone_Presidio\\Data")
prices_file = "16.16 Historical Commodity Price Data.xlsx"
xl_bk = xlrd.open_workbook(prices_file)
commodities = xl_bk.sheet_names()

models = {}
security_d = []
curve_prices_d = []
for ix, name in enumerate(commodities):
    b = xl_bk.sheet_by_index(ix)
    sz = len(b.row_values(6))
    dates = [datetime(*xlrd.xldate_as_tuple(i,0)) if type(i) == float
             else None
                for i in b.col_values(0)[7:]]
    com_maturities = b.row_values(0)[1::4]
    com_ab = commodities[ix]
    curve_prices = pd.DataFrame(np.array([pd.to_numeric(b.col_values(i)[7:],
                                                        errors = 'coerce'
                                                        )
                                            for i in range(2,sz,4)
                                            ]).T,
                                 columns = com_maturities,
                                 index = dates,
                                 )
    curve_prices_d += [curve_prices.dropna()]
    if False:#slow and aren't using yet
        sec_df = pd.DataFrame(list(zip(*[b.col_values(i)[7:]
                                                for i in range(1,sz,4)]
                                                )) )
        securities = np.unique(sec_df.values)
        securities = securities[~np.isin(securities, ('', '#N/A N/A'))]
                                                      
        def get_security(s):
            "returns prices for 1 single future"
            rows, _ = np.where(sec_df == s)
            #get all of row, column not just those indexes.
            return pd.Series(data = curve_prices.values[sec_df == s], 
                      index = curve_prices.index[rows],
                      name = s
                      )
    
        sec_list = [get_security(s) for s in securities]
        security_d += sec_list

def longest_index(df_list):
    "returns the index of the longest dataframe from a list of df's"
    return max([(i, df.shape[0]) 
                for i, df in enumerate(df_list)], 
                   key = lambda i: i[1]
                   )[0]
    
long_ix = longest_index(curve_prices_d)
df_idx = curve_prices_d.pop(long_ix)
curve_prices_df = df_idx.join(curve_prices_d)
#curve_prices_df.dropna(inplace = True)
curve_prices_d += [df_idx]

futures = [i.replace("COMB", "").replace("Comdty", "").replace(" ", "") 
            for i in curve_prices_df]#eg CL 1
futures_ab = set([re.sub("\d+", "",i) 
                    for i in futures])#eg CL
curve_prices_df.columns = futures

#long_ix = longest_index(curve_prices_d)
#df_idx = curve_prices_d.pop(long_ix)
#securities_df = df_idx.join(curve_prices_d)
#security_d+= [df_idx]

#%% Make Price Graphs from future's

#%%
from scipy import integrate
import defs

hist_val = curve_prices_df.reindex(curve_prices_df.index[::-1])
hist_pct = hist_val.pct_change(periods = 252)#6mo out
hist_vol = hist_pct.std(axis=0)

for ab in defs.abv_cme_url:
    if ab:
        tick = ab + "1"
        ix = futures.index(tick)
        base_ix = hist_val.iloc[:,ix].first_valid_index()
        base_prx = hist_val.loc[base_ix, tick]
        dist = ss.lognorm(loc = 0, scale = 1, s = hist_vol.values[ix])
        
        x = np.linspace(hist_pct.iloc[:,ix].min(),
                        hist_pct.iloc[:,ix].max(),
                        100)*2
        
        fig, ax =plt.subplots()
        x_axis = [i for i in  base_prx * (1 + x) if i > 0]
        
        probs = [integrate.quad(lambda x: dist.pdf(x/base_prx)/base_prx, i,j)[0]
                         for i,j in zip(x_axis[:-1], x_axis[1:])]
        probs = [100*i/sum(probs) for i in probs]
        
        plt.bar(x_axis[:-1], probs, label="Probabilities")
        plt.legend()
        plt.title(f"Probability of ending prices of {hist_vol.index[ix]} in 12mo")
        xformatter = mticker.FormatStrFormatter('$%.0f')
        ax.xaxis.set_major_formatter(xformatter)
        yformatter = mticker.FormatStrFormatter('%.1f%%')
        ax.yaxis.set_major_formatter(yformatter)
        plt.show()


#plt.plot(x_axis, dist.pdf(x), label='dist')
#plt.yscale('log')
#%%






#%% Predicting comodity pries
#impute missing
curve_prices_df = curve_prices_df.dropna(axis=0)
a=(curve_prices_df =='#N/A N/A')
curve_prices_df = curve_prices_df[~a.any(axis=1)]

#%%
front_cols = [i for i in curve_prices_df.columns 
             if '1 ' in i and '11' not in i and '21' not in i]
rest_cols = [i for i in curve_prices_df.columns if i not in front_cols]

X = curve_prices_df.loc[:,rest_cols]
Y = curve_prices_df.loc[:,front_cols[0]]
#%%
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

X_train, X_test, y_train, y_test = train_test_split(X, Y, random_state=0)
pipe = Pipeline([('impute', SimpleImputer()),
                     ('scaler', StandardScaler()),
                     ('linear', LinearRegression())])

pipe.fit(X_train, y_train)

#%%
#curve_prices_df = pd.concat(curve_prices_d, axis=1)

#%%
#Predicting revenue for each of the companies, by reading in revenue from model

#import pyxlsb
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
#%%
    
    
    
    
    
    
    
    
    
    
    
#a = pd.read_excel("16.16 Historical Commodity Price Data.xlsx", 'Corn')
#get size before read in?
with open(prices_file) as f:
    print(f.readline())
#%%
a = pd.read_excel(prices_file, 'Corn', 
                  skiprows = 6, 
                  index_col = 0,
                  use_cols = list(range(2,sz,3)))
#indx = pd.to_datetime(a.iloc[6:,0])
#%%
curve_prices = a.iloc[6:,2::4].astype(float)
curve_prices.columns = a.columns[1::4]
curve_prices.index = indx
#%%
sec_names = a.columns[1::4].unqiue()
#a.drop(labels = [1:5], axis=1)

a.drop(columns=[2::3])
#space cols
#unified index
#%%
a.iloc[:,1]



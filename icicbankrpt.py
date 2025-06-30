# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 18:13:14 2024

@author: ACER
"""

import pandas as pd
import streamlit as st 
import xlrd
st.set_page_config(page_title="Bank Statement Search", page_icon="bank", layout="wide")
st.title("  :bank: :blue[ICICI Bank Statement Search App]")
fl = st.file_uploader(" Upload a file using 'Browse files' ", type=(["xls"]))
st.button("Rerun") 

 
if fl is not None:
    @st.cache_data
    def load_data(fl):
        Bankdata = pd.read_excel(fl, header=12)
        print('columns ==', Bankdata.columns)
        return Bankdata
    Bankdata = load_data(fl)
    Bankdata.rename(columns={'Withdrawal Amount (INR )':'Withdrawals', 'Deposit Amount (INR )':'Deposits'}, inplace=True)
    print('columns 3', Bankdata.columns)
    #print('head', Bankdata.head(7))
    Bankdata['Withdrawals']= pd.to_numeric(Bankdata['Withdrawals'], errors='coerce') 
    #Bankdata['Balance']= pd.to_numeric(Bankdata['Balance'], errors='coerce')
    Bankdata['Deposits']= pd.to_numeric(Bankdata['Deposits'],  errors='coerce')
    Bankdata = Bankdata.drop(['Unnamed: 0','Cheque Number'], axis=1)
    Bankdata['Transaction Remarks'].fillna('', inplace=True)
    with st.expander("View All Data"):
       st.dataframe(Bankdata[['Value Date','Withdrawals', 'Deposits','Transaction Remarks']])   
    top_5_withdrawals = Bankdata.sort_values(by='Withdrawals', ascending=False).head(6)  
    #top_5_withdrawals = top_5_withdrawals.reset_index(drop=True)
    #top_5_wthdropt  = top_5_withdrawals.drop(index=0, axis=0, inplace=False) #drop Totals row
    top_5_deposits = Bankdata.sort_values(by='Deposits', ascending=False).head(6)
    #top_5_deposits = top_5_deposits.reset_index(drop=True)
    #top_5_depdropt  = top_5_deposits.drop(index=0, axis=0, inplace=False)
    with st.expander("Top 5 Withdrawls"):
       st.dataframe(top_5_withdrawals)   
    with st.expander("Top 5 Deposits"):  
       st.dataframe(top_5_deposits)
    stinput = st.text_input("Enter keyword to search -")
    #
    if len(stinput) > 0:
       print('stinput-1', stinput)
       #print(np.isnan(stinput))
       dfs1 = Bankdata.loc[Bankdata['Transaction Remarks'].str.contains(stinput, case=False)]
       def functrunc(description):
           templst = list(description.split('/'))
           return templst[3:5]
       dfs1['Transaction'] = dfs1['Transaction Remarks'].apply(functrunc) #adding a column for description
       dfs1w = dfs1['Withdrawals'].sum()
       dfs1d = dfs1['Deposits'].sum()
       sumdif = dfs1w - dfs1d
       st.write(f':money_with_wings: :red[WITHDRAWALS  -:  {dfs1w}]   :moneybag: :green[DEPOSITS   -:  {dfs1d}  ]')
       st.write(f':abacus: With - Dep = {sumdif}                 ')
       with st.expander("View Transactions"):
          st.dataframe(dfs1[['Value Date','Transaction', 'Withdrawals', 'Deposits','Transaction Remarks']])    
    else:
        print('stinput-2 ', stinput)
        dfs1d = 0
        dfs1w = 0
         
   
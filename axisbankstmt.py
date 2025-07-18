# -*- coding: utf-8 -*-
"""
Created on Mon Jun  2 16:04:19 2025

@author: PARI KANNAPPAN
"""

import pandas as pd
import streamlit as st
import numpy as np
st.set_page_config(page_title="Axis Bank Statement Search", page_icon="bank", layout="wide")
#st.markdown(MobileMonneyTransfer.png, unsafe_allow_html=True)
st.title("  :bank: :red[Bank Statement Search App]")
infile = st.file_uploader(" Upload a file using 'Browse files' ", type=(["xlsx"]))
#st.button("Rerun")  
if infile is not None:
    @st.cache_data
    def load_data(infile):
        Bankdata = pd.read_excel(
              infile,
               skiprows=lambda x: x in [0],  # skip these row indices
               header=2)
        return Bankdata
    Bankdata = load_data(infile)
    #print(Bankdata.head())
    Bankdata1 = Bankdata.drop(columns=['Chq No','Balance','Init. Br'])
    print(Bankdata1.head())
    def viewalldata(): 
        with st.expander("View All Data"):
           st.dataframe(Bankdata[['Date','Withdrawals', 'Deposits','Description']])
          #st.text(Bankdata1)
    if st.button("Click to viewalldata"):
       viewalldata()      
    stinput = st.text_input("Enter keyword to search -")
    #
    if len(stinput) > 0:
       print('stinput-1', stinput)
       #print(np.isnan(stinput))
       #Bankdata1 = Bankdata1.replace(["NaN", "nan", "null", "NA"], np.nan)  
       Bankdata2 = Bankdata1.dropna(subset=['Particulars'])
       Bankdata2['Tran Date'] = pd.to_datetime(Bankdata2['Tran Date'], errors='coerce')
       #print(Bankdata2.head(10))
       dfs1 = Bankdata2.loc[Bankdata2['Particulars'].str.contains(stinput, case=False)]
       def functrunc(description):
        
           templst = list(description.split(' '))
           return templst[9:12]
       dfs1['Desc'] = dfs1['Particulars'].apply(functrunc) #adding a column for description
       dfs1w = dfs1['Debit'].sum()
       dfs1d = dfs1['Credit'].sum()
       sumdif = dfs1w - dfs1d

       st.write(f':money_with_wings: :red[Debit  -:  {dfs1w}]   :moneybag: :green[Credit   -:  {dfs1d}  ]')
       st.write(f':abacus: With - Dep = {sumdif}')
       dfs2 = dfs1[['Tran Date', 'Desc', 'Debit', 'Credit','Particulars']]
       nooftrans = len(dfs1)
       #pt_list = dfs2['Particulars'].tolist()
       word_list = dfs2['Particulars'].str.split().explode().tolist() 
       word_list = [word for word in word_list if not word.endswith(',')]
       words_set = set(word_list)
       few_trans_all = list(words_set)
       mischr_list = ['IN','OF','of','FROM', '+', 'ORG','from', 'To','R','N',
                      '-','Ref:','NO', 'in','F','B']
       few_trans = [item for item in few_trans_all if item not in mischr_list ]
       #combined_set = set().union(*pt_set_list)
       col1, col2 = st.columns(2)
       with col1:
        selected_key =   st.multiselect(f' "you can choose keywords for {stinput} " ', few_trans) 
       st.table(selected_key)
       choices = '|'.join(selected_key)  # Regex OR pattern
       dfs3 = dfs2[dfs2['Particulars'].str.contains(choices, case=False, regex=True)]
       if len(selected_key) > 0:
        st.dataframe(dfs3)
       with st.expander(f' "View All {nooftrans} Transactions of keyword" {stinput}'):
          st.dataframe(dfs2)
    else:
     print('stinput-2 ', stinput)
     dfs1d = 0
     dfs1w = 0
       #-------
    #get data using date
    #
    #if st.button("Click to view with date input"):
    Bankdata1['Tran Date'] = pd.to_datetime(Bankdata1['Tran Date'], errors='coerce')
    startdate = pd.to_datetime(Bankdata1['Tran Date']).min()
    enddate   = pd.to_datetime(Bankdata1['Tran Date']).max()
    startfrt  = startdate.strftime('%d-%m-%Y')
    endfrt    = enddate.strftime('%d-%m-%Y')
    dfs4      = Bankdata1
    dfs4['month'] = dfs4['Tran Date'].dt.to_period('M').astype(str) 
    print('printing dfs4')
    print(dfs4.head(20))
    month_list = sorted(dfs4['month'].unique(), reverse=True)   # newest first
    month_list.remove('NaT')
    
    st.write(f'View data choosing dates.   Available date range {startfrt} -- {endfrt}')
       #st.write(f' View data choosing dates -- available data range {} -- {}')
    col3, col4 = st.columns(2)
    with col3:
     date1 = pd.to_datetime(st.date_input('Start date', startdate))
    with col4:
           date2 = pd.to_datetime(st.date_input('End date', enddate))
    df_datr = Bankdata1[(Bankdata1['Tran Date'] >= date1) & (Bankdata1['Tran Date'] <= date2)] 
    noofrows = len(df_datr)
    with st.container():     
        with st.expander(f' :green["View Data with Above date range" which has {noofrows} Transactions]'):
          st.text(df_datr)

    selected_month = st.selectbox('Select month', month_list)
    filtered_month_data = dfs4[dfs4['month'] == selected_month]
    st.dataframe(filtered_month_data)       
 

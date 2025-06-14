# -*- coding: utf-8 -*-
"""
Created on Mon Jun  2 16:04:19 2025

@author: ACER
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
    print(Bankdata.head())
    Bankdata1 = Bankdata.drop(columns=['Chq No','Balance','Init. Br'])
    print(Bankdata1.head())
    def viewalldata(): 
        with st.expander("View All Data"):
           #st.dataframe(Bankdata[['Date','Withdrawals', 'Deposits','Description']])
          st.text(Bankdata1)
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
       print(Bankdata2.head(10))
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
       few_trans = list(words_set)
       #combined_set = set().union(*pt_set_list)
       selected_key =   st.multiselect(f' "you can choose keywords for {stinput} " ', few_trans)
       st.text(selected_key)
       choices = '|'.join(selected_key)  # Regex OR pattern
       dfs3 = dfs2[dfs2['Particulars'].str.contains(choices, case=False, regex=True)]
       st.text(dfs3)
       with st.expander(f' "View {nooftrans} Transactions of keyword" {stinput}'):
          st.text(dfs2)
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
       
             
    
         
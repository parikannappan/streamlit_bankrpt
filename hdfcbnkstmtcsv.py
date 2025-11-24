# -*- coding: utf-8 -*-
"""
Created on Mom Nov 24 08:03:15 2025

@author: ACER
"""

import pandas as pd
import streamlit as st 
st.set_page_config(page_title="Bank Statement Search", page_icon="bank", layout="wide")
#st.markdown(MobileMonneyTransfer.png, unsafe_allow_html=True)
st.title("  :bank: :blue[HDFC Bank Statement Search App]")
fl = st.file_uploader(" Upload a file using 'Browse files' ", type=(["csv"]))
st.button("Rerun")  
if fl is not None:
    @st.cache_data
    def load_data(fl):
        Bankdata = pd.read_csv(fl, header=20)
        return Bankdata
    Bankdata = load_data(fl)
    Bankdata.columns = [col.strip() for col in Bankdata.columns]
    Bankdata.rename(columns={'Withdrawal Amt.':'Withdrawals', 'Deposit Amt.':'Deposits'}, inplace=True)
    print(f'Bankdata.columns', Bankdata.columns) 
    Bankdata['Withdrawals']= pd.to_numeric(Bankdata['Withdrawals'], errors='coerce') 
    #Bankdata['Balance']= pd.to_numeric(Bankdata['Balance'], errors='coerce')
    Bankdata['Deposits']= pd.to_numeric(Bankdata['Deposits'],  errors='coerce')
    Bankdata = Bankdata.drop(columns=['Chq./Ref.No.','Value Dt','Closing Balance'], axis=1)
    #print(Bankdata)
    with st.expander("View All Data"):
       #st.dataframe(Bankdata[['Date','Withdrawals', 'Deposits','Description']])
       st.dataframe(Bankdata)
    top_5_withdrawals = Bankdata.sort_values(by='Withdrawals', ascending=False).head(6)  
    top_5_withdrawals = top_5_withdrawals.reset_index(drop=True)
    top_5_wthdropt  = top_5_withdrawals.drop(index=0, axis=0, inplace=False) #drop Totals row
    top_5_deposits = Bankdata.sort_values(by='Deposits', ascending=False).head(6)
    top_5_deposits = top_5_deposits.reset_index(drop=True)
    top_5_depdropt  = top_5_deposits.drop(index=0, axis=0, inplace=False)
    with st.expander("Top 5 Withdrawls"):
       st.dataframe(top_5_wthdropt) 
    with st.expander("Top 5 Deposits"):
       st.dataframe(top_5_depdropt) 
    
    stinput = st.text_input("Enter keyword to search -")
    #
    if len(stinput) > 0:
       print('stinput-1', stinput)
       #print(np.isnan(stinput))
       Bankdata['Narration'] = Bankdata['Narration'].fillna('')
       dfs1 = Bankdata.loc[Bankdata['Narration'].str.contains(stinput, case=False)]
       def functrunc(description):
           templst = list(description.split(' '))
           return templst[7:10]
       dfs1['Desc'] = dfs1['Narration'].apply(functrunc) #adding a column for description
       dfs1w = dfs1['Withdrawals'].sum()
       dfs1d = dfs1['Deposits'].sum()
       sumdif = dfs1w - dfs1d
       st.write(f':money_with_wings: :red[WITHDRAWALS  -:  {dfs1w}]   :moneybag: :green[DEPOSITS   -:  {dfs1d}  ]')
       st.write(f':abacus: With - Dep = {sumdif}')
       dfs2 = dfs1[['Date','Desc', 'Withdrawals', 'Deposits','Narration']]
       #-------
       def style_dataframe(dfs2):
          return dfs2.style.set_table_styles(
          [{
            'selector': 'th',
            'props': [
                ('background-color', '#4CAF50'),
                ('color', 'white'),
                ('font-family', 'Arial, sans-serif'),
                ('font-size', '16px')
            ]
          }, 
         {
            'selector': 'td, th',
            'props': [
                ('border', '2px solid #4CAF50')
            ]
         }]
         )

       styled_df = style_dataframe(dfs2)

        
       with st.expander("View Transactions"):
          st.dataframe(styled_df)   
         
    else:
        print('stinput-2 ', stinput)
        dfs1d = 0
        dfs1w = 0
         
   
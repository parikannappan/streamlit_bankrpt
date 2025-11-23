# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 18:13:14 2025

@author: ACER
"""

import pandas as pd
import streamlit as st
import re
import io

# --- Configuration ---
st.set_page_config(page_title="Bank Statement Search", page_icon=":bank:", layout="wide")

# --- Helper Functions ---

def clean_currency(x):
    """Cleans currency strings and converts to float."""
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        # Remove commas and other non-numeric chars except dot and minus
        clean_str = re.sub(r'[^\d.-]', '', x)
        try:
            return float(clean_str)
        except ValueError:
            return 0.0
    return 0.0

@st.cache_data
def load_data(file):
    """
    Loads data from the uploaded Excel file using fixed header row 12 (original behavior).
    """
    try:
        # Use fixed header row as requested
        df = pd.read_excel(file, header=12)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def process_data(df):
    """
    Cleans and processes the dataframe: renames columns, converts types, filters invalid rows.
    """
    # Normalize column names for easier matching
    df.columns = df.columns.str.strip()
    
    # Flexible Column Mapping
    col_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'withdrawal' in col_lower or 'debit' in col_lower:
            col_map[col] = 'Withdrawals'
        elif 'deposit' in col_lower or 'credit' in col_lower:
            col_map[col] = 'Deposits'
        elif 'date' in col_lower and 'value' in col_lower:
            col_map[col] = 'Value Date'
        elif 'date' in col_lower and 'transaction' in col_lower:
            col_map[col] = 'Transaction Date'
        elif 'remark' in col_lower or 'particular' in col_lower or 'description' in col_lower:
            col_map[col] = 'Transaction Remarks'
        elif 'balance' in col_lower:
            col_map[col] = 'Balance'
            
    df.rename(columns=col_map, inplace=True)
    
    # Ensure required columns exist
    required_cols = ['Withdrawals', 'Deposits', 'Transaction Remarks']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        st.warning(f"Could not automatically identify columns: {missing_cols}. Please check your file format.")
        return df # Return as is, might fail later but better than crashing here

    # Data Cleaning
    df['Withdrawals'] = df['Withdrawals'].apply(clean_currency)
    df['Deposits'] = df['Deposits'].apply(clean_currency)
    
    # Fill NaNs
    df['Withdrawals'].fillna(0, inplace=True)
    df['Deposits'].fillna(0, inplace=True)
    df['Transaction Remarks'].fillna('', inplace=True)
    
    # Filter out "Total" rows or empty dates if possible
    if 'Value Date' in df.columns:
        df = df[pd.to_datetime(df['Value Date'], errors='coerce').notna()]
        
    return df

def extract_keywords(df):
    """Extracts keywords from transaction remarks."""
    word_list = df['Transaction Remarks'].str.split().explode().tolist()
    word_list = [str(word) for word in word_list]
    
    new_word_list = []
    for word in word_list:
        if isinstance(word, str) and '/' in word:
            new_word_list.extend(word.split('/'))
        else:
            new_word_list.append(word)
            
    # Filter junk words
    mischr_list = {'IN','OF','of','FROM', '+', 'ORG','from', 'To','R','N',
                   '-','Ref:','NO', 'in','F','B', 'The', 'the', 'A', 'a'}
    
    clean_words = [w for w in new_word_list if w not in mischr_list and not w.endswith(',') and len(w) > 1]
    return sorted(list(set(clean_words)))

# --- Main App ---

def main():
    st.title("  :bank: :blue[ICICI Bank Statement Search App]")
    
    uploaded_file = st.file_uploader(" :red[Upload your monthly/early stmt using 'Browse files' type xls/xlsx] ", type=(["xls", "xlsx"]))

    if uploaded_file is not None:
        raw_df = load_data(uploaded_file)
        
        if raw_df is not None:
            st.write("Debug: Detected Columns:", raw_df.columns.tolist()) # Debug info
            df = process_data(raw_df)
            
            # Check if critical columns exist before proceeding
            if 'Withdrawals' not in df.columns or 'Deposits' not in df.columns:
                st.error("Critical columns (Withdrawals/Deposits) not found. Please check the 'Debug: Detected Columns' above and ensure your file has the correct headers.")
                st.stop()

            # --- Summary Metrics ---
            total_withdrawals = df['Withdrawals'].sum()
            total_deposits = df['Deposits'].sum()
            net_flow = total_deposits - total_withdrawals
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Withdrawals", f"₹{total_withdrawals:,.2f}")
            col2.metric("Total Deposits", f"₹{total_deposits:,.2f}")
            col3.metric("Net Flow", f"₹{net_flow:,.2f}", delta_color="normal")
            
            st.divider()

            # --- Top Transactions ---
            col_top1, col_top2 = st.columns(2)
            
            with col_top1:
                st.subheader("Top 5 Withdrawals")
                top_5_withdrawals = df.sort_values(by='Withdrawals', ascending=False).head(5)
                st.dataframe(top_5_withdrawals[['Value Date', 'Transaction Remarks', 'Withdrawals']], use_container_width=True)
                
            with col_top2:
                st.subheader("Top 5 Deposits")
                top_5_deposits = df.sort_values(by='Deposits', ascending=False).head(5)
                st.dataframe(top_5_deposits[['Value Date', 'Transaction Remarks', 'Deposits']], use_container_width=True)

            st.divider()

            # --- Keyword Search ---
            st.subheader("Keyword Analysis")
            all_keywords = extract_keywords(df)
            
            col_search1, col_search2 = st.columns([1, 2])
            
            with col_search1:
                selected_keys = st.multiselect('Choose keywords to filter:', all_keywords)
            
            if selected_keys:
                # Regex OR pattern
                pattern = '|'.join([re.escape(k) for k in selected_keys])
                
                # Filter data
                choice_data = df[df['Transaction Remarks'].str.contains(pattern, case=False, regex=True, na=False)].copy()
                
                # Extract matched keyword for grouping
                choice_data['Matched_Keyword'] = choice_data['Transaction Remarks'].str.extract(f'({pattern})', flags=re.IGNORECASE, expand=False)
                
                with col_search2:
                    st.info(f"Found {len(choice_data)} transactions matching selected keywords.")
                
                st.dataframe(choice_data)
                
                # Chart
                if not choice_data.empty:
                    chart_data = choice_data.groupby('Matched_Keyword')[['Withdrawals', 'Deposits']].sum().reset_index()
                    st.bar_chart(chart_data, x='Matched_Keyword', y=['Withdrawals', 'Deposits'])

            st.divider()
            
            # --- Free Text Search ---
            st.subheader("Free Text Search")
            search_text = st.text_input("Enter text to search in remarks:")
            
            if search_text:
                search_results = df[df['Transaction Remarks'].str.contains(search_text, case=False, na=False)]
                
                s_withdrawals = search_results['Withdrawals'].sum()
                s_deposits = search_results['Deposits'].sum()
                
                st.write(f"**Results for '{search_text}':**")
                st.write(f":money_with_wings: Withdrawals: **{s_withdrawals:,.2f}** | :moneybag: Deposits: **{s_deposits:,.2f}** | Net: **{s_deposits - s_withdrawals:,.2f}**")
                
                st.dataframe(search_results)
                
            with st.expander("View Full Data"):
                st.dataframe(df)

if __name__ == "__main__":
    main()

         
            
   


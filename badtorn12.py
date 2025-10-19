import pandas as pa 
import streamlit as st 
st.set_page_config(page_title="Sports data", page_icon="badminton_racquet_and_shuttlecock", layout="wide")
st.title("  :badminton_racquet_and_shuttlecock: Badmintol tornament data")


from streamlit_gsheets import GSheetsConnection

url = "https://docs.google.com/spreadsheets/d/1-eEqWBsgVf2O-z2sjsrV5pKeU83z6qdo2szDlkLI3TU/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(spreadsheet=url, usecols=list(range(8)))
st.write(data)
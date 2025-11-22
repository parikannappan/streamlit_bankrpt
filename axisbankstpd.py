# app.py - With Search Summary + Charts
import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from io import BytesIO
#import plotly.express as px
import matplotlib.pyplot as plt

# ------------------- PDF Parsing Function (Same as working version) -------------------
def parse_axis_pdf(file_bytes):
    all_rows = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            in_table = False
            current_row = None

            for line in lines:
                line = line.strip()

                if "Tran Date" in line and "Particulars" in line:
                    in_table = True
                    continue

                if not in_table:
                    continue

                if any(skip in line.upper() for skip in ["OPENING BALANCE", "CLOSING BALANCE", "TRANSACTION TOTAL",
                                                         "END OF STATEMENT", "LEGENDS", "UNLESS THE CONSTITUENT"]):
                    continue

                date_match = re.match(r"^\s*(\d{2}-\d{2}-\d{4})", line)
                if date_match:
                    if current_row is not None and (current_row['debit'] > 0 or current_row['credit'] > 0):
                        all_rows.append([
                            current_row['date'],
                            current_row['desc'].strip(),
                            current_row['debit'],
                            current_row['credit'],
                            current_row['balance']
                        ])

                    date_str = date_match.group(1)
                    remainder = line[date_match.end():].strip()
                    
                    amounts = re.findall(r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b', line)
                    amounts = [float(amt.replace(',', '')) for amt in amounts if amt.replace(',', '').replace('.', '').replace('', '').isdigit() or '.' in amt]

                    debit = credit = balance = 0.0
                    if amounts:
                        balance = amounts[-1]
                        if len(amounts) >= 2:
                            prev_amt = amounts[-2]
                            if prev_amt < balance:
                                debit = prev_amt
                            else:
                                credit = prev_amt
                        if credit == 0 and debit == 0 and len(amounts) >= 2:
                            credit = amounts[0] if amounts[0] > balance else 0

                    desc = re.sub(r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b', '', remainder).strip()
                    desc = re.sub(r'\s+', ' ', desc)

                    current_row = {
                        'date': date_str,
                        'desc': desc if desc else remainder,
                        'debit': debit,
                        'credit': credit,
                        'balance': balance
                    }
                elif current_row is not None:
                    current_row['desc'] += " " + line.strip()

            if current_row is not None and (current_row['debit'] > 0 or current_row['credit'] > 0):
                all_rows.append([
                    current_row['date'],
                    current_row['desc'].strip(),
                    current_row['debit'],
                    current_row['credit'],
                    current_row['balance']
                ])

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows, columns=["Tran Date", "Particulars", "Debit", "Credit", "Balance"])
    df["Tran Date"] = pd.to_datetime(df["Tran Date"], format="%d-%m-%Y", dayfirst=True)
    df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0.0)
    df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0.0)
    df["Balance"] = pd.to_numeric(df["Balance"], errors='coerce').fillna(0.0)
    df = df.sort_values("Tran Date").reset_index(drop=True)
    df["Year-Month"] = df["Tran Date"].dt.strftime("%Y - %B")

    # Extract clean merchant name (optional enhancement)
    def extract_merchant(text):
        if pd.isna(text):
            return "Unknown"
        text = text.upper()
        if "UPI" in text:
            parts = text.split("/")
            for p in parts[2:]:
                if p and not p.startswith("P2") and len(p) > 3:
                    return p.strip()[:25]
        return text.split("/")[0].strip()[:25]

    df["Merchant"] = df["Particulars"].apply(extract_merchant)

    return df

# ------------------- Streamlit App -------------------
st.set_page_config(page_title="Axis Bank Analyzer + Summary", layout="wide")
st.title("Axis Bank Statement Analyzer")
st.markdown("**Upload → Filter → Search → Get Instant Summary!**")

uploaded_file = st.file_uploader("Upload Axis Bank PDF Statement", type="pdf")

if uploaded_file is not None:
    with st.spinner("Extracting transactions..."):
        df = parse_axis_pdf(uploaded_file.read())

    if df.empty:
        st.error("No transactions found!")
    else:
        st.success(f"Extracted {len(df):,} transactions")

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Total Debit", f"₹{df['Debit'].sum():,.2f}")
        with col2: st.metric("Total Credit", f"₹{df['Credit'].sum():,.2f}")
        with col3: st.metric("Net Flow", f"₹{df['Credit'].sum() - df['Debit'].sum():,.2f}")
        with col4: st.metric("Final Balance", f"₹{df['Balance'].iloc[-1]:,.2f}")

        st.markdown("---")
        st.subheader("Filters")

        col1, col2 = st.columns([1, 3])
        with col1:
            months = ["All Months"] + sorted(df["Year-Month"].unique().tolist())
            selected_month = st.selectbox("Select Month", months)

        with col2:
            search_term = st.text_input("Search in Particulars (e.g. 'PLAYO', 'Zomato', 'UPI')", "")

        filtered_df = df.copy()
        if selected_month != "All Months":
            filtered_df = filtered_df[filtered_df["Year-Month"] == selected_month]
        if search_term:
            filtered_df = filtered_df[filtered_df["Particulars"].str.contains(search_term, case=False, na=False)]

        st.write(f"**Showing {len(filtered_df):,} transactions**")

        # SEARCH SUMMARY (Only if search term is entered)
        if search_term:
            st.markdown("---")
            st.subheader(f"Search Summary for: **{search_term.upper()}**")

            total_debit = filtered_df["Debit"].sum()
            total_credit = filtered_df["Credit"].sum()
            net = total_credit - total_debit

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Transactions Found", len(filtered_df))
            with col2:
                st.metric("Total Spent (Debit)", f"₹{total_debit:,.2f}", delta=None)
            with col3:
                st.metric("Total Received (Credit)", f"₹{total_credit:,.2f}")
            with col4:
                st.metric("Net Flow", f"₹{net:,.2f}", delta="Good" if net > 0 else "Bad")

            # Top Merchants
            top_merchants = filtered_df.groupby("Merchant").agg({
                "Debit": "sum",
                "Credit": "sum",
                "Particulars": "count"
            }).rename(columns={"Particulars": "Count"}).sort_values("Debit", ascending=False).head(8)

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Top Payees / Merchants**")
                st.dataframe(top_merchants.style.format({
                    "Debit": "₹{:.2f}",
                    "Credit": "₹{:.2f}",
                    "Count": "{:.0f}"
                }), use_container_width=True)

            with col2:
                # Inside the summary:

                if len(top_merchants) > 1:
                    fig, ax = plt.subplots()
                    top_merchants.head(5).plot(kind='bar', y='Debit', ax=ax, color='skyblue')
                    ax.set_title("Top Spending")
                    ax.set_ylabel("Amount (₹)")
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
                            
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)

        # Show Data Table
        display_df = filtered_df[['Tran Date', 'Particulars', 'Debit', 'Credit', 'Balance']].copy()
        display_df["Tran Date"] = display_df["Tran Date"].dt.strftime("%d-%b-%Y")

        st.markdown("---")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Debit": st.column_config.NumberColumn("Debit", format="₹%.2f"),
                "Credit": st.column_config.NumberColumn("Credit", format="₹%.2f"),
                "Balance": st.column_config.NumberColumn("Balance", format="₹%.2f"),
            }
        )

        csv = display_df.to_csv(index=False).encode()
        st.download_button("Download Results as CSV", csv, f"axis_search_{search_term or 'all'}.csv", "text/csv")

else:
    st.info("Upload your Axis Bank PDF statement to start analyzing!")
    st.markdown("""
    ### Features
    - Accurate extraction from real Axis Bank PDFs
    - Month filter + Full-text search
    - Instant summary when you search (e.g. "Zomato", "Swiggy", "PLAYO")
    - Top merchants & pie chart
    - Export filtered data
    """)
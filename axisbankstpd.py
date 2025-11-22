# axis_bank_analyzer.py - FINAL VERSION
import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt

# ========================= DARK MODE & PAGE CONFIG =========================
st.set_page_config(page_title="My Axis Bank Analyzer", layout="wide")

# Dark mode toggle
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

theme_button = st.sidebar.button("Toggle Dark Mode" if st.session_state.theme == "light" else "Toggle Light Mode")
if theme_button:
    toggle_theme()

# Apply theme
if st.session_state.theme == "dark":
    st.markdown("""
    <style>
    .css-1d391kg, .css-1v0mbdj, .css-1y0t8qx {background-color: #0e1117; color: white;}
    .css-1q8dd2e {color: white;}
    </style>
    """, unsafe_allow_html=True)
    plt.style.use('dark_background')

# ========================= CATEGORY MAPPING =========================
CATEGORIES = {
    # Food & Dining
    "FOOD": ["Zomato", "Swiggy", "Domino", "KFC", "McDonald", "Cafe", "Restaurant", "Dairy", "Tea", "Food Corner", "Hanuman Store"],
    "GROCERIES": ["DMart", "Reliance", "More", "BigBasket", "Arun Fruits", "Vegetables", "Rice", "Chowdeshwari"],
    "FUEL": ["Petrol", "Bharat Petroleum", "Indian Oil", "HP", "Nayara"],
    "SHOPPING": ["Amazon", "Flipkart", "Myntra", "Medplus", "Health Mart", "Go Daddy"],
    "TRAVEL": ["BMTC", "Metro", "Uber", "Ola", "Rapido", "Redbus", "MakeMyTrip"],
    "BILLS": ["Atria Broadband", "Electricity", "Jio", "Airtel", "Water Bill", "PhonePe", "Recharge"],
    "ENTERTAINMENT": ["Playo", "BookMyShow", "Netflix", "Spotify", "Church", "Resurrection"],
    "HEALTH": ["Pharmacy", "Medplus", "Apollo", "Health", "Davaindia"],
    "EDUCATION": ["Byjus", "Unacademy", "Fees"],
    "INVESTMENT": ["Paytm Money", "Edelweiss", "Mutual Fund"],
    "TRANSFER": ["UPI/P2A", "NEFT", "IMPS", "ARULANA", "ILLANGOVAN", "PARI KANNAPPAN", "Self", "Return"],
    "OTHERS": []
}

def categorize_transaction(desc):
    desc_upper = desc.upper()
    for category, keywords in CATEGORIES.items():
        if any(k.upper() in desc_upper for k in keywords):
            return category
    if "UPI" in desc_upper or "NEFT" in desc_upper or "IMPS" in desc_upper:
        return "TRANSFER"
    return "OTHERS"

# ========================= PDF PARSING (Your Working Version) =========================
def parse_axis_pdf(file_bytes):
    all_rows = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            lines = text.split("\n")
            in_table = False
            current_row = None

            for line in lines:
                line = line.strip()
                if "Tran Date" in line and "Particulars" in line:
                    in_table = True
                    continue
                if not in_table: continue
                if any(skip in line.upper() for skip in ["OPENING BALANCE", "CLOSING BALANCE", "TRANSACTION TOTAL", "END OF STATEMENT"]):
                    continue

                date_match = re.match(r"^\s*(\d{2}-\d{2}-\d{4})", line)
                if date_match:
                    if current_row and (current_row['debit'] > 0 or current_row['credit'] > 0):
                        all_rows.append([current_row['date'], current_row['desc'].strip(),
                                       current_row['debit'], current_row['credit'], current_row['balance']])

                    date_str = date_match.group(1)
                    remainder = line[date_match.end():].strip()
                    amounts = [float(a.replace(',', '')) for a in re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', line)]
                    debit = credit = balance = 0.0
                    if amounts:
                        balance = amounts[-1]
                        if len(amounts) >= 2:
                            prev = amounts[-2]
                            debit = prev if prev < balance else 0
                            credit = prev if prev > balance else 0
                        if credit == 0 and len(amounts) >= 2:
                            credit = amounts[0] if amounts[0] > balance else 0

                    desc = re.sub(r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b', '', remainder)
                    desc = re.sub(r'\s+', ' ', desc).strip()

                    current_row = {'date': date_str, 'desc': desc or remainder,
                                 'debit': debit, 'credit': credit, 'balance': balance}
                elif current_row:
                    current_row['desc'] += " " + line.strip()

            if current_row and (current_row['debit'] > 0 or current_row['credit'] > 0):
                all_rows.append([current_row['date'], current_row['desc'].strip(),
                               current_row['debit'], current_row['credit'], current_row['balance']])

    if not all_rows: return pd.DataFrame()

    df = pd.DataFrame(all_rows, columns=["Tran Date", "Particulars", "Debit", "Credit", "Balance"])
    df["Tran Date"] = pd.to_datetime(df["Tran Date"], format="%d-%m-%Y", dayfirst=True)
    df[["Debit", "Credit", "Balance"]] = df[["Debit", "Credit", "Balance"]].apply(pd.to_numeric, errors='coerce').fillna(0)
    df = df.sort_values("Tran Date").reset_index(drop=True)
    df["Year-Month"] = df["Tran Date"].dt.strftime("%Y - %B")
    df["Category"] = df["Particulars"].apply(categorize_transaction)
    return df

# ========================= STREAMLIT UI =========================
st.title("Axis Bank Statement Analyzer")
st.caption("Auto-categorizes expenses • Dark Mode • Search & Summary • Monthly Report")

uploaded_file = st.file_uploader("Upload your Axis Bank PDF", type="pdf")

if uploaded_file:
    with st.spinner("Analyzing your statement..."):
        df = parse_axis_pdf(uploaded_file.read())

    if df.empty:
        st.error("No transactions found!")
    else:
        st.success(f"Found {len(df):,} transactions • ₹{df['Debit'].sum():,.0f} spent")

        # Summary Cards
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Total Spent", f"₹{df['Debit'].sum():,.0f}")
        with col2: st.metric("Total Received", f"₹{df['Credit'].sum():,.0f}")
        with col3: st.metric("Net Change", f"₹{df['Credit'].sum() - df['Debit'].sum():,.0f}")
        with col4: st.metric("Final Balance", f"₹{df['Balance'].iloc[-1]:,.0f}")

        st.markdown("---")

        # Filters
        col1, col2 = st.columns([1, 3])
        with col1:
            months = ["All"] + sorted(df["Year-Month"].unique().tolist())
            month = st.selectbox("Month", months)
        with col2:
            search = st.text_input("Search in Particulars", placeholder="e.g. Playo, Zomato, Petrol")

        filtered = df.copy()
        if month != "All":
            filtered = filtered[filtered["Year-Month"] == month]
        if search:
            filtered = filtered[filtered["Particulars"].str.contains(search, case=False, na=False)]

        # Category Summary
        if search:
            st.subheader(f"Summary: **{search.upper()}**")
            cat_summary = filtered.groupby("Category").agg({"Debit": "sum", "Credit": "sum", "Particulars": "count"}).round(0)
            cat_summary = cat_summary.rename(columns={"Particulars": "Count"}).sort_values("Debit", ascending=False)

            col1, col2 = st.columns([1.8, 2.2])
            with col1:
                st.dataframe(cat_summary.style.format({"Debit": "₹{:,.0f}", "Credit": "₹{:,.0f}", "Count": "{:}"}))
            with col2:
                if cat_summary["Debit"].sum() > 0:
                    fig, ax = plt.subplots(figsize=(6, 4))
                    ax.pie(cat_summary["Debit"], labels=cat_summary.index, autopct='%1.0f%%', startangle=90)
                    ax.set_title("Spending by Category")
                    st.pyplot(fig)
                    plt.close(fig)

        # Monthly Category Chart
        st.markdown("---")
        st.subheader("Monthly Spending by Category")
        monthly_cat = filtered.groupby(["Year-Month", "Category"])["Debit"].sum().unstack(fill_value=0)
        if not monthly_cat.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            monthly_cat.plot(kind="bar", stacked=True, ax=ax, cmap="tab20")
            ax.set_ylabel("Amount (₹)")
            ax.set_title("Expense Breakdown")
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            st.pyplot(fig)
            plt.close(fig)

        # Data Table
        display = filtered[["Tran Date", "Particulars", "Category", "Debit", "Credit"]].copy()
        display["Tran Date"] = display["Tran Date"].dt.strftime("%d %b")
        st.dataframe(display, use_container_width=True, hide_index=True)

        # Download
        csv = display.to_csv(index=False).encode()
        st.download_button("Download Data", csv, "my_expenses.csv", "text/csv")

else:
    st.info("Upload your Axis Bank PDF statement to begin!")
    st.markdown("### Features\n- Auto-categorizes every transaction\n- Dark/Light mode\n- Search with instant summary\n- Beautiful charts\n- Export to CSV")

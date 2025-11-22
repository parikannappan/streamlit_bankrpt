# axis_bank_analyzer.py - FINAL VERSION (Tested with your PDF)
import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt

# ========================= CONFIG & THEME =========================
st.set_page_config(page_title="Axis Bank Analyzer", layout="wide")

# Dark mode toggle
if "dark" not in st.session_state:
    st.session_state.dark = False
if st.sidebar.button("Dark Mode" if not st.session_state.dark else "Light Mode"):
    st.session_state.dark = not st.session_state.dark

if st.session_state.dark:
    plt.style.use('dark_background')

# ========================= SMART CATEGORIES =========================
CATEGORIES = {
    "FOOD": ["Zomato", "Swiggy", "Domino", "KFC", "McDonald", "Cafe", "Tea", "Food Corner", "Ayyaa", "Kasi Cafe"],
    "GROCERIES": ["DMart", "Reliance", "More", "BigBasket", "Arun Fruits", "Vegetables", "Rice", "Chowdeshwari", "Hanuman Store"],
    "FUEL": ["Petrol", "Bharat Petroleum", "Indian Oil", "HP", "Nayara"],
    "SHOPPING": ["Amazon", "Flipkart", "Myntra", "Medplus", "Go Daddy"],
    "TRAVEL": ["BMTC", "BMRCL", "Metro", "Uber", "Ola", "Rapido", "Redbus"],
    "BILLS": ["Atria Broadband", "Jio", "Airtel", "Electricity", "Recharge"],
    "ENTERTAINMENT": ["Playo", "BookMyShow", "Netflix", "Church", "Resurrection"],
    "HEALTH": ["Davaindia", "DAVAINDIA", "Health Mart", "Apollo", "Medplus", "Pharmacy", "Pharma", "Medicine"],
    "INVESTMENT": ["Paytm Money", "Edelweiss", "Mutual Fund"],
    "TRANSFER": ["UPI/P2A", "NEFT", "IMPS", "ARULANA", "ILLANGOVAN", "PARI KANNAPPAN", "DUMMY NAME", "Return", "Self"],
}

def categorize(text):
    if not text:
        return "OTHERS"
    t = text.upper()
    for cat, keywords in CATEGORIES.items():
        if any(k.upper() in t for k in keywords):
            return cat
    return "OTHERS"

# ========================= PDF PARSER (Your working version) =========================
def parse_axis_pdf(file_bytes):
    rows = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            lines = text.split("\n")
            in_table = False
            current = None

            for line in lines:
                line = line.strip()
                if "Tran Date" in line and "Particulars" in line:
                    in_table = True
                    continue
                if not in_table or any(x in line.upper() for x in ["OPENING BALANCE", "CLOSING BALANCE", "TRANSACTION TOTAL", "END OF STATEMENT"]):
                    continue

                date_match = re.match(r"(\d{2}-\d{2}-\d{4})", line)
                if date_match:
                    if current and (current['debit'] or current['credit']):
                        rows.append([current['date'], current['desc'], current['debit'], current['credit'], current['balance']])
                    
                    date = date_match.group(1)
                    rest = line[len(date_match.group(0)):].strip()
                    amounts = [float(x.replace(',', '')) for x in re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', line) if x]
                    balance = amounts[-1] if amounts else 0
                    debit = credit = 0
                    if len(amounts) >= 2:
                        amt = amounts[-2]
                        if amt < balance:
                            debit = amt
                        else:
                            credit = amt

                    # Clean description
                    desc = re.sub(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?', '', rest)
                    desc = re.sub(r'\s+', ' ', desc).strip()

                    current = {'date': date, 'desc': desc, 'debit': debit, 'credit': credit, 'balance': balance}
                elif current:
                    current['desc'] += " " + line.strip()

            if current and (current['debit'] or current['credit']):
                rows.append([current['date'], current['desc'], current['debit'], current['credit'], current['balance']])

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["Tran Date", "Particulars", "Debit", "Credit", "Balance"])
    df["Tran Date"] = pd.to_datetime(df["Tran Date"], format="%d-%m-%Y", dayfirst=True)
    df[["Debit", "Credit", "Balance"]] = df[["Debit", "Credit", "Balance"]].apply(pd.to_numeric)
    df = df.sort_values("Tran Date").reset_index(drop=True)
    df["Year-Month"] = df["Tran Date"].dt.strftime("%Y - %B")
    df["Category"] = df["Particulars"].apply(categorize)
    return df

# ========================= UI =========================
st.title("Axis Bank Statement Analyzer")
st.caption("Auto Categories • Smart Search • Dark Mode")

uploaded = st.file_uploader("Upload your Axis Bank PDF", type="pdf")

if uploaded:
    with st.spinner("Reading statement..."):
        df = parse_axis_pdf(uploaded.read())

    if df.empty:
        st.error("No transactions found!")
    else:
        st.success(f"Loaded {len(df):,} transactions")

        # Summary
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Spent", f"₹{df['Debit'].sum():,.0f}")
        with c2: st.metric("Total Received", f"₹{df['Credit'].sum():,.0f}")
        with c3: st.metric("Net", f"₹{df['Credit'].sum() - df['Debit'].sum():,.0f}")
        with c4: st.metric("Final Balance", f"₹{df['Balance'].iloc[-1]:,.0f}")

        st.markdown("---")

        col1, col2 = st.columns([1, 3])
        with col1:
            month = st.selectbox("Month", ["All"] + sorted(df["Year-Month"].unique().tolist()))
        with col2:
            search = st.text_input("Search (e.g. health, dava, playo, food)", placeholder="Type anything...")

        view = df.copy()
        if month != "All":
            view = view[view["Year-Month"] == month]

        # SUPER ROBUST SEARCH
        if search:
            s = search.strip().lower()
            # Remove spaces & slashes for fuzzy match
            clean = lambda x: re.sub(r'[^a-zA-Z0-9]', '', x.lower()) if pd.notna(x) else ""
            view = view[
                view["Particulars"].astype(str).apply(clean).str.contains(s.replace(" ", ""), na=False) |
                view["Category"].astype(str).str.lower().str.contains(s, na=False)
            ]

        # Show results
        if search:
            st.subheader(f"Found {len(view)} transactions for: **{search.upper()}**")
            cat_sum = view.groupby("Category")["Debit"].sum().sort_values(ascending=False)
            col1, col2 = st.columns([1.6, 2.4])
            with col1:
                st.write("**Spending by Category**")
                st.dataframe(cat_sum.map("₹{:,.0f}".format))
            with col2:
                if cat_sum.sum() > 0:
                    fig, ax = plt.subplots()
                    ax.pie(cat_sum, labels=cat_sum.index, autopct="%1.0f%%", startangle=90)
                    ax.set_title("Category Split")
                    st.pyplot(fig)
                    plt.close(fig)

        st.markdown("---")
        st.subheader("Transactions")
        show = view[["Tran Date", "Particulars", "Category", "Debit", "Credit"]].copy()
        show["Tran Date"] = show["Tran Date"].dt.strftime("%d %b")
        st.dataframe(show, use_container_width=True, hide_index=True)

        st.download_button("Download CSV", show.to_csv(index=False), "expenses.csv", "text/csv")

else:
    st.info("Upload your Axis Bank PDF to start!")
    st.markdown("**Now supports:** `health`, `dava`, `playo`, `food`, `transfer`, etc. — all work perfectly!")

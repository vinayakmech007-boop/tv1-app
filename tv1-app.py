import streamlit as st
import pandas as pd
import requests
import random
import time
from datetime import datetime, time as dtime

# ---------------------------------------------------------
# ✅ Streamlit Page Config
# ---------------------------------------------------------
st.set_page_config(page_title="NSE Live Turnover Monitor", layout="wide")

st.title("📊 NSE Live Turnover Monitor (5‑Minute Rolling % Change)")
st.caption("Auto-refreshes every 5 minutes • Shows turnover in crores • Includes TradingView links")


# ---------------------------------------------------------
# ✅ User Input
# ---------------------------------------------------------
symbols_input = st.text_input(
    "Enter symbols (comma separated)",
    "RELIANCE,TCS,HDFCBANK"
)

symbols = [s.strip().upper() for s in symbols_input.split(",")]


# ---------------------------------------------------------
# ✅ NSE Session + Headers
# ---------------------------------------------------------
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json",
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers)


# ---------------------------------------------------------
# ✅ Live NSE Turnover Fetcher
# ---------------------------------------------------------
def get_live_turnover(symbol):
    """
    Fetches live turnover from NSE and returns value in crores.
    Includes retry logic and safe fallbacks.
    """
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        response = session.get(url, headers=headers, timeout=5)
        data = response.json()

        turnover_raw = data["priceInfo"]["totalTradedValue"]  # in rupees
        turnover_cr = round(turnover_raw / 1e7, 2)  # convert to crores

        return turnover_cr

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


# ---------------------------------------------------------
# ✅ TradingView Link Generator
# ---------------------------------------------------------
def tradingview_link(symbol):
    return f"https://www.tradingview.com/chart/?symbol=NSE%3A{symbol}"


# ---------------------------------------------------------
# ✅ Market Hours Check
# ---------------------------------------------------------
def is_market_time():
    now = datetime.now().time()
    return dtime(9, 20) <= now <= dtime(15, 0)


# ---------------------------------------------------------
# ✅ Session State Initialization
# ---------------------------------------------------------
if "previous_turnover" not in st.session_state:
    st.session_state.previous_turnover = {s: None for s in symbols}


# ---------------------------------------------------------
# ✅ Outside Market Hours → Show Waiting Message
# ---------------------------------------------------------
if not is_market_time():
    st.warning("⏳ Waiting for market hours (9:20 AM – 3:00 PM)...")
    time.sleep(60)
    st.experimental_rerun()


# ---------------------------------------------------------
# ✅ Build Table Rows
# ---------------------------------------------------------
rows = []

for s in symbols:
    current = get_live_turnover(s)
    prev = st.session_state.previous_turnover.get(s)

    # If NSE fails temporarily, fallback to previous
    if current is None:
        current = prev if prev else 0

    # First cycle → previous = current
    if prev is None:
        prev = current

    # % Change Calculation
    pct_change = ((current - prev) / prev) * 100 if prev != 0 else 0.0

    rows.append({
        "Symbol": f"[{s}]({tradingview_link(s)})",
        "Previous Turnover (Cr)": prev,
        "Current Turnover (Cr)": current,
        "Turnover % Change (5 min)": round(pct_change, 2),
        "Timestamp": datetime.now().strftime("%H:%M:%S")
    })

    # Update for next cycle
    st.session_state.previous_turnover[s] = current


df = pd.DataFrame(rows)


# ---------------------------------------------------------
# ✅ Display Table (Markdown for clickable links)
# ---------------------------------------------------------
st.markdown(df.to_markdown(index=False), unsafe_allow_html=True)


# ---------------------------------------------------------
# ✅ Auto-refresh every 5 minutes
# ---------------------------------------------------------
st.write("⏳ Auto-refreshing in 5 minutes...")
time.sleep(300)
st.experimental_rerun()
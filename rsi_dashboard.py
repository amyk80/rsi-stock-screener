import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from time import sleep

# --- RSI calculation ---
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# --- Get S&P 500 tickers from Wikipedia ---
@st.cache_data
def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', {'id': 'constituents'})
    tickers = pd.read_html(str(table))[0]['Symbol'].tolist()
    tickers = [t.replace('.', '-') for t in tickers]  # BRK.B → BRK-B
    return tickers

# --- UI ---
st.set_page_config(page_title="RSI Screener", layout="centered")
st.title("📊 S&P 500 RSI Screener")
st.write("Automatically scans all S&P 500 stocks to show those with the **lowest** and **highest** RSI values.")

# Load tickers
tickers = get_sp500_tickers()
results = []

# Progress bar
progress = st.progress(0)
status_text = st.empty()

for i, ticker in enumerate(tickers):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="30d")
        if len(hist) < 15:
            continue
        rsi_series = calculate_rsi(hist['Close'])
        latest_rsi = rsi_series.dropna().iloc[-1]
        results.append({'Ticker': ticker, 'RSI': round(latest_rsi, 2)})
    except:
        continue
    progress.progress((i + 1) / len(tickers))
    status_text.text(f"Scanning {ticker}... ({i+1}/{len(tickers)})")

# Display results
if results:
    df = pd.DataFrame(results)
    low_rsi = df.sort_values(by='RSI').head(5)
    high_rsi = df.sort_values(by='RSI', ascending=False).head(5)

    st.subheader("📉 Top 5 Lowest RSI Stocks (Oversold)")
    st.dataframe(low_rsi)

    st.subheader("📈 Top 5 Highest RSI Stocks (Overbought)")
    st.dataframe(high_rsi)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Full RSI Report", data=csv, file_name="rsi_report.csv", mime="text/csv")
else:
    st.error("No RSI data found.")

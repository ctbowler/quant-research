import os
from dotenv import load_dotenv
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from tqdm import tqdm
from constants import *

# --- Load .env and API keys --- #
load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_API_SECRET")
client = CryptoHistoricalDataClient(API_KEY, API_SECRET)

# --- Parameters --- #
LOOKBACK_DAYS = LOOKBACK_PERIOD
END_DATE = ENTRY_DATE
START_DATE = END_DATE - timedelta(days=LOOKBACK_DAYS)

# --- Crypto pairs to test (Alpaca-supported) --- #
symbols = [
    "BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD", "AVAX/USD", "ADA/USD",
    "MATIC/USD", "LTC/USD", "BCH/USD", "LINK/USD", "UNI/USD", "DOT/USD",
    "SHIB/USD", "ATOM/USD", "ETC/USD", "XLM/USD", "NEAR/USD", "FIL/USD",
    "EOS/USD", "AAVE/USD"
]



# --- Pull OHLCV for each coin --- #
price_data = {}
volume_data = {}

for symbol in tqdm(symbols):
    try:
        req = CryptoBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=START_DATE,
            end=END_DATE
        )
        bars = client.get_crypto_bars(req).df
        if bars.empty:
            continue

        df = bars.xs(symbol, level="symbol")
        df = df.resample("1D").last().dropna()
        price_data[symbol] = df["close"]
        volume_data[symbol] = df["volume"] * df["close"]  # dollar volume
    except Exception as e:
        print(f"Error pulling {symbol}: {e}")

# --- Create DataFrame for ranking by liquidity --- #
liq_df = pd.DataFrame(volume_data)
avg_liq = liq_df.mean().sort_values(ascending=False)
top_symbols = avg_liq.head(20).index.tolist()

# Filter price data for just top 20
date = ENTRY_DATE.strftime("%m-%d-%Y")
price_df = pd.DataFrame({sym: price_data[sym] for sym in top_symbols}).dropna()
price_df.to_csv(f"../data/{date}/top_liquid_coins.csv")
print(f"../data/{date}/top_liquid_coins: {top_symbols}")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from polygon import RESTClient
from tqdm import tqdm
from constants import ENTRY_DATE, EXIT_DATE, API_KEY
tqdm.pandas() # For progress bar


"""
Author: Carson Bowler

This script filters the top 1500 liquid U.S. stocks based on momentum strength and risk.
It removes high-beta stocks and weak momentum performers, then ranks remaining stocks
by 2-12 month return. Finally, it applies a Frog-in-the-Pan (FIP) metric to measure
momentum smoothness and selects the top 50 stocks with the highest momentum quality.
"""



# --- Load CSV File with Ticker data --- #
df = pd.read_csv(r"FILE PATH FOR TOP 1500 STOCKS WITH MOMENTUM AND BETA COMPUTED")

# --- Filter out top 10% beta stocks --- #
df = df[df['beta'] < df['beta'].quantile(0.9)] # i.e. we are keeping bottom 90% quantile beta

# --- Filter out bottom 5% 9 month return stocks --- #
df = df[df['9month_return'] > df['9month_return'].quantile(0.05)] # i.e. we are keeping top 95% quantile 9 month return

# --- Filter out bottom 5% 6 month return stocks --- #
df = df[df['6month_return'] > df['6month_return'].quantile(0.05)] # i.e. we are keeping top 95% quantile 6 month return

# --- Sort by 2-12 month return --- #
df = df.sort_values(by="2month_return", ascending=False)
# Keep top 100 stocks with highest 2-12 month return
df = df.head(100).reset_index(drop=True) 

# --- Compute momentum quality of stocks based on Frog-in-the-Pan metric --- #
# First setup polygon API parameters
polygon_key = API_KEY
client = RESTClient(polygon_key)
# Setup a function to extract momentum quality for a given ticker
def get_momentum_quality(ticker, lookback = 365):
    # Extract daily bars for the last 365 days (252 trading days)
    try:
        # Set time window parameters
        end_date = ENTRY_DATE
        start_date = end_date - timedelta(days=lookback)
        # Make call to Polygon API to get daily bars
        bars = client.get_aggs(
            ticker,
            1, "day",
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
        # Store closing prices in a list
        prices = [bar.close for bar in bars if bar.close is not None]
        # Compute daily returns and store in a pandas series
        daily_returns = pd.Series(prices).pct_change().dropna().reset_index(drop=True)
        # Compute number of days where returns were positive
        positive_days = (daily_returns > 0).sum()
        # Assign a momentum score based on the number of positive days
        momentum_score = positive_days / len(daily_returns) if daily_returns.size > 0 else 0
        # Return the momentum score
        return momentum_score
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# --- Compute momentum quality score for each stock --- #
df['momentum_quality'] = df['ticker'].progress_apply(lambda x: get_momentum_quality(x))
# Sort by momentum quality
df = df.sort_values(by="momentum_quality", ascending=False)
# Keep top 50 stocks with highest momentum quality
df = df.head(50).reset_index(drop=True)

# --- Save the filtered DataFrame to a new CSV file --- #
df.to_csv(r"FILE PATH FOR FILTERED TOP 100 RETURNS", index=False)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from polygon import RESTClient
from datetime import datetime, timedelta
from tqdm import tqdm
from constants import ENTRY_DATE, EXIT_DATE, API_KEY
tqdm.pandas()  # For progress bar



"""
Author: Carson Bowler

This script computes beta and multiple momentum features for the top 1500 most
liquid U.S. stocks using the Polygon.io API. It calculates each stock’s beta 
via linear regression against SPY, then computes 2-12, 6-, and 9-month returns 
to support multi-factor momentum filtering. The results are saved to CSV for 
further portfolio construction.
"""



# --- Setup Polygon Key + API Client --- #
polygon_key = API_KEY
client = RESTClient(polygon_key)

# --- Time window parameters --- #
end_date = ENTRY_DATE
start_date = end_date - timedelta(days=365)

# --- Load top 1500 liquid tickers --- #
df = pd.read_csv(r"FILE PATH FOR TOP 1500 LIQUID STOCKS")

# --- Fetch SPY data and compute daily returns --- #
try:
    bars = client.get_aggs(
        "SPY",
        1, "day",
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    prices_spy = [bar.close for bar in bars if bar.close is not None]
    returns_spy = pd.Series(prices_spy).pct_change().dropna().reset_index(drop=True)
except Exception as e:
    print(f"Error fetching SPY data: {e}")
    returns_spy = pd.Series(dtype=float)

# --- Retrieve daily returns for each stock and compute Beta --- #
beta_dict = {}  # Initialize a dictionary to store beta values

# Loop through each ticker in the DataFrame
for ticker in df["ticker"]:
    try:
        # Fetch Stock Data
        bars = client.get_aggs(
            ticker,
            1, "day",
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
        # Store closing prices in a list
        prices_ticker = [bar.close for bar in bars if bar.close is not None]
        # Computing returns as percent change between consecutive days
        returns_ticker = pd.Series(prices_ticker).pct_change().dropna().reset_index(drop=True)
        # Align lengths of return series
        min_len = min(len(returns_spy), len(returns_ticker))
        if min_len < 50:
            continue  # Skip if not enough data
        # Prepare X and y for regression
        x = np.array(returns_spy[:min_len]).reshape(-1, 1)
        y = np.array(returns_ticker[:min_len])
        # Remove any rows with NaN values
        mask = ~np.isnan(x.flatten()) & ~np.isnan(y)
        # Keep only valid data
        x_clean = x[mask]   
        y_clean = y[mask]
        if len(x_clean) < 50:
            continue  # Skip if not enough valid data after cleaning

        # --- Linear Regression to find Beta ---
        beta_model = LinearRegression()
        beta_model.fit(x_clean, y_clean)
        beta = beta_model.coef_[0]
        # Store result
        beta_dict[str(ticker)] = beta

    except Exception as e:
        print(f"Error fetching or processing data for {ticker}: {e}")
        continue

# --- Map Beta values to DataFrame Corresponding to Each Ticker --- #
df["beta"] = df["ticker"].map(beta_dict)

# --- Compute Momentum (2-12 month returns, 6 and 9 month return lows) --- #
# Define a function to compute returns over a specified time period#
def get_returns(ticker, months = 6, end_date =end_date):
    # Convert lookback months to days
    days = months * 30 
    # Calculate the start date to fetch momentum data
    start_date = end_date - timedelta(days=days)
    buffer = 5 # days buffer to avoid weekends
    # --- Fetch Data using Polygon API --- #
    try:
        # --- Fetch Data at Start Date --- #
        bars = client.get_aggs(
            ticker,
            1, "day",
            (start_date - timedelta(days = buffer)).strftime("%Y-%m-%d"),
            (start_date).strftime("%Y-%m-%d")
        )
        # Convert price data with datetime and closing price to a list of tuples
        prices_start = [(pd.to_datetime(bar.timestamp, unit='ms'), bar.close) for bar in bars if bar.close is not None]
        # Filter prices to only include those within the specified date range
        prices_start = [p for p in prices_start if p[0] <= start_date]
        # Ensure price data is not empty
        if not prices_start:
            print(f"No data found for {ticker} near {start_date}")
            return None
        # Store closing price at start date
        start_price = sorted(prices_start, key = lambda x: x[0])[-1][1]
    
        # --- Fetch Data at End Date --- #
        bars = client.get_aggs(
            ticker,
            1, "day",
            (end_date - timedelta(days = buffer)).strftime("%Y-%m-%d"),
            (end_date).strftime("%Y-%m-%d")
        )
        # Convert price data with datetime and closing price to a list of tuples
        prices_end = [(pd.to_datetime(bar.timestamp, unit='ms'), bar.close) for bar in bars if bar.close is not None]
        # Filter prices to only include those within the specified date range
        prices_end = [p for p in prices_end if p[0] <= end_date]
        # Store closing price at end date
        end_price = sorted(prices_end, key = lambda x: x[0])[-1][1]

        # --- Calculate Returns --- #
        returns = (end_price - start_price) / start_price

        return returns
    except Exception as e:
        print(f"Error computing returns for {ticker}: {e}")
        return None
    
# --- Calculate 2-12 month returns (excluding past one or two months) --- #
df["2month_return"] = df["ticker"].progress_apply(lambda x: get_returns(x, months=10, end_date = end_date - timedelta(days = 60)))
# --- Calculate 6 month return --- #
df["6month_return"] = df["ticker"].progress_apply(lambda x: get_returns(x, months=6, end_date = end_date - timedelta(days = 365)))
# --- Calculate 9 month return --- #
df["9month_return"] = df["ticker"].progress_apply(lambda x: get_returns(x, months=9, end_date = end_date - timedelta(days = 365)))

# --- Filter out top 10% beta stocks --- #
df.to_csv(r"FILE PATH FOR TOP 1500 STOCKS WITH MOMENTUM AND BETA COMPUTED", index=False)
print("Beta and momentum data saved to CSV.")
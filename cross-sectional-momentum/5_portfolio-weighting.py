import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from polygon import RESTClient
from tqdm import tqdm
tqdm.pandas()  # For progress bar

# --- Setup Polygon Key + API Client --- #
api_key = "INSERT API KEY HERE"
client = RESTClient(api_key)

# --- Set Portfolio Parameters --- #
portfolio_size = 1_000_000
rebalance_date = datetime(2024, 5, 15 )

# --- Load filtered stocks --- #
df = pd.read_csv(r"FILE PATH FOR TOP 100 STOCKS BY RETURNS")
# Compute portfolio parameters
weights = [1 / len(df)] * len(df) # Equal weight for each stock
dollar_alloc = [portfolio_size * (1 / len(df))] * len(df) # Dollar allocation for each stock
# Function to retrieve the latest closing price for a given ticker
def get_latest_price(ticker):
    try:
        # Fetch daily bars for the last 2 days using Polygon API
        bars = client.get_aggs(
            ticker, 
            1, "day",
            (datetime.now() - timedelta(days = 2)).strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d")
        )
        # Obtain the latest closing price
        prices = [bar.close for bar in bars if bar.close is not None]
        # Ensure we have data, return last price in the list (most recent price)
        return prices[-1] if prices else None
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None
    
# --- Create DataFrame for top 50 stocks --- #
top_50_stocks = pd.DataFrame(list(zip(df['ticker'], weights, dollar_alloc)), columns = ['ticker', 'weights', 'dollar_alloc'])
# Store latest price and share allocation
top_50_stocks['latest_price'] = top_50_stocks['ticker'].progress_apply(lambda x: get_latest_price(x))
top_50_stocks['share_alloc'] = top_50_stocks.progress_apply(lambda x: x['dollar_alloc'] / x['latest_price'], axis=1)
# Round to nearest whole number shares
top_50_stocks['share_alloc'] = top_50_stocks['share_alloc'].round()

# --- Save to CSV --- #
top_50_stocks.to_csv(r"FILE PATH FOR TOP 50 FILTERED STOCKS TO INVEST IN", index=False)
print("Portfolio investment data saved.")
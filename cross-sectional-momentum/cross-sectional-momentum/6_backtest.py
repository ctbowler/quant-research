import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from polygon import RESTClient
from datetime import datetime
from tqdm import tqdm
from constants import ENTRY_DATE, EXIT_DATE, API_KEY


"""
Author: Carson Bowler

This script performs a full backtest of the momentum strategy by tracking the 
daily returns of each stock in the final portfolio from entry to rebalance date.
It computes weighted portfolio performance, compares it against SPY, and plots 
both cumulative portfolio value and individual stock return paths. It also saves 
portfolio and benchmark return data to CSV for further analysis.
"""



# --- Setup Polygon Key + API Client --- #
api_key = API_KEY
client = RESTClient(api_key)

# --- Backtesting Parameters --- #
start_date = ENTRY_DATE
rebalance_date = EXIT_DATE

# --- Load filtered stocks --- #
df = pd.read_csv(r"FILE PATH FOR TOP 50 FILTERED STOCKS TO INVEST IN")

# --- Function to compute return relative to entry --- #
def compute_relative_returns(ticker, end_date=rebalance_date):
    try:
        # Fetch daily bars for the last 2 days using Polygon API
        bars = client.get_aggs(ticker, 1, "day",
                               start_date.strftime("%Y-%m-%d"),
                               end_date.strftime("%Y-%m-%d"))
        daily_prices = [bar.close for bar in bars if bar.close is not None]
        dates = [pd.to_datetime(bar.timestamp, unit='ms').date() for bar in bars if bar.close is not None]
        # Ensure we have data
        if len(daily_prices) == 0:
            return None
        # Convert to Series and sort by date
        price_series = pd.Series(daily_prices, index=pd.to_datetime(dates)).sort_index()
        # Ensure we have data from start_date
        entry_price = price_series.iloc[0]
        # Compute relative returns
        if entry_price == 0:
            return None
        # Compute relative returns from entry price
        relative_returns = (price_series / entry_price) - 1
        return relative_returns
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# --- Compute return series for each stock --- #
# Initialize an empty DataFrame to store returns
returns_df = pd.DataFrame()
# Loop through each ticker in the DataFrame
for i, row in tqdm(df.iterrows(), total=len(df)):
    ticker = row['ticker']
    # Compute relative returns
    rel_returns = compute_relative_returns(ticker)
    # If returns are computed successfully, add to DataFrame
    if rel_returns is not None:
        returns_df[ticker] = rel_returns
    else:
        print(f"Failed to compute returns for {ticker}")

# --- Apply initial weights (fixed) --- #
weights = df.set_index('ticker')['weights']
weighted_returns_df = returns_df.multiply(weights, axis=1)

# --- Sum weighted returns to get portfolio cumulative return --- #
portfolio_cumulative_return = weighted_returns_df.sum(axis=1)

# --- Convert to portfolio value starting from $1,000,000 --- #
portfolio_value = 1_000_000 * (1 + portfolio_cumulative_return)

# --- Save to CSV --- #
results_df = pd.DataFrame({
    'portfolio_cumulative_return': portfolio_cumulative_return,
    'portfolio_value': portfolio_value
})
results_df.index.name = 'Date'
results_df.to_csv(r"FILE PATH FOR PORTFOLIO BACKTEST RESULTS", index=True)

# --- Fetch SPY data and compute daily returns --- #
spy_bars = client.get_aggs(
    "SPY", 1, "day",
    start_date.strftime("%Y-%m-%d"),
    rebalance_date.strftime("%Y-%m-%d")
)
spy_prices = [bar.close for bar in spy_bars if bar.close is not None]
spy_dates = [pd.to_datetime(bar.timestamp, unit='ms').date() for bar in spy_bars if bar.close is not None]
# Convert to Series
spy_series = pd.Series(spy_prices, index=pd.to_datetime(spy_dates)).sort_index()
spy_entry_price = spy_series.iloc[0]
spy_returns = (spy_series / spy_entry_price) - 1  # Cumulative return from Jan 3
spy_value = 1_000_000 * (1 + spy_returns)         # Scale to match portfolio dollars
# Convert to DataFrame with a column name
spy_returns_df = spy_returns.to_frame(name='Daily Returns')
# Save to CSV
spy_returns_df.to_csv(r"C:\Users\bowle\trading-scripts\momentum\spy_daily_returns.csv")

# --- Plot portfolio vs SPY --- #
import matplotlib.pyplot as plt
plt.figure(figsize=(14, 6))
# Plot lines with thicker linewidth
plt.plot(results_df.index, results_df['portfolio_value'], label='Portfolio Value', color='green', linewidth=2.2)
plt.plot(spy_returns.index, spy_value, label='SPY Value', color='blue', linestyle='--', linewidth=2.2)
# Aesthetic title
plt.title("Portfolio vs SPY (May 2024 – May 2025)", fontsize=18, fontweight='bold', fontname='DejaVu Sans')
plt.xlabel("Date", fontsize=12)
plt.ylabel("Portfolio Value ($)", fontsize=12)
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend(fontsize=12)
plt.tight_layout()
plt.show()

# --- Plot growth of $1 invested in each stock --- #
import matplotlib.pyplot as plt
plt.figure(figsize=(18, 10))
# Plot each stock's growth from $1
for ticker in returns_df.columns:
    plt.plot(returns_df.index, 1 + returns_df[ticker], label=ticker, linewidth=1.2)
# Title & axis labels
plt.title("Growth of $1 Invested in Each Ticker (Jan 2024 – Jan 2025)",
          fontsize=18, fontweight='bold', fontname='DejaVu Sans')
plt.xlabel("Date", fontsize=12)
plt.ylabel("Value of $1 Investment", fontsize=12)
# Grid
plt.grid(True, linestyle='--', alpha=0.5)
# Top-left legend with multiple columns
plt.legend(loc='upper left', bbox_to_anchor=(0, 1),
           ncol=4, fontsize=9, title='Tickers', frameon=False)
plt.tight_layout()
plt.show()





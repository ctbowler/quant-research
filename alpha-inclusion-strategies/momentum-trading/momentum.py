import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from polygon import RESTClient
import requests

"""
Momentum-Based Event Trading Strategy

This script implements a post-announcement momentum strategy that enters long or short positions 
1 day after an inclusion announcement. Stocks with extreme flow impact are selected, and each is 
paired with a sector-based hedge. Position sizing is capital-aware, beta-hedged, and constrained 
by liquidity and stop-loss rules. The strategy includes overnight holding costs using the Fed Funds 
rate and exits either on stop loss or at a pre-defined trade date. Outputs include trade-level and 
daily PnL, with Sharpe ratio computation for overall performance.
"""

# --- CONFIGURATION ---
polygon_key = "MY POLYGON KEY"
fred_key = "MY FRED KEY"
portfolio_size = 5_000_000
txn_cost_per_share = 0.01
position_loss_cap = 0.001 * portfolio_size  # cap of $5,000 per position
aggregate_loss_cap = 100_000  # portfolio-wide stop loss

# --- LOAD DATA ---
trades = pd.read_csv("polygon_announcement_to_trade_returns.csv", parse_dates=["Announced", "Trade Date"])
hedge_df = pd.read_csv("best_sector_hedge.csv")
zscore_df = pd.read_csv("normalized_volatility_momentum_analysis.csv")

# Filter to extreme flow impact trades only
trades = trades[trades["Flow Impact"] == "Extreme"]

# Merge sector-based hedge tickers and Z-scores
trades = trades.merge(hedge_df, on="Sector", how="left")
trades.rename(columns={"Hedge Ticker": "Best Hedge"}, inplace=True)
trades.dropna(subset=["Best Hedge"], inplace=True)
trades = trades.merge(zscore_df[["Ticker", "Return Z-Score"]], on="Ticker", how="left")
trades.sort_values("Announced", inplace=True)

client = RESTClient(polygon_key)

# --- HELPERS ---
def get_fed_funds_rate(date):
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={fred_key}&file_type=json&observation_start={date:%Y-%m-%d}&observation_end={date:%Y-%m-%d}"
    r = requests.get(url).json()
    try:
        return float(r['observations'][0]['value']) / 100
    except:
        return 0.0433

def get_ohlc_and_volume(ticker, start, end):
    aggs = client.get_aggs(ticker, 1, "day", start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    df = pd.DataFrame([{
        "date": datetime.utcfromtimestamp(bar.timestamp / 1000),
        "open": bar.open,
        "close": bar.close,
        "volume": bar.volume
    } for bar in aggs])
    if df.empty:
        return None
    df.set_index("date", inplace=True)
    df.sort_index(inplace=True)
    return df

# --- BACKTESTING LOOP ---
pnl_results = []
daily_pnl_records = []
capital_in_use = 0
net_pnl_total = 0
trades = trades.drop_duplicates(subset=["Ticker", "Announced", "Trade Date"])

for _, row in trades.iterrows():
    # Extract trade setup
    ticker = row["Ticker"]
    hedge = row["Best Hedge"]
    beta = row["Hedge Beta"]
    zscore = row["Return Z-Score"]
    ann_date = row["Announced"]
    trade_date = row["Trade Date"]
    start = ann_date + timedelta(days=1)  # entry date
    end = trade_date  # final allowed holding day

    if pd.isna(zscore) or (end - start).days < 2:
        continue

    direction = "SHORT" if zscore < -1 else "LONG"

    # Get ADV for sizing
    adv_data = get_ohlc_and_volume(ticker, ann_date - timedelta(days=60), ann_date - timedelta(days=1))
    if adv_data is None or adv_data.shape[0] < 20:
        continue
    adv = adv_data.tail(20)["volume"].mean()
    if pd.isna(adv) or adv == 0:
        continue
    max_shares = int(0.01 * adv)

    # Get price series
    stock_data = get_ohlc_and_volume(ticker, start, end)
    hedge_data = get_ohlc_and_volume(hedge, start, end)
    if stock_data is None or hedge_data is None or len(stock_data) < 2 or len(hedge_data) < 2:
        continue

    try:
        stock_open_date = stock_data.index[stock_data.index >= start].min()
        hedge_open_date = hedge_data.index[hedge_data.index >= start].min()
        stock_open = stock_data.loc[stock_open_date]["open"]
        hedge_open = hedge_data.loc[hedge_open_date]["open"]
    except:
        continue

    # Capital-aware position sizing (limit exposure to 5%)
    stock_shares = min(int((portfolio_size * 0.05) / stock_open), max_shares)
    stock_entry = stock_shares * stock_open

    hedge_dollars = abs(beta) * stock_entry
    hedge_shares = min(int(hedge_dollars / hedge_open), max_shares, int((portfolio_size * 0.05) / hedge_open))
    hedge_entry = hedge_shares * hedge_open

    this_trade_capital = stock_entry + hedge_entry

    if capital_in_use + this_trade_capital > portfolio_size:
        continue  # skip if not enough capital

    capital_in_use += this_trade_capital
    short_stock = zscore < -1
    stop_hit = False
    fed_rate = get_fed_funds_rate(ann_date)

    # Simulate holding period, checking for early stop
    for dt in stock_data.index[stock_data.index >= stock_open_date]:
        if dt not in hedge_data.index:
            continue
        stock_close = stock_data.loc[dt]["close"]
        hedge_close = hedge_data.loc[dt]["close"]

        stock_exit = stock_close * stock_shares
        hedge_exit = hedge_close * hedge_shares

        gross = (stock_entry - stock_exit if short_stock else stock_exit - stock_entry) - beta * (hedge_exit - hedge_entry)
        hold_days = (dt - stock_open_date).days
        overnight_cost = (stock_entry * (fed_rate + 0.015) + hedge_entry * (fed_rate + 0.01)) * (hold_days / 252)
        txn_cost = txn_cost_per_share * (stock_shares + hedge_shares)
        net = gross - txn_cost - overnight_cost

        daily_pnl_records.append({
            "Date": dt.date(),
            "Ticker": ticker,
            "Position": direction,
            "Net PnL": net
        })

        if net <= -position_loss_cap:
            stock_close_date = dt
            hedge_close_date = dt
            stop_hit = True
            break

    # If not stopped, exit at latest valid date
    if not stop_hit:
        stock_close_date = stock_data.index[stock_data.index <= end].max()
        hedge_close_date = hedge_data.index[hedge_data.index <= end].max()

    try:
        stock_close = stock_data.loc[stock_close_date]["close"]
        hedge_close = hedge_data.loc[hedge_close_date]["close"]
    except:
        continue

    stock_exit = stock_close * stock_shares
    hedge_exit = hedge_close * hedge_shares
    hedge_pnl = -beta * (hedge_exit - hedge_entry)
    gross_pnl = (stock_entry - stock_exit if short_stock else stock_exit - stock_entry) + hedge_pnl
    hold_days = (stock_close_date - stock_open_date).days
    overnight_cost = (stock_entry * (fed_rate + 0.015) + hedge_entry * (fed_rate + 0.01)) * (hold_days / 252)
    txn_cost = txn_cost_per_share * (stock_shares + hedge_shares)
    net_pnl = gross_pnl - txn_cost - overnight_cost

    capital_in_use -= this_trade_capital
    net_pnl_total += net_pnl

    if net_pnl_total <= -aggregate_loss_cap:
        print(f"\nPortfolio stop loss hit. Exiting.")
        break

    pnl_results.append({
        "Ticker": ticker,
        "Hedge Ticker": hedge,
        "Z-Score": zscore,
        "Position": direction,
        "Start Date": stock_open_date.date(),
        "End Date": stock_close_date.date(),
        "Gross PnL $": gross_pnl,
        "Hedge PnL $": hedge_pnl,
        "Net PnL $": net_pnl,
        "Net PnL %": net_pnl / this_trade_capital,
        "Capital Used": this_trade_capital,
        "Days Held": hold_days,
        "Stopped Early": stop_hit
    })

# --- EXPORT RESULTS ---
pnl_df = pd.DataFrame(pnl_results)
daily_pnl_df = pd.DataFrame(daily_pnl_records)

# --- PERFORMANCE METRICS ---
valid_trades = pnl_df[pnl_df["Days Held"] > 0].copy()
valid_trades["Daily Return"] = valid_trades["Net PnL %"] / valid_trades["Days Held"]

mean_daily = valid_trades["Daily Return"].mean()
excess_return = mean_daily - 0.0433 / 252
std_daily = valid_trades["Daily Return"].std()
sharpe_ratio = excess_return / std_daily * np.sqrt(252) if std_daily != 0 else np.nan

print(f"Total Sharpe Ratio: {sharpe_ratio:.2f}")

if pnl_df.empty:
    print("No trades passed filters.")
else:
    print(f"Total Net PnL: ${pnl_df['Net PnL $'].sum():,.2f}")
    

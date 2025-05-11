import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from arch import arch_model
from polygon import RESTClient
from datetime import datetime, timedelta
import requests
import time

# --- API Setup and Strategy Parameters ---

# Polygon.io API key for market data
polygon_key = "MY POLYGON KEY"
fred_key = "MY FRED KEY"
client = RESTClient(polygon_key)

# Strategy configuration
ticker = "LULU"  # stock being analyzed
entry_date = datetime(2023, 11, 30)  # strategy start date
end_date = entry_date + timedelta(days=365)  # simulate 1 year forward
arima_window = 60  # lookback window for ARIMA-GARCH
signal_threshold = 2.2  # signal strength threshold to enter trades
portfolio_size = 5_000_000  # total capital allocated
txn_cost_per_share = 0.01  # assumed cost per trade per share
risk_per_trade = 0.01  # risk budget per trade (1% of portfolio)
stop_loss_pct = 0.01  # maximum loss tolerated before exiting trade

# --- Helper Functions ---

# Pulls historical daily open/close/volume data using Polygon.io
def get_price_series(ticker, from_date, to_date):
    bars = client.get_aggs(ticker, 1, "day", from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d"))
    time.sleep(0.3)  # avoid rate limiting
    data = [{
        "date": pd.to_datetime(bar.timestamp, unit='ms'),
        "open": bar.open,
        "close": bar.close,
        "volume": bar.volume
    } for bar in bars]
    df = pd.DataFrame(data)
    df.set_index("date", inplace=True)
    return df.sort_index()

# Retrieves Fed Funds rate from FRED API for calculating overnight costs
def get_fed_funds_rate(date):
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={fred_key}&file_type=json&observation_start={date:%Y-%m-%d}&observation_end={date:%Y-%m-%d}"
    try:
        r = requests.get(url).json()
        return float(r['observations'][0]['value']) / 100
    except:
        return 0.0433  # default fallback rate (approx 4.33%)

# --- Load Price Data and Compute Volatility Models ---

# Fetch historical prices and returns going back 180 days for context
full_df = get_price_series(ticker, entry_date - timedelta(days=180), end_date)

# Compute log returns and a rolling volatility estimate (20-day window)
returns = 100 * full_df["close"].pct_change().dropna()
rolling_vol = returns.rolling(window=20).std()

# Fit a GARCH(1,1) model to the returns to estimate time-varying volatility
garch_model = arch_model(returns, vol='Garch', p=1, q=1).fit(disp='off')
garch_vol = garch_model.conditional_volatility


# --- Forecast Prices with ARIMA-GARCH Model ---
# Restrict forecast to the future simulation window
plot_start = entry_date
plot_end = end_date
price_df = full_df.loc[plot_start:plot_end].copy()

forecasted_prices = []

# Loop through each date and fit a rolling ARIMA-GARCH model
for current_date in price_df.index:
    window_start = current_date - timedelta(days=arima_window * 2)
    history = full_df[:current_date]
    history = history[history.index >= window_start]

    if len(history) >= arima_window:
        try:
            # Fit AR(5) + GARCH(1,1) model on recent return window
            history_returns = 100 * history["close"].pct_change().dropna()
            model = arch_model(history_returns, mean='ARX', lags=5, vol='GARCH', p=1, q=1)
            fit = model.fit(disp='off')
            forecast = fit.forecast(horizon=1)
            mean_forecast = forecast.mean.iloc[-1, 0]

            # Translate return forecast into a price forecast
            last_price = history["close"].iloc[-1]
            forecast_price = last_price * (1 + mean_forecast / 100)
            forecasted_prices.append((current_date, forecast_price))
        except:
            forecasted_prices.append((current_date, np.nan))
    else:
        forecasted_prices.append((current_date, np.nan))

# Store forecast in price dataframe
forecast_df = pd.Series({d: f for d, f in forecasted_prices}, name="Forecast")
price_df["forecast"] = forecast_df
price_df["signal_diff"] = price_df["forecast"] - price_df["close"]


# --- Generate Trading Signals ---
# Create long/short/neutral signals based on how far the forecast deviates from current price
signal_state = []
state = 0
for diff in price_df["signal_diff"]:
    if diff > signal_threshold:
        state = 1    # long signal
    elif diff < -signal_threshold:
        state = -1   # short signal
    elif abs(diff) < 0.5:
        state = 0    # exit signal
    signal_state.append(state)

price_df["signal"] = signal_state
price_df["position"] = price_df["signal"].shift(1).fillna(0)  # trade the next day


# --- Backtest PnL Simulation with Position Sizing and Stop Loss ---
# Track PnL, returns, and equity curve
pnl_list = []
return_pct_list = []
trade_pnl_list = []

cum_pnl = 0
entry_price = None
entry_idx = None
entry_pos = 0
shares = 0

# Simulate one trading day at a time
for i in range(1, len(price_df)):
    today = price_df.index[i]
    yest = price_df.index[i - 1]
    pos = price_df.loc[yest, "position"]

    # No position: no trade
    if pos == 0:
        pnl_list.append(0)
        return_pct_list.append(0)
        trade_pnl_list.append(0)
        entry_price = None
        entry_pos = 0
        continue

    # Retrieve price and volume info
    open_price = price_df.loc[today, "open"]
    close_price = price_df.loc[today, "close"]
    volume = price_df.loc[today, "volume"]
    adv = full_df["volume"].loc[:yest].tail(20).mean()  # 20-day ADV

    if np.isnan(open_price) or np.isnan(close_price) or adv == 0:
        pnl_list.append(0)
        return_pct_list.append(0)
        trade_pnl_list.append(0)
        continue

    # If new position, calculate position size based on stop loss constraint and liquidity cap
    if entry_pos != pos:
        entry_price = open_price
        entry_idx = i
        entry_pos = pos
        max_shares = int(0.01 * adv)  # limit to 1% of ADV
        shares = min(int(risk_per_trade * portfolio_size / (open_price * stop_loss_pct)), max_shares)

    # Compute overnight cost for holding the position
    fed_rate = get_fed_funds_rate(today)
    overnight_rate = fed_rate + (0.015 if pos > 0 else 0.01)
    gross_position_value = shares * open_price
    overnight_cost = gross_position_value * overnight_rate / 252  # annualized
    txn_cost = shares * txn_cost_per_share

    # Daily PnL from open to close (based on direction)
    gross_pnl = (close_price - open_price) * shares * pos

    # Apply stop loss: cap the loss and exit if breached
    stop_loss_value = stop_loss_pct * entry_price * shares
    current_loss = (close_price - entry_price) * shares * pos * -1

    if current_loss > stop_loss_value:
        gross_pnl = -stop_loss_value
        pos = 0  # exit position

    # Net PnL after all costs
    net_pnl = gross_pnl - txn_cost - overnight_cost
    return_pct = net_pnl / gross_position_value if gross_position_value > 0 else 0

    pnl_list.append(net_pnl)
    return_pct_list.append(return_pct)
    trade_pnl_list.append(net_pnl)


# --- Finalize and Store Simulation Results ---
price_df = price_df.iloc[1:]
price_df["net_pnl"] = pnl_list
price_df["return_pct"] = return_pct_list
price_df["equity"] = price_df["net_pnl"].cumsum()


# --- Performance Metrics ---
total_return = price_df["equity"].iloc[-1]

# Use a fixed risked capital of $50,000 for Sharpe Ratio calculation
daily_returns = price_df["net_pnl"] / 50000

# Annualized Sharpe Ratio (risk-adjusted return)
sharpe = (daily_returns.mean() - (0.0433/252) / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else np.nan

# Per-trade performance metrics
non_zero_returns = price_df["return_pct"][price_df["return_pct"] != 0]
non_zero_pnls = price_df["net_pnl"][price_df["net_pnl"] != 0]
avg_return_pct = non_zero_returns.mean() * 100
avg_dollar_return = non_zero_pnls.mean()


# Print summary
print(f"Total Net PnL: ${total_return:,.2f}")
print(f"Sharpe Ratio: {sharpe:.2f}")
print(f"Trade Count: {len(non_zero_returns)}")


# --- Plot Equity Curve ---
plt.figure(figsize=(12, 5))
plt.plot(price_df.index, price_df["equity"], label="Equity Curve", linewidth=2)
plt.axhline(0, color='gray', linestyle='--')
plt.title("Net PnL – ARIMA-GARCH Strategy (LULU)")
plt.ylabel("PnL ($)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# --- PLOT FORECASTED VS ACTUAL FOR MODEL VALIDATION---
plt.figure(figsize=(12, 4))
plt.plot(price_df.index, price_df["close"], label="Actual Close")
plt.plot(price_df.index, price_df["forecast"], label="Forecast", alpha=0.7)
plt.title("Forecast vs Actual Prices")
plt.legend()
plt.tight_layout()
plt.show()
# --- END OF SCRIPT ---


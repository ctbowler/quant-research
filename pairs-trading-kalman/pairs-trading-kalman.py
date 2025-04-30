import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

# Download 5-minute data for JPM and AAPL
tickers = ['JPM', 'AAPL']
data = yf.download(tickers, interval='5m', period='60d', progress=False)
data = data.between_time('09:30', '16:00')
close_prices = data['Close']

# Prepare the data
x = close_prices['JPM'].values
y = close_prices['AAPL'].values
n = len(x)

# Ensure x and y have the same length
if len(x) != len(y):
    min_len = min(len(x), len(y))
    x = x[:min_len]
    y = y[:min_len]

# Initialize Kalman filter parameters
alpha = np.zeros(n)  # Hedge ratio (alpha)
P = np.eye(2) * 1e3  # Initial state covariance
Q = np.eye(2) * 1e-3  # Process noise covariance
R = np.array([[1e-2]])  # Measurement noise covariance
H = np.array([[x[0], 1]])  # Measurement matrix

# Initialize trading variables
entry_price_x = None  # Entry price for Asset X
entry_price_y = None  # Entry price for Asset Y
position_x = 0  # 1 for long, -1 for short, 0 for no position (Asset X)
position_y = 0  # 1 for long, -1 for short, 0 for no position (Asset Y)
entry_index = None
pnl = []
positions = []
dates = []  # Track the dates corresponding to each position

# Track capital invested
capital_invested = 0  # Track total capital invested
portfolio_size = 50000  # Total portfolio size

# Stop-loss threshold (2% of portfolio size)
stop_loss_threshold = portfolio_size * 0.02  # 2% stop-loss = $1000

# Define rolling window size for z-score calculation (e.g., 20 periods)
window_size = 20
spread_history = []

# Kalman filter loop
for t in range(1, n):
    # Prediction step
    x_pred = np.array([alpha[t-1], 0])  # Predicted state
    P_pred = P + Q

    # Measurement update step
    y_t = y[t]
    innovation = y_t - H @ x_pred
    S = H @ P_pred @ H.T + R
    K = P_pred @ H.T @ np.linalg.inv(S)
    x_upd = x_pred + K @ innovation
    P = P_pred - K @ H @ P_pred

    # Update estimates
    alpha[t] = x_upd[0]

    # Define spread and update history
    spread = y_t - (alpha[t] * x[t])
    spread_history.append(spread)

    # Calculate rolling mean and standard deviation for z-score
    if len(spread_history) >= window_size:
        rolling_mean = np.mean(spread_history[-window_size:])
        rolling_std = np.std(spread_history[-window_size:])
    else:
        rolling_mean = np.mean(spread_history)
        rolling_std = np.std(spread_history)

    # Calculate z-score
    z_score = (spread - rolling_mean) / rolling_std

    # Generate trading signals based on z-score
    if position_x == 0 and position_y == 0:  # No open position
        if z_score > 1:  # Entry signal: spread is significantly above mean
            position_x = -alpha[t]  # Short Asset X (JPM)
            position_y = 1  # Long Asset Y (AAPL)
            entry_price_x = x[t]  # Track entry price for Asset X
            entry_price_y = y[t]  # Track entry price for Asset Y
            entry_index = t
            capital_invested += abs(position_x) * entry_price_x + abs(position_y) * entry_price_y  # Capital invested
        elif z_score < -1:  # Entry signal: spread is significantly below mean
            position_x = alpha[t]  # Long Asset X (JPM)
            position_y = -1  # Short Asset Y (AAPL)
            entry_price_x = x[t]  # Track entry price for Asset X
            entry_price_y = y[t]  # Track entry price for Asset Y
            entry_index = t
            capital_invested += abs(position_x) * entry_price_x + abs(position_y) * entry_price_y  # Capital invested
    elif position_x > 0 and position_y == -1:  # Long Asset X, Short Asset Y
        # Check for stop-loss
        unrealized_loss = abs(position_x) * (x[t] - entry_price_x) + abs(position_y) * (y[t] - entry_price_y)
        if unrealized_loss > stop_loss_threshold:  # Stop-loss threshold
            pnl.append(-unrealized_loss)  # Stop-loss exit
            positions.append((entry_index, t, 'Stop-Loss Exit', -unrealized_loss))
            dates.append(data.index[t])  # Track the date
            position_x = 0
            position_y = 0
            entry_price_x = None
            entry_price_y = None
            entry_index = None
        elif z_score > 0:  # Exit signal: spread has reverted to mean
            pnl.append((x[t] - entry_price_x) * alpha[t] - (entry_price_y - y[t]) * alpha[t])  # PnL for Asset X and Asset Y
            positions.append((entry_index, t, 'Long X, Short Y', (x[t] - entry_price_x) * alpha[t] - (entry_price_y - y[t]) * alpha[t]))
            dates.append(data.index[t])  # Track the date
            position_x = 0
            position_y = 0
            entry_price_x = None
            entry_price_y = None
            entry_index = None
    elif position_x < 0 and position_y == 1:  # Short Asset X, Long Asset Y
        # Check for stop-loss
        unrealized_loss = abs(position_x) * (entry_price_x - x[t]) + abs(position_y) * (y[t] - entry_price_y)
        if unrealized_loss > stop_loss_threshold:  # Stop-loss threshold
            pnl.append(-unrealized_loss)  # Stop-loss exit
            positions.append((entry_index, t, 'Stop-Loss Exit', -unrealized_loss))
            dates.append(data.index[t])  # Track the date
            position_x = 0
            position_y = 0
            entry_price_x = None
            entry_price_y = None
            entry_index = None
        elif z_score < 0:  # Exit signal: spread has reverted to mean
            pnl.append((entry_price_x - x[t]) * alpha[t] - (y[t] - entry_price_y) * alpha[t])  # PnL for Asset X and Asset Y
            positions.append((entry_index, t, 'Short X, Long Y', (entry_price_x - x[t]) * alpha[t] - (y[t] - entry_price_y) * alpha[t]))
            dates.append(data.index[t])  # Track the date
            position_x = 0
            position_y = 0
            entry_price_x = None
            entry_price_y = None
            entry_index = None

# Calculate cumulative PnL
cumulative_pnl = np.cumsum(pnl)

# **1. Compute Return Percentage**
final_pnl = cumulative_pnl[-1]
return_percentage = (final_pnl / capital_invested) * 100  # Based on capital invested
print(f"Return Percentage: {return_percentage:.2f}%")

# **2. Compute Sharpe Ratio**
daily_returns = np.diff(cumulative_pnl)  # Daily returns
mean_daily_return = np.mean(daily_returns)
std_daily_return = np.std(daily_returns)
sharpe_ratio = (mean_daily_return / std_daily_return) * np.sqrt(252)
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")

# Plot results
plt.figure(figsize=(14, 6))

# Plot hedge ratio (alpha)
plt.subplot(2, 1, 1)
plt.plot(data.index[1:], alpha[1:], label='Hedge Ratio (alpha)', color='blue')
plt.title('Dynamic Hedge Ratio (Kalman Filter)')
plt.xlabel('Time')
plt.ylabel('Hedge Ratio')
plt.legend()
plt.grid()

# Plot cumulative PnL
plt.subplot(2, 1, 2)
plt.plot(dates, cumulative_pnl, label='Cumulative PnL', color='green')  # Use `dates` for x-axis
plt.title('Cumulative Profit and Loss')
plt.xlabel('Time')
plt.ylabel('Cumulative PnL')
plt.legend()
plt.grid()

plt.tight_layout()
plt.show()

# Display trade details
for trade in positions:
    print(f"Trade from {data.index[trade[0]]} to {data.index[trade[1]]}: {trade[2]} position, PnL = {trade[3]:.2f}")

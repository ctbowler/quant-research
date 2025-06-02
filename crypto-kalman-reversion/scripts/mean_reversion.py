import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from ta.momentum import RSIIndicator

def backtest_kalman_single_asset(price, Q, R, z_thresh, rsi_entry, stop_loss_pct=0.05, capital=5000, window_size=30, plot=True):
    from ta.momentum import RSIIndicator
    import numpy as np
    import matplotlib.pyplot as plt

    # === Kalman Filter Mean Estimation ===
    n = len(price)
    kf_mean = np.zeros(n)
    P = 1.0
    kf_mean[0] = price.iloc[0]

    for t in range(1, n):
        pred = kf_mean[t - 1]
        P += Q
        K = P / (P + R)
        kf_mean[t] = pred + K * (price.iloc[t] - pred)
        P = (1 - K) * P

    # === Indicators ===
    spread = price - kf_mean
    spread_z = (spread - spread.rolling(window_size).mean()) / spread.rolling(window_size).std()
    rsi = RSIIndicator(close=price, window=14).rsi()

    # === Trading Logic ===
    position = 0
    entry_price = 0
    capital_invested = 0
    pnl = []
    positions = []
    dates = []

    for t in range(window_size, len(price)):
        p = price.iloc[t]
        z = spread_z.iloc[t]
        r = rsi.iloc[t]

        if position == 0 and z < -z_thresh and r < rsi_entry:
            entry_price = p
            position = capital / p
            capital_invested += capital
            entry_index = t
        elif position > 0:
            unrealized_pnl = (p - entry_price) * position
            unrealized_loss = -unrealized_pnl
            if p > kf_mean[t] or unrealized_loss > capital * stop_loss_pct:
                pnl.append(unrealized_pnl)
                positions.append((entry_index, t, unrealized_pnl))
                dates.append(price.index[t])
                position = 0

    # === Performance ===
    cumulative_pnl = np.cumsum(pnl)
    final_pnl = cumulative_pnl[-1] if len(cumulative_pnl) else 0
    return_pct = (final_pnl / capital_invested) * 100 if capital_invested else 0
    sharpe = 0
    if len(pnl) > 1:
        daily_returns = np.diff(cumulative_pnl)
        sharpe = (np.mean(daily_returns) / np.std(daily_returns)) * np.sqrt(252)

    # === Plot ===
    if plot and pnl:
        trade_dates = [price.index[end] for (_, end, _) in positions]
        plt.figure(figsize=(14, 4))
        plt.plot(trade_dates, cumulative_pnl, label='Cumulative PnL', color='purple')
        plt.title("Cumulative PnL Over Time [AVAX/USD]")
        plt.xlabel("Time")
        plt.ylabel("PnL ($)")
        plt.grid()
        plt.legend()
        plt.tight_layout()
        plt.show()

    return {
        "final_pnl": final_pnl,
        "return_pct": return_pct,
        "sharpe": sharpe,
        "trades": len(pnl),
        "pnl_curve": cumulative_pnl
    }

# Run Grid Search for Parameter Optimization
df = pd.read_csv(r"PATH", index_col=0, parse_dates=True)
price_series = df["AVAX/USD"].dropna()
results = backtest_kalman_single_asset(price_series, Q=0.0001, R=0.001, z_thresh=1, rsi_entry=30)
print(results['sharpe'])

"""
import itertools
import pandas as pd
from tqdm import tqdm

# Define parameter ranges
q_values = [1e-5, 1e-4, 1]
r_values = [0.001, 0.01, 1]
z_thresholds = [0.8, 1.0, 1.2]
rsi_levels = [30, 35, 40]

# Cartesian product of all combinations
param_grid = list(itertools.product(q_values, r_values, z_thresholds, rsi_levels))


results_list = []

for Q, R, z_thresh, rsi_entry in tqdm(param_grid, desc = "optimizing parameters"):
    # Run backtest with current parameter combination
    res = backtest_kalman_single_asset(
        price_series,
        Q=Q,
        R=R,
        z_thresh=z_thresh,
        rsi_entry=rsi_entry,
        plot=False
    )
    results_list.append({
        "Q": Q,
        "R": R,
        "z_thresh": z_thresh,
        "rsi_entry": rsi_entry,
        "Sharpe": res["sharpe"],
        "Return %": res["return_pct"],
        "PnL": res["final_pnl"],
        "Trades": res["trades"]
    })

# Convert to DataFrame for sorting/filtering
grid_results = pd.DataFrame(results_list)

# Sort by Sharpe or Return %
top_by_sharpe = grid_results.sort_values(by="Sharpe", ascending=False).head(10)
top_by_return = grid_results.sort_values(by="Return %", ascending=False).head(10)

print("Top by Sharpe:")
print(top_by_sharpe)

print("\nTop by Return %:")
print(top_by_return)
"""
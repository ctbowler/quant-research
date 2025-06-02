# 🔁 Crypto Kalman Filter Mean Reversion Strategy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
---

### 🕮 **Overview**

This project implements a **Kalman filter-based mean reversion strategy** applied to cryptocurrencies. Inspired by statistical arbitrage techniques used in equities, the goal is to identify short-term undervaluation of an asset relative to its dynamically estimated fair value and capture returns as it reverts back.

The strategy is applied to **single assets**, not pairs, using:

- **Kalman Filter** to estimate an adaptive price mean,  
- **Z-score of price deviations** from the mean to trigger trades,  
- **RSI filtering** to reduce trades during strong downward momentum,
- **$5000** portfolio value.
- **Stop-loss logic** to contain adverse moves. A maximum of 5% of our portfolio is risked.

Both **backtests** and **live paper trading simulations** are included.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
---

### 📐 **Strategy Motivation and Design**

Traditional mean reversion strategies rely on fixed moving averages or Bollinger Bands. This project explores a **Kalman filter** approach — a recursive algorithm that continuously estimates a latent state (in this case, a price mean) based on noisy observations.

By combining the Kalman filter with a **rolling z-score** and **RSI momentum filter**, this strategy attempts to isolate statistically significant price dips that are also oversold, offering high-probability bounce scenarios.

> 🔍 Entry occurs when price is far below the Kalman mean (z-score < –1) **and** RSI < 30.  
> 💰 Exit is triggered when price reverts to mean **or** drawdown exceeds 5%.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
---

### 🧪 **Pipeline Workflow**

1. **Filter Top Liquid Coins**  
   - Uses Alpaca's historical crypto data to compute dollar volume.  
   - Keeps top 20 most liquid coins over a 4-month lookback.  
   - Outliers with extreme volatility or data gaps are dropped.

2. **Backtest Kalman Strategy on Each Coin**  
   - Run `mean_reversion.py` to simulate the Kalman-RSI strategy over historical prices.  
   - Use grid search to tune hyperparameters (Q, R, z-threshold, RSI).  
   - Evaluate by Sharpe Ratio, Return %, and PnL.

3. **Live Paper Trading via Alpaca**  
   - Price data from **Binance** (5-minute candles)  
   - Trade execution via **Alpaca** paper account  
   - Order logic uses limit buys and market exits  
   - Trade logs and PnL stored in local CSVs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
---

### 💻 **Codebase Overview**

| File                     | Description |
|--------------------------|-------------|
| `filter_liquidity.py`    | Filters top 20 coins by 4-month average dollar volume from Alpaca API |
| `mean_reversion.py`      | Kalman mean estimator + backtester with z-score/RSI entry and stop-loss exits |
| `paper_trader.py`        | Real-time Alpaca trader using Binance prices and Alpaca order placement |
| `constants.py`           | Centralizes date, API keys, and global parameters for filtering and backtests |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
---

### 📊 **Backtest Results (Top Coins by Sharpe)**

Test Period: `Jan 3, 2024` — `Apr 3, 2024`  
Capital per coin: `$5,000`  

| Coin | Sharpe Ratio | Return % | Trades |
|------|--------------|----------|--------|
| LTC  | **1.58**     | 23.4%    | 9      |
| AAVE | **1.38**     | 18.7%    | 7      |
| LINK | 1.13         | 16.4%    | 6      |
| DOGE | 0.47         | 5.1%     | 4      |
| ETH  | -0.15        | -2.9%    | 2      |

📈 Visuals:
<p align="center">
  <img src="plots/LTC_backtest.png" width="800">
  <br>
  <em>Figure 1: LTC/USD backtest — Kalman PnL curve</em>
</p>

### 📌 Key Observations
- High performers (LTC, AAVE, LINK) exhibited **frequent, clean oscillations** around the Kalman mean — ideal for reversion strategies.
- Poor performers like ETH and DOGE often **trended through** the estimated mean or **whipsawed** violently, producing false signals.
- RSI helped avoid entries during strong downward momentum, improving risk control.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
---

### 🧠 **Kalman Filter Logic**

The Kalman filter recursively estimates a latent price mean:

```math
μₜ = μₜ₋₁ + Kₜ(pₜ − μₜ₋₁),  
Kₜ = Pₜ / (Pₜ + R),  
Pₜ = (1 − Kₜ)Pₜ + Q

# 🧠 Kalman Filter-Based Crypto Mean Reversion Strategy

This project implements a systematic **mean reversion trading strategy** for cryptocurrencies using an **adaptive Kalman filter** to estimate the evolving fair value (local mean) of asset prices.

> 📈 "When price drifts below a statistically inferred fair value and momentum confirms oversold conditions — buy and wait for the bounce."

## 🔧 Strategy Summary

This strategy:
- Applies a **Kalman filter** to estimate a time-varying mean of crypto prices.
- Computes a **z-score** of the spread between price and estimated mean.
- Confirms entries using **RSI** to avoid false signals in trending regimes.
- Exits positions once price mean-reverts or triggers a stop-loss.

Used for both **historical backtests** and a **live paper trading simulation** via the Alpaca API.

---

## 📂 Project Structure

```bash
.
├── filter_liquidity.py        # Selects top-liquid coins from Alpaca
├── mean_reversion.py          # Backtester with Kalman filter + RSI strategy
├── paper_trader.py            # Live paper trading engine (Alpaca + Binance price feed)
├── constants.py               # Centralized parameters and date ranges
├── data/                      # Folder for saved price and volume data
├── results/                   # Folder for strategy performance outputs
└── plots/                     # Visual PnL charts (to be added)

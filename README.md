# 📊 Quantitative Finance Research Portfolio

This repository showcases research projects in **quantitative finance**, **algorithmic trading**, and **stochastic modeling**. Each folder contains a self-contained analysis or strategy, focused on simulation-based methods, time series models, and financial signal interpretation.

All Sharpe ratios below reflect **out-of-sample backtesting** only — no real capital was deployed. Full writeups and code are included in each folder.

---

## 🔍 Project Highlights

### Crypto Mean Reversion + Paper Trader  
**Sharpe varies by coin**  
- Mean reversion strategy using Kalman-filtered dynamic mean estimation  
- Alpha signals generated from z-scores and RSI  
- Backtested on 4 crypto assets  
- Includes a paper trading script integrated with Alpaca

---

### Index Inclusion Strategies  

**AR-GARCH Forecasting**  
**Sharpe = 2.75**  
- Time series modeling of returns and volatility post-index inclusion  
- Combines AR and GARCH models to predict short-term movements

**Momentum on Inclusions**  
**Sharpe = 2.99**  
- Event-driven strategy using z-score thresholds and flow data  
- Targets momentum bursts after S&P 500 additions

---

### Passive Momentum Strategy  
**Sharpe = 1.74**  
- Long-only cross-sectional momentum with 12-month holding period  
- Filters by liquidity, beta, return smoothness, and 2–12 month momentum  
- Tested across two market regimes (uptrend & drawdown)

---

### Kalman Pairs Trading  
**Sharpe = 2.66**  
- Statistical arbitrage using Kalman filter for dynamic hedge ratio estimation  
- Mean-reverting spread modeled and traded using z-score thresholds

---

### IMC Prosperity Trading Competition  
[View Repo →](https://github.com/ctbowler/prosperity3-trading)  
- Live competition codebase with trading logic across:  
  - Market making  
  - Options pricing (Black-Scholes)  
  - Spread trading  
  - Multi-asset momentum

---

### Heston vs Black-Scholes Volatility Models  
*No Sharpe — model analysis only*  
- Monte Carlo simulation comparing option prices and vol surfaces  
- Highlights differences between stochastic (Heston) and constant (B-S) volatility assumptions

---

## 🧰 Tools & Stack
- Python (NumPy, pandas, matplotlib, statsmodels, `ta`, scikit-learn)
- Jupyter notebooks for writeups and visualizations
- Alpaca API for live market integration

---

## 📎 Purpose
This portfolio was built to showcase applied research in quant finance and is intended for use in job applications across:
- Quantitative trading / research  
- Financial engineering  
- Systematic strategy development

---


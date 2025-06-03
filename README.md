# 📊 Quantitative Trading Strategies

This repository showcases research projects in **quantitative finance**, **algorithmic trading**, and **systems development**. Each folder contains a self-contained analysis or strategy, focused on simulation-based methods, time series models, and financial signal interpretation.

All Sharpe ratios below reflect **out-of-sample backtesting** only — no real capital was deployed. Full writeups and code are included in each folder.

---

## 🔶 Project Highlights

### 🔹 Crypto Mean Reversion + Paper Trader  
**Sharpe varies by coin**  
- Mean reversion strategy using Kalman-filtered dynamic mean estimation  
- Alpha signals generated from z-scores and RSI  
- Backtested on 5 crypto assets  
- Includes a paper trading script integrated with Alpaca
- [Link](https://github.com/ctbowler/quant-research/tree/master/crypto-kalman-reversion)
---

### 🔹 Index Inclusion Strategies  

**AR-GARCH Forecasting**  
**Sharpe = 2.75**  
- Time series modeling of returns and volatility post-index inclusion  
- Combines AR and GARCH models to predict short-term movements
- [Link](https://github.com/ctbowler/quant-research/tree/master/index-inclusion-strategies/ar-garch-forecasting)
- 
**Momentum on Inclusions**  
**Sharpe = 2.99**  
- Event-driven strategy using z-score thresholds and flow data  
- Targets momentum bursts after S&P 500 additions
- [Link](https://github.com/ctbowler/quant-research/tree/master/index-inclusion-strategies/momentum-trading)

---

### 🔹 Passive Momentum Strategy  
**Sharpe = 1.74**  
- Long-only cross-sectional momentum with 12-month holding period  
- Filters by liquidity, beta, return smoothness, and 2–12 month momentum  
- Tested across two market regimes (uptrend & drawdown)
- [Link](https://github.com/ctbowler/quant-research/tree/master/passive-momentum)
---

### 🔹 Kalman Pairs Trading  
**Sharpe = 2.66**  
- Statistical arbitrage using Kalman filter for dynamic hedge ratio estimation  
- Mean-reverting spread modeled and traded using z-score thresholds
- [Link](https://github.com/ctbowler/quant-research/tree/master/pairs-trading-kalman)
---

### 🔹 IMC Prosperity Trading Competition  
- Live competition codebase with trading logic across:  
  - Market making  
  - Options pricing (Black-Scholes)  
  - Spread trading  
  - Multi-asset momentum
 
  [View Repo →](https://github.com/ctbowler/prosperity3-trading)  


---

### 🔹 Heston vs Black-Scholes Volatility Models  
*No Sharpe — model analysis only*  
- Monte Carlo simulation comparing option prices and vol surfaces  
- Highlights differences between stochastic (Heston) and constant (B-S) volatility assumptions
- [Link](https://github.com/ctbowler/quant-research/tree/master/options/heston-vs-bsm-volatility)
---

## 🔶 Systems & Infrastructure Projects

### 🔹 Low-Latency C++ Crypto Trading Engine  
**Real-time Coinbase GUI with custom order book and candlestick charting**  
- Built in **C++20** with ImGui + OpenGL for low-latency visualization  
- Uses **shared memory (`mmap`)** to stream real-time order book + trade data from a Python WebSocket client  
- Implements custom **OrderBook**, **PriceBuffer**, and **CandleBuffer** data structures for efficient constant-time access  
- Tick rate decoupled from GUI — user-defined update frequency (e.g., 10ms)  
- Designed for **high-frequency market simulation**, with modular components and threading for order parsing, rendering, and memory I/O  
- Optimized for <1ms latency if upgraded to a native C++ WebSocket client  

[Link →](https://github.com/ctbowler/quant-research/tree/master/low-latency-crypto-engine)


---

## 🔶 Purpose
This portfolio was built to showcase applied research in quant finance and is intended for use in job applications across:
- Quantitative trading / research  
- Financial engineering  
- Systematic strategy development

---


# 📊 Quantitative Finance Research Portfolio

This repository presents a curated collection of research projects in quantitative finance, algorithmic trading, and stochastic modeling. Each folder contains a self-contained analysis or trading strategy with a focus on simulation-based methods, time series modeling, and financial signal interpretation. All listed Sharpe ratios come from backtesting. 

## 🧠 Project Highlights

- **Kalman Filter-Based Pairs Trading (Sharpe = 2.66)**  
  Dynamic hedge ratio estimation using a Kalman filter for spread-based statistical arbitrage.

- **Index Inclusion Strategies**
  *AR-GARCH Forecasting for Index Additions (Sharpe = 2.75): Time series modeling of returns and volatility following index inclusion events using AR and GARCH models.*
  *Momentum Trading on Index Additions (Sharpe = 2.99): Event-driven momentum strategy leveraging z-score thresholds and trade flow data for signal generation*

- **Crypto Mean Reversion + Paper Trading Bot**
  Simualated mean reversion strategy that aims to profit off volatilty clustering and swing dynamics for intraday trading over a single quarter. A kalman filter was used to dynamically estimate the mean of an asset over a rolling window. Z-scores and RSI were used to generate alpha signals, and out-of-sample backtests were perforemd for 4 different coins. 

- **IMC Prosperity Competition**
  https://github.com/ctbowler/prosperity3-trading
  This repository contains my trading algorithms developed for the IMC Prosperity Trading Competition. Strategies focus on options (Black-Scholes), market making, spread trading, and multi-asset momentum detection across a range of structured products.
  
- **Heston vs Black-Scholes Volatility Modeling**  
  Monte Carlo simulation comparing option pricing and implied volatility surfaces under stochastic (Heston) and constant (Black-Scholes) volatility models. No backtesting, purely for model analysis and understanding. 


  

Each project includes Python code, visualizations, and brief write-ups focused on the core modeling techniques and their applications in trading, pricing, or risk forecasting.

---

📎 Designed for research, portfolio building, and job applications in quantitative trading, research, or financial engineering.


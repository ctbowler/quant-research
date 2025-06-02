# 📈 Alpha Inclusion Strategies

This directory contains two distinct trading strategies designed to exploit price distortions around stock **index inclusion events** — moments when stocks are added to major indices like the S&P 500 or S&P 600. These events often trigger **predictable flows from passive funds**, creating exploitable opportunities for informed traders.

Both strategies leverage **alternative alpha signals** and risk-aware execution models. While they differ in trade structure and frequency, they share a common goal: capturing excess return from flow-driven dislocations around index events.

---

## 📂 Strategy Summaries

### `momentum_index_additions/`
A cross-sectional momentum strategy targeting S&P 600 additions. It ranks stocks by their announcement-to-open return and filters using a z-score relative to peer flow-driven names. Long-only by default, but applies short filters for extreme negative momentum. All trades are hedged using cointegrated ETFs to isolate idiosyncratic flow effects.

- **Holding period:** announcement to 1 day before inclusion  
- **Sharpe Ratio:** 2.99  
- **Capital:** $5M with tight stop-loss rules  
- **Event-driven, diversified across many stocks and sectors**

---

### `ar_garch_index_additions/`
A high-frequency forecasting strategy using a rolling **AR(5)-GARCH(1,1)** model on a single large-cap inclusion stock (LULU). It captures intraday dislocations caused by post-inclusion price pressure. Signals are generated daily, with 1-day holding periods and directional trades based on forecast error thresholds.

- **Holding period:** 1 day  
- **Sharpe Ratio:** 2.75  
- **Trades:** 125 across the year  
- **Single-stock, volatility-driven strategy**

---

## 🧠 Why These Strategies Matter

Inelastic market behavior — where price is disproportionately affected by large flow imbalances — makes inclusion events especially attractive for short-term alpha generation. These strategies are designed to test that hypothesis from different angles: **cross-sectional momentum** and **time-series volatility modeling**.

Each project is self-contained, with full code, data handling, and backtesting logic.

---

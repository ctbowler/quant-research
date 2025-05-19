**Momentum Strategy Backtest and RSI Filter Analysis**

---

### **Overview**

This project explores a core hypothesis from [Alpha Architect](https://alphaarchitect.com/): that **momentum strategies** can deliver superior risk-adjusted returns by selecting stocks with strong recent performance while **filtering out short-term mean-reverting noise**. Specifically, we aim to test whether **avoiding crowded or "overbought" trades using RSI logic** improves long-term momentum execution.

Two different portfolio entry points are analyzed:

1. **January 3, 2024** — momentum strategy initiated during a broad market uptrend
2. **May 2024** — strategy initiated during a market reversion phase (drawdown scenario)

We simulate performance under two conditions:

* **Unfiltered**: Hold all positions until the end of the test period
* **RSI-filtered**: Drop positions if momentum decays despite recent gains (30d return > 0 but RSI < 50)

The benchmark is the SPDR S\&P 500 ETF Trust (SPY), used to contextualize relative performance and volatility.

---

### **Strategy Motivation and Ideology**

The strategy is inspired by the quantitative research of **Alpha Architect**, particularly their insights into "momentum crashes" and **investor crowding risk**. In their work, they argue that many investors naively chase past winners — leading to **overbought conditions**, sharp reversals, and **poor short-term timing**. The key idea here is that **recent winners** with strong price momentum but weakening RSI signals may represent **unsustainable trades due for reversion**.

Thus, our process includes:

* Ranking stocks by recent momentum (e.g., past 3–6 month returns)
* Investing in a fixed-weight long-only portfolio
* Monitoring **post-entry RSI + 30-day return**, and **exiting if signs of reversal appear**
* **Not reallocating capital** after exit — reflecting a conservative real-world scenario where idle capital may sit in cash or treasuries

We believe this framework reflects a realistic test of Alpha Architect’s ideas, and allows us to evaluate **when** and **why** momentum trades fail.

---

### **Portfolio Construction**

#### **Ticker Selection**

Filtered tickers were selected based on prior momentum rankings (e.g. past 3–6 month return and volume filters). The selected tickers were saved to `portfolio_investment.csv` with their respective weights and latest prices at the entry date.

#### **Initial Capital**

\$1,000,000 equally weighted across selected stocks using the weights in `portfolio_investment.csv`.

#### **Data Source**

All price data was pulled from **Polygon.io** using the REST API with the endpoint:

```python
client.get_aggs(ticker, 1, "day", start_date, end_date)
```

---

### **RSI Exit Filter**

After entry, positions were held until either:

* The end of the backtest period
* A custom RSI-based exit signal triggered

#### **Exit Logic**

After holding for 3 months:

* If 30-day return is positive **and** RSI < 50:

  * Exit position (stop tracking further gains/losses)

#### **RSI Calculation**

```math
\text{RSI} = 100 - \frac{100}{1 + RS},
```

where:

* $RS = \frac{\text{avg gain (14d)}}{\text{avg loss (14d)}}$

Exits were **not** rebalanced across remaining positions. Proceeds were held in cash (not reinvested), ensuring conservative capital assumptions.

---

### **Performance Metrics**

The following metrics were used:

* **Cumulative Return:**

```math
R_t = \sum_i w_i \cdot \left( \frac{P_{i,t}}{P_{i,0}} - 1 \right)
```

* **Portfolio Value:**

```math
V_t = V_0 \cdot (1 + R_t)
```

* **Volatility:** 30-day rolling standard deviation of daily returns
* **Benchmark:** SPY ETF performance over the same period

---

### **Results Summary**

#### **1. Entry on January 3, 2024**

**Unfiltered Portfolio:**

* **Cumulative Return:** \~48%
* **Final Value:** \~\$1.48M
* **Volatility:** Elevated but trending with SPY

**RSI-Filtered Portfolio:**

* **Cumulative Return:** Peaked early, declined sharply after exits
* **Final Value:** Flatlined after majority exits
* **Observation:** Proceeds from exits were not reallocated, causing underperformance in later months

**SPY:**

* **Cumulative Return:** \~27%
* **Final Value:** \~\$1.27M

![Unfiltered Portfolio vs SPY](unfiltered_portfolio.png)

#### **2. Entry in May 2024 (During Reversion)**

*(Analysis in progress)*

* Initial results show reduced momentum persistence
* Filtering may help reduce post-entry whipsaws

---

### **Key Learnings**

* Momentum strategies can outperform in rising markets
* RSI filtering may be too aggressive and lead to premature exits
* Not reallocating capital after exits significantly impacts long-term performance
* Unfiltered portfolios held through volatility tend to perform better in uptrending environments

---

### **Future Improvements**

* Add **partial reallocation** logic post-exit
* Explore **different RSI thresholds** (e.g., 40, 30)
* Use **EMA or trend filters** alongside RSI
* Evaluate **sector-neutral** portfolio construction
* Include **Sharpe ratio**, **max drawdown**, and **Calmar ratio** in metrics

---

### **References**

* [Alpha Architect Blog](https://alphaarchitect.com/): Inspiration for momentum ranking logic
* [Polygon.io API Docs](https://polygon.io/docs/)
* [RSI - Investopedia](https://www.investopedia.com/terms/r/rsi.asp)
* Jegadeesh & Titman (1993): "Returns to Buying Winners and Selling Losers"

---

### **File Structure**

```
📂 momentum/
├── portfolio_investment.csv           # Tickers and weights
├── cumulative_returns_unfiltered.csv  # Jan 3, 2024 portfolio performance
├── cumulative_returns_rsi_filtered.csv
├── spy_daily_returns.csv              # SPY benchmark
├── rsi_exit_log.csv                   # Exit dates per ticker
└── plots/
    ├── unfiltered_portfolio.png
    ├── volatility_vs_returns.png
```

---

### **Contact**

If you'd like to discuss or extend this project, feel free to reach out or open an issue!

# Kalman Filter-Based Pairs Trading Strategy

This repository implements a **cointegration-based pairs trading strategy** using a **Kalman Filter** to dynamically estimate the hedge ratio between two stocks (JPM and AAPL). The strategy uses **spread mean reversion** to generate trading signals and includes **risk management** via a stop-loss mechanism.

---

## Strategy Overview

- **Assets**: JPMorgan Chase (JPM) and Apple Inc. (AAPL)
- **Data**: 5-minute bar data over the past 60 trading days
- **Approach**:
  - Use a Kalman filter to track the time-varying hedge ratio `αₜ`
  - Compute the spread between the two assets
  - Use the z-score of the spread to identify entry and exit signals
  - Limit exposure to one position per asset at a time
  - Use a 2% stop-loss to cap downside risk based on a virtual portfolio size of $50,000

---

## Math and Modeling

### 1. Cointegration Verification

- Confirmed that JPM and AAPL are cointegrated using the Augmented Dickey-Fuller (ADF) test on residuals of the linear combination.
- ADF p-value was statistically significant, indicating stationarity of the spread.

### 2. Kalman Filter

- Dynamically estimates the regression:

  `yₜ = αₜ xₜ + βₜ + εₜ`

- Kalman filter tracks the time-varying `αₜ` (hedge ratio).
- State vector:

  `xₜ = [ αₜ, βₜ ]ᵀ`

The intercept term βₜ was consistently estimated as 0 throughout the Kalman filtering process, implying that the relationship between the two assets was driven by the dynamic hedge ratio αₜ.

- Matrices used:
  - `Q`: Process noise covariance
  - `R`: Measurement noise
  - `P`: State covariance (updated every step)
  

### 3. Signal Logic

- Spread:

  `Sₜ = yₜ - αₜ xₜ`

- Z-score (computed over a rolling window of 20):

  `zₜ = (Sₜ - μₜ) / σₜ`

- **Entry Conditions**:
  - Go long AAPL, short JPM if `zₜ > 1`
  - Go short AAPL, long JPM if `zₜ < -1`

- **Exit Condition**: `zₜ → 0`
- **Stop-Loss**: Triggered if unrealized loss exceeds $1000

---

## Results

- **Final Cumulative PnL**: $81
- **Sharpe Ratio**: 2.66
- **Return Estimate**: ~15% return assuming max capital deployed = $520

![kalman_pairs_trading](https://github.com/user-attachments/assets/ea0d8407-7165-4d56-8563-1de5c7cfc18d)

The large variability in the estimated hedge ratio reflects the nonstationary relationship between the assets (APPLE + JP MORGAN). Despite this behavior, the Kalman Filter algorithm successfully adapted in real time, maintaining profitability during those volatile periods. This demonstrates the power of adaptive filtering techniques like Kalman filtering in dynamic, highly non-stationary environments.


The strategy holds only one unit (scaled by `α`) per asset at a time, which limits notional exposure but keeps risk tight and consistent. This design results in relatively low nominal PnL, but the return-to-risk ratio is strong, indicating high strategy efficiency.

---

## Optimization

I experimented with **Bayesian Optimization** to tune Kalman filter parameters (`Q`, `R`, and initial `P`). Final chosen values did not affect cumulative pnl or sharpe ratio, indicating that my initial guesses were already strong.

---

## Files

- `kalman_pairs_trading.py`: Main script with full strategy and plots
- `README.md`: This file

---

## Next Steps

- Add volatility filtering
- Test with more liquid, correlated asset pairs
- Compare with static linear regression hedge ratios
- Add dynamic position sizing

---



Built by Carson Bowler. For questions or improvements, feel free to contact me! ctbowler@outlook.com


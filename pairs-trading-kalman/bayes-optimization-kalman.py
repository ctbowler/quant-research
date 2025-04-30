import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from skopt import Optimizer
from skopt.space import Real, Integer

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

# Define the backtest function with Kalman filter
def backtest_with_params(params):
    Q, R, P = params  # Unpack the parameters for Kalman filter

    alpha = np.zeros(n)  # Hedge ratio (alpha)
    P_matrix = np.eye(2) * P  # State covariance
    Q_matrix = np.eye(2) * Q  # Process noise covariance
    R_matrix = np.array([[R]])  # Measurement noise covariance
    H = np.array([[x[0], 1]])  # Measurement matrix
    
    # Track positions, PnL, and dates
    position_x = 0
    position_y = 0
    pnl = []

    # Kalman filter loop
    for t in range(1, n):
        x_pred = np.array([alpha[t-1], 0])  # Predicted state
        P_pred = P_matrix + Q_matrix

        # Measurement update step
        y_t = y[t]
        innovation = y_t - H @ x_pred
        S = H @ P_pred @ H.T + R_matrix
        K = P_pred @ H.T @ np.linalg.inv(S)
        x_upd = x_pred + K @ innovation
        P_matrix = P_pred - K @ H @ P_pred

        alpha[t] = x_upd[0]  # Update hedge ratio

        # Spread and trading signals
        spread = y_t - (alpha[t] * x[t])
        
        # Entry/Exit signals based on z-score
        if position_x == 0 and position_y == 0:  # No open position
            if spread > 1:  # Entry signal: spread is significantly above mean
                position_x = -int(alpha[t])  # Short Asset X (JPM)
                position_y = 1   # Long Asset Y (AAPL)
                entry_price_x = x[t]
                entry_price_y = y[t]
            elif spread < -1:  # Entry signal: spread is significantly below mean
                position_x = int(alpha[t])  # Long Asset X (JPM)
                position_y = -1  # Short Asset Y (AAPL)
                entry_price_x = x[t]
                entry_price_y = y[t]
        elif position_x > 0 and position_y == -1:  # Long X, Short Y
            if spread < 0:  # Exit signal: spread has reverted to mean
                pnl.append((x[t] - entry_price_x) * alpha[t] - (entry_price_y - y[t]) * alpha[t])
                position_x = 0
                position_y = 0
        elif position_x < 0 and position_y == 1:  # Short X, Long Y
            if spread > 0:  # Exit signal: spread has reverted to mean
                pnl.append((entry_price_x - x[t]) * alpha[t] - (y[t] - entry_price_y) * alpha[t])
                position_x = 0
                position_y = 0

    # Return final cumulative PnL for optimization
    return np.sum(pnl)  # Total PnL for optimization

# Define the search space for Q, R, and P
search_space = [
    Real(1e-6, 1e-2, prior='uniform', name='Q'),  # Process noise covariance
    Real(1e-3, 1e-1, prior='uniform', name='R'),  # Measurement noise covariance
    Integer(1e2, 1e4, name='P'),  # Initial covariance matrix (as an integer)
]

# Set up the optimizer (Bayesian Optimization)
opt = Optimizer(
    dimensions=search_space,  # Define the parameter space
    acq_func='EI',  # Expected Improvement acquisition function
    n_initial_points=5,  # Number of initial random points
    random_state=42
)

# Run the optimization process
n_iter = 50  # Number of iterations for optimization
for i in range(n_iter):
    # Suggest the next set of parameters to try
    next_params = opt.ask()

    # Evaluate the performance of the suggested parameters
    performance = backtest_with_params(next_params)
    
    # Tell the optimizer the result of this evaluation
    opt.tell(next_params, performance)

# Get the best parameters and performance
print(f"Best Parameters: {opt.Xi[np.argmin(opt.yi)]}")
import numpy as np

print(f"Best Performance (PnL): {-np.min(opt.yi)}")  # Using np.min() on the list

# You can now re-run the strategy with the optimized parameters

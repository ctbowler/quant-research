# heston_vs_bsm_iv.py

import numpy as np
import matplotlib.pyplot as plt
from math import log, sqrt
from scipy.stats import norm as NormalDist

# --- PARAMETERS ---
S0 = 100
T = 1.0
r = 0.01
M = 1000
N = 252
dt = T / N
strikes = np.linspace(60, 140, 40)

# --- HESTON PARAMETERS ---
v0 = 0.04
kappa = 2.0
theta = 0.04
sigma = 0.5
rho = -0.7

# --- BLACK-SCHOLES CLASS ---
class BlackScholes:
    @staticmethod
    def black_scholes_call(spot, strike, time_to_expiry, volatility):
        d1 = (log(spot / strike) + 0.5 * volatility**2 * time_to_expiry) / (volatility * sqrt(time_to_expiry))
        d2 = d1 - volatility * sqrt(time_to_expiry)
        return spot * NormalDist().cdf(d1) - strike * NormalDist().cdf(d2)

    @staticmethod
    def black_scholes_put(spot, strike, time_to_expiry, volatility):
        d1 = (log(spot / strike) + 0.5 * volatility**2 * time_to_expiry) / (volatility * sqrt(time_to_expiry))
        d2 = d1 - volatility * sqrt(time_to_expiry)
        return strike * np.exp(-r * time_to_expiry) * NormalDist().cdf(-d2) - spot * NormalDist().cdf(-d1)

    @staticmethod
    def implied_volatility(call_price, spot, strike, time_to_expiry, max_iterations=100, tolerance=1e-5):
        low_vol = 0.01
        high_vol = 6
        volatility = 0.5 * (low_vol + high_vol)
        for _ in range(max_iterations):
            estimated_price = BlackScholes.black_scholes_call(spot, strike, time_to_expiry, volatility)
            diff = estimated_price - call_price
            if abs(diff) < tolerance:
                break
            if diff > 0:
                high_vol = volatility
            else:
                low_vol = volatility
            volatility = 0.5 * (low_vol + high_vol)
        return volatility

# --- STEP 1: SIMULATE HESTON PATHS ---
S = np.zeros((M, N+1))
v = np.zeros((M, N+1))
S[:, 0] = S0
v[:, 0] = v0

for t in range(N):
    Z1 = np.random.normal(size=M)
    Z2 = np.random.normal(size=M)
    dW_v = np.sqrt(dt) * Z1
    dW_S = np.sqrt(dt) * (rho * Z1 + np.sqrt(1 - rho**2) * Z2)

    v[:, t+1] = np.abs(v[:, t] + kappa * (theta - v[:, t]) * dt + sigma * np.sqrt(v[:, t]) * dW_v)
    S[:, t+1] = S[:, t] * np.exp((r - 0.5 * v[:, t]) * dt + np.sqrt(v[:, t]) * dW_S)

S_T = S[:, -1]

# --- STEP 2: HESTON PRICING ---
call_prices_heston = []
put_prices_heston = []

for K in strikes:
    call_payoffs = np.maximum(S_T - K, 0)
    put_payoffs = np.maximum(K - S_T, 0)
    call_price = np.exp(-r * T) * np.mean(call_payoffs)
    put_price = np.exp(-r * T) * np.mean(put_payoffs)
    call_prices_heston.append(call_price)
    put_prices_heston.append(put_price)

# --- STEP 3: Realized Vol ---
log_returns = np.log(S[:, 1:] / S[:, :-1])
realized_vol = np.mean(np.std(log_returns, axis=1)) * np.sqrt(252)

# --- STEP 4: BSM Pricing and Implied Vol ---
call_prices_bsm = [BlackScholes.black_scholes_call(S0, K, T, realized_vol) for K in strikes]


call_iv_heston = [BlackScholes.implied_volatility(price, S0, K, T) for K, price in zip(strikes, call_prices_heston)]
call_iv_bsm = [BlackScholes.implied_volatility(price, S0, K, T) for K, price in zip(strikes, call_prices_bsm)]


# --- STEP 5: PLOTS ---
plt.figure(figsize=(10, 5))
plt.plot(strikes, call_iv_heston, label='Call IV (Heston)', color='blue')
plt.plot(strikes, call_iv_bsm, label='Call IV (BSM)', linestyle='--', color='green')
plt.axvline(S0, color='gray', linestyle='--', label='Spot Price (100)')
plt.title("Implied Volatility Curve (Calls)")
plt.xlabel("Strike Price")
plt.ylabel("Implied Volatility")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

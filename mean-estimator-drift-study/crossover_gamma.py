import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Parameters
n_days = 100          # Larger number of days
mu_0 = 50
sigma = 1.0            # Noise standard deviation
rolling_window = 50
gamma_values = np.linspace(0.0, 0.02, 1000)  # Finer sweep over drift rates
n_simulations_per_gamma = 5    # Average over multiple simulations

# Store MSEs
mse_expanding_list = []
mse_rolling_list = []

# Simulation function
def simulate_mse(gamma, n_days, mu_0, sigma, rolling_window):
    t = np.arange(n_days)
    mu_true = mu_0 + gamma * t
    spread = mu_true + np.random.normal(0, sigma, size=n_days)
    
    spread_series = pd.Series(spread)
    
    mu_expanding = spread_series.expanding(min_periods=1).mean()
    mu_rolling = spread_series.rolling(window=rolling_window, min_periods=1).mean()
    
    residual_expanding = mu_expanding - mu_true
    residual_rolling = mu_rolling - mu_true
    
    # Ignore first 'rolling_window' points when calculating MSE
    residual_expanding = residual_expanding[rolling_window:]
    residual_rolling = residual_rolling[rolling_window:]
    
    mse_expanding = np.mean(residual_expanding**2)
    mse_rolling = np.mean(residual_rolling**2)
    
    return mse_expanding, mse_rolling

# Run simulation across different drift rates
for gamma in gamma_values:
    mse_exp_total = 0
    mse_roll_total = 0
    for _ in range(n_simulations_per_gamma):
        mse_exp, mse_roll = simulate_mse(gamma, n_days, mu_0, sigma, rolling_window)
        mse_exp_total += mse_exp
        mse_roll_total += mse_roll
    mse_expanding_list.append(mse_exp_total / n_simulations_per_gamma)
    mse_rolling_list.append(mse_roll_total / n_simulations_per_gamma)

# Plot MSEs vs Drift Rate
plt.figure(figsize=(12,6))
plt.plot(gamma_values, mse_expanding_list, label='Expanding Mean MSE', color='blue')
plt.plot(gamma_values, mse_rolling_list, label='Rolling Mean MSE', color='red')
plt.axvline(x=gamma_values[np.argmin(np.abs(np.array(mse_expanding_list) - np.array(mse_rolling_list)))], linestyle='--', color='black', label='Crossover Gamma')
plt.xlabel('Drift Rate (gamma)')
plt.ylabel('Mean Squared Error')
plt.title('MSE of Expanding vs Rolling Mean vs Drift Rate (Averaged Simulations)')
plt.legend()
plt.grid(True)
#plt.show()

# Print the estimated crossover point
gamma_crossover = gamma_values[np.argmin(np.abs(np.array(mse_expanding_list) - np.array(mse_rolling_list)))]

# Corrected theoretical crossover gamma using final corrected formula
sigma_squared = sigma**2
corrected_gamma = np.sqrt(
    (4 * sigma_squared * (1/rolling_window - 1/n_days)) /
    ((n_days - 1)**2 - (rolling_window - 1)**2)
)

print(f"Simulated crossover gamma: {gamma_crossover:.5f}")
print(f"Final corrected theoretical crossover gamma: {corrected_gamma:.5f}")



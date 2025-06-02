from pathlib import Path
from datetime import datetime

"""
Author: Carson Bowler

This constants file centralizes key parameters used across the momentum 
pipeline, including the portfolio entry and exit dates, and the Polygon API key. 
It allows for consistent date management and easy updates across scripts.
"""


# Entry Date
ENTRY_DATE = datetime(2024, 1, 3)

# Trade Exit Date
EXIT_DATE = datetime(2024, 4, 3)

# Lookback Period: for calculating ADV and cointegration
LOOKBACK_PERIOD = 365 / 3 # 4 months

# Polygon API Key
API_KEY = "KFzmL8ylDoI1Ej0M69h5Bm4GUrLpgbmj"

# File Paths
current_dir = Path(__file__).resolve().parent.parent
US_COMMON_STOCKS_PATH = current_dir / "data" / "us_common_stocks.csv"
date_str = ENTRY_DATE.strftime("%Y-%m-%d")
TOP_1500_LIQUID_STOCKS_PATH = f"../data/{date_str}/top_1500_liquid_stocks_{date_str}.csv"
COINTEGRATION_CANDIDATES_PATH = f"../data/{date_str}/cointegration_candidates_{date_str}.csv"
FILTERED_COINTEGRATION_CANDIDATES_PATH = f"../data/{date_str}/filtered_cointegrated_pairs.csv"
FINAL_CANDIDATES_PATH = f"../data/{date_str}/final_candidates_{date_str}.csv"
TRADE_SIGNALS_PATH = f"../data/{date_str}/trade_signals_{date_str}.csv"
BACKTEST_DATA_PATH = f"../data/{date_str}/backtest_data_{date_str}.csv"

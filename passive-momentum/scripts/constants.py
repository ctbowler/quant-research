"""
Author: Carson Bowler

This constants file centralizes key parameters used across the momentum 
pipeline, including the portfolio entry and exit dates, and the Polygon API key. 
It allows for consistent date management and easy updates across scripts.
"""


# constants.py

from datetime import datetime

# Entry Date
ENTRY_DATE = datetime(2025, 1, 3)

# Trade Exit Date
EXIT_DATE = datetime(2025, 1, 3)

# Polygon API Key
API_KEY = "INSERT API KEY HERE"

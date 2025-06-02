import requests
import pandas as pd
import time

# --- Fetch US Common Stocks from Polygon API ---
api_key = "INSERT API KEY HERE"
base_url = "https://api.polygon.io/v3/reference/tickers"
# Set up parameters for the API request
tickers = []
cursor = None
# Loop to fetch all pages of results
while True:
    params = {
        "type": "CS",           # Common Stocks
        "market": "stocks",
        "active": "true",
        "limit": 1000,
        "apiKey": api_key
    }
    # Add cursor if available to fetch next page
    if cursor:
        params["cursor"] = cursor
    # Make the API request
    response = requests.get(base_url, params=params)
    data = response.json()
    # Check for errors in the response
    if "results" not in data:
        print("Error fetching results:", data)
        break
    # Append the results to the tickers list
    tickers.extend(data["results"])
    # Check if there is a next page
    cursor = data.get("next_url", None)
    if cursor:
        # Extract the cursor value from the next_url
        cursor = cursor.split("cursor=")[-1]
        time.sleep(1)  # Respect API rate limits
    else:
        break

# --- Convert the list of tickers to a DataFrame ---
df = pd.DataFrame(tickers)
# Save to CSV
df.to_csv(r"FILE PATH FOR US COMMON STOCKS", index=False)
print(f"Saved {len(df)} tickers.")

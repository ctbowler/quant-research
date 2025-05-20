import pandas as pd
import numpy as np
import time
from polygon import RESTClient
from datetime import datetime, timedelta
from tqdm import tqdm

# --- Setup Polygon Key + API Client --- #
polygon_key = "INSERT API KEY HERE"
client = RESTClient(polygon_key)

# --- Load all tickers ---
df = pd.read_csv(r"FILE PATH FOR US COMMON STOCKS")
tickers = df["ticker"].tolist()

# --- Set time window ---
end_date = datetime(2024, 6, 12 )
start_date = end_date - timedelta(days=365)

# --- Store liquidity info ---
results = []

for ticker in tqdm(tickers, desc="Processing Tickers"):
    try:
        bars = client.get_aggs(
            ticker,
            1, "day",
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
        time.sleep(0.3)  # To avoid rate limits

        # Compute avg dollar volume
        volume = [bar.volume for bar in bars if bar.close and bar.volume]
        if len(volume) >= 200:  # Ensure we have enough data
            # Calculate average dollar volume
            adv = np.mean(volume)
            results.append((ticker, adv))
    except Exception as e:
        continue


# --- Convert to DataFrame ---
liq_df = pd.DataFrame(results, columns=["ticker", "avg_dollar_volume"])
liq_df = liq_df.sort_values(by="avg_dollar_volume", ascending=False).head(1500)

# Save to CSV
liq_df.to_csv(r"FILE PATH FOR TOP 1500 LIQUID STOCKS", index=False)
print("Saved top 1500 liquid stocks.")

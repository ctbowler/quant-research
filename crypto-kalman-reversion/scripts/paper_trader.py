import os
import numpy as np
import pandas as pd
import time
from ta.momentum import RSIIndicator
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoLatestQuoteRequest
import sys
import requests
import pandas as pd


# Accept symbol as command-line argument (preferred)
if len(sys.argv) > 1:
    symbol = sys.argv[1].upper()
else:
    symbol = input("Enter crypto pair (e.g. LINK/USD): ").upper()
base_symbol = symbol.split("/")[0]
binance_symbol = symbol.replace("/", "")

#Logging setup
log_dir = r"INSERT DIRECTORY HERE"
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"{base_symbol}_paper_trades.csv")
pnl_log_file = os.path.join(log_dir, f"{base_symbol}_live_pnl_log.csv")


load_dotenv()
ALPACA_API_KEY = ""
ALPACA_API_SECRET = ""

# === Alpaca Clients ===
trading_client = TradingClient(ALPACA_API_KEY, ALPACA_API_SECRET, paper=True)
data_client = CryptoHistoricalDataClient(ALPACA_API_KEY, ALPACA_API_SECRET)


# === Parameters ===
base_symbol = symbol.split("/")[0]
capital = 100000  # Total capital for trading
stop_loss_pct = 0.05
z_thresh = 1.0
rsi_entry = 30
window_size = 30
qty = None  # Will be computed based on capital

# === Storage ===
in_position = False
entry_price = None
def fetch_bars_from_binance(symbol="BTCUSDT", limit=1000):
    
    url = "https://api.binance.us/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "5m",
        "limit": limit
    }

    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "_close_time", "_quote_asset_vol", "_num_trades", "_taker_base_vol", "_taker_quote_vol", "_ignore"
    ])
    
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df[["open", "high", "low", "close", "volume", "_close_time"]].astype(float)
    return df



def apply_kalman(price):
    n = len(price)
    kf_mean = np.zeros(n)
    P = 1.0
    Q = 0.0001
    R = 0.01
    kf_mean[0] = price.iloc[0]

    for t in range(1, n):
        pred = kf_mean[t - 1]
        P += Q
        K = P / (P + R)
        kf_mean[t] = pred + K * (price.iloc[t] - pred)
        P = (1 - K) * P

    return pd.Series(kf_mean, index=price.index)

from alpaca.data.live import CryptoDataStream

def get_best_bid_ask(symbol="UNI/USD"):
    request = CryptoLatestQuoteRequest(symbol_or_symbols=[symbol])
    quote = data_client.get_crypto_latest_quote(request)
    q = quote[symbol]
    return q.bid_price, q.ask_price




def place_limit_order():
    global qty
    best_bid, best_ask = get_best_bid_ask(symbol)
    qty = round(capital / best_ask, 4)
    spread= best_ask - best_bid

    limit_price = round(best_ask, 2) + 0.1*spread  # or use more decimals if needed

    order = LimitOrderRequest(
        symbol=base_symbol,
        qty=qty,
        side=OrderSide.BUY,
        type="limit",
        time_in_force=TimeInForce.GTC,
        limit_price=limit_price
    )

    trading_client.submit_order
    print(f"✅ Placed LIMIT BUY for {qty} {base_symbol} at ${limit_price:.2f}")



def close_position(price):
    global in_position, entry_price, qty

    if qty:
        order = MarketOrderRequest(
            symbol=base_symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.GTC
        )
        trading_client.submit_order(order)
        print(f"🚪 Exited position at ${price:.2f}")
        pnl = (price - entry_price) * qty
        log_trade("SELL", price, pnl)
        print(f"💰 PnL from trade: ${pnl:.2f}")


    in_position = False
    entry_price = None
    qty = None
    


def log_unrealized_pnl(position):
    pnl_data = {
        "timestamp": pd.Timestamp.now(),
        "entry_price": float(position.avg_entry_price),
        "current_price": float(position.current_price),
        "qty": float(position.qty),
        "unrealized_pnl": float(position.unrealized_pl),
        "unrealized_pct": float(position.unrealized_plpc)
    }
    pd.DataFrame([pnl_data]).to_csv(pnl_log_file, mode="a", header=not os.path.exists(pnl_log_file), index=False)


def log_trade(action, price, pnl=0):
    row = {
        "timestamp": pd.Timestamp.now(),
        "action": action,
        "price": price,
        "pnl": pnl
    }
    pd.DataFrame([row]).to_csv(log_file, mode="a", header=not os.path.exists(log_file), index=False)




# === Main Trading Loop ===
def run_strategy():
    global in_position, entry_price, qty
    try:
        position = trading_client.get_open_position(symbol=base_symbol)
        in_position = True
        entry_price = float(position.avg_entry_price)
        qty = float(position.qty)

        # Log if new entry just filled
        if not os.path.exists(log_file) or pd.read_csv(log_file)["action"].iloc[-1] != "BUY":
             log_trade("BUY", entry_price)

    except:
        in_position = False


    bars = fetch_bars_from_binance(binance_symbol, limit=1000)
    closetime = bars["_close_time"].copy()
    price = bars["close"].dropna()
    

    if len(price) < window_size + 1:
        return

    kalman_mean = apply_kalman(price)
    kalman_mean = kalman_mean.reindex(price.index)  # Ensures same index

    spread = price - kalman_mean
    z_score = (spread - spread.rolling(window_size).mean()) / spread.rolling(window_size).std()
    rsi = RSIIndicator(close=price, window=14).rsi()

    latest_price = price.iloc[-1]
    latest_z = z_score.iloc[-1]
    latest_rsi = rsi.iloc[-1]

    print(f"[{price.index[-1]}] Price: {latest_price:.2f}, Z: {latest_z:.2f}, RSI: {latest_rsi:.2f},Close Time: {closetime.iloc[-1]}")

    # === ENTRY ===
    if not in_position and latest_z < -z_thresh and latest_rsi < rsi_entry:
        place_limit_order()

    # === EXIT ===
    elif in_position:
        avg_entry = float(position.avg_entry_price)
        qty = float(position.qty)
        stop_loss_price = avg_entry * (1 - stop_loss_pct)

        if latest_price > kalman_mean.iloc[-1] or latest_price < stop_loss_price:
            close_position(latest_price)

        # log live PnL
        log_unrealized_pnl(position)

        

if __name__ == "__main__":
    while True:
        try:
            run_strategy()
            time.sleep(300)  # 5 min
        except KeyboardInterrupt:
            print("🛑 Stopping bot.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(60)

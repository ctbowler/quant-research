import struct
import time

TOP_N = 20  # Number of top bid/ask levels to include in the order book

#

# --- PACK ORDERBOOK UPDATES (WEBSOCKET)--- #
def pack_orderbook(product_id: str, top_bids, top_asks, bid_liquidity, ask_liquidity, timestamp):
    """
    Packs order book updates data into a compact binary format.
    Fields:
        - product_id (10s): asset name like "ETH-USD"
        - timestamp (d): UNIX timestamp
        - bid_liquidity, ask_liquidity (2d): total liquidity on each side
        - top_bids (40d): up to 20 (price, size) pairs
        - top_asks (40d): up to 20 (price, size) pairs
    """
    # Convert product_id string to 10-byte padded binary
    product_id_bytes = product_id.encode('utf-8')[:10].ljust(10, b'\x00')
    timestamp_bytes = timestamp.encode('utf-8')[:23].ljust(23, b'\x00')

    # Ensure exactly TOP_N entries (pad with zeros if fewer)
    bid_data = [(float(p), float(q)) for p, q in top_bids[:TOP_N]]
    ask_data = [(float(p), float(q)) for p, q in top_asks[:TOP_N]]
    bid_data += [(0.0, 0.0)] * (TOP_N - len(bid_data))
    ask_data += [(0.0, 0.0)] * (TOP_N - len(ask_data))

    # Flatten [(p1, q1), (p2, q2), ...] → [p1, q1, p2, q2, ...]
    flat_bids = [x for pair in bid_data for x in pair]
    flat_asks = [x for pair in ask_data for x in pair]

    # Format: 10s = product_id, 3d = timestamp + 2 liquidity, 40d = 20 bid pairs, 40d = 20 ask pairs
    fmt = f"<10s 23s 2d {TOP_N * 2}d {TOP_N * 2}d"
    packed = struct.pack(fmt, product_id_bytes, timestamp_bytes, bid_liquidity, ask_liquidity, *flat_bids, *flat_asks)
    return packed

# --- PACK CANDLE DATA --- #
def pack_candles(product_id: str, open_pr, high, low, close, volume, timestamp):
    """
    Packs a candle into binary format.
    Fields:
        - product_id (10s)
        - timestamp (23s)
        - open, high, low, close, volume (5d)
    """
    product_id_bytes = product_id.encode('utf-8')[:10].ljust(10, b'\x00')
    timestamp_bytes = timestamp.encode('utf-8')[:23].ljust(23, b'\x00')

    fmt = "<10s 23s 5d"
    packed = struct.pack(fmt, product_id_bytes, timestamp_bytes, open_pr, high, low, close, volume)
    return packed

# --- PACK MARKET ORDER --- #
def pack_marketorders(product_id: str, price, size, timestamp):
    """
    Packs the latest market order (trade) into binary format.
    Fields:
        - product_id (10s)
        - timestamp (23s)
        - price (d)
        - size (d)
    """
    product_id_bytes = product_id.encode('utf-8')[:10].ljust(10, b'\x00')
    timestamp_bytes = timestamp.encode('utf-8')[:23].ljust(23, b'\x00')

    fmt = "<10s 23s 2d"
    packed = struct.pack(fmt, product_id_bytes, timestamp_bytes, price, size)
    return packed

import asyncio
import websockets
import json
from collections import defaultdict
import signal
import os
import time
import threading
import mmap
from binary_structs import *
import struct

ORDERBOOK_TYPE = bytes([1])
CANDLE_TYPE    = bytes([2])
MARKET_TYPE    = bytes([3])

SHM_NAMES = {
    ORDERBOOK_TYPE: "Local\\orderbook_data",
    CANDLE_TYPE:    "Local\\candle_data",
    MARKET_TYPE:    "Local\\market_data"
}
SHM_SIZE = 4096

class SharedMemoryWriter:
    def __init__(self, shm_name, shm_size=4096):
        self.shm_name = shm_name
        self.shm_size = shm_size
        self.lock = threading.Lock()
        self.running = True
        self.new_data = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def write(self, binary_msg: bytes):
        with self.lock:
            if len(binary_msg) > self.shm_size:
                print(f"\u274c Shared memory write too large for {self.shm_name}")
                return
            self.new_data = binary_msg

    def _run(self):
        try:
            self.mm = mmap.mmap(-1, self.shm_size, tagname=self.shm_name)
        except Exception as e:
            print(f"\u274c Failed to create mmap {self.shm_name}: {e}")
            return

        while self.running:
            with self.lock:
                if self.new_data:
                    data = self.new_data
                    self.mm.seek(0)
                    self.mm.write(data + b'\x00' * (self.shm_size - len(data)))
                    self.new_data = None
                    self.mm.flush()
            time.sleep(0.001)  # Sleep to avoid busy waiting

    def stop(self):
        self.running = False
        self.thread.join()
        self.mm.close()

class CoinbaseWebSocketClient:
    def __init__(self, products, top_n=20):
        self.ws_url = "wss://advanced-trade-ws.coinbase.com"
        self.products = products
        self.top_n = top_n
        self.bids = defaultdict(dict)
        self.asks = defaultdict(dict)
        self.keep_running = True
        self.last_ob_update = 0
        self.last_market_update = 0
        self.last_orderbook_binary = None
        self.last_market_binary = None
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, *args):
        print("Shutting down WebSocket client...")
        self.keep_running = False

    def update_book(self, product_id, side, price, size):
        price = float(price)
        size = float(size)
        book = self.bids[product_id] if side == "bid" else self.asks[product_id]
        if size == 0:
            book.pop(price, None)
        else:
            book[price] = size

    def get_book_stats(self, product_id):
        sorted_bids = sorted(self.bids[product_id].items(), key=lambda x: -x[0])[:self.top_n]
        sorted_asks = sorted(self.asks[product_id].items(), key=lambda x: x[0])[:self.top_n]
        return {
            "top_bids": sorted_bids,
            "top_asks": sorted_asks,
            "bid_liquidity": sum(self.bids[product_id].values()),
            "ask_liquidity": sum(self.asks[product_id].values()),
        }

    def find_offer_start(self, updates):
        for i, update in enumerate(updates):
            if update["side"] == "offer":
                return i
        return None

    async def connect(self):
        async with websockets.connect(self.ws_url, max_size=2**23) as ws:
            subscribe_msgs = [
                {"type": "subscribe", "channel": "level2", "product_ids": self.products},
                {"type": "subscribe", "channel": "market_trades", "product_ids": self.products},
            ]
            for msg in subscribe_msgs:
                await ws.send(json.dumps(msg))
                print(f"[WebSocket] Subscribed to: {msg['channel']}")

            while self.keep_running:
                try:
                    raw_msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                msg = json.loads(raw_msg)
                channel = msg.get("channel")
                events = msg.get("events", [])

                if channel == "l2_data":
                    for event in events:
                        product_id = event["product_id"]
                        now = time.time()

                        if event["type"] == "snapshot":
                            offer_idx = self.find_offer_start(event["updates"])
                            if offer_idx is not None:
                                self.bids[product_id].clear()
                                self.asks[product_id].clear()
                                for update in event["updates"][:self.top_n]:
                                    if update["side"] == "bid":
                                        self.update_book(product_id, update["side"], update["price_level"], update["new_quantity"])
                                for update in event["updates"][offer_idx:offer_idx+self.top_n]:
                                    if update["side"] == "offer":
                                        self.update_book(product_id, update["side"], update["price_level"], update["new_quantity"])

                        elif event["type"] == "update":
                            if now - self.last_ob_update < 1.0:
                                continue
                            self.last_ob_update = now

                            self.bids[product_id].clear()
                            self.asks[product_id].clear()
                            for update in event["updates"]:
                                self.update_book(product_id, update["side"], update["price_level"], update["new_quantity"])

                        stats = self.get_book_stats(product_id)
                        timestamp = event["updates"][0]["event_time"] if event["updates"] else ""
                        binary_orderbook = pack_orderbook(
                            product_id, stats["top_bids"], stats["top_asks"],
                            stats["bid_liquidity"], stats["ask_liquidity"], timestamp[:23]
                        )
                        if binary_orderbook != self.last_orderbook_binary:
                            writers[ORDERBOOK_TYPE].write(binary_orderbook)
                            self.last_orderbook_binary = binary_orderbook

                elif channel == "market_trades":
                    now = time.time()
                    #if now - self.last_market_update < 0.02:
                        #continue
                    self.last_market_update = now

                    for event in events:
                        if event["type"] == "update":
                            for trade in event.get("trades", []):
                                product_id = trade["product_id"]
                                binary_market = pack_marketorders(
                                    product_id, float(trade["price"]), float(trade["size"]), "123"
                                )
                                if binary_market != self.last_market_binary:
                                    writers[MARKET_TYPE].write(binary_market)
                                    self.last_market_binary = binary_market
                                    
        

async def safe_connect(client):
    while client.keep_running:
        try:
            await client.connect()
        except Exception as e:
            print(f"[safe_connect Error] {e}")
            await asyncio.sleep(5)

async def main():
    products = ["BTC-USD"]
    client = CoinbaseWebSocketClient(products)
    await asyncio.gather(safe_connect(client))

if __name__ == "__main__":
    writers = {
        ORDERBOOK_TYPE: SharedMemoryWriter(SHM_NAMES[ORDERBOOK_TYPE], SHM_SIZE),
        CANDLE_TYPE:    SharedMemoryWriter(SHM_NAMES[CANDLE_TYPE], SHM_SIZE),
        MARKET_TYPE:    SharedMemoryWriter(SHM_NAMES[MARKET_TYPE], SHM_SIZE),
    }

    try:
        asyncio.run(main())
    finally:
        for w in writers.values():
            w.stop()

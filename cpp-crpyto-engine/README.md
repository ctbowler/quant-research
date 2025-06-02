# ⚡ C++ Crypto Trading Engine (Real-Time GUI w/ Coinbase API)

This project is a **low-latency, real-time trading engine and market visualizer**, built in **modern C++** and powered by live data from the **Coinbase Advanced WebSocket API**. It features a custom-built order book, high-performance rendering using **ImGui + OpenGL**, and a multi-threaded architecture that streams data from a Python client into C++ via **shared memory**.

<p align="center">
  <img src="images/orderbook.png" width="600">
  <br>
  <em>Real-time order book depth</em>
</p>

---

## 🚀 Features

- 📈 **Real-Time Order Book Visualization**
  - Depth ladder displays live bid/ask volume
  - Last trade marker and mid-price overlays

- 📊 **Live Price Chart (Tick or Candle View)**
  - Animated chart with optional smoothing, fading, and zooming
  - Custom plotting renderer with glow and trailing effects

- 🧠 **Optimized Trading Engine Core**
  - Thread-safe `OrderBook`, `PriceBuffer`, and `CandleBuffer` data structures
  - High-frequency updates with minimal memory contention

- 🔁 **Shared Memory Streaming from Python**
  - Python Coinbase WebSocket client feeds raw order book + trade data
  - Data transferred using `mmap` shared memory buffer (non-blocking, real-time)
  - No sockets or file I/O = faster IPC

- ⚙️ **Multi-Threaded Architecture**
  - Separate threads for:
    - Shared memory reading
    - GUI rendering
    - Order book updating
  - Mutex locks used sparingly to avoid stalling GUI

- 💡 **Built for Extensibility**
  - Plug in your own strategies (market making, reversion, analytics)
  - Clean C++ modular design — each component is testable

---

## 📐 Architecture Overview


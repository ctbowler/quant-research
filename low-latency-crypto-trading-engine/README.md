# C++ Crypto Trading Engine (Coinbase Real-Time GUI)

A real-time crypto trading engine and visualizer built in modern C++, powered by Coinbase Advanced WebSocket data. This project features a custom order book engine, low-latency rendering with ImGui + OpenGL, and a modular design optimized for performance and extensibility. The goal was to give myself an easy way to trade on coinbase without the hassle of navigating through their UI. I also wanted to add a candlestick chart to my toolset as well as L2 updates with at my own tick rate. 

<img src="src/visualization2.gif" width="600" alt="Order Book Preview">
<p align="center"><em>Live order book depth visualization</em></p>

---

## Features

- **Real-time order book depth and trade flow**
- **High-performance GUI** built with ImGui + OpenGL
- **Shared memory interface** between Python and C++ for real-time data
- **Custom trading engine core** with multi-threaded updates
- **Streaming price chart** with optional glow, fade, and smoothing
- **Modular C++ architecture** with extensible buffers, strategy hooks, and rendering layers

---

## Data Flow Optimization
To achieve low-latency data transfer between the Python WebSocket client and the C++ trading engine, this system uses **memory-mapped shared memory (mmap)** as the communication layer. The Python streamer receives market data from the Coinbase Advanced WebSocket API, encodes it into **binary-packed structs**, and writes it directly to shared memory.

On the C++ side, a SharedMemoryReader thread continuously reads from this buffer, decoding the byte stream into structured messages (OrderBook, Trade, etc.) without the overhead of sockets or file I/O — on average my *raw* data per socket request was 4x smaller than its json equivalent, hence initializing static containers with pre-set sizes can reduce json overhead. This architecture enables real-time data flow and rendering with minimal delay, making it optimal for high-frequency market visualization and strategy simulation.

<img src="src/data-flow-diagram.png" width="400" alt="src/data-flow-diagram.png">


---

## Performance-Oriented Design

| Component         | Optimization Highlights                                                                 |
|------------------|------------------------------------------------------------------------------------------|
| **OrderBook**     | Custom data structure for fast bid/ask updates and market/limit order simulation        |
| **PriceBuffer**   | Rolling buffer for tick-level prices, supports real-time fade smoothing and glow effects |
| **CandleBuffer**  | Efficient OHLC aggregation with real-time partial candle updates                        |
| **Shared Memory** | `mmap` between Python and C++ for low-overhead, non-blocking interprocess communication |
| **Threading**     | Background worker threads for memory reads, orderbook parsing, and GUI refresh          |

---

## Dependencies

- C++20 compiler
- CMake 3.16+
- [GLFW](https://www.glfw.org/)
- [ImGui](https://github.com/ocornut/imgui) (include core files and backends)
- Python 3.8+
  - `websocket-client` or `aiohttp`

> ⚠️ Note: This project does **not** include ImGui or GLFW — you must install or link them manually.

---

## Purpose and Future Development
This system was built for research and performance benchmarking in real-time trading infrastructure. It's structured for future expansion, including:
- Strategy plugin support (market making, mean reversion, arbitrage)
- Simulated order execution with conversion tracking
- UI enhancements for zoom, multi-asset display, and toggles
- Possible integration with live trading APIs (e.g., Alpaca or Coinbase Advanced)




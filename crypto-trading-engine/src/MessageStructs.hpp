#pragma once
#include <cstdint>
#include<iostream>



#pragma pack(push,1)

enum class MessageType : uint8_t {
	ORDERBOOK = 1,
	CANDLE = 2,
	MARKET = 3
};

// Message type 'O'
struct OrderBookMessage {
	char product_id[10];
	char timestamp[23];
	double bid_liquidity;
	double ask_liquidity;
	double bids[40];
	double asks[40];
};	
	
// Message type 'C'
struct CandleMessage {
	char timestamp[23];
	double open;
	double high;
	double low;
	double close;
	double volume;
};

// Message type 'M'
struct MarketOrderMessage {
	char product_id[10];
	char timestamp[23];
	double price;
	double size;
};

// Message type 'S'
struct OrderBookSnapshot {
	char product_id[10];
	char timestamp[23];
	double bid_levels[120];
	double ask_levels[120];

	// Debugging: Print current snapshot
	void print_snapshot() const {
		std::cout << "Product: " << std::string(product_id, 10) << "\n";
		std::cout << "Timestamp: " << timestamp << "\n";

		std::cout << "\nBIDS:\n";
		for (int i = 0; i < 20; ++i) {
			double price = bid_levels[i * 3];
			double size = bid_levels[i * 3 + 1];
			double num_orders = bid_levels[i * 3 + 2];
			if (price > 0)
				std::cout << "[BID] Price: " << price << " Qty: " << size << " Orders: " << num_orders << "\n";
		}

		std::cout << "\nASKS:\n";
		for (int i = 0; i < 20; ++i) {
			double price = ask_levels[i * 3];
			double size = ask_levels[i * 3 + 1];
			double num_orders = ask_levels[i * 3 + 2];
			if (price > 0)
				std::cout << "[ASK] Price: " << price << " Qty: " << size << " Orders: " << num_orders << "\n";
		}
	}
};

#pragma pack(pop)
// Order.hpp
#include <iostream>
#include <string>
#pragma once

enum class OrderType {
	LIMIT,
	MARKET
};

enum class OrderSide {
	BUY,
	SELL
};

struct Order {
	int id;
	OrderSide side; // BUY or SELL
	double price;
	double quantity;
	OrderType type;
	std::string timestamp;

	Order(int id, OrderSide side, double price, double quantity, OrderType type, std::string timestamp);

	void updateQty(const int size);
	
};


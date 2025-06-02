// OrderBook.hpp
#include <iostream>
#include <map> // for std::map
#include <deque> // for std::deque
#include "Order.hpp" // for Order objects
#include <string>
#include <optional>
#include <unordered_map>
#include <tuple>
#include "PriceBuffer.hpp"

#pragma once

class OrderBook{

public:

	// Store lists of Orders in a map structure with the keys being the order price
	std::map<double, std::deque<Order>> asks; // asks order in ascending order by default
	std::map<double, std::deque<Order>, std::greater<double>> bids; // sort bids in descending order

	// Hashmap to store all orders with their respective prices and orderSide. This is used to optimize reverse key searches 
	// for order modification and cancellation (as opposed to sorting through a map + deque)
	std::unordered_map<int, std::tuple<OrderSide, double, std::deque<Order>::iterator>> orderIteratorIndex;
	

	// Default Constructor
	OrderBook();

	

	void clearBook();

	// Method to print most recent bid/ask orders in order book
	void printOrders() const;

	std::optional<double> getBestBid() const;

	std::optional<double> getBestAsk() const;

	int getBidVolume() const;

	int getAskVolume() const;

	// Method to match trades 
	bool matchBuyOrder(const Order& in_order);

	bool matchSellOrder(const Order& in_order);

	bool isMarket(const Order& order) const;

	bool isLimit(const Order& order) const;

	bool cancelOrder(const int orderID);



	const std::map<double, std::deque<Order>, std::greater<double>>& getBidMap();

	const std::map<double, std::deque<Order>>& getAskMap();

	void insertLimitOrder(const Order& o);


};

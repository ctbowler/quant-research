// OrderBook.cpp
#include "Order.hpp"
#include "OrderBook.hpp"
#include <string>
#include <map>
#include <deque>
#include <iostream>
#include <optional>
#include <algorithm>
#include "PriceBuffer.hpp"


OrderBook::OrderBook() {
}


// ** Checker Functions ** // 
// Functions designed to check a value or condition without modifying the state of the object

// Check if an order is a market order
bool OrderBook::isMarket(const Order& order) const {
	if (order.type == OrderType::MARKET) {
		return true;
	}
	return false;
}

// Check if an order is a limit order
// Function is redundant but I added it for readability purposes for later on
bool OrderBook::isLimit(const Order& order) const {
	// If it's a market order it cannot be a limit order
	if (isMarket(order)) {
		return false;
	}
	// If it's not a market order then it must be a limit order
	return true;
}


// ** Retriever Functions ** //
// Retrieve or access a value without modifying the state of the object instance

std::optional<double> OrderBook::getBestBid() const {
	if (bids.empty()) {
		return std::nullopt;
	}
	return bids.begin()->first;
}

std::optional<double> OrderBook::getBestAsk() const {
	if (asks.empty()) {
		return std::nullopt;
	}
	return asks.begin()->first;
}

int OrderBook::getBidVolume() const {
	// Check if bid list is empty
	if (bids.empty()) {
		return 0;
	}
	// Initialize a volume counter
	int total_vol{};
	// Loop through each price-orders pair
	for (const auto& [price, orders] : bids) {
		// Check if bid price was previously initialized but no orders currently exist
		if (!orders.empty()) {
			// Loop through orders
			for (const Order& order : orders) {
				// Sum total order quantity
				total_vol += order.quantity;
			}
		}
	}
	return total_vol;
}

int OrderBook::getAskVolume() const {
	// Check if ask list is empty
	if (asks.empty()) {
		return 0;
	}
	// Initialize volume counter
	int total_vol{};
	// Loop through each price-order pair
	for (const auto& [price, orders] : asks) {
		// Check if ask price was previously initialized but no orders currently exist
		if (!orders.empty()) {
			// Loop through orders
			for (const Order& order : orders) {
				// Sum total order quantity
				total_vol += order.quantity;
			}
		}
	}

	return total_vol;
}

const std::map<double, std::deque<Order>, std::greater<double>>& OrderBook::getBidMap() {
	return bids;
}

const std::map<double, std::deque<Order>>& OrderBook::getAskMap() {
	return asks;
}

// ** Mutator Functions ** // 
// Functions that perform a task which may require the object members/state to be modified.
// Modifications are marked with a comment // *modification* //


// Method to clear entire order book for real-time updating
void OrderBook::clearBook() {
	asks.clear();
	bids.clear();
	orderIteratorIndex.clear();

}

// Match all buy orders if possible. If all or no orders were matched, return false
bool OrderBook::matchBuyOrder(const Order& in_order) {

	int ask_vol{ getAskVolume() }; // Total number of asks in orderbooks
	double rem_orders{ in_order.quantity };
	const std::optional<double> best_ask = getBestAsk();

	// IF asks exist, check order matching
	if (ask_vol > 0) {
		// Market Orders
		if (isMarket(in_order)) {
			for (auto it = asks.begin(); it != asks.end() && rem_orders > 0;) {
				// Dereference iterator to obtain map key-value pair
				auto& [price, orderbook_orders] = *it;
				while (!orderbook_orders.empty() && rem_orders > 0) {
					Order& ask_order = orderbook_orders.front();
					double const match_size = std::min(ask_order.quantity, rem_orders);
					ask_order.updateQty(ask_order.quantity - match_size);
					if (ask_order.quantity == 0) {
						orderbook_orders.pop_front();
					}
					rem_orders -= match_size;
					// Debugging print statement
					std::cout << "Buy MARKET order matched @ " << price << " for qty of " << match_size << "\n";
					std::cout << "Remaining qty: " << rem_orders << "\n";
				}	
				if (orderbook_orders.empty()) {
					it = asks.erase(it);
				}
				else {
					++it;
				}
			}
			if (rem_orders > 0) {
				// TODO: Handle logic to tell user that their market trades were not FULLY filled
			}
		}

		// Limit Orders
		if (isLimit(in_order)) {
			for (auto it = asks.begin(); it != asks.end() && rem_orders > 0;) {
				// Dereference iterator to obtain map key-value pair
				auto& [price, orderbook_order] = *it;
				if (price > in_order.price) {
					break;
				}
				while (!orderbook_order.empty() && rem_orders > 0) {
					Order& ask_order = orderbook_order.front();
					int const match_size = std::min(ask_order.quantity, rem_orders);
					ask_order.updateQty(ask_order.quantity - match_size);
					if (ask_order.quantity == 0) {
						orderbook_order.pop_front();
					}
					rem_orders -= match_size;
					// Debugging print statement
					/**
					std::cout << "Buy LIMIT order matched @ " << price << " for qty of " << match_size << "\n";
					std::cout << "Remaining qty: " << rem_orders << "\n";
					**/
				}
				if (orderbook_order.empty()) {
					it = asks.erase(it);
				}
				else {
					++it;
				}
			}
		}
	}

	if (rem_orders > 0 && isLimit(in_order)) {
		// If none or only some limit orders were filled, add the rest to the book
		const Order new_order{ in_order.id, in_order.side, in_order.price, rem_orders, in_order.type, in_order.timestamp };
		auto& deque_ref = bids[in_order.price];
		deque_ref.push_back(new_order);
		orderIteratorIndex[new_order.id] = { in_order.side, in_order.price, std::prev(deque_ref.end()) };
		// Print debug statement
		if (rem_orders < in_order.quantity) {
			//std::cout << "Partial Fill. Bid order posted witha qty: " << new_order.quantity << " and price: " << new_order.price << "\n";
		}
		else {
			//std::cout<< "No Fills Possible. Bid order posted witha qty: " << new_order.quantity << " and price: " << new_order.price << "\n";
		}
		

		return true;
	}

	return false;
	
}

// Match all sell orders if possible. Returns true if the order was added to the orderbook after matching, returns false otherwise.
bool OrderBook::matchSellOrder(const Order& in_order) {

	int bid_vol{ getBidVolume() }; // Total number of bids in orderbok
	double rem_orders{ in_order.quantity };	// Remaining orders left to sell
	const std::optional<double> best_bid = getBestBid();

	// If bids exist, check order matching
	if (bid_vol > 0) {
		// Market Orders
		if (isMarket(in_order)) {
			// Manually declare iterators so that we dont get undefined behavior when removing a map object as we iterate through it
			for (auto it = bids.begin(); it != bids.end() && rem_orders > 0;) {
				// Dereference iterator to obtain map key-value pair
				auto& [price, orderbook_orders] = *it;
				while (!orderbook_orders.empty() && rem_orders > 0) {
					Order& bid_order = orderbook_orders.front();
					double const match_size = std::min(bid_order.quantity, rem_orders); // Size of order being matched to seller
					bid_order.updateQty(bid_order.quantity - match_size);
					if (bid_order.quantity == 0) {
						orderbook_orders.pop_front(); // Remove each bid if it has been successfully filled
					}
					rem_orders -= match_size;
					// Debugging print statement
					std::cout << "Sell MARKET order matched @ " << price << " for qty of " << match_size << "\n";
					std::cout << "Remaining qty: " << rem_orders << "\n";
				}
				// If bid list is empty for this price, remove that pair from the bid map
				if (orderbook_orders.empty()) {
					it = bids.erase(it); // erase() will increment iterator for me
				} 
				// Update iterator to next value 
				else {
					++it;
				}
			}			
			if (rem_orders > 0) {
				// TODO: Handle logic to tell user that their market trades were not FULLY filled
			}
		}

		// Limit Orders
		else if (isLimit(in_order) && best_bid && *best_bid >= in_order.price) {
			for (auto it = bids.begin(); it != bids.end() && rem_orders > 0;) {
				auto& [price, orderbook_orders] = *it;
				if (price < in_order.price) {
					break;
				}
				while (!orderbook_orders.empty() && rem_orders > 0) {
					Order& bid_order = orderbook_orders.front();
					int const match_size = std::min(bid_order.quantity, rem_orders); // Size of order being matched to seller
					// Update orderbook: 
					// Change size of order on the orderbook if there's remaining quantity
					bid_order.updateQty(bid_order.quantity - match_size);
					if (bid_order.quantity == 0) {
						orderbook_orders.pop_front();
					}
					// Update remaining order quantity
					rem_orders -= match_size;

					// Debugging print:
					/***
					std::cout << "Sell LIMIT order matched @ " << price << " for qty of " << match_size << "\n";
					std::cout << "Remaining qty: " << rem_orders << "\n";
					***/
				}

				if (orderbook_orders.empty()) {
					it = bids.erase(it);
				}
				else {
					++it;
				}
			}
			
		}

	}
	
	if (rem_orders > 0 && isLimit(in_order)) {
		// If none or only some limit orders were filled, add the rest to the book
		const Order new_order{ in_order.id, in_order.side, in_order.price, rem_orders, in_order.type, in_order.timestamp };
		auto& deque_ref = asks[in_order.price];
		deque_ref.push_back(new_order);
		orderIteratorIndex[new_order.id] = { in_order.side, in_order.price, std::prev(deque_ref.end()) };
		// Print debug statement
		if (rem_orders < in_order.quantity) {
			//std::cout << "Partial Fill. Ask order posted witha qty: " << new_order.quantity << " and price: " << new_order.price << "\n";
		}
		else {
			//std::cout << "No fills possible. Ask order posted witha qty: " << new_order.quantity << " and price: " << new_order.price << "\n";
		}
			

		return true;
	}

	return false;

}

void OrderBook::insertLimitOrder(const Order& o) {
	if (o.side == OrderSide::BUY) {
		auto& dq = bids[o.price];
		dq.push_back(o);
		orderIteratorIndex[o.id] = { o.side, o.price, std::prev(dq.end()) };
		
	}
	else {
		auto& dq = asks[o.price];
		dq.push_back(o);
		orderIteratorIndex[o.id] = { o.side, o.price, std::prev(dq.end()) };
	
	}
}

// Cancel order
bool OrderBook::cancelOrder(const int orderID) {
	auto it = orderIteratorIndex.find(orderID);
	// if key was not found:
	if (it == orderIteratorIndex.end()) return false;

	//
	auto const [side, price, orderIt] = it->second;
	if (side == OrderSide::BUY) {
		auto& book = bids[price];
		book.erase(orderIt);
		if (book.empty()) {
			bids.erase(price);
		}
	}
	else {
		auto& book = asks[price];
		book.erase(orderIt);
		if (book.empty()) {
			asks.erase(price);
		}

	}
	orderIteratorIndex.erase(orderID);

	// Debugging
	std::cout << "\nRemoved Order#" << orderID << " ($" << price << ") from the orderbook!\n";
	return true;
}




// ** Control Functions ** //
// Functions designed for the sole purpose of modifying the value of a class member or state


// ** Printing Functions ** //
void OrderBook::printOrders() const {
	std::cout << "\n---ORDERBOOK ORDERS---\n";

	// Loop through all [price, bids] in order book
	for (const auto& [price, orders] : bids) {
		// Display current bid price
		std::cout << "\nBids for $" << price << "\n";
		for (const auto& order : orders){
			// Display information for each bid
			std::cout << "ID: "
				<< order.id
				<< " | Qty: "
				<< order.quantity
				<< " | Side: "
				<< "BUY\n";
		}
	}
	
	// Loop through all [price,asks] in order book
	for (const auto& [price, orders] : asks) {
		// Display current ask price
		std::cout << "\nAsks for $" << price << "\n";
		// For each price, loop through all ask orders
		for (const auto& order : orders) {
			// Display ask orders for each price
			std::cout << "ID: "
				<< order.id
				<< " | Qty: "
				<< order.quantity
				<< " | Side: "
				<< "SELL\n";
		}
	}
	std::cout << "\n---------------------\n";
}




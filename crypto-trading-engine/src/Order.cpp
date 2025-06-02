// Order.cpp
#include <iostream>
#include <string>
#include <cassert>
#include "Order.hpp"
#include <string>

Order::Order(int id, OrderSide side, double price, double quantity, OrderType type, std::string timestamp)
	: id(id), side(side), price(price), quantity(quantity), type(type), timestamp(timestamp){
}

void Order::updateQty(int const new_qty) {
	assert(new_qty >= 0, "An order match resulted in a negative or zero quantity!");
	quantity = new_qty;
}


#include "PriceBuffer.hpp"
#include<iostream>
#include<string>
#include<array>
#include<atomic>
#include <vector>


void PriceBuffer::add(float price) {
	data[index % MAX_PRICES] = price;
	index++;
}

size_t PriceBuffer::getIndex() {
	return index.load();
}
std::vector<float> PriceBuffer::getRecentList() {
	std::vector<float> price_list;
	size_t start = index > MAX_PRICES ? index - MAX_PRICES : 0;
	for (size_t i = start; i < index; ++i) {
		price_list.push_back(data[i % MAX_PRICES]);
	}
	return price_list;


}

float PriceBuffer::getLast() {
	if (index > 0) {
		size_t i = (index - 1) % MAX_PRICES;
		return data[i];
	}
	return 0.0f; // or std::nanf("") if invalid
}
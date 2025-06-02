#pragma once
#include<iostream>
#include<string>
#include<atomic>
#include<array>
#include<vector>
constexpr size_t MAX_PRICES = 10000;

class PriceBuffer {
public:
	void add(float price);

	std::vector<float> getRecentList();
	size_t getIndex();

	float getLast();

private:
	std::array<float, MAX_PRICES> data{};
	std::atomic<size_t> index{ 0 };
};


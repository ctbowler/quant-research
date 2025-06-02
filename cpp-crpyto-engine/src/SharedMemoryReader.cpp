#include "SharedMemoryReader.hpp"
#include <iostream>
#include <cstring>
#include <mutex>
#include<string>
#include "CandleBuffer.hpp" 

SharedMemoryReader::SharedMemoryReader(const std::wstring& name, size_t size)
    : shmName(name), shmSize(size), hMapFile(NULL), shmPtr(nullptr) {
}

SharedMemoryReader::~SharedMemoryReader() {
    if (shmPtr) UnmapViewOfFile(shmPtr);
    if (hMapFile) CloseHandle(hMapFile);
}

bool SharedMemoryReader::initialize(int max_attempts, int delay_ms) {
    for (int attempt = 1; attempt <= max_attempts; ++attempt) {
        hMapFile = OpenFileMappingW(FILE_MAP_READ, FALSE, shmName.c_str());
        if (hMapFile) {
            shmPtr = MapViewOfFile(hMapFile, FILE_MAP_READ, 0, 0, shmSize);
            if (shmPtr) {
                const char* data = reinterpret_cast<const char*>(shmPtr);
                std::cout << "[C++] Read from shared memory: " << std::string(data, 32) << std::endl;
                return true;
            }
            else {
                std::cerr << "[SharedMemoryReader] Failed to map view of file: " << GetLastError() << std::endl;
                CloseHandle(hMapFile);
                hMapFile = NULL;
            }
        }
        else {
            std::cerr << "[SharedMemoryReader] Failed to open file mapping (Attempt " << attempt
                << "): " << GetLastError() << std::endl;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));
    }

    return false;
}



bool SharedMemoryReader::isReady() const {
    return shmPtr != nullptr;
}

MessageType SharedMemoryReader::getMessageType() const {
    return static_cast<MessageType>(reinterpret_cast<const char*>(shmPtr)[0]);
}




bool SharedMemoryReader::readOrderBook(OrderBook& book, std::mutex& book_mtx) {

    OrderBookMessage temp;
    std::memcpy(&temp, reinterpret_cast<const char*>(shmPtr), sizeof(OrderBookMessage));

    std::lock_guard<std::mutex> lock(book_mtx);
    book.clearBook();

    for (int i = 0; i < 40; i += 2) {
        double bid_price = temp.bids[i];
        double bid_qty = temp.bids[i + 1];
        double ask_price = temp.asks[i];
        double ask_qty = temp.asks[i + 1];

        char safe_ts[24];
        std::memcpy(safe_ts, temp.timestamp, 23);
        safe_ts[23] = '\0';
        std::string ts(safe_ts);

        if (bid_price > 0 && bid_qty > 0)
            book.insertLimitOrder(Order(1, OrderSide::BUY, bid_price, bid_qty, OrderType::LIMIT, safe_ts));
        if (ask_price > 0 && ask_qty > 0)
            book.insertLimitOrder(Order(2, OrderSide::SELL, ask_price, ask_qty, OrderType::LIMIT, safe_ts));
    }

    return true;
}







bool SharedMemoryReader::readMarket(PriceBuffer& price_buffer, std::mutex& pricebuffer_mtx) {
    auto* ptr = reinterpret_cast<const MarketOrderMessage*>(reinterpret_cast<const char*>(shmPtr));

    std::lock_guard<std::mutex> lock(pricebuffer_mtx);

    price_buffer.add(ptr->price);
    
    return true;


}




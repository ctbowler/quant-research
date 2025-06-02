#pragma once
#include "MessageStructs.hpp"
#include <string>
#include <optional>
#include <windows.h>
#include "OrderBook.hpp"
#include "Order.hpp"
#include <mutex>
#include "PriceBuffer.hpp"
#include "CandleBuffer.hpp"

class SharedMemoryReader {
public:
    SharedMemoryReader(const std::wstring& shm_name, size_t shm_size);
    

    bool initialize(int max_attempts, int delay_ms);
    bool isReady() const;

    bool readOrderBook(OrderBook& order, std::mutex& book_mtx);
    bool readCandle(CandleBuffer& buffer, std::mutex& mutex);
    bool readMarket(PriceBuffer& price_buffer, std::mutex& pricebuffer_mtx);


    MessageType getMessageType() const;
    ~SharedMemoryReader();
private:
    std::wstring shmName;
    size_t shmSize;
    HANDLE hMapFile;
    void* shmPtr;
};
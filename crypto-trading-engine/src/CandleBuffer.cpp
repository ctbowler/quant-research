#include "CandleBuffer.hpp"

void CandleBuffer::addCandle(const std::string& timestamp_min, const CandleMessage& tick) {
    buffer[timestamp_min].emplace_back(tick);
}

std::map<std::string, std::vector<CandleMessage>>& CandleBuffer::getBuffer() {
    return buffer;
}

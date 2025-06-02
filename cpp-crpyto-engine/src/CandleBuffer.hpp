#pragma once
#include <string>
#include <vector>
#include <map>
#include "MessageStructs.hpp"

enum class CandlePosition {
    EARLIEST,
    NEWEST,
    MIDDLE
};

class CandleBuffer {
public:
    CandlePosition addCandle(const std::string& timestamp_min, const CandleMessage& tick) {

        buffer[timestamp_min].emplace_back(tick);

        if (buffer.size() > max_candles) {
            buffer.erase(buffer.begin());
        }

        auto it = buffer.begin();
        if (timestamp_min == it->first) return CandlePosition::EARLIEST;
        auto last_it = buffer.end();
        --last_it;
        if (timestamp_min == last_it->first) return CandlePosition::NEWEST;

        std::cout << "[CANDLE BUFFER] Added candle for " << timestamp_min << "\n";

        return CandlePosition::MIDDLE;
    }

    std::map<std::string, std::vector<CandleMessage>>& getBuffer() {
        return buffer;
    }

    bool hasData() const {
        return !buffer.empty();
    }

    CandleMessage getLastCandle() const {
        if (buffer.empty()) return {};
        auto it = buffer.end();
        --it;
        const auto& vec = it->second;
        if (!vec.empty()) {
            return vec.back();
        }
        return {};
    }

private:
    std::map<std::string, std::vector<CandleMessage>> buffer;
    const size_t max_candles = 500;
};

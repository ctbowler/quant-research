#pragma once
#include <cstring>
#include "CandleBuffer.hpp"
#include "imgui/imgui.h"
#include <vector>
#include <string>
#include <algorithm>
#include <ctime>
#include <iomanip>
#include <chrono>
#include <sstream>

// Helper function to build candles from market price
// Helper function to build candles from market price
// Helper function to build candles from market price
inline void UpdateCandle(CandleBuffer& buffer, PriceBuffer& price_buffer) {
    static std::string last_minute = "";
    static CandleMessage current_candle{};
    static bool initialized = false;

    double price = price_buffer.getLast();

    // Get current minute timestamp
    auto now = std::chrono::system_clock::now();
    auto t = std::chrono::system_clock::to_time_t(now);
    std::tm tm{};
    localtime_s(&tm, &t);
    char minute_buf[20];
    std::strftime(minute_buf, sizeof(minute_buf), "%Y-%m-%dT%H:%M", &tm);
    std::string current_minute(minute_buf);

    if (!initialized || current_minute != last_minute) {
        if (initialized) {
            // Finalize previous candle
            strncpy_s(current_candle.timestamp, sizeof(current_candle.timestamp),
                last_minute.c_str(), _TRUNCATE);
            buffer.addCandle(last_minute, current_candle);
        }

        // Start new candle
        current_candle = CandleMessage{};
        strncpy_s(current_candle.timestamp, sizeof(current_candle.timestamp),
            current_minute.c_str(), _TRUNCATE);

        current_candle.open = price;
        current_candle.high = price;
        current_candle.low = price;
        current_candle.close = price;
        current_candle.volume = 0.0;

        last_minute = current_minute;
        initialized = true;
    }
    else {
        // Update ongoing candle
        current_candle.close = price;
        current_candle.high = std::max(current_candle.high, price);
        current_candle.low = std::min(current_candle.low, price);
    }
    std::cout << "[CANDLE THREAD] Price: " << price << ", Minute: " << current_minute << "\n";

}




inline void RenderCandleChart(CandleBuffer& buffer, PriceBuffer& price_buffer) {
    static float zoom_level = 1.0f;
    static float y_zoom_scale = 1.0f;

    // --- ImGui Chart UI ---
    ImGui::SetNextWindowPos(ImVec2(850, 100), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(700, 400), ImGuiCond_FirstUseEver);

    ImGui::Begin("Candlestick Chart", nullptr,
        ImGuiWindowFlags_NoCollapse |
        ImGuiWindowFlags_NoScrollbar |
        ImGuiWindowFlags_NoScrollWithMouse |
        ImGuiWindowFlags_NoSavedSettings);

    ImGui::SliderFloat("X Zoom", &zoom_level, 0.1f, 2.0f, "%.2fx");
    ImGui::SliderFloat("Y Zoom", &y_zoom_scale, 0.1f, 5.0f, "%.1fx");

    ImVec2 pos = ImGui::GetCursorScreenPos();
    ImVec2 size = ImGui::GetContentRegionAvail();
    ImDrawList* draw = ImGui::GetWindowDrawList();

    draw->AddRectFilled(pos, ImVec2(pos.x + size.x, pos.y + size.y), IM_COL32(10, 10, 10, 255));

    const auto& buf = buffer.getBuffer();
    if (buf.size() < 2) {
        ImGui::Text("Waiting for candle data...");
        ImGui::End();
        return;
    }

    std::vector<CandleMessage> candles;
    for (const auto& [minute, messages] : buf) {
        if (!messages.empty())
            candles.push_back(messages.back());
    }

    if (candles.size() < 2) {
        ImGui::Text("Not enough candle points.");
        ImGui::End();
        return;
    }

    size_t visible = static_cast<size_t>(candles.size() * (1.0f / zoom_level));
    visible = std::clamp(visible, size_t(2), candles.size());
    auto start = candles.end() - visible;
    std::vector<CandleMessage> view(start, candles.end());

    auto max_it = std::max_element(view.begin(), view.end(), [](const auto& a, const auto& b) { return a.high < b.high; });
    auto min_it = std::min_element(view.begin(), view.end(), [](const auto& a, const auto& b) { return a.low < b.low; });

    float max_price = static_cast<float>(max_it->high);
    float min_price = static_cast<float>(min_it->low);
    float mid_price = static_cast<float>(view.back().close);
    float range = std::max<float>((max_price - min_price) / y_zoom_scale, 1e-6f);
    float y_min = mid_price - range / 2;
    float y_max = mid_price + range / 2;

    float candle_width = size.x / static_cast<float>(view.size());
    float half_width = candle_width * 0.4f;

    auto price_to_y = [&](float price) {
        return pos.y + size.y * (1.0f - (price - y_min) / (y_max - y_min));
        };

    for (size_t i = 0; i < view.size(); ++i) {
        const CandleMessage& c = view[i];
        double live_close = (i == view.size() - 1) ? price_buffer.getLast() : c.close;

        float x_center = pos.x + i * candle_width + candle_width * 0.5f;
        float y_open = price_to_y(static_cast<float>(c.open));
        float y_close = price_to_y(static_cast<float>(live_close));
        float y_high = price_to_y(static_cast<float>(c.high));
        float y_low = price_to_y(static_cast<float>(c.low));

        ImU32 color = (live_close >= c.open) ? IM_COL32(0, 255, 0, 220) : IM_COL32(255, 0, 0, 220);

        draw->AddLine(ImVec2(x_center, y_high), ImVec2(x_center, y_low), color, 1.0f);
        draw->AddRectFilled(ImVec2(x_center - half_width, y_open), ImVec2(x_center + half_width, y_close), color);
    }

    int grid_lines = 5;
    for (int i = 1; i < grid_lines; ++i) {
        float frac = (float)i / grid_lines;
        float y = pos.y + size.y * frac;
        draw->AddLine(ImVec2(pos.x, y), ImVec2(pos.x + size.x, y), IM_COL32(255, 255, 255, 20));
        float price = y_max - frac * (y_max - y_min);
        char label[32];
        snprintf(label, sizeof(label), "$%.2f", price);
        draw->AddText(ImVec2(pos.x + 5, y - 8), IM_COL32(200, 200, 200, 180), label);
    }

    ImGui::InvisibleButton("candlespace", size);
    ImGui::End();
}

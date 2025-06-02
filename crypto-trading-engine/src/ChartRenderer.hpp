#pragma once
#include "PriceBuffer.hpp"
#include "imgui/imgui.h"
#include <algorithm>
#include <iostream>

std::mutex candle_mutex;

inline void RenderOpenGLChart(PriceBuffer& buffer) {
    static float zoom_level = 1.0f;
    static float y_zoom_scale = 1.0f;

    ImGui::SetNextWindowPos(ImVec2(100, 100), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(700, 400), ImGuiCond_FirstUseEver);

    ImGui::Begin("Live Price Chart", nullptr,
        ImGuiWindowFlags_NoCollapse |
        ImGuiWindowFlags_NoScrollbar |
        ImGuiWindowFlags_NoScrollWithMouse |
        ImGuiWindowFlags_NoSavedSettings);

    ImGui::SliderFloat("X Zoom (Zoom Out to Show More)", &zoom_level, 0.01f, 2.0f, "%.2fx");
    ImGui::SliderFloat("Y Zoom", &y_zoom_scale, 0.1f, 5.0f, "%.1fx");

    ImVec2 pos = ImGui::GetCursorScreenPos();
    ImVec2 size = ImGui::GetContentRegionAvail();
    ImVec2 mouse = ImGui::GetMousePos();
    ImDrawList* draw = ImGui::GetWindowDrawList();

    draw->AddRectFilled(pos, ImVec2(pos.x + size.x, pos.y + size.y), IM_COL32(10, 10, 10, 255));

    static std::vector<float> cached_prices;
    static std::vector<ImVec2> points;
    static size_t last_index = -1;

    size_t current_index = buffer.getIndex();
    if (cached_prices.empty()) {
        cached_prices = buffer.getRecentList();
        last_index = current_index;
    }

    cached_prices = buffer.getRecentList();
    if (cached_prices.size() < 2) {
        ImGui::Text("Not enough data to render chart.");
        ImGui::End();
        return;
    }


    size_t visible_count = static_cast<size_t>(cached_prices.size() * (1.0f / zoom_level));
    visible_count = std::clamp(visible_count, size_t(2), cached_prices.size());

    // 1. Select recent prices based on zoom level
    auto start_it = cached_prices.end() - visible_count;
    std::vector<float> view_prices(start_it, cached_prices.end());

    // 2. Downsample based on available screen pixels
    size_t max_render_points = static_cast<size_t>(size.x); // 1 point per pixel max
    if (view_prices.size() > max_render_points) {
        std::vector<float> downsampled;
        size_t stride = view_prices.size() / max_render_points;
        stride = std::max<size_t>(1, stride);

        for (size_t i = 0; i < view_prices.size(); i += stride) {
            downsampled.push_back(view_prices[i]);
        }
        view_prices = std::move(downsampled);
    }


    float last_price = view_prices.back();
    float y_range = (*std::max_element(view_prices.begin(), view_prices.end()) - *std::min_element(view_prices.begin(), view_prices.end()));
    y_range = std::max(y_range / y_zoom_scale, 1e-6f);
    float min_price = last_price - y_range / 2;
    float max_price = last_price + y_range / 2;
    float range = max_price - min_price;

    if (last_price < min_price || last_price > max_price) {
        min_price = last_price - y_range / 2;
        max_price = last_price + y_range / 2;
        range = max_price - min_price;
    }

    points.clear();
    points.reserve(view_prices.size());
    for (size_t i = 0; i < view_prices.size(); ++i) {
        float x = pos.x + ((float)i / (view_prices.size() - 1)) * size.x;
        float y = pos.y + size.y * (1.0f - (view_prices[i] - min_price) / range);
        points.emplace_back(x, y);
    }


    draw->AddPolyline(points.data(), points.size(), IM_COL32(255, 255, 255, 255), false, 2.0f);
    draw->AddCircleFilled(points.back(), 4.0f, IM_COL32(255, 0, 0, 255));

    draw->AddLine(ImVec2(pos.x, pos.y), ImVec2(pos.x + size.x, pos.y), IM_COL32(255, 255, 255, 30));
    draw->AddLine(ImVec2(pos.x, pos.y + size.y), ImVec2(pos.x + size.x, pos.y + size.y), IM_COL32(255, 255, 255, 30));

    int grid_lines = 5;
    for (int i = 1; i < grid_lines; ++i) {
        float frac = (float)i / grid_lines;
        float y = pos.y + size.y * frac;
        draw->AddLine(ImVec2(pos.x, y), ImVec2(pos.x + size.x, y), IM_COL32(255, 255, 255, 20));
        float price = max_price - frac * range;
        char label[32];
        snprintf(label, sizeof(label), "$%.2f", price);
        draw->AddText(ImVec2(pos.x + 5, y - 8), IM_COL32(200, 200, 200, 180), label);
    }

    if (ImGui::IsWindowHovered()) {
        float mx = mouse.x;
        if (mx >= pos.x && mx <= pos.x + size.x) {
            size_t idx = std::min((size_t)((mx - pos.x) / size.x * view_prices.size()), view_prices.size() - 1);
            float px = pos.x + ((float)idx / (view_prices.size() - 1)) * size.x;
            float py = pos.y + size.y * (1.0f - (view_prices[idx] - min_price) / range);
            draw->AddLine(ImVec2(px, pos.y), ImVec2(px, pos.y + size.y), IM_COL32(255, 255, 255, 60), 1.0f);

            char label[32];
            snprintf(label, sizeof(label), "$%.2f", view_prices[idx]);
            draw->AddText(ImVec2(px + 6, pos.y + 6), IM_COL32(255, 255, 255, 255), label);
        }
    }

    ImGui::SetCursorScreenPos(ImVec2(pos.x + 10, pos.y + 10));
    ImGui::PushFont(ImGui::GetFont());
    ImGui::TextColored(ImVec4(1.0f, 1.0f, 0.0f, 1.0f), "$%.2f", last_price);
    ImGui::PopFont();

    ImGui::InvisibleButton("chartspace", size);
    ImGui::End();
}

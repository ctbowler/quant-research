#define NOMINMAX
#include <iostream>
#include <string>
#include <thread>
#include <mutex>
#include <chrono>
#include <GLFW/glfw3.h>
#include <GL/gl.h>
#include "imgui/imgui.h"
#include "imgui/backends/imgui_impl_glfw.h"
#include "imgui/backends/imgui_impl_opengl3.h"
#include "Order.hpp"
#include "OrderBook.hpp"
#include "PriceBuffer.hpp"
#include "ChartRenderer.hpp"
#include "SharedMemoryReader.hpp"
#include "CandleBuffer.hpp"
#include "CandleRenderer.hpp"
#include <algorithm>

//*** GLOBAL VARIABLES *** //
OrderBook book;
PriceBuffer price_buffer;
std::mutex book_mutex;
std::mutex pricebuffer_mutex;
CandleBuffer candle_buffer;
extern std::mutex candle_mutex;

int main() {
    if (!glfwInit()) return -1;
    

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 0);
    GLFWwindow* window = glfwCreateWindow(1280, 720, "Order Book GUI", nullptr, nullptr);
    if (!window) return -1;
    glfwMakeContextCurrent(window);
    glfwSwapInterval(1); // Enable VSync

    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO(); (void)io;
    ImGui::StyleColorsDark();

    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL3_Init("#version 130");

    // --- Shared memory reader threads --- //
    std::thread orderbook_thread([] {
        SharedMemoryReader reader(L"Local\\orderbook_data", 4096);
        if (!reader.initialize(20, 500)) {
            std::cerr << "❌ Could not initialize orderbook shared memory.\n";
            return;
        }
        while (true) {
            reader.readOrderBook(book, book_mutex);
            std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        }
        });

    std::thread market_thread([] {
        SharedMemoryReader reader(L"Local\\market_data", 4096);
        if (!reader.initialize(20, 500)) {
            std::cerr << "❌ Could not initialize market shared memory.\n";
            return;
        }
        while (true) {
            reader.readMarket(price_buffer, pricebuffer_mutex);
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
        });

    std::thread candle_thread([] {
        while (true) {
            {
                std::lock_guard<std::mutex> lock(pricebuffer_mutex);
                UpdateCandle(candle_buffer, price_buffer);
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(500));  // or 1000ms
        }
        });
    candle_thread.detach();




   

    
    orderbook_thread.detach();
    market_thread.detach();
    

    using clock = std::chrono::steady_clock;
    auto last_frame_time = clock::now();

    while (!glfwWindowShouldClose(window)) {
        auto now = clock::now();
        float frame_ms = std::chrono::duration<float, std::milli>(now - last_frame_time).count();
        if (frame_ms < 16.67f) {
            std::this_thread::sleep_for(std::chrono::milliseconds((int)(16.67f - frame_ms)));
        }
        last_frame_time = clock::now();

        glfwPollEvents();
        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();

        ImGui::Begin("Order Book");
        if (ImGui::BeginTable("OrderTable", 4, ImGuiTableFlags_Borders | ImGuiTableFlags_RowBg)) {
            ImGui::TableSetupColumn("Time");
            ImGui::TableSetupColumn("Side");
            ImGui::TableSetupColumn("Price");
            ImGui::TableSetupColumn("Qty");
            ImGui::TableHeadersRow();

            {
                std::lock_guard<std::mutex> lock(book_mutex);
                for (const auto& [price, orders] : book.getBidMap()) {
                    for (const auto& o : orders) {
                        ImGui::TableNextRow();
                        ImGui::TableSetColumnIndex(0); ImGui::Text("%s", o.timestamp.c_str());
                        ImGui::TableSetColumnIndex(1); ImGui::TextColored(ImVec4(0.1f, 1.0f, 0.1f, 1.0f), "BUY");
                        ImGui::TableSetColumnIndex(2); ImGui::Text("%.2f", o.price);
                        ImGui::TableSetColumnIndex(3); ImGui::Text("%.4f", o.quantity);
                    }
                }
                for (const auto& [price, orders] : book.getAskMap()) {
                    for (const auto& o : orders) {
                        ImGui::TableNextRow();
                        ImGui::TableSetColumnIndex(0); ImGui::Text("%s", o.timestamp.c_str());
                        ImGui::TableSetColumnIndex(1); ImGui::TextColored(ImVec4(1.0f, 0.3f, 0.3f, 1.0f), "SELL");
                        ImGui::TableSetColumnIndex(2); ImGui::Text("%.2f", o.price);
                        ImGui::TableSetColumnIndex(3); ImGui::Text("%.4f", o.quantity);
                    }
                }
            }
            ImGui::EndTable();
        }
        ImGui::End();

        ImGui::Begin("Submit Order");
        static int orderId = 300;
        static float price = 100.0f;
        static double quantity = 10;
        static int side = 0;
        ImGui::InputInt("Order ID", &orderId);
        ImGui::InputFloat("Price", &price);
        ImGui::InputDouble("Quantity", &quantity);
        ImGui::RadioButton("Buy", &side, 0); ImGui::SameLine();
        ImGui::RadioButton("Sell", &side, 1);
        if (ImGui::Button("Submit Order")) {
            Order newOrder = { orderId, (side == 0) ? OrderSide::BUY : OrderSide::SELL, price, quantity, OrderType::LIMIT, "" };
            std::lock_guard<std::mutex> lock(book_mutex);
            if (side == 0) book.matchBuyOrder(newOrder);
            else book.matchSellOrder(newOrder);
        }
        ImGui::End();

        ImGui::Begin("Cancel Order");
        static int cancelId = 0;
        ImGui::InputInt("Order ID", &cancelId);
        if (ImGui::Button("Cancel")) {
            std::lock_guard<std::mutex> lock(book_mutex);
            if (!book.cancelOrder(cancelId)) {
                ImGui::TextColored(ImVec4(1, 0.3f, 0.3f, 1), "❌ Cancel failed (not found)");
            }
        }
        ImGui::End();

        {
            std::lock_guard<std::mutex> lock(pricebuffer_mutex);
            RenderOpenGLChart(price_buffer);
        }
        {
            std::lock_guard<std::mutex> lock(candle_mutex);
            RenderCandleChart(candle_buffer, price_buffer);
        }


      


        ImGui::Begin("Candle Buffer Info");
        {
            std::lock_guard<std::mutex> lock(candle_mutex);
            const auto& buf = candle_buffer.getBuffer();
            if (!buf.empty()) {
                auto last = std::prev(buf.end()); // gets the last (most recent) entry
                const auto& ticks = last->second;
                if (!ticks.empty()) {
                    const auto& c = ticks.back();
                    ImGui::Text("Latest Candle");
                    ImGui::Text("Open: %.2f", c.open);
                    ImGui::Text("Close: %.2f", c.close);
                    ImGui::Text("High: %.2f", c.high);
                    ImGui::Text("Low: %.2f", c.low);
                    ImGui::Text("Volume: %.4f", c.volume);
                    ImGui::Text("Time: %s", c.timestamp);
                }
            }
        }
        ImGui::End();


        ImGui::Render();
        int display_w, display_h;
        glfwGetFramebufferSize(window, &display_w, &display_h);
        glViewport(0, 0, display_w, display_h);
        glClearColor(0.1f, 0.1f, 0.1f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
        glfwSwapBuffers(window);
    }

    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();
    glfwDestroyWindow(window);
    glfwTerminate();
    return 0;
}

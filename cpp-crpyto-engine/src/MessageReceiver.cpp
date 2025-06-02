#include <iostream>
#include <cstring>
#include <winsock2.h> // for sockets
#include <ws2tcpip.h> // for close()
#include "MessageStructs.hpp" // corresponding structures for imported binary data
#include <mutex>
#include "OrderBook.hpp"
#include <atomic>
#include <optional>


#pragma comment(lib, "ws2_32.lib")

// Shared data containers
std::optional<CandleMessage> latestCandle;
std::optional<MarketOrderMessage> latestTrade;

// Mutexes for each
std::mutex candle_mutex;
std::mutex trade_mutex;
std::mutex snapshot_mutex;

// Signal to exit gracefully
std::atomic<bool> running(true);

void messageReceiver(SOCKET client_fd, OrderBook& book, std::mutex& mtx, PriceBuffer& price_buffer) {


    // **** Read And Write Data ****
    while (true) {
        // --- Read 4-byte length header ---
        uint32_t msg_len = 0;
        int header_bytes = recv(client_fd, reinterpret_cast<char*>(&msg_len), sizeof(uint32_t), MSG_WAITALL);
        if (header_bytes != sizeof(uint32_t)) {
            std::cerr << "[Error] Failed to read message length. Exiting.\n";
            break;
        }

        // --- Read 1-byte message type ---
        char msg_type;
        int type_byte = recv(client_fd, &msg_type, 1, MSG_WAITALL);
        if (type_byte != 1) {
            std::cerr << "[Error] Failed to read message type. Expected byte size not aligning. Exiting.\n";
            break;
        }

        // --- Read message payload (msg_len - 1 because type byte is already read) ---
        std::vector<char> buffer(msg_len - 1);
        int payload_bytes = recv(client_fd, buffer.data(), msg_len - 1, MSG_WAITALL);
        if (payload_bytes != static_cast<int>(msg_len - 1)) {
            std::cerr << "[Error] Failed to read message payload. Exiting.\n";
            break;
        }

        else if (msg_type == 'O') {
            if (buffer.size() != sizeof(OrderBookMessage)) {
                std::cerr << "[Error] OrdeBook byte length doesnt match the buffer size!\n";
                continue;
            }

            OrderBookMessage* ob = reinterpret_cast<OrderBookMessage*>(buffer.data());
            std::lock_guard lock(mtx);

            book.clearBook();

            for (int i = 0; i < 40; i += 2) {
                //Order new_bid = Order(book.generateOrderID(), OrderSide::BUY, ob->bids[i], ob->bids[i + 1], OrderType::LIMIT, ob->timestamp);
                //Order new_ask = Order(book.generateOrderID(), OrderSide::SELL, ob->asks[i], ob->asks[i + 1], OrderType::LIMIT, ob->timestamp);

                //if (ob->bids[i + 1] > 0)
                //    book.insertLimitOrder(std::ref(new_bid), 0);
                //if (ob->asks[i + 1] > 0)
                //    book.insertLimitOrder(std::ref(new_ask), 0);

            }
        }
        else if (msg_type == 'U') {
            if (buffer.size() != sizeof(OrderBookMessage)) {
                std::cerr << "[Error] OrdeBook byte length doesnt match the buffer size!\n";
            }

            OrderBookMessage *ob_update = reinterpret_cast<OrderBookMessage*>(buffer.data());
            std::lock_guard lock(mtx);

            book.clearBook();

            for (int i = 0; i < 40; i += 2) {
                double bid_price = ob_update->bids[i];
                double bid_qty = ob_update->bids[i + 1];
                double ask_price = ob_update->asks[i];
                double ask_qty = ob_update->asks[i + 1];

                /**
                if (bid_qty > 0) {
                    Order new_bid = Order(book.generateOrderID(), OrderSide::BUY, bid_price, bid_qty, OrderType::LIMIT, ob_update->timestamp);
                    book.insertLimitOrder(std::ref(new_bid), 0);
                }

                if (ask_qty > 0) {
                    Order new_ask = Order(book.generateOrderID(), OrderSide::SELL, ask_price, ask_qty, OrderType::LIMIT, ob_update->timestamp);
                    book.insertLimitOrder(std::ref(new_ask), 0);
                }
                **/
            }
        }
        else if (msg_type == 'C') {
            if (buffer.size() != sizeof(CandleMessage)) {
                std::cerr << "[Error] Candle size mismatch.\n";
                continue;
            }

            CandleMessage* cm = reinterpret_cast<CandleMessage*>(buffer.data());
            std::lock_guard<std::mutex> lock(candle_mutex);
            latestCandle = *cm;
        }


        else if (msg_type == 'M') {
            if (buffer.size() != sizeof(MarketOrderMessage)) {
                std::cerr << "[Error] Market order size mismatch.\n";
                continue;
            }

            MarketOrderMessage* mom = reinterpret_cast<MarketOrderMessage*>(buffer.data());
            std::lock_guard<std::mutex> lock(mtx);
            double recent_price = mom->price;
            price_buffer.add(recent_price);
        }

        else {
            std::cerr << "[Error] Unknown message type: " << static_cast<int>(msg_type) << "\n";
            continue;
        }
    }

}

void runSocketReceiver(OrderBook& book, std::mutex& mtx, PriceBuffer& price_buffer) {
    // Initialize Winsock
    WSADATA wsaData; // struct for implementation info
    int wsaInit = WSAStartup(MAKEWORD(2, 2), &wsaData); // initializing windows socket api
    if (wsaInit != 0) {
        std::cerr << "WSAStartup failed with error: " << wsaInit << "\n";

    }

    // Create socket
    SOCKET server_fd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP); // ipv4 address family, socket stream = TCP, TCP protocol
    if (server_fd == INVALID_SOCKET) {
        std::cerr << "Socket creation failed.\n";
        WSACleanup();

    }


    // Bind to port 9999
    sockaddr_in server_addr{};
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(9999);
    if (bind(server_fd, (sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        std::cerr << "Bind failed.\n";
        closesocket(server_fd);
        WSACleanup();

    }

    // Listen for connections
    if (listen(server_fd, 1) == SOCKET_ERROR) {
        std::cerr << "Listen failed.\n";
        closesocket(server_fd);
        WSACleanup();

    }

    std::cout << "Server is listening on port 9999...\n";

    //  Accept a client connection
    SOCKET client_fd = accept(server_fd, nullptr, nullptr);
    if (client_fd == INVALID_SOCKET) {
        std::cerr << "Accept failed.\n";
        closesocket(server_fd);
        WSACleanup();

    }

    std::cout << "Client connected!\n";
    messageReceiver(client_fd, book, mtx, price_buffer);
   

    // Cleanup
    closesocket(client_fd);
    closesocket(server_fd);
    WSACleanup();


}
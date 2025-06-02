cmake_minimum_required(VERSION 3.16)
project(TradingEngine)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# === Source Files ===
file(GLOB_RECURSE SRC_FILES src/*.cpp src/*.hpp)

# === Add Executable ===
add_executable(TradingEngine ${SRC_FILES})

# === Include Paths ===
# These must point to your local or system-installed ImGui and GLFW
target_include_directories(TradingEngine PRIVATE
    src/
    path/to/imgui             # User must set this
    path/to/imgui/backends    # User must set this
)

# === Link Libraries ===
find_package(OpenGL REQUIRED)
find_package(glfw3 REQUIRED)

target_link_libraries(TradingEngine PRIVATE
    OpenGL::GL
    glfw
)

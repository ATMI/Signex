cmake_minimum_required(VERSION 3.10)
project(Signex)

set(CMAKE_CXX_STANDARD 17)

link_directories(darknet)
add_executable(Signex main.cpp)

target_link_libraries(Signex darknet)
include_directories(darknet/include)

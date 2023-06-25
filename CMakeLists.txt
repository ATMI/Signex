cmake_minimum_required(VERSION 3.10)
project(Signex)

set(CMAKE_CXX_STANDARD 17)

link_directories(darknet)
add_executable(Signex main.cpp)

target_link_libraries(Signex darknet)
include_directories(darknet/include)

add_executable(shufflels shufflels.cpp)

add_custom_target(
		make-lists
		DEPENDS shufflels
		COMMAND rm ../cfg/test.lst ../cfg/train.lst || true
		COMMAND cd ../cfg && ${CMAKE_CURRENT_BINARY_DIR}/shufflels ../dataset/images jpg 80
)

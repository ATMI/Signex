cmake_minimum_required(VERSION 3.10)
project(signex)

set(CMAKE_CXX_STANDARD 17)

link_directories(darknet)
add_executable(signex main.cpp)

target_link_libraries(signex darknet)
include_directories(darknet/include)

add_executable(shufflels shufflels.cpp)

set(DARKNET_PATH ${CMAKE_CURRENT_LIST_DIR}/darknet)

add_custom_target(
		darknet
		COMMAND cd ${DARKNET_PATH} && make OPENCV=1 GPU=1
)

add_custom_target(
		darknet-clean
		COMMAND cd ${DARKNET_PATH} && make clean
)

add_custom_target(
		make-lists
		DEPENDS shufflels
		COMMAND rm ../cfg/test.lst ../cfg/train.lst || true
		COMMAND cd ../cfg && ${CMAKE_CURRENT_BINARY_DIR}/shufflels ../dataset/images jpg 80
)

add_custom_target(
		start-train
		DEPENDS darknet make-lists
		COMMAND cd ${CMAKE_CURRENT_LIST_DIR}/cfg && screen -dmS train ${DARKNET_PATH}/darknet detector train data.cfg net.cfg \"\" -clear -dont_show
)

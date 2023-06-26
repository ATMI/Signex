cmake_minimum_required(VERSION 3.10)
project(signex)

set(CMAKE_CXX_STANDARD 17)

link_directories(darknet)
add_executable(signex main.cpp)

target_link_libraries(signex darknet)
include_directories(darknet/include)

add_executable(shufflels shufflels.cpp)

set(DARKNET_DIR ${CMAKE_CURRENT_LIST_DIR}/darknet)
set(DATASET_DIR ${CMAKE_CURRENT_LIST_DIR}/dataset)
set(MODELS_DIR ${CMAKE_CURRENT_LIST_DIR}/models)

set(CFG_DIR ${CMAKE_CURRENT_LIST_DIR}/cfg)
set(DATA_CFG ${CFG_DIR}/data.cfg)
set(NET_CFG ${CFG_DIR}/net.cfg)

set(TEST_CFG ${CFG_DIR}/test.cfg)
set(TEST_WEIGHTS ${MODELS_DIR}/net.backup)

file(GLOB TEST_IMAGES ${DATASET_DIR}/test/*)
list(LENGTH TEST_IMAGES TEST_IMAGES_COUNT)

if (${TEST_IMAGES_COUNT} GREATER 0)
	message("In total ${TEST_IMAGES_COUNT} test image(-s) found")
	string(RANDOM LENGTH 5 ALPHABET "0123456789" RANDOM_INDEX)
	math(EXPR TEST_IMAGE_INDEX "${RANDOM_INDEX} % ${TEST_IMAGES_COUNT}")
	message("Random index: ${TEST_IMAGE_INDEX}")
	list(GET TEST_IMAGES ${TEST_IMAGE_INDEX} TEST_IMAGE)
	message("Test file: ${TEST_IMAGE}")
else ()
	message("No test images found")
endif ()

add_custom_target(
		darknet
		COMMAND cd ${DARKNET_DIR} && make OPENCV=1 GPU=1
)

add_custom_target(
		darknet-clean
		COMMAND cd ${DARKNET_DIR} && make clean
)

add_custom_target(
		make-lists
		DEPENDS shufflels
		COMMAND rm ../cfg/test.lst ../cfg/train.lst || true
		COMMAND cd ../cfg && ${CMAKE_CURRENT_BINARY_DIR}/shufflels ../dataset/images jpg 80
)

add_custom_target(
		train
		DEPENDS darknet make-lists
		COMMAND cd ${DARKNET_DIR} && screen -dmS train ./darknet detector train ${DATA_CFG} ${NET_CFG} \"\" -clear -dont_show
)

add_custom_target(
		test
		DEPENDS darknet make-lists
		COMMAND cd ${DARKNET_DIR} && ./darknet detector test ${DATA_CFG} ${TEST_CFG} ${TEST_WEIGHTS} ${TEST_IMAGE}
)

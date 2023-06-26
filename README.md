# Signex

Signex is open source signature & stamp recognition tool, that uses YOLO-based model and
modified [Darknet](https://github.com/ATMI/darknet) framework.

## Table of Contents

* [Introduction](#introduction)
* [Architecture](#architecture)
* [Requirements](#requirements)
* [Installation](#installation)
* [Usage](#usage)
* [Contributing](#contributing)
* [License](#license)

## Introduction

Signature & stamp recognition is a valuable tool in various domains, including banking, legal, and security
applications. This architecture provides a framework for building a signature recognition system using machine learning
algorithms.

## Requirements

To run the signature recognition architecture, the following requirements should be fulfilled:

* Linux machine, this project was not tested on Windows & Mac
* Sufficient computing resources (CPU/GPU) for training and inference

## Installation

1. Clone the repository:

```shell
git clone --recurse-submodules git@gitlab.pg.innopolis.university:sofwarus-progectus/signature-recognition.git
```

2. Optionally you can install:

* OpenCV - version 4.x
* CUDA & cuDNN

## Build

Signex uses Darknet to run & train neural networks. By default, Darknet is built with OpenCV and CUDA support. To
disable them, modify the `darknet` target
in the [CMake file](CMakeLists.txt):

```cmake
add_custom_target(
		darknet
		COMMAND cd ${DARKNET_PATH} && make OPENCV=1 GPU=1
)
```

Available options (set 1 to enable, otherwise - 0):

* `DEBUG` - build debug version of darknet
* `OPENCV` - use OpenCV to load & transform images
* `GPU` - use CUDA to run & train neural network, set your GPU `ARCH` in the [Darknet's Makefile](darknet/Makefile)
* `CUDNN` - unsafe, not tested
* `OPENMP` - unsafe, not tested

Build `start-train` target to build all required dependencies and start the training process.

There is a possibility, that you will need to specify custom include and lib paths in the
[Darknet's Makefile](darknet/Makefile) to build it:

* OpenCV:

```makefile
ifeq ($(OPENCV), 1) 
COMMON+= -DOPENCV
CFLAGS+= -DOPENCV
LDFLAGS+= `pkg-config --libs opencv4` -lstdc++ # Add OpenCV lib path here
COMMON+= -I/usr/include/opencv4 `pkg-config --cflags opencv4` # Add OpenCV include path here
endif
```

* CUDA

```makefile
ifeq ($(GPU), 1)
NVCC_FLAGS+= -ccbin g++-11
COMMON+= -DGPU -I/usr/local/cuda/include/ -I/opt/cuda/targets/x86_64-linux/include # Add CUDA include path here
CFLAGS+= -DGPU
LDFLAGS+= -L/usr/local/cuda/lib64 -L/opt/cuda/targets/x86_64-linux/lib -lcuda -lcudart -lcublas -lcurand # Add CUDA lib path here
endif
```

## Usage

### Training

To train your custom model:

1. Download/prepare dataset
2. Put all images in the [dataset/images](dataset/images) folder, currently all training images should be `.jpg`
3. Put labels in the [dataset/labels](dataset/labels) folder, each label file name should correspond to the image file
   name.
   Label format is the same as Darknet's label format
4. Add required class names to [cfg/classes.lst](cfg/classes.lst), separated by newline:

```
Signature
Stamp
```

5. Change classes number in [cfg/data.cfg](cfg/data.cfg):

```ini
classes = 2
```

6. Modify [cfg/net.cfg](cfg/net.cfg):
	1. Set classes number in each [yolo] layer:
   ```ini
   [yolo]
   classes = 2
   ```
	2. Set filters number in each [convolutional] layer before each [yolo] layer. Number of filters can be calculated
	   using the formula `filters = (classes + 5) * 3`:
   ```ini
   [convolutional]
   filters = 21
   ```

### Testing

You can use CMake `test` target to run model test. It will automatically select random file
from [dataset/test](dataset/test).

## Contributing

We welcome contributions to enhance the signature recognition architecture. If you would like to contribute, please
follow these steps:

1. Fork the repository on GitLab.

2. Create a new branch with the name `feature/feature_name` for your feature or bug fix.

3. Implement your changes or additions.

4. Commit and push your changes to your forked repository.

5. Submit a merge request, clearly describing the changes you have made.

## License

Signex is licensed under the [WTFPL](LICENSE.fuck).

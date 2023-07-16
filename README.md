# Signex

Signex is open source signature & stamp recognition tool, that uses YOLO-based model and
modified [Pytorch](https://github.com/ATMI/darknet) framework.

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
   SSH: git clone —depth 1 --recurse-submodules git@gitlab.pg.innopolis.university:sofwarus-progectus/signature-recognition.git

   HTTPS: git clone —depth 1 --recurse-submodules https://gitlab.pg.innopolis.university/sofwarus-progectus/signature-recognition.git
```

2. Navigate to project and set up a virtual environment 

   ```shell
      cd signature-recognition

      python -m venv venv
   ```
3. Activate venv
   ```shell
      **Linux:**
      . venv/bin/activate
      **Windows:**
      venv\Scripts\activate
   ``` 

   
   <!-- ```shell
      
   ```     -->
4. Install requirements
   ```shell
      pip install -r requirements.txt
   ```  

<!-- 
2. Optionally you can install:

* OpenCV - version 4.x
* CUDA & cuDNN -->

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

6. Modify [cfg/net.yaml](cfg/net.yaml):
	1. Set classes number in each [yolo] layer:
   ```ini
      nc: 2
   ```
	2. Set filters number in each [convolutional] layer before each [yolo] layer. Number of filters can be calculated
	   using the formula `filters = (classes + 5) * 3`:
   ```ini
   [convolutional]
   filters = 21
   ```
7. Start training
   ```shell
      python yolov7/train.py --workers 8 --device 0 --batch-size 160 --data data/data.yaml --img 640 640 --cfg cfg/net.yaml --weights '' --name signex --hyp hyp/hyp.net.yaml
   ```
   **Command Parameters**
   - `--workers 8`: Number of worker processes to use for data loading during training. You can increase this value to speed up data loading if you have sufficient CPU resources.

   - `--device 0`: Specify the device (GPU) to be used for training.

   - `--batch-size 160`: Number of samples in each training batch.

   - `--data data/data.yaml`: Path to the YAML file (`data.yaml`) containing dataset configuration, including the dataset location, number of classes, and other relevant information.

   - `--img 640 640`: Size of the input images during training.

   - `--cfg cfg/net.yaml`: Path to the YAML file (`net.yaml`) containing the network architecture configuration for the YOLOv7 model.

   - `--weights ''`: Path to the pre-trained weights file to initialize the model. Use an empty string (`''`) if you want to train the model from scratch.

   - `--name signex`: Name for the training run.

   - `--hyp hyp/hyp.net.yaml`: Path to the YAML file (`hyp.net.yaml`) containing hyperparameters for training, such as learning rate, weight decay, etc.

8. Run the Neural Network
   ```shell
   python yolov7/detect.py --weights ./weights/best.pt --conf 0.5 --img-size 640 --source <PATH_TO_FOLDER_WITH_IMAGES>
   ```
   - `--weights ./weights/best.pt`: Path to the trained weights file of your YOLOv7 model.

   - `--conf 0.5`: Confidence threshold for object detection. Objects with a detection confidence score below this threshold will be filtered out.

   - `--img-size 640`: Size of the input images during detection. Ensure that this value matches the image size used during training.


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

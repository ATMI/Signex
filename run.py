import sys

import cv2
import numpy as np
import torch
from numpy import random

from yolov7 import models

sys.modules["models"] = models

import yolov7.utils.datasets
from yolov7.models.experimental import attempt_load
from yolov7.utils.general import check_img_size, non_max_suppression, scale_coords
from yolov7.utils.plots import plot_one_box

WEIGHTS = "weights/best.pt"
IMG_SIZE = 640
CONF_THRESH = 0.45
IOU_THRESH = 0.45

with torch.no_grad():
	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
	model = attempt_load([WEIGHTS], device)

	stride = int(model.stride.max())
	img_size = check_img_size(IMG_SIZE, s=stride)

	names = model.module.names if hasattr(model, "module") else model.names
	colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]

	# todo: Loop
	img0 = cv2.imread("...")
	img = yolov7.utils.datasets.letterbox(img0, img_size, stride=stride)[0]

	# Convert
	img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
	img = np.ascontiguousarray(img)
	img = torch.from_numpy(img).to(device)
	img = img.float()
	img /= 255.0  # 0 - 255 to 0.0 - 1.0
	if img.ndimension() == 3:
		img = img.unsqueeze(0)

	with torch.no_grad():
		pred = model(img)[0]
	pred = non_max_suppression(pred, CONF_THRESH, IOU_THRESH, classes=None, agnostic=False)

	for i, det in enumerate(pred):  # detections per image
		if len(det):
			# Rescale boxes from img_size to im0 size
			gn = torch.tensor(img0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
			det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()

			for *xyxy, conf, cls in reversed(det):
				label = f'{names[int(cls)]} {conf:.2f}'
				plot_one_box(xyxy, img0, label=label, color=colors[int(cls)], line_thickness=1)

		cv2.imwrite(f"test/{i}.png", img0)

import sys

import numpy as np
import torch
from numpy import random

from yolov7 import models

sys.modules["models"] = models

import yolov7.utils.datasets
from yolov7.models.experimental import attempt_load
from yolov7.utils.general import check_img_size, non_max_suppression, scale_coords
from yolov7.utils.plots import plot_one_box


class Detector:
	def __init__(self, weights, img_size=640):
		with torch.no_grad():
			self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
			self.model = attempt_load([weights], self.device)

			self.stride = int(self.model.stride.max())
			self.img_size = check_img_size(img_size, s=self.stride)

			self.names = self.model.module.names if hasattr(self.model, "module") else self.model.names
			self.colors = [[random.randint(0, 255) for _ in range(3)] for _ in self.names]

	def detect(self, image, conf_thresh=0.45, iou_thresh=0.45):
		img = yolov7.utils.datasets.letterbox(image, self.img_size, stride=self.stride)[0]

		# Convert
		img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
		img = np.ascontiguousarray(img)
		img = torch.from_numpy(img).to(self.device)
		img = img.float()
		img /= 255.0  # 0 - 255 to 0.0 - 1.0
		if img.ndimension() == 3:
			img = img.unsqueeze(0)

		with torch.no_grad():
			pred = self.model(img)[0]
		pred = non_max_suppression(pred, conf_thresh, iou_thresh, classes=None, agnostic=False)

		for i, det in enumerate(pred):  # detections per image
			if len(det):
				# Rescale boxes from img_size to im0 size
				gn = torch.tensor(image.shape)[[1, 0, 1, 0]]  # normalization gain whwh
				det[:, :4] = scale_coords(img.shape[2:], det[:, :4], image.shape).round()

				for *xyxy, conf, cls in reversed(det):
					label = f'{self.names[int(cls)]} {conf:.2f}'
					plot_one_box(xyxy, image, label=label, color=self.colors[int(cls)], line_thickness=1)

		return image

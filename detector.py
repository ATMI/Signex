import queue
import sys
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum

import numpy as np
import torch
from numpy import random

from yolov7 import models

sys.modules["models"] = models

import yolov7.utils.datasets
from yolov7.models.experimental import attempt_load
from yolov7.utils.general import check_img_size, non_max_suppression, scale_coords
from yolov7.utils.plots import plot_one_box


class Task(Enum):
	STOP = 0,
	DETECT = 1


class Detector:

	def __init__(self, weights, max_workers, img_size=640):
		self.queue = queue.Queue()
		self.weights = weights
		self.img_size = img_size
		self.executor = ThreadPoolExecutor(max_workers=max_workers)
		for _ in range(max_workers):
			self.executor.submit(self.worker)

	def worker(self):
		with torch.no_grad():
			device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
			model = attempt_load([self.weights], device)
			stride = int(model.stride.max())
			img_size = check_img_size(self.img_size, s=stride)
			names = model.module.names if hasattr(model, "module") else model.names
			colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]

			def __detect__(image, conf_thresh=0.45, iou_thresh=0.45):
				img = yolov7.utils.datasets.letterbox(image, img_size, stride=stride)[0]

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
				pred = non_max_suppression(pred, conf_thresh, iou_thresh, classes=None, agnostic=False)

				for i, det in enumerate(pred):  # detections per image
					if len(det):
						# Rescale boxes from img_size to im0 size
						gn = torch.tensor(image.shape)[[1, 0, 1, 0]]  # normalization gain whwh
						det[:, :4] = scale_coords(img.shape[2:], det[:, :4], image.shape).round()

						for *xyxy, conf, cls in reversed(det):
							label = f'{names[int(cls)]} {conf:.2f}'
							plot_one_box(xyxy, image, label=label, color=colors[int(cls)], line_thickness=1)

				return image

			while True:
				(task, args) = self.queue.get()
				match task:
					case Task.STOP:
						break
					case Task.DETECT:
						(image, future) = args
						result = __detect__(image)
						future.set_result(result)
						self.queue.task_done()

	def detect(self, image) -> Future:
		future = Future()
		self.queue.put((Task.DETECT, (image, future)))
		return future

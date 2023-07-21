import queue
import sys
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from enum import Enum
from typing import List

import cv2
import numpy as np
import torch
from numpy import random
from torch import nn

from yolov7 import models
from yolov7.models import yolo
from yolov7.models.experimental import attempt_load
from yolov7.utils.datasets import letterbox
from yolov7.utils.general import check_img_size, non_max_suppression, scale_coords

sys.path.append('../yolov7')
sys.modules["models"] = models
sys.modules["models.yolo"] = yolo


class Task(Enum):
	STOP = 0,
	DETECT = 1


@dataclass
class Bbox:
	x1: int
	y1: int
	x2: int
	y2: int


@dataclass
class Detection:
	cls: int
	name: str
	conf: float
	bbox: Bbox


class Detector:

	def __init__(self, weights, max_workers, log, img_size=640):
		self.queue = queue.Queue()
		self.log = log

		self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
		self.model = attempt_load(weights, self.device)

		self.stride = int(self.model.stride.max())
		self.img_size = check_img_size(img_size, s=self.stride)

		self.names = self.model.module.names if hasattr(self.model, "module") else self.model.names
		self.colors = [[random.randint(0, 255) for _ in range(3)] for _ in self.names]

		self.model = nn.DataParallel(self.model)
		self.executor = ThreadPoolExecutor(max_workers=max_workers)

		for _ in range(max_workers):
			self.executor.submit(self.worker)

	def worker(self):
		while True:
			try:
				(task, args) = self.queue.get()
				if not self.handle_task(task, args):
					break
			except Exception as e:
				self.log(e)
			finally:
				self.queue.task_done()

	def handle_task(self, task, args):
		match task:
			case Task.STOP:
				return False
			case Task.DETECT:
				(image, conf_thresh, iou_thresh, future) = args
				self.__detect__(image, future, conf_thresh, iou_thresh)
		return True

	def __detect__(self, img, future, conf_thresh, iou_thresh):
		try:
			with torch.no_grad():
				pred = self.model(img)[0]

			pred = non_max_suppression(pred, conf_thresh, iou_thresh, classes=None, agnostic=False)
			future.set_result((True, pred))
		except Exception as e:
			future.set_result((False, e))
			self.log(e)

	def detect(self, image, conf_thresh, iou_thresh) -> List[Detection] | None:
		try:
			img = letterbox(image, self.img_size, stride=self.stride)[0]
			img = img[:, :, ::-1].transpose(2, 0, 1)
			img = np.ascontiguousarray(img)
			img = torch.from_numpy(img).to(self.device)
			img = img.float()
			img /= 255.0
			if img.ndimension() == 3:
				img = img.unsqueeze(0)

			future = Future()
			self.queue.put((Task.DETECT, (img, conf_thresh, iou_thresh, future)))
			(ok, pred) = future.result()

			if ok:
				result = []
				for i, det in enumerate(pred):
					if len(det):
						det[:, :4] = scale_coords(img.shape[2:], det[:, :4], image.shape).round()

						for *xyxy, conf, cls in reversed(det):
							cls = int(cls)
							bbox = Bbox(int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3]))
							detection = Detection(cls, self.names[cls], float(conf), bbox)
							result.append(detection)

				return result
		except Exception as e:
			self.log(e)
		return None

	def draw_boxes(self, img, pred, line_thickness=3):
		try:
			tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1

			for detection in pred:
				label = f'{detection.name} {detection.conf:.2%}'
				color = self.colors[detection.cls]

				c1 = (detection.bbox.x1, detection.bbox.y1)
				c2 = (detection.bbox.x2, detection.bbox.y2)

				cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)

				tf = max(tl - 1, 1)
				t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
				c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
				cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
				cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf,
							lineType=cv2.LINE_AA)
			return True
		except Exception as e:
			self.log(e)
			return False

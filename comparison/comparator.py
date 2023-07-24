import queue
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum

import cv2
import numpy as np
import torch
from PIL import Image
from torch import nn
from torchvision import transforms


class Task(Enum):
	STOP = 0,
	COMPARE = 1


class Comparator:
	def __init__(self, weights, input_size, max_workers, log):
		self.queue = queue.Queue()
		self.log = log

		self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
		self.model = torch.load(weights, map_location=self.device)

		self.input_size = input_size
		self.transform = transforms.Compose([
			lambda image: Comparator.preprocess_image(image, self.input_size),
			Comparator.image_to_tensor()
		])

		self.model.eval()
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
			case Task.COMPARE:
				(image_a, image_b, future) = args
				self.__compare__(image_a, image_b, future)
		return True

	def __compare__(self, image_a, image_b, future: Future):
		try:
			image_a = image_a.to(self.device).unsqueeze(0)
			image_b = image_b.to(self.device).unsqueeze(0)

			with torch.no_grad():
				output_a = self.model(image_a)
				output_b = self.model(image_b)

			similarity = min(1, (1 - nn.functional.cosine_similarity(output_a, output_b)).item())
			future.set_result((True, similarity))
		except Exception as e:
			self.log(e)
			future.set_result((False, e))

	def compare(self, image_a, image_b):
		try:
			image_a = self.transform(image_a)
			image_b = self.transform(image_b)

			future = Future()
			self.queue.put((Task.COMPARE, (image_a, image_b, future)))
			(ok, result) = future.result()

			if ok:
				return result
		except Exception as e:
			self.log(e)
		return None

	@staticmethod
	def preprocess_image(image, input_size):
		image = cv2.resize(image, (input_size, input_size), interpolation=cv2.INTER_LINEAR)
		image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 12)
		image = Image.fromarray(image)
		return image

	@staticmethod
	def image_to_tensor():
		return transforms.Compose([
			transforms.ToTensor(),  # Convert the image to a tensor
			transforms.Normalize(mean=[0.485], std=[0.229])
		])

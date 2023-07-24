import os
import random
from collections import defaultdict

import cv2
from torch.utils import data

from signex_utils.pair import Pair


class TriDataset(data.Dataset):
	def __init__(self, root_dir, transform=None):
		self.signatures = self.load(root_dir)
		if len(self.signatures) == 1:
			raise Exception()

		self.root_dir = root_dir
		self.transform = transform

	def __len__(self):
		return len(self.signatures)

	def __getitem__(self, index1):
		(anchor_dir, anchor_list) = self.signatures[index1]

		while True:
			index2 = random.randint(0, len(self.signatures) - 1)
			if index1 != index2:
				(negative_dir, negative_list) = self.signatures[index2]
				break

		def load_img(img_dir, img_name):
			return cv2.imread(os.path.join(self.root_dir, img_dir, img_name), cv2.IMREAD_GRAYSCALE)

		(anchor_entry, positive_entry) = random.sample(anchor_list, 2)
		negative_entry = random.choice(negative_list)

		anchor_entry.first += 1
		positive_entry.first += 1
		negative_entry.first += 1

		anchor_img = load_img(anchor_dir, anchor_entry.second)
		positive_img = load_img(anchor_dir, positive_entry.second)
		negative_img = load_img(negative_dir, negative_entry.second)

		if self.transform:
			anchor_img = self.transform(anchor_img)
			positive_img = self.transform(positive_img)
			negative_img = self.transform(negative_img)

		return anchor_img, positive_img, negative_img

	@staticmethod
	def load(root_dir):
		dataset = defaultdict(list)

		for dir_name in os.listdir(root_dir):
			dir_path = os.path.join(root_dir, dir_name)
			if not os.path.isdir(dir_path):
				continue

			for file_name in os.listdir(dir_path):
				file_path = os.path.join(dir_path, file_name)
				if not os.path.isfile(file_path):
					continue

				dataset[dir_name].append(Pair(0, file_name))

		return list(dataset.items())

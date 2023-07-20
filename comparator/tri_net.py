from torch import nn


class TriNet(nn.Module):
	def __init__(self, model):
		super(TriNet, self).__init__()
		self.model = model

	def forward_once(self, x):
		return self.model(x)

	def forward(self, anchor, positive, negative):
		anchor_embedding = self.forward_once(anchor)
		positive_embedding = self.forward_once(positive)
		negative_embedding = self.forward_once(negative)
		return anchor_embedding, positive_embedding, negative_embedding

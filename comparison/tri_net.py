from torch import nn


class TriNet(nn.Module):
	def __init__(self, model):
		super(TriNet, self).__init__()
		self.model = model

	def forward(self, x):
		return self.model(x)

	def forward_tri(self, anchor, positive, negative):
		anchor_embedding = self.forward(anchor)
		positive_embedding = self.forward(positive)
		negative_embedding = self.forward(negative)
		return anchor_embedding, positive_embedding, negative_embedding

class Pair:
	def __init__(self, first, second):
		self.first = first
		self.second = second

	def __repr__(self):
		return str(self)

	def __str__(self) -> str:
		return f"({self.first}, {self.second})"

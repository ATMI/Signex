class Result:
	def __init__(self, value=None, error=None):
		self.value = value
		self.error = error
		self.is_success = error is None

	@staticmethod
	def success(value):
		return Result(value=value)

	@staticmethod
	def failure(error):
		return Result(error=error)

	def get_or_throw(self):
		if self.is_success:
			return self.value
		else:
			raise Exception(self.error)

	def get_or_default(self, default_value):
		if self.is_success:
			return self.value
		else:
			return default_value

	def map(self, transform):
		if self.is_success:
			return Result.success(transform(self.value))
		else:
			return Result.failure(self.error)

	def flat_map(self, transform):
		if self.is_success:
			return transform(self.value)
		else:
			return Result.failure(self.error)

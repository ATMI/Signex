from http.client import BAD_REQUEST, OK, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED

from api.values import CONTENT_PLAIN_TEXT


class Response:
	def __init__(self, status: int, body, headers: [(str, str)]):
		self.status = status
		self.body = body
		self.headers = headers

	@classmethod
	def error(cls, code: int, message: str) -> 'Response':
		return cls(code, message, [CONTENT_PLAIN_TEXT])

	@classmethod
	def bad_request(cls, message: str) -> 'Response':
		return cls.error(BAD_REQUEST, message)

	@classmethod
	def ok(cls, body, headers):
		return cls(OK, body, headers)

	@classmethod
	def internal_server_error(cls, code: int) -> 'Response':
		return cls.error(INTERNAL_SERVER_ERROR, f"Internal server error occurred, code: {code}\n")

	@classmethod
	def no_required_field(cls, field_name) -> 'Response':
		return cls.bad_request(f"Can not find required field: '{field_name}'\n")

	@classmethod
	def no_such_method(cls, method, name) -> 'Response':
		return cls.bad_request(f"Can not find requested method: '{method}: {name}'\n")

	@classmethod
	def invalid_content_type(cls, provided, expected) -> 'Response':
		return cls.bad_request(f"Invalid content type:\nProvided: '{provided}'\nExpected: '{expected}'\n")

	@classmethod
	def not_implemented(cls) -> 'Response':
		return cls.error(NOT_IMPLEMENTED, "This method is not yet implemented\n")

import cgi
from enum import Enum
from http.client import INTERNAL_SERVER_ERROR, BAD_REQUEST, OK, NOT_IMPLEMENTED
from typing import Dict, Tuple, Callable

import cv2
import numpy as np
from flup.server.fcgi import WSGIServer

from detector import Detector


class Header(Enum):
	class Key(Enum):
		CONTENT_TYPE = "Content-Type"
		CONTENT_DISPOSITION = "Content-Dispositon"

	class Value(Enum):
		PLAIN_TEXT = "text/plain"
		MULTIPART_FD = "multipart/form-data"
		IMAGE_JPEG = "image/jpeg"

	CONTENT_PLAIN_TEXT = (Key.CONTENT_TYPE, Value.PLAIN_TEXT)
	CONTENT_MULTIPART_FD = (Key.CONTENT_TYPE, Value.MULTIPART_FD)
	CONTENT_JPEG = (Key.CONTENT_TYPE, Value.IMAGE_JPEG)


class CgiField(Enum):
	DOCUMENT_URI = "DOCUMENT_URI"
	REQUEST_METHOD = "REQUEST_METHOD"
	CONTENT_TYPE = "CONTENT_TYPE"


class InternalError(Enum):
	UNKNOWN = -1
	NO_CGI_INPUT = -2
	CANT_READ_CGI_FIELD = -3
	CANT_ENCODE_IMAGE = -4


class Response:
	def __init__(self, status: int, body, headers: [Header]):
		self.status = status
		self.body = body
		self.headers = headers

	@classmethod
	def error(cls, code: int, message: str) -> 'Response':
		return cls(code, message, [Header.CONTENT_PLAIN_TEXT])

	@classmethod
	def bad_request(cls, message: str) -> 'Response':
		return cls.error(BAD_REQUEST, message)

	@classmethod
	def ok(cls, body, headers):
		return cls(OK, body, headers)

	@classmethod
	def internal_server_error(cls, code: InternalError) -> 'Response':
		return cls.error(INTERNAL_SERVER_ERROR, f"Internal server error occurred, code: {code.value}\n")

	@classmethod
	def no_required_field(cls, field_name) -> 'Response':
		return cls.bad_request(f"Can not find required field: '{field_name}'\n")

	@classmethod
	def no_such_method(cls, method, name) -> 'Response':
		return cls.bad_request(f"Can not find requested method: '{method}: {name}'\n")

	@classmethod
	def invalid_content_type(cls, provided, expected) -> 'Response':
		return cls.bad_request(f"Invalid content type:\nProvided: '{provided}'\nExpected: '{expected}\n")

	@classmethod
	def not_implemented(cls) -> 'Response':
		return cls.error(NOT_IMPLEMENTED, "This method is not yet implemented\n")


class Api:
	def __init__(self, address, detector, log):
		self.log = log
		self.detector = detector
		self.server = WSGIServer(self.accept_request, bindAddress=address)
		self.handlers: Dict[Tuple[str, str], Callable[[dict], Response]] = {
			("/detect", "POST"): self.detect,
			("/compare", "POST"): self.compare
		}

	def handle_request(self, environ: dict) -> Response:
		request_method = environ.get(CgiField.REQUEST_METHOD)
		if request_method is None:
			return Response.no_required_field(CgiField.REQUEST_METHOD)

		document_uri = environ.get(CgiField.DOCUMENT_URI)
		if document_uri is None:
			return Response.no_required_field(CgiField.DOCUMENT_URI)

		handler = self.handlers.get((document_uri, request_method))
		if handler is None:
			return Response.no_such_method(request_method, document_uri)

		return handler(environ)

	def accept_request(self, environ: dict, start_response):
		response = Response.internal_server_error(InternalError.UNKNOWN)
		try:
			response = self.handle_request(environ)
		except Exception as e:
			self.log(e)
		finally:
			start_response(f"{response.status}", response.headers)
			return [response.body]

	async def detect(self, environ) -> Response:
		content_type = environ.get(CgiField.CONTENT_TYPE)
		if not content_type or not content_type.startswith(Header.Value.MULTIPART_FD):
			return Response.invalid_content_type(content_type, Header.Value.MULTIPART_FD)

		input_stream = environ.get("wsgi.input")
		if not input_stream:
			return Response.internal_server_error(InternalError.NO_CGI_INPUT)

		form = cgi.FieldStorage(fp=input_stream, environ=environ)

		image_field = form.getvalue("image")
		if image_field is None:
			return Response.no_required_field("image")

		try:
			image_data = image_field.file.read()
		except Exception as e:
			self.log(e)
			return Response.internal_server_error(InternalError.CANT_READ_CGI_FIELD)

		try:
			image_array = np.frombuffer(image_data, dtype=np.uint8)
			image_mat = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
		except Exception as e:
			self.log(e)
			return Response.bad_request("Can not decode provided image\n")

		result = await self.detector.detect(image_mat)
		(ok, result_data) = cv2.imencode(".jpg", result)

		if not ok:
			return Response.internal_server_error(InternalError.CANT_ENCODE_IMAGE)

		headers = [Header.CONTENT_JPEG, (Header.Key.CONTENT_DISPOSITION, "inline; filename=result.jpg")]
		return Response.ok(result_data.tobytes(), headers)

	def compare(self, environ) -> Response:
		return Response.not_implemented()

	def run(self):
		self.server.run()


if __name__ == "__main__":
	try:
		detector = Detector("weights/best.pt", max_workers=1)
		api = Api(("localhost", 8080), detector, print)
		api.run()
	except Exception as e:
		print(e)

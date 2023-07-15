import cgi
from http import HTTPStatus
from http.client import INTERNAL_SERVER_ERROR, BAD_REQUEST, OK, NOT_IMPLEMENTED
from typing import Dict, Tuple, Callable

import cv2
import numpy as np
from flup.server.fcgi import WSGIServer

from detector import Detector

CONTENT_TYPE = "Content-Type"
CONTENT_DISPOSITION = "Content-Dispositon"

PLAIN_TEXT = "text/plain"
MULTIPART_FD = "multipart/form-data"
IMAGE_JPEG = "image/jpeg"

CONTENT_PLAIN_TEXT = (CONTENT_TYPE, PLAIN_TEXT)
CONTENT_MULTIPART_FD = (CONTENT_TYPE, MULTIPART_FD)
CONTENT_JPEG = (CONTENT_TYPE, IMAGE_JPEG)

CGI_DOCUMENT_URI = "DOCUMENT_URI"
CGI_REQUEST_METHOD = "REQUEST_METHOD"
CGI_CONTENT_TYPE = "CONTENT_TYPE"
CGI_INPUT = "wsgi.input"

UNKNOWN = -1
NO_CGI_INPUT = -2
CANT_READ_CGI_FIELD = -3
CANT_ENCODE_IMAGE = -4
DETECT_FAILURE = -5


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
		request_method = environ.get(CGI_REQUEST_METHOD)
		if request_method is None:
			return Response.no_required_field(CGI_REQUEST_METHOD)

		document_uri = environ.get(CGI_DOCUMENT_URI)
		if document_uri is None:
			return Response.no_required_field(CGI_DOCUMENT_URI)

		handler = self.handlers.get((document_uri, request_method))
		if handler is None:
			return Response.no_such_method(request_method, document_uri)

		return handler(environ)

	def accept_request(self, environ: dict, start_response):
		response = Response.internal_server_error(UNKNOWN)
		try:
			response = self.handle_request(environ)
		except Exception as e:
			self.log(e)
		finally:
			status = HTTPStatus(response.status)
			start_response(f"{status.value} {status.phrase}", response.headers)
			return [response.body]

	def detect(self, environ) -> Response:
		content_type = environ.get(CGI_CONTENT_TYPE)
		if not content_type or not content_type.startswith(MULTIPART_FD):
			return Response.invalid_content_type(content_type, MULTIPART_FD)

		input_stream = environ.get(CGI_INPUT)
		if not input_stream:
			return Response.internal_server_error(NO_CGI_INPUT)

		try:
			form = cgi.FieldStorage(fp=input_stream, environ=environ)
		except Exception as e:
			self.log(e)
			return Response.bad_request("Invalid input stream field storage\n")

		image_data = form.getvalue("image")
		if image_data is None:
			return Response.no_required_field("image")

		try:
			image_array = np.frombuffer(image_data, dtype=np.uint8)
			image_mat = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
		except Exception as e:
			self.log(e)
			return Response.bad_request("Can not decode provided image\n")

		(ok, result) = self.detector.detect(image_mat).result()
		if not ok:
			self.log(result)
			return Response.internal_server_error(DETECT_FAILURE)

		(ok, result_data) = cv2.imencode(".jpg", result)

		if not ok:
			return Response.internal_server_error(CANT_ENCODE_IMAGE)

		headers = [CONTENT_JPEG, (CONTENT_DISPOSITION, "inline; filename=result.jpg")]
		return Response.ok(result_data.tobytes(), headers)

	def compare(self, environ) -> Response:
		return Response.not_implemented()

	def run(self):
		self.server.run()


if __name__ == "__main__":
	detector = Detector("weights/best.pt", max_workers=1)
	api = Api(("localhost", 8080), detector, print)
	api.run()

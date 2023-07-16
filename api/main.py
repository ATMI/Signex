import cgi
import json
from http import HTTPStatus
from typing import Dict, Tuple, Callable

import cv2
import numpy as np
from flup.server.fcgi import WSGIServer

from api.response import Response
from api.values import *
from detector import Detector
from utils.result import Result


class Api:
	def __init__(self, address, detector: Detector, log):
		self.log = log
		self.detector = detector
		self.server = WSGIServer(self.accept_request, bindAddress=address)
		self.handlers: Dict[Tuple[str, str], Callable[[dict], Response]] = {
			("/detect", "POST"): self.detect,
			("/detect_and_draw", "POST"): self.detect_and_draw,
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
		response = Response.internal_server_error(ACCEPT_REQUEST_FAILURE)
		try:
			response = self.handle_request(environ)
		except Exception as e:
			self.log(e)
		finally:
			status = HTTPStatus(response.status)
			start_response(f"{status.value} {status.phrase}", response.headers)
			return [response.body]

	def get_field_storage(self, environ) -> Result:
		try:
			content_type = environ.get(CGI_CONTENT_TYPE)
			if not content_type or not content_type.startswith(MULTIPART_FD):
				return Result.failure(Response.invalid_content_type(content_type, MULTIPART_FD))

			input_stream = environ.get(CGI_INPUT)
			if not input_stream:
				return Result.failure(Response.internal_server_error(NO_CGI_INPUT))

			return Result.success(cgi.FieldStorage(fp=input_stream, environ=environ))
		except Exception as e:
			self.log(e)
		return Result.failure(Response.internal_server_error(GET_FIELD_STORAGE_FAILURE))

	def detect(self, environ) -> Response:
		try:
			result = self.__detect__(environ)
			if result.is_success():
				(pred, _) = result.value
			else:
				return result.error

			result = json.dumps(pred, default=lambda obj: obj.__dict__)
			return Response.ok(result, [CONTENT_JSON])
		except Exception as e:
			self.log(e)
		return Response.internal_server_error(DETECT_FAILURE)

	def detect_and_draw(self, environ) -> Response:
		try:
			result = self.__detect__(environ)
			if result.is_success():
				(pred, img) = result.value
			else:
				return result.error

			self.detector.draw_boxes(img, pred)
			(ok, result_data) = cv2.imencode(".jpg", img)

			if not ok:
				return Response.internal_server_error(CANT_ENCODE_IMAGE)

			headers = [CONTENT_JPEG, (CONTENT_DISPOSITION, "inline; filename=result.jpg")]
			return Response.ok(result_data.tobytes(), headers)
		except Exception as e:
			self.log(e)
		return Response.internal_server_error(DETECT_FAILURE)

	def get_field_value(self, field_storage: cgi.FieldStorage, field_name, handler):
		try:
			value = field_storage.getvalue(field_name)
			return Result.success(handler(value))
		except Exception as e:
			self.log(e)
		return Result.failure(Response.invalid_field_value(field_name))

	def get_float(self, field_storage: cgi.FieldStorage, field_name, default):
		return self.get_field_value(
			field_storage,
			field_name,
			lambda val:
			default if val is None else float(val)
		)

	def get_image(self, field_storage: cgi.FieldStorage, field_name):
		return self.get_field_value(
			field_storage,
			field_name,
			lambda img:
			cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_COLOR)
		)

	def __detect__(self, environ) -> Result:
		try:
			(field_storage, error) = self.get_field_storage(environ)
			if error:
				return Result.failure(error)

			(img, error) = self.get_image(field_storage, "image")
			if error:
				return Result.failure(error)

			(conf_thresh, error) = self.get_float(field_storage, "conf_thresh", 0.25)
			if error:
				return Result.failure(error)

			(iou_thresh, error) = self.get_float(field_storage, "iou_thresh", 0.25)
			if error:
				return Result.failure(error)

			result = self.detector.detect(img, conf_thresh, iou_thresh)

			if result is not None:
				return Result.success((result, img))
		except Exception as e:
			self.log(e)
		return Result.failure(Response.internal_server_error(BASE_DETECT_FAILURE))

	def compare(self, environ) -> Response:
		return Response.not_implemented()

	def run(self):
		self.server.run()


if __name__ == "__main__":
	detector = Detector("weights/best.pt", 1, print)
	api = Api(("localhost", 8080), detector, print)
	api.run()

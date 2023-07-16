import cgi
import json
from http import HTTPStatus
from typing import Dict, Tuple, Callable

import cv2
import numpy as np
from flup.server.fcgi import WSGIServer

from api.response import Response
from api.values import CGI_REQUEST_METHOD, CGI_DOCUMENT_URI, CGI_CONTENT_TYPE, MULTIPART_FD, CGI_INPUT, \
	NO_CGI_INPUT, BASE_DETECT_FAILURE, DETECT_FAILURE, GET_FIELD_STORAGE_FAILURE, ACCEPT_REQUEST_FAILURE, CONTENT_JSON, \
	CONTENT_JPEG, CANT_ENCODE_IMAGE, CONTENT_DISPOSITION
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
			if result.is_success:
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
			if result.is_success:
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

	def __detect__(self, environ) -> Result:
		try:
			result = self.get_field_storage(environ)
			if result.is_success:
				field_storage: cgi.FieldStorage = result.value
			else:
				return result

			image_data = field_storage.getvalue("image")
			if image_data is None:
				return Result.failure(Response.no_required_field("image"))

			conf_thresh = field_storage.getvalue("conf", default=0.25)
			iou_thresh = field_storage.getvalue("iou", default=0.25)

			image_array = np.frombuffer(image_data, dtype=np.uint8)
			image_mat = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
			result = self.detector.detect(image_mat, conf_thresh, iou_thresh)

			if result:
				return Result.success((result, image_mat))
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

import cgi
from http import HTTPStatus

import cv2
import numpy as np
from flup.server.fcgi import WSGIServer

from detector import Detector


def detect(environ):
	content_type = environ.get("CONTENT_TYPE")
	if not content_type or not content_type.startswith("multipart/form-data"):
		return HTTPStatus.BAD_REQUEST, "Invalid input format", [("Content-Type", "text/plain")]

	input_stream = environ["wsgi.input"]
	form = cgi.FieldStorage(fp=input_stream, environ=environ)

	image_field = form["image"]
	if image_field is None:
		return HTTPStatus.BAD_REQUEST, "No valid 'image' to process was provided", [("Content-Type", "text/plain")]

	image_data = image_field.file.read()
	image_array = np.frombuffer(image_data, dtype=np.uint8)
	image_mat = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

	result = detector.detect(image_mat)
	(ok, result_data) = cv2.imencode(".jpg", result)

	if not ok:
		return HTTPStatus.INTERNAL_SERVER_ERROR, "Failed to process image", [("Content-Type", "text/plain")]

	headers = [("Content-Type", "image/jpeg"), ("Content-Dispositon", "inline; filename=result.jpg")]
	return HTTPStatus.OK, result_data.tobytes(), headers


handlers = {
	("/detect", "POST"): detect
}


def app(environ, start_response):
	print(environ)

	status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
	response = "Some inner error occurred, please contact the developers to report the issue\n"
	headers = [("Content-Type", "text/plain")]

	try:
		document_uri = environ["DOCUMENT_URI"]
		request_method = environ["REQUEST_METHOD"]
		handler = handlers.get((document_uri, request_method))

		if handler:
			status, response, headers = handler(environ)
		else:
			status = HTTPStatus.METHOD_NOT_ALLOWED
			response = "Unknown method\n"

	except Exception as e:
		# TODO: handle error appropriately
		print(e)
		pass
	finally:
		start_response(f"{status.value} {status.phrase}", headers)
		return [response]


if __name__ == "__main__":
	detector = Detector("weights/best.pt")
	WSGIServer(app, bindAddress=("localhost", 8080)).run()

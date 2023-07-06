from http import HTTPStatus


# from detector import Detector


def detect(environ):
	return HTTPStatus.OK, "It is detect method", [("Content-Type", "text/plain")]


handlers = {
	("/detect", "GET"): detect
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

	except Exception:
		# TODO: handle error appropriately
		pass
	finally:
		start_response(f"{status.value} {status.phrase}", headers)
		return [response]


if __name__ == "__main__":
	from flup.server.fcgi import WSGIServer

	# detector = Detector("weights/best.pt")

	WSGIServer(app, bindAddress=("localhost", 8080)).run()

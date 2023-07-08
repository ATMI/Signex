import unittest
from http import HTTPStatus
from unittest.mock import MagicMock

from api import detect, api


class TestDetect(unittest.TestCase):
	def test_detect_invalid_content_type(self):
		environ = {
			"CONTENT_TYPE": "application/json",
			"wsgi.input": MagicMock(),
		}

		status, message, headers = detect(environ)

		self.assertEqual(status, HTTPStatus.BAD_REQUEST)
		self.assertEqual(message, "Invalid input format\n")
		self.assertEqual(headers, [("Content-Type", "text/plain")])

	def test_detect_missing_image_field(self):
		environ = {
			"CONTENT_TYPE": "multipart/form-data",
			"wsgi.input": MagicMock(),
		}

		status, message, headers = detect(environ)

		self.assertEqual(status, HTTPStatus.BAD_REQUEST)
		self.assertEqual(message, "No valid 'image' to process was provided\n")
		self.assertEqual(headers, [("Content-Type", "text/plain")])


class ApiTests(unittest.TestCase):
	def test_known_handler(self):
		# Simulating an environment with a known handler
		environ = {"DOCUMENT_URI": "/detect", "REQUEST_METHOD": "POST"}
		response = api(environ, self.mock_start_response)

		# Asserting the response
		self.assertEqual(response, ["Invalid input format\n"])
		self.assertEqual(self.mock_status, "400 Bad Request")
		self.assertEqual(self.mock_headers, [("Content-Type", "text/plain")])

	def test_unknown_handler(self):
		# Simulating an environment with an unknown handler
		environ = {"DOCUMENT_URI": "/unknown", "REQUEST_METHOD": "GET"}
		response = api(environ, self.mock_start_response)

		# Asserting the response
		self.assertEqual(response, ["Unknown method\n"])
		self.assertEqual(self.mock_status, "405 Method Not Allowed")
		self.assertEqual(self.mock_headers, [("Content-Type", "text/plain")])

	# TODO: fix handling of empty environment
	def test_exception_handling(self):
		# Simulating an environment that raises an exception
		environ = {}
		response = api(environ, self.mock_start_response)

		# Asserting the response
		self.assertEqual(response, ["Some inner error occurred, please contact the developers to report the issue\n"])
		self.assertEqual(self.mock_status, "500 Internal Server Error")
		self.assertEqual(self.mock_headers, [("Content-Type", "text/plain")])

	def mock_start_response(self, status, headers):
		# Store the status and headers for assertions
		self.mock_status = status
		self.mock_headers = headers


if __name__ == '__main__':
	unittest.main()

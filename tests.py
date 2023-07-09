import unittest
from unittest.mock import MagicMock, patch

from api import Api


class ApiTests(unittest.TestCase):
	def setUp(self):
		self.detector = MagicMock()
		self.log = MagicMock()
		self.api = Api(("localhost", 8080), self.detector, self.log)

	def test_handle_request_no_request_method(self):
		# Purpose: Test handling a request with no 'REQUEST_METHOD' field
		# Expected behavior: The API should respond with a status code 400 and an error message indicating the missing field
		environ = {}
		response = self.api.handle_request(environ)
		self.assertEqual(response.status, 400)
		self.assertEqual(response.body, "Can not find required field: 'REQUEST_METHOD'\n")

	def test_handle_request_no_document_uri(self):
		# Purpose: Test handling a request with no 'DOCUMENT_URI' field
		# Expected behavior: The API should respond with a status code 400 and an error message indicating the missing field
		environ = {"REQUEST_METHOD": "POST"}
		response = self.api.handle_request(environ)
		self.assertEqual(response.status, 400)
		self.assertEqual(response.body, "Can not find required field: 'DOCUMENT_URI'\n")

	def test_handle_request_no_such_method(self):
		# Purpose: Test handling a request with an unknown method
		# Expected behavior: The API should respond with a status code 400 and an error message indicating the unknown method
		environ = {"REQUEST_METHOD": "POST", "DOCUMENT_URI": "/unknown"}
		response = self.api.handle_request(environ)
		self.assertEqual(response.status, 400)
		self.assertEqual(response.body, "Can not find requested method: 'POST: /unknown'\n")

	def test_detect_invalid_content_type(self):
		# Purpose: Test handling a request with an invalid content type
		# Expected behavior: The API should respond with a status code 400 and an error message indicating the invalid content type
		environ = {"REQUEST_METHOD": "POST", "DOCUMENT_URI": "/detect", "CONTENT_TYPE": "application/json"}
		response = self.api.handle_request(environ)
		self.assertEqual(response.status, 400)
		self.assertEqual(response.body,
						 "Invalid content type:\nProvided: 'application/json'\nExpected: 'multipart/form-data'\n")

	@patch("api.np.frombuffer")
	@patch("api.cv2.imdecode")
	def test_detect_no_image_field(self, mock_imdecode, mock_frombuffer):
		# Purpose: Test handling a request with no image field in the input stream
		# Expected behavior: The API should respond with a status code 400 and an error message indicating the missing image field
		mock_imdecode.return_value = MagicMock()
		mock_frombuffer.return_value = MagicMock()

		environ = {
			"REQUEST_METHOD": "POST",
			"DOCUMENT_URI": "/detect",
			"CONTENT_TYPE": "multipart/form-data",
			"wsgi.input": MagicMock()
		}
		form = MagicMock()
		form.getvalue.return_value = None
		environ["wsgi.input"].read.return_value = form
		response = self.api.handle_request(environ)

		self.assertEqual(response.status, 400)
		self.assertEqual(response.body, "Invalid input stream field storage\n")


if __name__ == "__main__":
	unittest.main()

import unittest
from http import HTTPStatus
from unittest.mock import MagicMock

from api import detect


class TestDetect(unittest.TestCase):
	def test_detect_invalid_content_type(self):
		environ = {
			"CONTENT_TYPE": "application/json",
			"wsgi.input": MagicMock(),
		}

		status, message, headers = detect(environ)

		self.assertEqual(status, HTTPStatus.BAD_REQUEST)
		self.assertEqual(message, "Invalid input format")
		self.assertEqual(headers, [("Content-Type", "text/plain")])

	def test_detect_missing_image_field(self):
		environ = {
			"CONTENT_TYPE": "multipart/form-data",
			"wsgi.input": MagicMock(),
		}

		status, message, headers = detect(environ)

		self.assertEqual(status, HTTPStatus.BAD_REQUEST)
		self.assertEqual(message, "No valid 'image' to process was provided")
		self.assertEqual(headers, [("Content-Type", "text/plain")])


if __name__ == '__main__':
	unittest.main()

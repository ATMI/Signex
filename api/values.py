CONTENT_TYPE = "Content-Type"
CONTENT_DISPOSITION = "Content-Dispositon"

PLAIN_TEXT = "text/plain"
MULTIPART_FD = "multipart/form-data"
IMAGE_JPEG = "image/jpeg"
APPLICATION_JSON = "application/json"

CONTENT_PLAIN_TEXT = (CONTENT_TYPE, PLAIN_TEXT)
CONTENT_MULTIPART_FD = (CONTENT_TYPE, MULTIPART_FD)
CONTENT_JPEG = (CONTENT_TYPE, IMAGE_JPEG)
CONTENT_JSON = (CONTENT_TYPE, APPLICATION_JSON)

CGI_DOCUMENT_URI = "DOCUMENT_URI"
CGI_REQUEST_METHOD = "REQUEST_METHOD"
CGI_CONTENT_TYPE = "CONTENT_TYPE"
CGI_INPUT = "wsgi.input"

ACCEPT_REQUEST_FAILURE = -1
NO_CGI_INPUT = -2
CANT_READ_CGI_FIELD = -3
CANT_ENCODE_IMAGE = -4
DETECT_FAILURE = -5
BASE_DETECT_FAILURE = -6
GET_FIELD_STORAGE_FAILURE = -7
COMPARE_FAILURE = -8

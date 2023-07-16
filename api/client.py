import sys

import requests

URL = "..."

arguments = sys.argv

if len(arguments) != 2:
	print("Invalid arguments number, usage:\npython client.py document_path")
else:
	image_path = arguments[1]
	files = {"image": open(image_path, "rb")}

	response = requests.post(f"{URL}/detect", files=files)
	status_code = response.status_code

	print(status_code)
	match status_code:
		case 200:
			print("Successfully processed image, saving result to 'result.jpg'")
			with open("result.jpg", "wb") as f:
				f.write(response.content)
		case _:
			print(response.content)

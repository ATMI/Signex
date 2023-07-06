def myapp(environ, start_response):
	print(environ)
	start_response('200 OK', [('Content-Type', 'text/plain')])
	return ['Hello World!\n']


if __name__ == '__main__':
	from flup.server.fcgi import WSGIServer

	WSGIServer(myapp, bindAddress=('localhost', 8080)).run()

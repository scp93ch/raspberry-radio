#!/usr/bin/env python

# This code is copyright Stephen C Phillips (http://scphillips.com).
# It is licensed under GPL v3.

import socket
import subprocess

# Configuration 
PORT = 8080

def radio(cmd):
	"""Runs the 'radio' command (which runs mpc) and IGNORES the output."""

	print "Executing: radio " + cmd
	proc = subprocess.Popen(['radio', cmd], stdout=subprocess.PIPE)
	output = proc.communicate()[0]
	print output

# This is the web page that we send back to the web browser, regardless of what is requested
body = """
<html>
<head><title>BBC Radio</title></head>
<body>
<ul>
<li><a href="/radio/bbc1">BBC1</a></li>
<li><a href="/radio/bbc2">BBC2</a></li>
<li><a href="/radio/stop">Stop</a></li>
<li><a href="/radio/reset">Reset</a></li>
</ul>
</body>
</html>
"""

# Standard socket stuff
host = ''
port = PORT
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, port))
sock.listen(1)  # don't queue up any requests

# Loop forever, listening for requests:
while True:
	print "Waiting..."
	csock, caddr = sock.accept()
	print "Connection from: " + `caddr`
	
	req = csock.recv(1024)  # Get the request from the socket, 1kB max
	print "Request: " + req

	# The lines in a request each end with \r\n and the first line is what we want
	req = req.split("\r\n")[0]

	# Requests that we want will look like "GET /radio/bbc4 HTTP 1.1"
	if req.startswith("GET /radio/"):
		cmd = req.split("/")[2] # gets everything after the "/radio/"
		cmd = cmd.split(" ")[0] # gets the part before the space
		radio(cmd) # runs the radio command

	# Generally just return the same web page
	if req.startswith("GET /radio/") or req.startswith("GET / "):
		message = "HTTP/1.0 200 OK\r\n" + \
				"Content-Type: text/html\r\n" + \
				"\r\n" + \
				body
	# Any other requests (such as for the favicon) we return a 404 error code
	else:
		message = "HTTP/1.0 404 Not Found\r\n\r\n"

	# Send the message back to the web browser and close the child socket
	csock.sendall(message)
	csock.close()

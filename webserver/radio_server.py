#!/usr/bin/env python

# This code is copyright Stephen C Phillips (http://scphillips.com).
# It is licensed under GPL v3.

import socket
import subprocess
import json
import os
import sys
import select
import logging
import logging.handlers
import argparse

# Configuration 
DEFAULT_PAGE = "index.html"
LOG_FILENAME = "/var/log/radio_server.log"
LOG_LEVEL = logging.INFO

# Defaults
PORT = 8080
ROOT_DIR = "."

# Parse command line arguments
parser = argparse.ArgumentParser(description="Simple web server to control BBC radio")
parser.add_argument("-p", "--port", help="port to listen on (default " + str(PORT) + ")", type=int)
parser.add_argument("-d", "--directory", help="directory to serve files from (default '" + ROOT_DIR + "')")

args = parser.parse_args()
if args.directory:
	ROOT_DIR = os.path.normpath(args.directory)
if args.port:
	PORT = args.port

# Define MIME types for some common filename endings
CTYPE = {
	".js": "application/javascript",
	".html": "text/html",
	".css": "text/css",
	".png": "image/png",
	".woff": "application/font-woff",
	}

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

station_id = {}  # Store the ID of a station keyed by its name

def radio(cmd):
	"""Runs the 'radio' command (which runs mpc) and parses the output.

	Returns a tuple of (HTTP status code, body)
	Deals with the commands: stations, status, stop, reset 
	Other commands are assumed to be a station choice
	"""

	body = ""
	status = "200"

	logger.info("Executing: radio " + cmd)
	proc = subprocess.Popen(['radio', cmd], stdout=subprocess.PIPE)
	output = proc.communicate()[0]
	logger.debug(output)

	if cmd == "stations":
		body = json.dumps({"stations": output.rstrip().split("\n")})
	elif "ERROR" in output:
		status = "503"  # Service Unavailable
	elif "No such station" in output:
		status = "404"  # File Not Found
	elif cmd == "stop" or cmd == "reset":
		# Just assume these worked
		body = json.dumps({"status": "Stopped"})
	else:
		# Then it is "status" or an existing station name
		if "[playing]" in output:
			# The first or second line is the radio station name
			lines = output.rstrip().split("\n")
			if lines[0].startswith("Fetching"):
				station = lines[1]
			else:
				station = lines[0]

			if cmd != "status":
				# We get the ID from the command and link the ID to the station name
				st_id = cmd
				station_id[station] = st_id
			else:
				# Get the ID from the cache with a fall-back
				st_id = station_id.get(station, "Unknown station")

			body = json.dumps({"status": "Playing", "station": station, "id": st_id})
		else:
			body = json.dumps({"status": "Stopped"})
	
	logger.info(status + ": " + body)
	return (status, body)


def page(filename):
	"""Returns a file from the filesystem.

	Returns a tuple of (HTTP status code, content-type, body).
	"""

	# Create complete filepath using ROOT_DIR and remove e.g. all "../"
	if filename.startswith(os.sep):
		filename = filename[1:]
	filepath = os.path.join(ROOT_DIR, filename)
	filepath = os.path.normpath(filepath)
	# Check that the filepath is within ROOT_DIR
	if not filepath.startswith(ROOT_DIR):
		logger.info("403: file out of bounds")
		return ("403", "", "")  # Forbidden
	# If it is a folder then add on e.g. "index.html"
	if os.path.isdir(filepath):
		filepath = os.path.join(filepath, DEFAULT_PAGE)
	# Check the file exists
	if not os.path.exists(filepath):
		logger.info("404: file does not exist")
		return ("404", "", "")  # File Not Found

	# Read the file
	fyle = open(filepath)
	data = fyle.read()
	fyle.close()
	# Guess the file type, defaulting to HTML
	extension = os.path.splitext(filepath)[1]
	ctype = CTYPE.get(extension, "text/html")
	# Return it with status and content type
	logger.info("200: '" + filepath + "' " + ctype)
	return ("200", ctype, data)


# Standard socket stuff
host = ''
port = PORT
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, port))
sock.listen(1)  # don't queue up any requests

# Loop forever, listening for requests:
while True:
	status = ""
	body = ""
	content_type = "application/json"  # default

	logger.debug("Waiting...")
	
	# When a connection is made to sock then it is handed off to another socket, csock
	csock, caddr = sock.accept()
	logger.info("Connection from: " + `caddr`)
	
	try:
		# select waits until the csock is ready to read (or times out after 1 second)
		ready = select.select([csock], [], [], 1)
		if ready[0]:
			req = csock.recv(1024)  # Get the request from the socket, 1kB max
		else:
			raise Exception("Socket read timed out")

		# Uncomment this to see the whole HTTP request:
		#print "Request: " + req

		# The lines in a request each end with \r\n
		req_lines = req.split("\r\n")

		# The first line is most important
		req = req_lines[0]

		# If it is a GET then just ignore any parameters(!)
		if req.startswith("GET") and "?" in req:
			req = req[:req.index("?")]

		logger.info("Request: " + req)

		# If it is a POST then try and find (only one line of) parameters and put into req_body
		if req.startswith("POST"):
			# If there is an \r\n\r\n in the request then take the last line as the request body for a POST
			# TODO: sometimes this fails with list index out of range
			if req_lines[-2] == "":
				req_body = req_lines[-1]
				logger.info("Request body: " + req_body)

		# Perform different actions depending on the HTTP request
		if req.startswith("GET /playing "):
			status, body = radio("status")
		elif req.startswith("GET /stations "):
			status, body = radio("stations")
		elif req.startswith("POST /playing "):
			# Request body is e.g. "station=BBC4"
			station = req_body.split("=")[1]
			if station == "":
				status, body = radio("stop")
			else:
				status, body = radio(station)
		elif req.startswith("POST /reset"):
			status, body = radio("reset")
		else:
			# Default to assuming it was a GET for a page
			filename = req.split(" ")[1]
			status, content_type, body = page(filename)

		message = ""
		if status == "200":
			message = "HTTP/1.0 200 OK\r\n" + \
				"Content-Type: " + content_type + "\r\n" + \
				"\r\n" + \
				body
		elif status == "403":
			message = "HTTP/1.0 403 Forbidden\r\n\r\n"
		elif status == "404":
			message = "HTTP/1.0 404 Not Found\r\n\r\n"
		elif status == "503":
			message = "HTTP/1.0 503 Service Unavailable\r\n\r\n"
		csock.sendall(message)
	except Exception as e:
		logger.warning(e)
	finally:
		csock.close()

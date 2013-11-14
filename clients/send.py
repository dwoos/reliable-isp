#!/usr/bin/env python

import sys
import socket

authenticator = sys.argv[1]
ip = sys.argv[2]
message = sys.argv[3:]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(authenticator + ':' + ' '.join(message), 0, (ip, 3459))

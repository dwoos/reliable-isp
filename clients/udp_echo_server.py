#!/usr/bin/env python

import sys
import json
import socket
import SocketServer

class EchoHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        # self.request is the client connection
        data = self.request[0]  # clip input at 1Kb
        print data

class SimpleServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.UDPServer.__init__(self, server_address, RequestHandlerClass)

if __name__ == "__main__":
    server = SimpleServer(('0.0.0.0', 3459), EchoHandler)
    # terminate with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

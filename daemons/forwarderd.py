#!/usr/bin/env python

import sys
import json
import socket
import SocketServer
from kazoo.client import KazooClient

config = json.loads(open(sys.argv[1]).read())

zookeeper = KazooClient(hosts=','.join(config['zookeeper']))
zookeeper.start()

class ForwardHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        print 'got a packet'
        # self.request is the client connection
        pkt = self.request[0].strip()
        authenticator, _, data =  pkt.partition(':')
        next_hop_ip = zookeeper.get('/circuit/{0}/next_ip'.format(authenticator))[0]
        next_hop_authenticator = zookeeper.get('/circuit/{0}/next_auth'.format(authenticator))[0]
        print 'sending to {0}'.format(next_hop_ip)
        if next_hop_authenticator == '0':
            forward_data = data
        else:
            forward_data = next_hop_authenticator + ':' + data
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(forward_data, 0, (next_hop_ip, 3459))

class SimpleServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.UDPServer.__init__(self, server_address, RequestHandlerClass)

if __name__ == "__main__":
    server = SimpleServer(('0.0.0.0', 3459), ForwardHandler)
    # terminate with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

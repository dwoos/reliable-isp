#!/usr/bin/env python

import sys
import SocketServer
from random import randint
from kazoo.client import KazooClient
import circuitd_pb2 as pb

zookeeper = KazooClient(hosts='localhost:2181')
zookeeper.start()

def new_authenticator():
    return randint(0, 2**63)

def is_valid_client(client_id):
    return True

class CircuitHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        # self.request is the client connection
        data = self.request.recv(1024)  # clip input at 1Kb
        cr = pb.CreateCircuit()
        cr.ParseFromString(data)
        if (is_valid_client(cr.client_id)):
            authenticator = new_authenticator()
            transaction = zookeeper.transaction()
            transaction.create('/circuit/{0}/next_ip'.format(authenticator), b'{0}'.format(cr.next_hop_ip))
            transaction.create('/circuit/{0}/next_auth'.format(authenticator, b'{0}'.format(cr.next_hop_authenticator)))
            transaction.commit()
            response = pb.CircuitCreated()
            response.request.CopyFrom(cr)
            response.authenticator = authenticator
            self.request.send(response.SerializeToString())
        self.request.close()

class SimpleServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)

if __name__ == "__main__":
    server = SimpleServer((sys.argv[1], int(sys.argv[2])), CircuitHandler)
    # terminate with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

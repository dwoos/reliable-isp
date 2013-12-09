#!/usr/bin/env python

import sys
import json
import SocketServer
from random import randint
from kazoo.client import KazooClient
import messages_pb2 as pb

# load local isp zookeeper server ips
# load local isp PoP ips
config = json.loads(open(sys.argv[1]).read())

# open zookeeper client connection
zookeeper = KazooClient(hosts=','.join(config['zookeeper']))
zookeeper.start()

# initialize the circuit state root directory in zookeeper
if not zookeeper.exists('/circuit'):
    zookeeper.create('/circuit')

def new_authenticator():
    return randint(0, 2**31)

def is_valid_client(client_id):
    return True

def get_my_ip():
    import subprocess
    return subprocess.check_output(['curl', '-s', 'http://ipecho.net/plain'])

class CircuitHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        print 'Creating circuit'
        # self.request is the client connection
        data = self.request.recv(1024)  # clip input at 1Kb
        cr = pb.CreateCircuit()
        cr.ParseFromString(data)
        print cr
        if (is_valid_client(cr.client_id)):

            # store circuit state in zookeeper
            authenticator = new_authenticator()
            transaction = zookeeper.transaction()
            if not zookeeper.exists('/circuit/{0}'.format(authenticator)):
                transaction.create('/circuit/{0}'.format(authenticator), b'{0}'.format(cr.client_id))
            transaction.create('/circuit/{0}/next_ip'.format(authenticator), b'{0}'.format(cr.next_hop_ip[0]))
            transaction.create('/circuit/{0}/next_ips'.format(authenticator), b'{0}'.format(','.join(cr.next_hop_ip)))
            transaction.create('/circuit/{0}/next_auth'.format(authenticator), b'{0}'.format(cr.next_hop_authenticator))
            transaction.commit()

            # create response to client
            response = pb.CircuitCreated()
            response.request.CopyFrom(cr)
            response.authenticator = authenticator

            # the transit isp can have multiple PoPs for establish circuit
            for ip in config['ips']:
                response.ip.append(ip)

            # send response to create circuit request from client
            self.request.send(response.SerializeToString())

            print "circuit created"

        else:
            print "invalid client id"
        self.request.close()

class SimpleServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)

if __name__ == "__main__":
    print "Starting circuit server"
    server = SimpleServer(('0.0.0.0', 3456), CircuitHandler)
    # terminate with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

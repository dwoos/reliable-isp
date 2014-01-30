#!/usr/bin/env python

import sys
import socket
import json
import SocketServer
from kazoo.client import KazooClient
import messages_pb2 as pb
import subprocess

CHECK_TIMEOUT = 2
COMPLETE_TIMEOUT = 5

PORT = 3457

NON_RECURSIVE_CHECK = '0'
RECURSIVE_CHECK = '1'

PING_FAILURE = '0'
PING_SUCCESS = '1'

CHECK_FAILURE = '0'
CHECK_SUCCESS = '1'

config = json.loads(open(sys.argv[1]).read())

zookeeper = KazooClient(hosts=','.join(config['zookeeper']))
zookeeper.start()

def get_my_ip():
    return subprocess.check_output(['curl', '-s', 'http://ipecho.net/plain'])

class FailoverHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        print "Received failover check request"
        sys.stdout.flush()

        # determine check message type
        data = self.request[0].strip('\0')
        check_type = data[0]
        client_socket = self.request[1]

        # if it's a standby ISP node; acknowledge ping
        if check_type == NON_RECURSIVE_CHECK:
            client_socket.sendto(PING_SUCCESS, self.client_address)
            return

        # now check for failure at the next hop
        authenticator = int(data[1:])
        print authenticator
        next_authenticator = int(zookeeper.get('/circuit/{0}/next_auth'.format(authenticator))[0])
        print next_authenticator

        # return CHECK_SUCCESS if we are at last hop ISP

        # we arbitrarily decide that service id < 10000 in our experiments
        # this is a hack, need better way to detect that we are at the last hop ISP
        if next_authenticator < 10000:
            print "we're the last hop, so we can't check anymore. succeeding"
            sys.stdout.flush()
            client_socket.sendto(CHECK_SUCCESS, self.client_address)
            return

        # otherwise ping all next_ips
        next_ip = zookeeper.get('/circuit/{0}/next_ip'.format(authenticator))[0]
        next_ips = zookeeper.get('/circuit/{0}/next_ips'.format(authenticator))[0].split(',')

        print "parallel ping " + str(next_ips)
        sys.stdout.flush()

        # initialize ping results to be all failures = 0
        ping_results = [CHECK_FAILURE] * len(next_ips)
        
        current_next_ip_index = -1
        for i in xrange(len(next_ips)):
            ip = next_ips[i]
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(CHECK_TIMEOUT)

            try:
                if ip == next_ip:
                    current_next_ip_index = i
                    print 'set i  = ' + str(i)
                    # send recursive check
                    recursive_check_msg = RECURSIVE_CHECK + str(next_authenticator)
                    sock.sendto(recursive_check_msg, (ip, PORT))
                    received = sock.recv(1024)
                    print "receive from recursive check = " + received
                else:
                    # send recursive check
                    non_recursive_check_msg = NON_RECURSIVE_CHECK
                    sock.sendto(non_recursive_check_msg, (ip, PORT))
                    received = sock.recv(1024)
                    print "receive from non_recursive check = " + received
                # update ping results
                ping_results[i] = received
            except socket.timeout:
                print "timed out on pinging " + ip
                ping_results[i] = CHECK_FAILURE

        print "parallel ping results = " + str(ping_results)

        if ping_results[current_next_ip_index] == PING_FAILURE:
            # found the failure
            print "found failure at next hop = " + next_ip
            print "attempt to failover to an available next hop router"
            for i in xrange(len(next_ips)):
                if ping_results[i] == PING_SUCCESS:
                    print 'successfully fails over to new next hop = ' + next_ips[i]
                    zookeeper.set('/circuit/{0}/next_ip'.format(authenticator), next_ips[i])
                    client_socket.sendto(CHECK_SUCCESS, self.client_address)
                    return

        # none of the next_ips work
        print 'failover fails'
        client_socket.sendto(CHECK_FAILURE, self.client_address)
        return

class SimpleServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.UDPServer.__init__(self, server_address, RequestHandlerClass)

if __name__ == "__main__":
    server = SimpleServer((get_my_ip(), PORT), FailoverHandler)
    # terminate with Ctrl-C
    try:
        print "gonna serve"
        sys.stdout.flush()
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

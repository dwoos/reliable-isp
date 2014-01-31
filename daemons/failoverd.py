#!/usr/bin/env python

import sys
import socket
import json
import SocketServer
from kazoo.client import KazooClient
import subprocess
import threading
import os


NON_RECURSIVE_CHECK = '0'
RECURSIVE_CHECK = '1'

PING_FAILURE = '0'
PING_SUCCESS = '1'

CHECK_FAILURE = '0'
CHECK_SUCCESS = '1'

my_ip = str(os.system("ping $HOSTNAME -c 1 | head -1 | awk '{print $3}' | tr -d '()'"))
PORT = 3457

#if my_ip.startswith('128.95'):
#    CHECK_TIMEOUT = 0.001
#elif my_ip.startswith('171.67'):
CHECK_TIMEOUT = 0.002

# initialize zookeeper client
config = json.loads(open(sys.argv[1]).read())

zookeeper = KazooClient(hosts=','.join(config['zookeeper']))
zookeeper.start()

class PingNextHopThread(threading.Thread):
    def __init__(self, ip, port, next_authenticator, isRecursive):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.next_authenticator = next_authenticator
        self.isRecursive = isRecursive
        self.ping_response = 'x'
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(CHECK_TIMEOUT)
        try:
            if self.isRecursive:
                # send recursive check
                recursive_check_msg = RECURSIVE_CHECK + str(self.next_authenticator)
                sock.sendto(recursive_check_msg, (self.ip, self.port))
                received = sock.recv(1024)
                #print "receive from recursive check = " + received
            else:
                # send recursive check
                non_recursive_check_msg = NON_RECURSIVE_CHECK
                sock.sendto(non_recursive_check_msg, (self.ip, self.port))
                received = sock.recv(1024)
                #print "receive from non_recursive check = " + received
            # update ping results
            self.ping_response = received
        except socket.timeout:
            #print "timed out on pinging " + self.ip
            self.ping_response = CHECK_FAILURE
        

#def get_my_ip():
#    return subprocess.check_output(['curl', '-s', 'http://ipecho.net/plain'])

class FailoverHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        #print "Received failover check request"
        #sys.stdout.flush()

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
        next_authenticator = int(zookeeper.get('/circuit/{0}/next_auth'.format(authenticator))[0])

        # return CHECK_SUCCESS if we are at last hop ISP

        # we arbitrarily decide that service id < 10000 in our experiments
        # this is a hack, need better way to detect that we are at the last hop ISP
        if next_authenticator < 10000:
            #print "we're the last hop, so we can't check anymore. succeeding"
            #sys.stdout.flush()
            client_socket.sendto(CHECK_SUCCESS, self.client_address)
            return

        # otherwise ping all next_ips
        next_ip = zookeeper.get('/circuit/{0}/next_ip'.format(authenticator))[0]
        next_ips = zookeeper.get('/circuit/{0}/next_ips'.format(authenticator))[0].split(',')

        #print "parallel ping " + str(next_ips)
        #sys.stdout.flush()

        # initialize ping results to be all failures = 0
        ping_results = [CHECK_FAILURE] * len(next_ips)
        
        # spawn a thread for each ping
        ping_threads = []
        current_next_ip_index = -1
        for i in xrange(len(next_ips)):
            ip = next_ips[i]
            if ip == next_ip:
                current_next_ip_index = i
                t = PingNextHopThread(ip, PORT, next_authenticator, True)
                t.start()
                ping_threads.append(t)
            else:
                t = PingNextHopThread(ip, PORT, next_authenticator, False)
                t.start()
                ping_threads.append(t)

        # join and gather response from all pings
        for i in xrange(len(next_ips)):
            t = ping_threads[i]
            t.join()
            ping_results[i] = t.ping_response

        print "parallel ping results = " + str(ping_results)

        if ping_results[current_next_ip_index] == PING_FAILURE:
            # found the failure
            #print "found failure at next hop = " + next_ip
            #print "attempt to failover to an available next hop router"
            for i in xrange(len(next_ips)):
                if ping_results[i] == PING_SUCCESS:
                    #print 'successfully fails over to new next hop = ' + next_ips[i]
                    # delete the old service table entry
                    subprocess.call(['/taas/src/tools/servicetool', 'del', 
                                    str(authenticator), str(next_ip), 'taas', str(next_authenticator)])
                    # fill in updated next_ip in service table
                    subprocess.call(['/taas/src/tools/servicetool', 'add', 
                                    str(authenticator), str(next_ips[i]), 'taas', str(next_authenticator)])
                    client_socket.sendto(CHECK_SUCCESS, self.client_address)
                    # call zookeeper
                    zookeeper.set('/circuit/{0}/next_ip'.format(authenticator), next_ips[i])
                    return

        # none of the next_ips work
        #print 'failover fails'
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
    server = SimpleServer((my_ip, PORT), FailoverHandler)
    # terminate with Ctrl-C
    try:
        print "gonna serve"
        sys.stdout.flush()
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

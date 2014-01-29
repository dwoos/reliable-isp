#!/usr/bin/env python

import sys
import socket
import json
import SocketServer
from kazoo.client import KazooClient
import messages_pb2 as pb
import subprocess

ACK_TIMEOUT = 5

PORT = 3457

config = json.loads(open(sys.argv[1]).read())

zookeeper = KazooClient(hosts=','.join(config['zookeeper']))
zookeeper.start()


def get_my_ip():
    #return subprocess.check_output(["ifconfig | grep 10.128 | awk '{print $2}' | cut -c 6-"],
    #                               shell=True).strip()
    return subprocess.check_output(['curl', '-s', 'http://ipecho.net/plain'])

class FailoverHandler(SocketServer.BaseRequestHandler):
    def fail(self, req):
        fail = pb.FailoverComplete()
        fail.request.CopyFrom(req)
        fail.success = False
        self.request.send(fail.SerializeToString())
        self.request.close()

    def ack(self, req):
        ack = pb.CheckFailoverAcknowledge()
        ack.request.CopyFrom(req)
        self.request.send(ack.SerializeToString())


    def succeed(self, req):
        success = pb.FailoverComplete()
        success.request.CopyFrom(req)
        success.success = True
        self.request.send(success.SerializeToString())
        self.request.close()

    def handle(self):
        # self.request is the client connection
        print "Received failover check request"
        sys.stdout.flush()
        data = self.request.recv(1024)  # clip input at 1Kb
        req = pb.CheckFailover()
        req.ParseFromString(data)
        print "ACKing"
        sys.stdout.flush()
        self.ack(req)

        if not req.should_forward:
            print "no need to forward, so we're done"
            sys.stdout.flush()
            # cool, we're done
            self.request.close()
            return
        # now check for failure at the next hop
        next_authenticator = int(zookeeper.get('/circuit/{0}/next_auth'.format(req.authenticator))[0])
        if not next_authenticator:
            print "we're the last hop, so we can't check anymore. succeeding"
            sys.stdout.flush()
            return self.succeed(req)
        next_ip = zookeeper.get('/circuit/{0}/next_ip'.format(req.authenticator))[0]

        print "going to check " + next_ip
        sys.stdout.flush()
        next_req = pb.CheckFailover()
        next_req.authenticator = next_authenticator
        next_req.should_forward = True

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(5)
        try:
            sock.connect((next_ip, PORT))
            sock.send(next_req.SerializeToString())
            data = sock.recv(1024)
            ack = pb.CheckFailoverAcknowledge()
            ack.ParseFromString(data)
            assert ack.request == next_req
        except socket.error:
            print "ping of {0} timed out--we've found the problem!".format(next_ip)
            sys.stdout.flush()
            # we've found the failure
            ping_req = pb.CheckFailover()
            ping_req.authenticator = next_authenticator
            ping_req.should_forward = False
            ping_req_data = ping_req.SerializeToString()
            next_ips = zookeeper.get('/circuit/{0}/next_ips'.format(req.authenticator))[0]
            for ip in next_ips.split(','):
                if ip == next_ip:
                    continue
                print "checking " + ip
                sys.stdout.flush()
                ping_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ping_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                ping_sock.settimeout(5)
                try:
                    ping_sock.connect((ip, PORT))
                    ping_sock.send(ping_req_data)
                    data = ping_sock.recv(1024)
                    ping_sock.close()
                    ping_ack = pb.CheckFailoverAcknowledge()
                    ping_ack.ParseFromString(data)
                    assert ping_ack.request == ping_req
                    # ok, this is our new ip
                    print ip + " seems to work! let's use it."
                    sys.stdout.flush()
                    zookeeper.set('/circuit/{0}/next_ip'.format(req.authenticator), ip)
                    return self.succeed(req)
                except Exception as e:
                    print e
                    sys.stdout.flush()
                    print ip + " failed"
                    sys.stdout.flush()
                    continue
            # ok, we're out of ips. fail!
            return self.fail(req)
        except e:
            # some other error, bail
            print e
            sys.stdout.flush()
            return self.fail(req)
        else:
            # wait for complete, then return to client
            try:
                sock.settimeout(10)
                data = sock.recv(1024)
                sock.close()
                complete = pb.FailoverComplete()
                complete.ParseFromString(data)
                assert complete.request == next_req
                if complete.success:
                    return self.succeed(req)
                return self.fail(req)
            except:
                return self.fail(req)


class SimpleServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)

if __name__ == "__main__":
    server = SimpleServer((get_my_ip(), 3457), FailoverHandler)
    # terminate with Ctrl-C
    try:
        print "gonna serve"
        sys.stdout.flush()
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

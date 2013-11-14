import sys
import socket
import messages_pb2 as pb

authenticator = int(sys.argv[1])
first_ip = sys.argv[2]

check = pb.CheckFailover()
check.authenticator = authenticator
check.should_forward = True

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
try:
    sock.connect((first_ip, 3457))
    sock.send(check.SerializeToString())
    data = sock.recv(1024)
    ack = pb.CheckFailoverAcknowledge()
    ack.ParseFromString(data)
    assert ack.request == check
except:
    print "failover at first isp"
    exit(1)
sock.settimeout(10)
try:
    data = sock.recv(1024)
    complete = pb.FailoverComplete()
    complete.ParseFromString(data)
    assert complete.request == check
except:
    print "strange failure at first isp"
    raise
if complete.success:
    print "we're good!"
else:
    print "failover has failed, bail"

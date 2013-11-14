import sys
import socket
import messages_pb2 as pb

ips = list(reversed(sys.argv[1:]))

next_hop_ips = [ips[0]]
ips = ips[1:]
next_hop_authenticator = None
for ip in ips:
    print ip
    print next_hop_ips
    cc = pb.CreateCircuit()
    cc.client_id = 2
    cc.next_hop_ip.extend(next_hop_ips)
    if next_hop_authenticator:
        cc.next_hop_authenticator = next_hop_authenticator

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, 3456))
    sock.send(cc.SerializeToString())

    data = sock.recv(1024)
    ccr = pb.CircuitCreated()
    ccr.ParseFromString(data)
    sock.close()
    next_hop_authenticator = ccr.authenticator
    next_hop_ips = ccr.ip
print next_hop_authenticator

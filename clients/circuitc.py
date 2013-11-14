import sys
import socket
import messages_pb2 as pb

# argv format to circuitc.py
# python circuitc.py first_isp middle_isp last_isp the_other_endhost

# need to establish circuit in the REVERSE order
# from the last isp to the first isp
# in order to obtain the next_hop_authenticator
ips = list(reversed(sys.argv[1:]))

# get the_other_endhost ip
# the_other_endhost has a single ip
# but for transit segments, there can be multiple next_hop_ips
next_hop_ips = [ips[0]]

# get the ips for all transit isps in REVERSE order
# starting from the_other_endhost side
ips = ips[1:]

# the_other_endhost doesn't need an authenticator
# create circuit request will fill in the authenticator
# for transit segments between isp hops
next_hop_authenticator = None

# establish circuit from the last_isp backwards to client 
for ip in ips:
    print ip
    print next_hop_ips
    cc = pb.CreateCircuit()
    cc.client_id = 2
    cc.next_hop_ip.extend(next_hop_ips)
    # the previous create circuit request will have filled in the authenticator 
    if next_hop_authenticator:
        cc.next_hop_authenticator = next_hop_authenticator

    # send create circuit request to ip
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, 3456))
    sock.send(cc.SerializeToString())

    # reply from circuitd server
    data = sock.recv(1024)
    ccr = pb.CircuitCreated()
    ccr.ParseFromString(data)
    sock.close()

    # fill in the authenticator and next_hop_ips for the next create circuit request
    next_hop_authenticator = ccr.authenticator
    next_hop_ips = ccr.ip
print next_hop_authenticator

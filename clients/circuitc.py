import sys
import time
import socket
import os
import messages_pb2 as pb
from kazoo.client import KazooClient
from kazoo.recipe import watchers
from telnetlib import Telnet

#def get_my_ip():
#    import netifaces as ni
#    return ni.ifaddresses('eth7')[2][0]['addr']
#
#try:
#    servd_conn = Telnet(get_my_ip(), 9999)
#    servd_conn.read_until('help\n')
#except socket.error:
#    print "Local servd not running, so we won't be able to get service info"
#
#def get_local_service_table():
#    servd_conn.write('s\r\n')
#    # put a delay in
#    servd_conn.read_some()
#    servd_conn.write('h\r\n')
#    all_service_lines = servd_conn.read_until('service table\n').split('\n')[3:-7]
#    all_service_entries = [filter(None, line.split(' ')) for line in all_service_lines]
#    taas_entries = [entry for entry in all_service_entries if entry[-2] not in ('0', 'none')]
#    return {entry[-2]: entry[-1] for entry in taas_entries}

# delete default forwarding rules
os.system('~/taas/src/tools/servicetool del 0:0 127.0.0.1')
os.system('~/taas/src/tools/servicetool del 0:0 128.208.6.255')
os.system('~/taas/src/tools/servicetool del 0:0 128.95.1.120')

def register_service(auth, ip_addr):
    # use a catch all rule 0:0
    return os.system("~/taas/src/tools/servicetool add 0:0 {0} taas {1}".format(ip_addr, str(auth)))


# argv format to circuitc.py
# python circuitc.py first_isp middle_isp last_isp the_other_endhost server_service_id

# need to establish circuit in the REVERSE order
# from the last isp to the first isp
# in order to obtain the next_hop_authenticator
ips = list(reversed(sys.argv[1:]))

# the_other_endhost doesn't need an authenticator
# create circuit request will fill in the authenticator
# for transit segments between isp hops
next_hop_authenticator = int(ips[0])

# get the_other_endhost ip
# the_other_endhost has a single ip
# but for transit segments, there can be multiple next_hop_ips
next_hop_ips = [ips[1]]

# get the ips for all transit isps in REVERSE order
# starting from the_other_endhost side
ips = ips[2:]

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

# populate the client's own Serval service table
register_service(next_hop_authenticator, next_hop_ips[0])

import socket
import circuitd_pb2 as pb
HOST, PORT = 'localhost', 3456
# SOCK_STREAM == a TCP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#sock.setblocking(0)  # optional non-blocking
sock.connect((HOST, PORT))

cc = pb.CreateCircuit()
cc.client_id = 2
cc.next_hop_ip = 10
cc.next_hop_authenticator = 5

sock.send(cc.SerializeToString())
reply = sock.recv(16384)  # limit reply to 16K
sock.close()
cr = pb.CircuitCreated()
cr.ParseFromString(reply)
print cr

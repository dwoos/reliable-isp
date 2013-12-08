TAAS_DIR = /taas

clients/udp_taas_client: clients/messages.pb-c.c clients/trigger_failover.c clients/udp_taas_client.c
	libtool --mode=link gcc -Wall -g -I$(TAAS_DIR)/include -L$(TAAS_DIR)/src/libserval -lserval -lprotobuf-c -o clients/udp_taas_client clients/messages.pb-c.c clients/trigger_failover.c clients/udp_taas_client.c

daemons/udp_taas_server: daemons/udp_taas_server.c
	libtool --mode=link gcc -Wall -g -I$(TAAS_DIR)/include -L$(TAAS_DIR)/src/libserval/-lserval -o daemons/udp_taas_server daemons/udp_taas_server.c

protobufs:
	protoc messages.proto --python_out=daemons/
	protoc messages.proto --python_out=clients/


default: daemons/udp_taas_server clients/udp_taas_client protobufs

clean:
	rm clients/udp_taas_client
	rm daemons/udp_taas_daemon

.PHONY: default protobufs clean

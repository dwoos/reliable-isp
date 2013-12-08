TAAS_DIR = /taas

clients/udp_taas_client: clients/messages.pb-c.c clients/trigger_failover.c clients/udp_taas_client.c
	cd clients
	libtool --mode=link gcc -Wall -g -O0 -fno-inline -I/taas/include -L/taas/src/libserval -lserval -lprotobuf-c -o udp_taas_client messages.pb-c.c trigger_failover.c udp_taas_client.c
	cd ..

daemons/udp_taas_server: clients/udp_taas_server.c
	cd daemons
	libtool --mode=link gcc -Wall -g -O0 -fno-inline -I/taas/include -L/taas/src/libserval -lserval -o udp_taas_server udp_taas_server.c
	cd ..

default: daemons/udp_taas_server clients/udp_taas_client
	protoc messages.proto --python_out=daemons/
	protoc messages.proto --python_out=clients/

.PHONY: default

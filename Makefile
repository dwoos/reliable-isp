TAAS_DIR = /taas

clients/udp_taas_client:
	gcc -I$(TAAS_DIR)/include -L$(TAAS_DIR)/src/libserval -lserval clients/trigger_failover.c clients/udp_taas_client.c -o clients/udp_taas_client

daemons/udp_taas_server:
	gcc -I$(TAAS_DIR)/include -L$(TAAS_DIR)/src/libserval -lserval daemons/udp_taas_server.c -o daemons/udp_taas_server

default: clients/udp_taas_server clients/udp_taas_client
	protoc messages.proto --python_out=daemons/
	protoc messages.proto --python_out=clients/

.PHONY: default

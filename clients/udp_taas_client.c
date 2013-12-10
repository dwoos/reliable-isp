/* -*- Mode: C++; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 8 -*- */
// Copyright (c) 2010 The Trustees of Princeton University (Trustees)

// Permission is hereby granted, free of charge, to any person obtaining a
// copy of this software and/or hardware specification (the “Work”) to deal
// in the Work without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or
// sell copies of the Work, and to permit persons to whom the Work is
// furnished to do so, subject to the following conditions: The above
// copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Work.

// THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
// THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
// OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
// ARISING FROM, OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER
// DEALINGS IN THE WORK.
#include <libserval/serval.h>
#include <netinet/serval.h>
#include <sys/socket.h>
#include <errno.h>
#include <stdlib.h>
#include <ctype.h>
#include <unistd.h>
#include <signal.h>
#include <sys/time.h>

#define FAILOVER_PORT 3457

static char *local_ip;
static int local_port;
static int service_id;
static char *isp;
static unsigned long long taas;
static int failover_timeout;

static int sock;

static int sock_backchannel;

int trigger_failover(char *hostname, int portno, unsigned long long auth);

void signal_handler(int sig)
{
        printf("signal caught! closing socket...\n");
        //close(sock);
}

int set_reuse_ok(int soc)
{
	int option = 1;

	if (setsockopt(soc, SOL_SOCKET, SO_REUSEADDR,
                       &option, sizeof(option)) < 0) {
		fprintf(stderr, "proxy setsockopt error");
		return -1;
	}
	return 0;
}

int set_timeout(int s) {
        struct timeval tv;

        tv.tv_sec = failover_timeout;
        tv.tv_usec = 0;

        if (setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, (char *)&tv,
                       sizeof(struct timeval)) < 0) {
                printf("set timeout failed\n");
                return -1;
        }
        return 0;
}

int client(char *ip) {
	struct sockaddr_sv srvaddr;
	struct sockaddr_sv cliaddr;
        struct sockaddr_in myaddr;
        struct sockaddr_in dummyaddr;
        int dummysize;
	int ret = 0;
	unsigned N = 2000;
	char sbuf[N];
        char rbuf[N+1];

        sock_backchannel = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

        if (sock_backchannel == -1) {
                fprintf(stderr, "socket: %s\n",
                        strerror_sv(errno));
                return -1;
        }
        set_reuse_ok(sock_backchannel);
        set_timeout(sock_backchannel);
        memset((char *)&myaddr, 0, sizeof(myaddr));
        myaddr.sin_family = AF_INET;
        inet_aton(ip, &myaddr.sin_addr);
        myaddr.sin_port = htons(local_port);

        bind(sock_backchannel, (struct sockaddr *)&myaddr, sizeof(myaddr));

	bzero(&srvaddr, sizeof(srvaddr));
	srvaddr.sv_family = AF_SERVAL;
	srvaddr.sv_srvid.s_sid32[0] = htonl(service_id);

	sock = socket_sv(AF_SERVAL, SOCK_DGRAM, SERVAL_PROTO_UDP);


        if (sock == -1) {
                fprintf(stderr, "socket: %s\n",
                        strerror_sv(errno));
                return -1;
        }

	set_reuse_ok(sock);

	bzero(&cliaddr, sizeof(cliaddr));
	cliaddr.sv_family = AF_SERVAL;
	cliaddr.sv_srvid.s_sid32[0] = htonl(local_port);

        ret = bind_sv(sock, (struct sockaddr *) &cliaddr, sizeof(cliaddr));

	if (ret < 0) {
		fprintf(stderr, "bind: %s\n",
                        strerror_sv(errno));
		return -1;
	}


        ret = connect_sv(sock, (struct sockaddr *)&srvaddr, sizeof(srvaddr));

	if (ret < 0) {
		fprintf(stderr, "connect: %s\n",
			strerror_sv(errno));
		return -1;
	}

	printf("connected\n");
        fflush(stdout);
        // hack around race condition
        sleep(10);

	while (1) {
                sprintf(sbuf, "ping %s %d", ip, local_port);
		//printf("client: sending \"%s\" to service ID %s\n",
                //sbuf, service_id_to_str(&srvaddr.sv_srvid));

                ret = sendto_sv(sock, sbuf, strlen(sbuf), 0, (struct sockaddr *)&srvaddr, sizeof(srvaddr));

		if (ret < 0) {
			fprintf(stderr, "send failed (%s)\n",
                                strerror_sv(errno));
                        break;
		}

		ret = recvfrom(sock_backchannel, rbuf, N, 0, (struct sockaddr *)&dummyaddr, &dummysize);
		rbuf[ret] = 0;

                if (ret == 0) {
                        printf("server closed\n");
                        break;
                }
                else if (ret < 0) {
                        printf("failure detected!\n");
                        fflush(stdout);
                        struct timeval t1, t2;
                        double elapsed_time;
                        gettimeofday(&t1, NULL);
                        trigger_failover(isp, FAILOVER_PORT, taas);
                        gettimeofday(&t2, NULL);
                        elapsed_time = (t2.tv_sec - t1.tv_sec) * 1000.0;
                        elapsed_time += (t2.tv_usec - t1.tv_usec) / 1000.0;
                        printf("FAILOVER IN %f\n", elapsed_time);
                        fflush(stdout);
                        sleep(60);
                }
                else {
                        //printf("Response from server: %s\n", rbuf);

                        if (strcmp(sbuf, "quit") == 0)
                                break;
                }
                sleep(1);
	}

	if (close_sv(sock) < 0)
		fprintf(stderr, "close: %s\n",
                        strerror_sv(errno));

        return ret;
}

int main(int argc, char **argv)
{
	struct sigaction action;
        int ret;

	memset(&action, 0, sizeof(struct sigaction));
        action.sa_handler = signal_handler;

	/* The server should shut down on these signals. */
        //sigaction(SIGTERM, &action, 0);
	//sigaction(SIGHUP, &action, 0);
	//sigaction(SIGINT, &action, 0);
        if (argc != 6) {
                printf("Usage: udp_taas_client local_ip local_port service_id isp failover_timeout\n");
                exit(0);
        }
        local_ip = argv[1];
        local_port = atoi(argv[2]);
        service_id = atoi(argv[3]);
        isp = argv[4];
        taas = service_id;
        failover_timeout = atoi(argv[5]);

        ret = client(argv[1]);

        printf("client done..\n");

        return ret;
}

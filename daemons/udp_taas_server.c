/* -*- Mode: C; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 8 -*- */
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
#include <errno.h>
#include <stdlib.h>
#include <ctype.h>
#include <unistd.h>

int set_reuse_ok(int sock);

int server(short sid)
{
        int backchannel_sock;

        backchannel_sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
        set_reuse_ok(backchannel_sock);


        int sock, backlog = 8;;
        struct sockaddr_sv servaddr, cliaddr;

        if ((sock = socket_sv(AF_SERVAL, SOCK_DGRAM, SERVAL_PROTO_UDP)) < 0) {
                fprintf(stderr, "error creating AF_SERVAL socket: %s\n",
                        strerror_sv(errno));
                return -1;
        }
        memset(&servaddr, 0, sizeof(servaddr));
        servaddr.sv_family = AF_SERVAL;
        servaddr.sv_srvid.s_sid32[0] = htonl(sid);

        set_reuse_ok(sock);

        if (bind_sv(sock, (struct sockaddr *)&servaddr,
                    sizeof(servaddr)) < 0) {
                fprintf(stderr, "error binding socket: %s\n",
                        strerror_sv(errno));
                close_sv(sock);
                return -1;
        }

        printf("server: bound to service id %d\n", sid);

        listen_sv(sock, backlog);

        do {
                socklen_t l = sizeof(cliaddr);
                int k = 0;

                printf("calling accept\n");

                int fd = accept_sv(sock, (struct sockaddr *)&cliaddr, &l);

                if (fd < 0) {
                        fprintf(stderr, "error accepting new conn %s\n",
                                strerror_sv(errno));
                        return -1;
                }

                printf("server: recv conn from service id %s; got fd = %d\n",
                       service_id_to_str(&cliaddr.sv_srvid), fd);


                do {
                        unsigned N = 2000;
                        char buf[N];
                        int n;

                        /* printf("server: waiting on client request\n"); */

                        if ((n = recvfrom_sv(sock, buf, N, 0, (struct sockaddr *)&cliaddr, &l)) < 0) {
                                fprintf(stderr,
                                        "server: error receiving client request: %s\n",
                                        strerror_sv(errno));
                                break;
                        }
                        if (n == 0) {
                                fprintf(stderr, "server: received EOF; "
                                        "listening for new conns\n");
                                break;
                        }
                        buf[n] = '\0';

                        printf("server: request (%d bytes): %s\n", n, buf);
                        if (n > 0) {
                                strtok(buf, " ");
                                char *ip;
                                int port;
                                char *sbuf = "pong";
                                ip = strtok(NULL, " ");
                                port = atoi(strtok(NULL, " "));
                                struct sockaddr_in backchannel_addr;
                                memset((char*)&backchannel_addr, 0, sizeof(backchannel_addr));
                                backchannel_addr.sin_family = AF_INET;
                                backchannel_addr.sin_port = htons(port);
                                inet_aton(ip, &backchannel_addr.sin_addr);
                                sendto(backchannel_sock, sbuf, strlen(sbuf), 0, (struct sockaddr *)&backchannel_addr, sizeof(backchannel_addr));
                                /* if (strcmp(buf, "quit") == 0) */
                                /*         break; */
                        }
                        k++;
                } while (1);
                close_sv(fd);
                printf("Server listening for NEW connections\n");
        } while (1);
        close_sv(sock);

        printf("Exiting\n");

        return -1;
}

int set_reuse_ok(int sock)
{
        int option = 1;
        if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR,
                       &option, sizeof(option)) < 0) {
                fprintf(stderr, "proxy setsockopt error");
                return -1;
        }
        return 0;
}

int main(int argc, char **argv)
{
        return server(atoi(argv[1]));
}

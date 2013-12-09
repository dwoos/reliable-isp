/*
 * tcpclient.c - A simple TCP client
 * usage: tcpclient <host> <port>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <netdb.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>

#include "messages.pb-c.h"

#define BUFSIZE 1024
#define MAX_MSG_SIZE 1024

#define CONNECT_TIMEOUT 5
#define CHECK_REQUEST_TIMEOUT 5
#define CHECK_ACK_TIMEOUT 5
#define CHECK_COMPLETE_TIMEOUT 10

/*
 * error - wrapper for perror
 */
void error(char *msg) {
    perror(msg);
    exit(0);
}

int trigger_failover(char *hostname, int portno, unsigned long long auth) {
    int sockfd, n;
    struct sockaddr_in serveraddr;
    struct hostent *server;

    /* socket: create the socket */
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0)
        error("ERROR opening socket");

    /* gethostbyname: get the server's DNS entry */
    server = gethostbyname(hostname);
    if (server == NULL) {
        fprintf(stderr,"ERROR, no such host as %s\n", hostname);
        exit(0);
    }

    /* build the server's Internet address */
    bzero((char *) &serveraddr, sizeof(serveraddr));
    serveraddr.sin_family = AF_INET;
    bcopy((char *)server->h_addr,
            (char *)&serveraddr.sin_addr.s_addr, server->h_length);
    serveraddr.sin_port = htons(portno);

    /* make connection non-blocking */
    fcntl(sockfd, F_SETFL, O_NONBLOCK);

    /* connect: create a connection with the server */
    n = connect(sockfd, (struct sockaddr *)&serveraddr, sizeof(serveraddr));

    /* set timeout option in tcp connection */
    struct timeval tv;
    tv.tv_sec = CONNECT_TIMEOUT;  /* 5 Secs Timeout */
    tv.tv_usec = 0;

    fd_set fdset;
    FD_ZERO(&fdset);
    FD_SET(sockfd, &fdset);

    if (select(sockfd + 1, NULL, &fdset, NULL, &tv) == 1) {
        int so_error;
        socklen_t len = sizeof so_error;

        getsockopt(sockfd, SOL_SOCKET, SO_ERROR, &so_error, &len);

        if (so_error == 0) {
            printf("Connected to %s:%d for failover protocol\n", hostname, portno);
        } else {
            fprintf(stderr, "connection error, failover at first isp");
            return 1;
        }
    }

    /* construct check failover message */
    Messages__CheckFailover check_msg = MESSAGES__CHECK_FAILOVER__INIT; // CheckFailover
    char buf_backing[1000000];
    void *buf = buf_backing;

    check_msg.authenticator = auth;
    check_msg.should_forward = 1;
    unsigned len = messages__check_failover__get_packed_size(&check_msg);

    messages__check_failover__pack(&check_msg,buf);

    /* send check message */
    n = write(sockfd, buf, len);
    tv.tv_sec = CHECK_REQUEST_TIMEOUT;
    tv.tv_usec = 0;
    if (select(sockfd + 1, NULL, &fdset, NULL, &tv) == 1) {
        int so_error;
        socklen_t len = sizeof so_error;

        getsockopt(sockfd, SOL_SOCKET, SO_ERROR, &so_error, &len);

        if (so_error == 0) {
            printf("check message sent\n");
        } else {
            fprintf(stderr, "fail to send check message; failover at first isp");
            return 1;
        }
    }

    /* read ack */
    bzero(buf, BUFSIZE);

    tv.tv_sec = CHECK_ACK_TIMEOUT;
    tv.tv_usec = 0;
    if (select(sockfd + 1, &fdset, NULL, NULL, &tv) == 1) {
        int so_error;
        socklen_t len = sizeof so_error;

        getsockopt(sockfd, SOL_SOCKET, SO_ERROR, &so_error, &len);

        if (so_error == 0) {
            n = read(sockfd, buf, BUFSIZE);
            printf("ack received\n");
        } else {
            fprintf(stderr, "fail to receive ack; failover at first isp");
            return 1;
        }
    }

    /* construct check failover acknowledgement */
    // Unpack the message using protobuf-c.
    Messages__CheckFailoverAcknowledge *ack_msg;
    ack_msg = messages__check_failover_acknowledge__unpack(NULL, n, buf);
    if (ack_msg == NULL) {
        fprintf(stderr, "error unpacking incoming ack message\n");
        return 1;
    }

    // failover ack message
    Messages__CheckFailover *check_request = ack_msg->request;
    printf("Ack msg: auth=%" PRIu64 "\n",check_request->authenticator);  // required field

    if (check_request->authenticator != check_msg.authenticator) {
        fprintf(stderr, "error in acknowledge message authenticator");
        return 1;
    }

    // free the ack message
    messages__check_failover_acknowledge__free_unpacked(ack_msg, NULL);


    /* read complete */
    bzero(buf, BUFSIZE);

    tv.tv_sec = CHECK_COMPLETE_TIMEOUT;
    tv.tv_usec = 0;
    if (select(sockfd + 1, &fdset, NULL, NULL, &tv) == 1) {
        int so_error;
        socklen_t len = sizeof so_error;

        getsockopt(sockfd, SOL_SOCKET, SO_ERROR, &so_error, &len);

        if (so_error == 0) {
            n = read(sockfd, buf, BUFSIZE);
            printf("complete received\n");
        } else {
            fprintf(stderr, "fail to receive complete; failover fail");
            return 1;
        }
    }


    /* construct failover complete */
    // Unpack the message using protobuf-c.
    Messages__FailoverComplete *complete_msg;
    complete_msg = messages__failover_complete__unpack(NULL, n, buf);
    if (complete_msg == NULL) {
        fprintf(stderr, "error unpacking incoming complete message\n");
        return 1;
    }

    // failover complete message
    check_request = complete_msg->request;
    printf("Complete msg: auth=%" PRIu64 "\n",check_request->authenticator);  // required field

    if (check_request->authenticator != check_msg.authenticator) {
        fprintf(stderr, "error in complete message authenticator");
        return 1;
    }

    if (complete_msg->success) {
        printf("failover success\n");
    } else {
        printf("failover failed\n");
    }

    // free complete message
    messages__failover_complete__free_unpacked(complete_msg, NULL);

    close(sockfd);

    return 0;
}

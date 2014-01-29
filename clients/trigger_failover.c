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

#define CONNECT_TIMEOUT 10
#define CHECK_REQUEST_TIMEOUT 10
#define CHECK_ACK_TIMEOUT 10
#define CHECK_COMPLETE_TIMEOUT 10

/*
 * error - wrapper for perror
 */
#define error(msg) \
            do { perror(msg); return false; } while (0)

int trigger_failover(char *next_hop, int port, unsigned long long auth) {
    /* socket: create the socket */
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0)
        error("ERROR opening socket");

    /* build the server's Internet address */
    struct sockaddr_in next_hop_addr;
    bzero((char *) &next_hop_addr, sizeof(next_hop_addr));
    next_hop_addr.sin_family = AF_INET;
    inet_aton(next_hop, &next_hop_addr.sin_addr);
    next_hop_addr.sin_port = htons(port);

    /* make connection non-blocking for timeout */
    int fcntl_flags = fcntl(sockfd, F_GETFL, 0);
    if (fcntl(sockfd, F_SETFL, fcntl_flags | O_NONBLOCK) == -1)
        error("fcntl");

    /* set timeout option in tcp connection */
    struct timeval tv;
    tv.tv_sec = CONNECT_TIMEOUT;  /* 5 Secs Timeout */
    tv.tv_usec = 0;

    /* master_fdset for select */
    fd_set master_fdset;
    FD_ZERO(&master_fdset);
    FD_SET(sockfd, &master_fdset);

    /* try to connect before timeout */
    fd_set fdset;
    memcpy(&fdset, &master_fdset, sizeof(master_fdset));

    /* connect: create a connection with the server */
    int n = connect(sockfd, (struct sockaddr *)&next_hop_addr, sizeof(next_hop_addr));

    int rc = select(sockfd + 1, NULL, &fdset, NULL, &tv);
    if (rc == -1) {
        error("select");
    } else if (rc == 0) {
        // timeout in connect
        fprintf(stderr, "connection error, failover at first isp");
        return false;
    }
    
    // printf("Connected to %s:%d for failover protocol\n", hostname, port);

    char buf[BUFSIZE];
    /* construct check failover message */
    Messages__CheckFailover check_msg = MESSAGES__CHECK_FAILOVER__INIT; // CheckFailover
    check_msg.authenticator = auth;
    check_msg.should_forward = 1;
    unsigned len = messages__check_failover__get_packed_size(&check_msg);
    messages__check_failover__pack(&check_msg,buf);

    /* send check message */
    tv.tv_sec = CHECK_REQUEST_TIMEOUT;
    tv.tv_usec = 0;
    memcpy(&fdset, &master_fdset, sizeof(master_fdset));
    n = write(sockfd, buf, len);
    rc = select(sockfd + 1, NULL, &fdset, NULL, &tv);
    if (rc == -1) {
        error("select");
    } else if (rc == 0) {
        // timeout in send check_request
        fprintf(stderr, "timeout in sending check_request, failover at first isp");
        return false;
    }

    /* read ack */
    bzero(buf, BUFSIZE);
    tv.tv_sec = CHECK_ACK_TIMEOUT;
    tv.tv_usec = 0;
    memcpy(&fdset, &master_fdset, sizeof(master_fdset));
    rc = select(sockfd + 1, &fdset, NULL, NULL, &tv);
    if (rc == -1) {
        error("select");
    } else if (rc == 0) {
        // timeout in send check_request
        fprintf(stderr, "fail to receive ack; failover at first isp");
        return false;
    }

    /* construct check failover acknowledgement */
    // Unpack the message using protobuf-c.
    Messages__CheckFailoverAcknowledge *ack_msg;
    ack_msg = messages__check_failover_acknowledge__unpack(NULL, n, buf);
    if (ack_msg == NULL) {
        fprintf(stderr, "error unpacking incoming ack message\n");
        return false;
    }

    // failover ack message
    Messages__CheckFailover *check_request = ack_msg->request;
    //    printf("Ack msg: auth=%" PRIu64 "\n",check_request->authenticator);  // required field
    if (check_request->authenticator != check_msg.authenticator) {
        fprintf(stderr, "error in acknowledge message authenticator");
        return false;
    }

    // free the ack message
    messages__check_failover_acknowledge__free_unpacked(ack_msg, NULL);

    /* read complete */
    bzero(buf, BUFSIZE);

    tv.tv_sec = CHECK_COMPLETE_TIMEOUT;
    tv.tv_usec = 0;
    memcpy(&fdset, &master_fdset, sizeof(master_fdset));
    rc = select(sockfd + 1, &fdset, NULL, NULL, &tv);
    if (rc == -1) {
        error("select");
    } else if (rc == 0) {
        fprintf(stderr, "fail to receive complete; failover fail");
        return false;
    }


    /* construct failover complete */
    // Unpack the message using protobuf-c.
    Messages__FailoverComplete *complete_msg;
    complete_msg = messages__failover_complete__unpack(NULL, n, buf);
    if (complete_msg == NULL) {
        fprintf(stderr, "error unpacking incoming complete message\n");
        return false;
    }

    // failover complete message
    check_request = complete_msg->request;
    //    printf("Complete msg: auth=%" PRIu64 "\n",check_request->authenticator);  // required field

    if (check_request->authenticator != check_msg.authenticator) {
        fprintf(stderr, "error in complete message authenticator");
        return false;
    }

    bool failover_ret;
    if (complete_msg->success) {
        printf("failover success\n");
        failover_ret = true;
    } else {
        printf("failover failed\n");
        failover_ret = false;
    }
    fflush(stdout);

    // free complete message
    messages__failover_complete__free_unpacked(complete_msg, NULL);

    close(sockfd);

    return failover_ret;
}

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <arpa/inet.h>

#include "err.h"
#include "common.h"

#define BUFFER_SIZE 700000

char shared_buffer[BUFFER_SIZE];

int main() {

    char *host = "127.0.0.1";
    uint16_t port = 19761;
    int packets = atoi(argv[3]);
    size_t size = atoi(argv[4]);
    struct sockaddr_in server_address = get_address(host, port);

    int socket_fd = open_socket();

    connect_socket(socket_fd, &server_address);

    char *server_ip = get_ip(&server_address);
    uint16_t server_port = get_port(&server_address);

    char *s = malloc(size * sizeof(char));
    memset(s, 'a', size);

    for (int i = 0; i < packets; i++) {
        // size_t message_length = strnlen(argv[i], BUFFER_SIZE);
        int flags = 0;
        send_message(socket_fd, s, size, flags);
        printf("Sent %zd bytes to %s:%u\n", size, server_ip, server_port);
    }

    // // Notify server that we're done sending messages
    // CHECK_ERRNO(shutdown(socket_fd, SHUT_WR));

    // size_t received_length;
    // do {
    //     memset(shared_buffer, 0, BUFFER_SIZE); // clean the buffer
    //     size_t max_length = BUFFER_SIZE - 1; // leave space for the null terminator
    //     int flags = 0;
    //     received_length = receive_message(socket_fd, shared_buffer, max_length, flags);
    //     printf("Received %zd bytes from %s:%u: '%s'\n", received_length, server_ip, server_port, shared_buffer);
    // } while (received_length > 0);

    CHECK_ERRNO(close(socket_fd));

    return 0;
}

// 49900 - 49999 takie porty dostępne
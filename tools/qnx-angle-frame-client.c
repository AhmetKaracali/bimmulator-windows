/* Bounded QNX TCP client for the host ANGLE frame RPC smoke path. */
typedef unsigned char U8;
typedef unsigned short U16;
typedef unsigned int U32;
typedef unsigned int Size;

#include "angle-frame-rpc.h"

extern int socket(int, int, int);
extern int connect(int, const void *, unsigned int);
extern int read(int, void *, Size);
extern int write(int, const void *, Size);
extern int close(int);
extern int puts(const char *);
extern void _exit(int);

struct QnxSockaddrIn {
    U8 length;
    U8 family;
    U16 port;
    U32 address;
    U8 zero[8];
};

static U8 frame[64u * 64u * 4u];

static int read_exact(int fd, U8 *buffer, Size length)
{
    Size offset = 0;
    while (offset < length) {
        int count = read(fd, buffer + offset, length - offset);
        if (count <= 0) return -1;
        offset += (Size)count;
    }
    return 0;
}

static int write_exact(int fd, const U8 *buffer, Size length)
{
    Size offset = 0;
    while (offset < length) {
        int count = write(fd, buffer + offset, length - offset);
        if (count <= 0) return -1;
        offset += (Size)count;
    }
    return 0;
}

void _start(void)
{
    const U8 color[4] = { 51, 153, 230, 255 };
    U8 request[IDRIVE_ANGLE_RPC_REQUEST_SIZE] = { 0 };
    U8 response[IDRIVE_ANGLE_RPC_RESPONSE_SIZE] = { 0 };
    struct QnxSockaddrIn peer;
    int fd;

    request[0] = 'I'; request[1] = 'D'; request[2] = '6'; request[3] = 'R';
    idrive_rpc_put_u16(request + 4, 1);
    idrive_rpc_put_u16(request + 6, 1);
    idrive_rpc_put_u32(request + 8, 64);
    idrive_rpc_put_u32(request + 12, 64);
    request[16] = color[0]; request[17] = color[1];
    request[18] = color[2]; request[19] = color[3];

    peer.length = sizeof(peer);
    peer.family = 2; /* AF_INET */
    peer.port = (U16)(((IDRIVE_ANGLE_RPC_PORT & 0xffu) << 8) |
                      (IDRIVE_ANGLE_RPC_PORT >> 8));
    peer.address = 0xfdc730a0u; /* 160.48.199.253 in QNX little-endian memory */
    for (unsigned int i = 0; i < sizeof(peer.zero); ++i) peer.zero[i] = 0;

    fd = socket(2, 1, 0); /* AF_INET, SOCK_STREAM */
    if (fd < 0) {
        puts("ID6RPC_FAIL stage=socket");
        _exit(1);
    }
    if (connect(fd, &peer, sizeof(peer)) != 0) {
        puts("ID6RPC_FAIL stage=connect host=160.48.199.253 port=41416");
        close(fd);
        _exit(2);
    }
    if (write_exact(fd, request, sizeof(request)) != 0) {
        puts("ID6RPC_FAIL stage=write-request");
        close(fd);
        _exit(3);
    }
    if (read_exact(fd, response, sizeof(response)) != 0) {
        puts("ID6RPC_FAIL stage=read-response-header");
        close(fd);
        _exit(4);
    }
    if (response[0] != 'I' || response[1] != 'D' ||
        response[2] != '6' || response[3] != 'A' ||
        idrive_rpc_get_u16(response + 4) != 1 ||
        idrive_rpc_get_u16(response + 6) != 0 ||
        idrive_rpc_get_u32(response + 8) != 64 ||
        idrive_rpc_get_u32(response + 12) != 64 ||
        idrive_rpc_get_u32(response + 16) != sizeof(frame)) {
        puts("ID6RPC_FAIL stage=invalid-response");
        close(fd);
        _exit(5);
    }
    if (read_exact(fd, frame, sizeof(frame)) != 0) {
        puts("ID6RPC_FAIL stage=read-frame");
        close(fd);
        _exit(6);
    }
    close(fd);

    for (Size offset = 0; offset < sizeof(frame); offset += 4) {
        for (Size channel = 0; channel < 4; ++channel) {
            int delta = (int)frame[offset + channel] - (int)color[channel];
            if (delta < -2 || delta > 2) {
                puts("ID6RPC_FAIL stage=pixel-color");
                _exit(7);
            }
        }
    }
    puts("ID6RPC_OK backend=host-angle depth=24 width=64 height=64 payload_bytes=16384 wire_bytes=16428 rgba=51,153,229,255");
    _exit(0);
}

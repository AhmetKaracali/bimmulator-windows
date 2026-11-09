/* WSL2 port: tiny QNX HTTP/1.0 client. The guest has no wget/curl, so this helper downloads
 * http://160.48.199.253:41600/overlay.tar (the host, through QEMU user networking) to
 * /dev/shmem/wsl-overlay.tar before HmiMain3D starts. Exit status: 0 = saved, 1 = no
 * connection, 2 = HTTP status other than 200, 3 = local file error.
 * Freestanding build like the other helpers: the guest supplies libc.so.3 and libsocket.so.3.
 */
extern int socket(int, int, int);
extern int connect(int, const void *, unsigned);
extern int open(const char *, int, ...);
extern int read(int, void *, unsigned);
extern int write(int, const void *, unsigned);
extern int close(int);
extern int puts(const char *);
extern void _exit(int);

#define AF_INET 2
#define SOCK_STREAM 1
#define O_WRONLY 0x0001
#define O_CREAT 0x0100
#define O_TRUNC 0x0200

struct qnx_sockaddr_in {          /* BSD layout used by QNX io-pkt */
    unsigned char sin_len;
    unsigned char sin_family;
    unsigned short sin_port;      /* network byte order */
    unsigned int sin_addr;        /* network byte order */
    char sin_zero[8];
};

static const char request[] =
    "GET /overlay.tar HTTP/1.0\r\nHost: 160.48.199.253\r\nConnection: close\r\n\r\n";
static char buffer[16384];

static int write_all(int fd, const char *data, int length)
{
    while (length > 0) {
        int written = write(fd, data, (unsigned)length);
        if (written <= 0) return -1;
        data += written;
        length -= written;
    }
    return 0;
}

void _start(void)
{
    struct qnx_sockaddr_in address = {
        sizeof(struct qnx_sockaddr_in), AF_INET,
        (unsigned short)((41600 >> 8) | ((41600 & 0xff) << 8)),
        /* 160.48.199.253 in network byte order on a little-endian CPU */
        (unsigned int)(160u | (48u << 8) | (199u << 16) | (253u << 24)),
        {0}
    };
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0 || connect(sock, &address, sizeof(address)) < 0) {
        puts("wsl-fetch: host not reachable");
        _exit(1);
    }
    if (write_all(sock, request, (int)sizeof(request) - 1) < 0) {
        puts("wsl-fetch: request failed");
        _exit(1);
    }

    /* Read until the end of the HTTP headers, check the status line, keep the body start. */
    int have = 0, body = -1;
    while (body < 0 && have < (int)sizeof(buffer)) {
        int got = read(sock, buffer + have, (unsigned)(sizeof(buffer) - (unsigned)have));
        if (got <= 0) break;
        have += got;
        for (int i = 3; i < have; i++) {
            if (buffer[i - 3] == '\r' && buffer[i - 2] == '\n' && buffer[i - 1] == '\r' && buffer[i] == '\n') {
                body = i + 1;
                break;
            }
        }
    }
    if (body < 0 || have < 12 || buffer[9] != '2' || buffer[10] != '0' || buffer[11] != '0') {
        puts("wsl-fetch: no overlay served");
        close(sock);
        _exit(2);
    }

    int out = open("/dev/shmem/wsl-overlay.tar", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (out < 0 || write_all(out, buffer + body, have - body) < 0) {
        puts("wsl-fetch: cannot write /dev/shmem/wsl-overlay.tar");
        _exit(3);
    }
    for (;;) {
        int got = read(sock, buffer, sizeof(buffer));
        if (got <= 0) break;
        if (write_all(out, buffer, got) < 0) {
            puts("wsl-fetch: write failed");
            _exit(3);
        }
    }
    close(out);
    close(sock);
    puts("wsl-fetch: overlay saved");
    _exit(0);
}

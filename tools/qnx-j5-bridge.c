/* WSL2 port: stand-in for the Jacinto's MOSTSubSystemServer.DSYSMOSTServer (DSI 4.5).
 *
 * The OMAP's MOST client (`most --devmode=client --serverRoleName=MOSTSubSystemServer`) needs
 * the DSYSMOSTServer that normally runs on the HU's Jacinto. This guest helper registers that
 * interface with the local servicebroker through BMW's own DSI C library
 * (libsys_dsi_base.cpp-ne.so.4) and forwards everything over TCP to a host program
 * (vendor/iocsim/j5_server.py) that implements the server logic:
 *
 *   frame  = u32 length-of-rest, u32 kind, u32 id, u32 arg, payload
 *   guest -> host: 1 HELLO, 2 REQUEST(id=request id, arg=DSI request type, raw payload),
 *                  3 END_OF_REPLY_WAIT (diagnostic), 4 NOTIFY_FILL(id)
 *   host -> guest: 10 RESPONSE(id, arg=response type e.g. 0x200, raw payload)
 *                  11 ATTRIBUTE(id, raw payload) -> cached + DSIServerSendNotification
 *                  12 END (host finished replying to the current request)
 *
 * Payload bytes are passed through unchanged; the DSI stream starts writing at offset 0x10, so
 * natural alignment inside the payload matches the original encoder.
 * Freestanding build like qnx-wsl-fetch.c; the guest supplies the real libraries.
 */
extern int socket(int, int, int);
extern int connect(int, const void *, unsigned);
extern int read(int, void *, unsigned);
extern int write(int, const void *, unsigned);
extern int close(int);
extern int puts(const char *);
extern int usleep(unsigned);
extern void *memcpy(void *, const void *, unsigned);
extern void *memset(void *, int, unsigned);
extern void _exit(int);
extern int poll(void *, unsigned, int);
extern int pthread_create(int *, const void *, void *(*)(void *), void *);
extern int pthread_mutex_init(void *, const void *);
extern int pthread_mutex_lock(void *);
extern int pthread_mutex_unlock(void *);

extern int DSIInit(void);
extern int DSIServerInit(void *, const char *, const char *, int, int);
extern int DSIServerRun(void *);
extern int DSIOpen(void *);
extern int DSIClose(void *);
extern int DSIWrite(void *, const void *, int, int);
extern int DSIServerSendResponse(void *, int, int, void *);
extern int DSIServerSendNotification(void *, int);

#define AF_INET 2
#define SOCK_STREAM 1
#define POLLIN 0x0001
#define PORT 5600
#define MAX_PAYLOAD 65536
#define MAX_ATTRS 16

struct qnx_sockaddr_in {
    unsigned char sin_len, sin_family;
    unsigned short sin_port;
    unsigned int sin_addr;
    char sin_zero[8];
};
struct pollfd_q { int fd; short events, revents; };

static unsigned int server[0x200 / 4];        /* DSI server struct (0x108 used by BMW stubs) */
static unsigned int mutex[8];
static int sock = -1;
static unsigned char rx[MAX_PAYLOAD + 16];
static unsigned char tx[MAX_PAYLOAD + 16];
static unsigned char attr_data[MAX_ATTRS][1024];
static int attr_len[MAX_ATTRS];

static void say(const char *text) { puts(text); }

static int write_all(const void *data, int length)
{
    const unsigned char *p = data;
    while (length > 0) {
        int n = write(sock, p, (unsigned)length);
        if (n <= 0) return -1;
        p += n; length -= n;
    }
    return 0;
}

static int read_all(void *data, int length)
{
    unsigned char *p = data;
    while (length > 0) {
        int n = read(sock, p, (unsigned)length);
        if (n <= 0) return -1;
        p += n; length -= n;
    }
    return 0;
}

static int send_frame(unsigned kind, unsigned id, unsigned arg, const void *payload, int length)
{
    unsigned head[4] = { 12u + (unsigned)length, kind, id, arg };
    if (write_all(head, 16) < 0) return -1;
    return length ? write_all(payload, length) : 0;
}

/* Reads one host frame into rx; returns kind or -1. */
static int read_frame(unsigned *id, unsigned *arg, int *length)
{
    unsigned head[4];
    if (read_all(head, 16) < 0) return -1;
    int size = (int)head[0] - 12;
    if (size < 0 || size > MAX_PAYLOAD) return -1;
    if (size && read_all(rx, size) < 0) return -1;
    *id = head[2]; *arg = head[3]; *length = size;
    return (int)head[1];
}

static void handle_host_frame(int kind, unsigned id, unsigned arg, int length)
{
    if (kind == 10) {
        unsigned int stream[0x80 / 4];
        memset(stream, 0, sizeof(stream));
        DSIOpen(stream);
        if (length) DSIWrite(stream, rx, length, 1);
        DSIServerSendResponse(server, arg ? (int)arg : 0x200, (int)id, stream);
        DSIClose(stream);
    } else if (kind == 11) {
        unsigned slot = id & 0xff;
        if (slot < MAX_ATTRS && length <= (int)sizeof(attr_data[0])) {
            memcpy(attr_data[slot], rx, (unsigned)length);
            attr_len[slot] = length;
            DSIServerSendNotification(server, (int)id);
        }
    }
}

/* DSI notification-data callback: write the cached attribute value. */
static int on_fill(void *srv, void *stream, unsigned id)
{
    (void)srv;
    unsigned slot = id & 0xff;
    if ((id & 0xff000000u) != 0xc0000000u || slot >= MAX_ATTRS) return 0;
    if (attr_len[slot]) DSIWrite(stream, attr_data[slot], attr_len[slot], 1);
    return 1;
}

/* DSI request callback: forward the raw request, then apply the host's replies while the
 * requesting client's session is still active. */
static void on_request(void *srv, unsigned int *stream, unsigned id)
{
    (void)srv;
    int size = (int)stream[0], pos = (int)stream[3];
    const unsigned char *data = (const unsigned char *)stream[4];
    int length = (data && size > pos) ? size - pos : 0;
    pthread_mutex_lock(mutex);
    if (sock >= 0 && send_frame(2, id, server[0xc8 / 4], data + pos, length) == 0) {
        for (;;) {
            unsigned rid, rarg; int rlen;
            int kind = read_frame(&rid, &rarg, &rlen);
            if (kind < 0) { say("j5-bridge: host link lost"); _exit(3); }
            if (kind == 12) break;
            handle_host_frame(kind, rid, rarg, rlen);
        }
    }
    pthread_mutex_unlock(mutex);
}

static void *host_reader(void *unused)
{
    (void)unused;
    for (;;) {
        struct pollfd_q p = { sock, POLLIN, 0 };
        pthread_mutex_lock(mutex);
        if (poll(&p, 1, 20) > 0 && (p.revents & POLLIN)) {
            unsigned id, arg; int length;
            int kind = read_frame(&id, &arg, &length);
            if (kind < 0) { say("j5-bridge: host link lost"); _exit(3); }
            handle_host_frame(kind, id, arg, length);
        }
        pthread_mutex_unlock(mutex);
        usleep(2000);
    }
    return 0;
}

void _start(void)
{
    struct qnx_sockaddr_in address = {
        sizeof(struct qnx_sockaddr_in), AF_INET,
        (unsigned short)((PORT >> 8) | ((PORT & 0xff) << 8)),
        (unsigned int)(160u | (48u << 8) | (199u << 16) | (253u << 24)), {0}
    };
    for (int attempt = 0; ; attempt++) {
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock >= 0 && connect(sock, &address, sizeof(address)) == 0) break;
        if (sock >= 0) close(sock);
        sock = -1;
        if (attempt == 0) say("j5-bridge: waiting for host j5_server on 160.48.199.253:5600");
        usleep(1000000);
    }
    say("j5-bridge: connected to host");
    pthread_mutex_init(mutex, 0);
    send_frame(1, 0x00040005u, 0, "MOSTSubSystemServer.DSYSMOSTServer", 34);

    DSIInit();
    memset(server, 0, sizeof(server));
    DSIServerInit(server, "DSYSMOSTServer", "MOSTSubSystemServer", 4, 5);
    server[0xd4 / 4] = (unsigned int)on_fill;
    server[0xd8 / 4] = (unsigned int)on_request;

    int thread;
    pthread_create(&thread, 0, host_reader, 0);
    say("j5-bridge: DSYSMOSTServer 4.5 registering as MOSTSubSystemServer");
    DSIServerRun(server);
    say("j5-bridge: DSIServerRun returned");
    _exit(1);
}

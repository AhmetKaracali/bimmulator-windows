/* Link-only symbols for qnx-j5-bridge (compiled once per soname). The guest's real libc.so.3,
 * libsocket.so.3 and libsys_dsi_base.cpp-ne.so.4 are used at runtime. */
#if defined(J5_LIBSOCKET)
int socket(int d, int t, int p) { return -1; }
int connect(int f, const void *a, unsigned l) { return -1; }
#elif defined(J5_LIBDSI)
int DSIInit(void) { return 0; }
int DSIServerInit(void *s, const char *i, const char *r, int a, int b) { return 0; }
int DSIServerRun(void *s) { return 0; }
int DSIOpen(void *s) { return 0; }
int DSIClose(void *s) { return 0; }
int DSIWrite(void *s, const void *d, int l, int a) { return 0; }
int DSIServerSendResponse(void *s, int t, int i, void *st) { return 0; }
int DSIServerSendNotification(void *s, int i) { return 0; }
#else
int read(int f, void *d, unsigned s) { return -1; }
int write(int f, const void *d, unsigned s) { return -1; }
int close(int f) { return 0; }
int puts(const char *t) { return 0; }
int usleep(unsigned u) { return 0; }
void *memcpy(void *d, const void *s, unsigned n) { return d; }
void *memset(void *d, int c, unsigned n) { return d; }
void _exit(int s) { for (;;) {} }
int poll(void *f, unsigned n, int t) { return 0; }
int pthread_create(int *t, const void *a, void *(*f)(void *), void *g) { return 0; }
int pthread_mutex_init(void *m, const void *a) { return 0; }
int pthread_mutex_lock(void *m) { return 0; }
int pthread_mutex_unlock(void *m) { return 0; }
#endif

/* Link-only symbols for qnx-wsl-fetch. The guest loads the real libraries at runtime;
 * this file is compiled twice, once per soname (libc.so.3 and libsocket.so.3). */
#ifdef WSL_FETCH_LIBSOCKET
int socket(int domain, int type, int protocol) { return -1; }
int connect(int fd, const void *address, unsigned length) { return -1; }
#else
int open(const char *path, int flags, ...) { return -1; }
int read(int fd, void *data, unsigned size) { return -1; }
int write(int fd, const void *data, unsigned size) { return -1; }
int close(int fd) { return 0; }
int puts(const char *text) { return 0; }
void _exit(int status) { for (;;) {} }
#endif

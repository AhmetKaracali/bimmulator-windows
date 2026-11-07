/* Link-only symbols. The guest loads its actual libc.so.3 at runtime. */
int open(const char *path, int flags, ...) { return 0; }
int close(int fd) { return 0; }
int devctl(int fd, int command, void *data, unsigned size, int *info) { return 0; }
int puts(const char *text) { return 0; }
void _exit(int status) { for (;;) {} }

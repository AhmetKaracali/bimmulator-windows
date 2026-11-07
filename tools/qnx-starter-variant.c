/* Local emulator probe for NBTevo starter's 32-bit development variant. */
extern int open(const char *, int, ...);
extern int close(int);
extern int devctl(int, int, void *, unsigned, int *);
extern int puts(const char *);
extern void _exit(int);
#ifndef IDRIVE_VARIANT_MASK
#error IDRIVE_VARIANT_MASK must be supplied by the build script
#endif

void _start(void)
{
    unsigned int variant = IDRIVE_VARIANT_MASK;
    int fd = open("/dev/starter/variant", 2); /* O_RDWR */
    if (fd < 0) {
        puts("starter variant: open failed");
        _exit(1);
    }
    /* Observed in this firmware's starter handler; four-byte input. */
    int result = devctl(fd, 0x80040503, &variant, sizeof(variant), 0);
    close(fd);
    if (result) {
        puts("starter variant: devctl failed");
        _exit(2);
    }
    puts("starter development variant accepted");
    _exit(0);
}

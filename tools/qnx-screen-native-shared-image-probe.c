/*
 * Bounded probe for the producer-side QNX Screen/shared-memory contract
 * recovered from libcommunication_graphics.cpp-ne.so.
 *
 * It exercises shm_open/shm_ctl/mmap/mlock/mem_offset64, Screen buffer
 * physical properties, pixmap attachment and screen_read_window. It does not
 * call EGL, pretend that the receiver succeeded, or represent a BMW HMI frame.
 */
typedef unsigned int uint32_t;
typedef unsigned long long uint64_t;
typedef long long int64_t;

extern int screen_create_context(void **, int);
extern int screen_create_window(void **, void *);
extern int screen_set_window_property_iv(void *, int, const int *);
extern int screen_create_window_buffers(void *, int);
extern int screen_get_window_property_iv(void *, int, int *);
extern int screen_get_window_property_pv(void *, int, void **);
extern int screen_get_buffer_property_iv(void *, int, int *);
extern int screen_get_buffer_property_pv(void *, int, void **);
extern int screen_get_buffer_property_llv(void *, int, int64_t *);
extern int screen_post_window(void *, void *, int, const int *, int);
extern int screen_read_window(void *, void *, int, const int *, int);
extern int screen_create_buffer(void **);
extern int screen_set_buffer_property_iv(void *, int, const int *);
extern int screen_set_buffer_property_pv(void *, int, void **);
extern int screen_set_buffer_property_llv(void *, int, const int64_t *);
extern int screen_create_pixmap(void **, void *);
extern int screen_set_pixmap_property_iv(void *, int, const int *);
extern int screen_attach_pixmap_buffer(void *, void *);
extern int getpid(void);
extern int shm_open(const char *, int, unsigned int);
extern int shm_unlink(const char *);
extern int shm_ctl(int, int, uint64_t, uint64_t);
extern int ftruncate(int, int64_t);
extern void *mmap(void *, unsigned int, int, int, int, int64_t);
extern int munmap(void *, unsigned int);
extern int mlock(const void *, unsigned int);
extern int munlock(const void *, unsigned int);
extern int close(int);
extern int mem_offset64(const void *, int, uint32_t, uint64_t *, uint32_t *);
extern int *__get_errno_ptr(void);
extern char *strerror(int);
extern void puts(const char *);
extern unsigned sleep(unsigned);
extern void _exit(int);

enum {
    SCREEN_PROPERTY_BUFFER_SIZE = 5,
    SCREEN_PROPERTY_FORMAT = 14,
    SCREEN_PROPERTY_PROTECTED = 36,
    SCREEN_PROPERTY_PHYSICALLY_CONTIGUOUS = 32,
    SCREEN_PROPERTY_POINTER = 34,
    SCREEN_PROPERTY_RENDER_BUFFERS = 37,
    SCREEN_PROPERTY_SIZE = 40,
    SCREEN_PROPERTY_STRIDE = 44,
    SCREEN_PROPERTY_USAGE = 48,
    SCREEN_PROPERTY_VISIBLE = 51,
    SCREEN_PROPERTY_PHYSICAL_ADDRESS = 55,
    SCREEN_PROPERTY_POSITION = 35,
    SCREEN_PROPERTY_ZORDER = 54,
    SCREEN_FORMAT_RGBA8888 = 8,
    SCREEN_USAGE_READ_WRITE = 6,
    /* Value observed in RemoteEGLImageSource::createImage. */
    SCREEN_USAGE_NATIVE_PIXMAP = 14,
    WIDTH = 1280,
    HEIGHT = 480,
    PIXEL_BYTES = WIDTH * HEIGHT * 4,
    SHM_OPEN_CREATE_EXCLUSIVE_RDWR = 0x502,
    SHM_MODE_0660 = 0x1b0,
    SHMCTL_ANON_PHYS = 0x3,
    PROT_READ_WRITE_NOCACHE = 0xb00,
    MAP_SHARED = 1,
};

static void append_text(char *out, unsigned int *length, const char *text)
{
    while (*text && *length < 190) out[(*length)++] = *text++;
}

static void append_unsigned(char *out, unsigned int *length, unsigned int value)
{
    char digits[16];
    unsigned int count = 0;
    do {
        digits[count++] = (char)('0' + value % 10);
        value /= 10;
    } while (value && count < sizeof(digits));
    while (count && *length < 190) out[(*length)++] = digits[--count];
}

static void append_hex64(char *out, unsigned int *length, uint64_t value)
{
    static const char hex[] = "0123456789abcdef";
    int started = 0;
    for (int shift = 60; shift >= 0 && *length < 190; shift -= 4) {
        unsigned int nibble = (unsigned int)((value >> shift) & 15U);
        if (nibble || started || shift == 0) {
            out[(*length)++] = hex[nibble];
            started = 1;
        }
    }
}

static void report_memory(const char *prefix, uint64_t physical,
                          uint32_t contiguous)
{
    char out[192];
    unsigned int length = 0;
    append_text(out, &length, prefix);
    append_text(out, &length, " pa=0x");
    append_hex64(out, &length, physical);
    append_text(out, &length, " bytes=");
    append_unsigned(out, &length, PIXEL_BYTES);
    append_text(out, &length, " contiguous_bytes=");
    append_unsigned(out, &length, contiguous);
    out[length] = '\0';
    puts(out);
}

static void report_read(unsigned int mismatches)
{
    char out[192];
    unsigned int length = 0;
    append_text(out, &length, "NATIVE_IMAGE_READ rc=0 mismatched_pixels=");
    append_unsigned(out, &length, mismatches);
    out[length] = '\0';
    puts(out);
}

static void fill_window(void *pixels, int stride)
{
    static const uint32_t colors[3] = { 0xff0000ffU, 0xff00ff00U, 0xffff0000U };
    for (int y = 0; y < HEIGHT; y++) {
        uint32_t *row = (uint32_t *)((char *)pixels + y * stride);
        for (int x = 0; x < WIDTH; x++) {
            unsigned int band = (unsigned int)(x * 3 / WIDTH);
            row[x] = colors[band];
        }
    }
}

static unsigned int count_mismatches(const void *pixels)
{
    static const uint32_t colors[3] = { 0xff0000ffU, 0xff00ff00U, 0xffff0000U };
    unsigned int mismatches = 0;
    for (int y = 0; y < HEIGHT; y++) {
        const uint32_t *row = (const uint32_t *)((const char *)pixels + y * WIDTH * 4);
        for (int x = 0; x < WIDTH; x++) {
            unsigned int band = (unsigned int)(x * 3 / WIDTH);
            if (row[x] != colors[band]) mismatches++;
        }
    }
    return mismatches;
}

static void fail(const char *message)
{
    puts(message);
    {
        int *error_slot = __get_errno_ptr();
        if (error_slot) {
            char out[96];
            unsigned int length = 0;
            append_text(out, &length, "NATIVE_IMAGE_ERRNO=");
            append_unsigned(out, &length, (unsigned int)*error_slot);
            out[length] = '\0';
            puts(out);
            if (*error_slot) puts(strerror(*error_slot));
        }
    }
    _exit(2);
}

void _start(void)
{
    void *context = 0, *window = 0, *source_buffer = 0, *source_pixels = 0;
    void *image_buffer = 0, *pixmap = 0, *image_pixels = 0;
    void *render_buffers[1] = { 0 };
    int dimensions[2] = { WIDTH, HEIGHT };
    /* createImage passes height * stride followed by the adjacent value 1. */
    int size_property[2] = { PIXEL_BYTES, 1 };
    int position[2] = { 0, 0 }, damage[4] = { 0, 0, WIDTH, HEIGHT };
    int format = SCREEN_FORMAT_RGBA8888, usage = SCREEN_USAGE_READ_WRITE;
    int visible = 1, zorder = 2000, source_stride = 0, actual_format = 0;
    int protected_content = 0, contiguous_property = 1, image_stride = WIDTH * 4;
    int pixmap_usage = SCREEN_USAGE_NATIVE_PIXMAP;
    uint64_t physical_address = 0, actual_physical_address = 0;
    uint32_t contiguous_length = 0;
    char shm_name[96];
    unsigned int name_length = 0;
    int descriptor;
    void *shared_pixels;

    puts("QNX Screen native shared-image probe: producer endpoint only");
    if (screen_create_context(&context, 0) || screen_create_window(&window, context))
        fail("NATIVE_IMAGE_FAIL context/window creation");
    if (screen_set_window_property_iv(window, SCREEN_PROPERTY_FORMAT, &format) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_USAGE, &usage) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_BUFFER_SIZE, dimensions) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_SIZE, dimensions) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_POSITION, position) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_ZORDER, &zorder) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_VISIBLE, &visible) ||
        screen_create_window_buffers(window, 1))
        fail("NATIVE_IMAGE_FAIL source window setup");
    if (screen_get_window_property_pv(window, SCREEN_PROPERTY_RENDER_BUFFERS,
                                      render_buffers))
        fail("NATIVE_IMAGE_FAIL render buffer query");
    source_buffer = render_buffers[0];
    if (!source_buffer ||
        screen_get_buffer_property_pv(source_buffer, SCREEN_PROPERTY_POINTER,
                                      &source_pixels) ||
        screen_get_buffer_property_iv(source_buffer, SCREEN_PROPERTY_STRIDE,
                                      &source_stride) ||
        !source_pixels || source_stride < WIDTH * 4)
        fail("NATIVE_IMAGE_FAIL source buffer pointer/stride");
    fill_window(source_pixels, source_stride);
    if (screen_post_window(window, source_buffer, 1, damage, 0))
        fail("NATIVE_IMAGE_FAIL source screen_post_window");

    append_text(shm_name, &name_length, "/dev/idrive6_native_image_");
    append_unsigned(shm_name, &name_length, (unsigned int)getpid());
    shm_name[name_length] = '\0';
    descriptor = shm_open(shm_name, SHM_OPEN_CREATE_EXCLUSIVE_RDWR, SHM_MODE_0660);
    if (descriptor < 0) fail("NATIVE_IMAGE_FAIL shm_open");
    /* SimpleSharedMem::open calls shm_ctl(fd, SHMCTL_ANON|SHMCTL_PHYS, 0, size)
     * before ftruncate/mmap, so QNX allocates the physically contiguous backing
     * that the later mem_offset64 query requires. */
    if (shm_ctl(descriptor, SHMCTL_ANON_PHYS, 0, PIXEL_BYTES))
        fail("NATIVE_IMAGE_FAIL shm_ctl(ANON|PHYS)");
    puts("NATIVE_IMAGE_SHM_CTL_OK flags=3; physically contiguous backing requested");
    if (ftruncate(descriptor, PIXEL_BYTES))
        puts("NATIVE_IMAGE_FTRUNCATE_NOTE native target ignores this return value");
    shared_pixels = mmap(0, PIXEL_BYTES, PROT_READ_WRITE_NOCACHE, MAP_SHARED, descriptor, 0);
    if ((long long)shared_pixels == -1) fail("NATIVE_IMAGE_FAIL mmap");
    if (mlock(shared_pixels, PIXEL_BYTES)) fail("NATIVE_IMAGE_FAIL mlock");
    if (screen_get_window_property_iv(window, SCREEN_PROPERTY_FORMAT, &actual_format))
        fail("NATIVE_IMAGE_FAIL window format query");
    /* Target createImage constructs the Screen buffer before mem_offset64. */
    if (screen_create_buffer(&image_buffer))
        fail("NATIVE_IMAGE_FAIL screen_create_buffer");
    *__get_errno_ptr() = 0;
    if (mem_offset64(shared_pixels, -1, PIXEL_BYTES, &physical_address,
                     &contiguous_length)) {
        int shared_error = *__get_errno_ptr();
        uint64_t source_physical_address = 0;
        uint32_t source_contiguous_length = 0;
        char out[96];
        unsigned int length = 0;
        append_text(out, &length, "NATIVE_IMAGE_SHARED_MEM_OFFSET_ERRNO=");
        append_unsigned(out, &length, (unsigned int)shared_error);
        out[length] = '\0';
        puts(out);
        if (shared_error) puts(strerror(shared_error));
        if (mem_offset64(source_pixels, -1, source_stride * HEIGHT,
                         &source_physical_address, &source_contiguous_length)) {
            int source_error = *__get_errno_ptr();
            length = 0;
            append_text(out, &length, "NATIVE_IMAGE_CONTROL_SCREEN_MEM_OFFSET_ERRNO=");
            append_unsigned(out, &length, (unsigned int)source_error);
            out[length] = '\0';
            puts(out);
            if (source_error) puts(strerror(source_error));
        } else {
            report_memory("NATIVE_IMAGE_CONTROL_SCREEN_MEM_OFFSET",
                          source_physical_address, source_contiguous_length);
        }
        *__get_errno_ptr() = shared_error;
        fail("NATIVE_IMAGE_FAIL mem_offset64 after native shm_ctl setup");
    }
    report_memory("NATIVE_IMAGE_MEM_OFFSET", physical_address, contiguous_length);
    if (contiguous_length < PIXEL_BYTES)
        puts("NATIVE_IMAGE_CONTIGUITY_NOTE target continues with the reported first physical offset");

    if (screen_set_buffer_property_iv(image_buffer, SCREEN_PROPERTY_PROTECTED,
                                      &protected_content))
        fail("NATIVE_IMAGE_FAIL screen_set_buffer_property_iv(PROTECTED)");
    if (screen_set_buffer_property_iv(image_buffer, SCREEN_PROPERTY_FORMAT,
                                      &actual_format))
        fail("NATIVE_IMAGE_FAIL screen_set_buffer_property_iv(FORMAT)");
    if (screen_set_buffer_property_iv(image_buffer, SCREEN_PROPERTY_BUFFER_SIZE,
                                      dimensions))
        fail("NATIVE_IMAGE_FAIL screen_set_buffer_property_iv(BUFFER_SIZE)");
    if (screen_set_buffer_property_iv(image_buffer, SCREEN_PROPERTY_SIZE,
                                      size_property))
        fail("NATIVE_IMAGE_FAIL screen_set_buffer_property_iv(SIZE)");
    if (screen_set_buffer_property_iv(image_buffer, SCREEN_PROPERTY_STRIDE,
                                      &image_stride))
        fail("NATIVE_IMAGE_FAIL screen_set_buffer_property_iv(STRIDE)");
    if (screen_set_buffer_property_pv(image_buffer, SCREEN_PROPERTY_POINTER,
                                      &shared_pixels))
        fail("NATIVE_IMAGE_FAIL screen_set_buffer_property_pv(POINTER)");
    if (screen_set_buffer_property_llv(image_buffer, SCREEN_PROPERTY_PHYSICAL_ADDRESS,
                                       (const int64_t *)&physical_address))
        fail("NATIVE_IMAGE_FAIL screen_set_buffer_property_llv(PHYSICAL_ADDRESS)");
    if (screen_set_buffer_property_iv(image_buffer, SCREEN_PROPERTY_PHYSICALLY_CONTIGUOUS,
                                      &contiguous_property))
        fail("NATIVE_IMAGE_FAIL screen_set_buffer_property_iv(PHYSICALLY_CONTIGUOUS)");
    if (screen_get_buffer_property_iv(image_buffer, SCREEN_PROPERTY_FORMAT,
                                      &format) ||
        screen_get_buffer_property_iv(image_buffer, SCREEN_PROPERTY_PHYSICALLY_CONTIGUOUS,
                                      &contiguous_property) ||
        screen_get_buffer_property_llv(image_buffer, SCREEN_PROPERTY_PHYSICAL_ADDRESS,
                                       (int64_t *)&actual_physical_address))
        fail("NATIVE_IMAGE_FAIL screen buffer property readback");
    if (format != actual_format || contiguous_property != 1 ||
        actual_physical_address != physical_address)
        fail("NATIVE_IMAGE_UNSUPPORTED Screen buffer properties did not retain requested values");
    if (screen_create_pixmap(&pixmap, context))
        fail("NATIVE_IMAGE_FAIL screen_create_pixmap");
    if (screen_set_pixmap_property_iv(pixmap, SCREEN_PROPERTY_FORMAT,
                                      &actual_format))
        fail("NATIVE_IMAGE_FAIL screen_set_pixmap_property_iv(FORMAT)");
    if (screen_set_pixmap_property_iv(pixmap, SCREEN_PROPERTY_BUFFER_SIZE,
                                      dimensions))
        fail("NATIVE_IMAGE_FAIL screen_set_pixmap_property_iv(BUFFER_SIZE)");
    if (screen_set_pixmap_property_iv(pixmap, SCREEN_PROPERTY_USAGE,
                                      &pixmap_usage))
        fail("NATIVE_IMAGE_FAIL screen_set_pixmap_property_iv(USAGE=14)");
    if (screen_attach_pixmap_buffer(pixmap, image_buffer))
        fail("NATIVE_IMAGE_FAIL screen_attach_pixmap_buffer");
    if (screen_get_buffer_property_pv(image_buffer, SCREEN_PROPERTY_POINTER,
                                      &image_pixels) || image_pixels != shared_pixels)
        fail("NATIVE_IMAGE_FAIL shared pointer readback");
    puts("NATIVE_IMAGE_READY; source window posted; reading the full window into shared image buffer");
    sleep(2);
    if (screen_read_window(window, image_buffer, 1, damage, 0))
        fail("NATIVE_IMAGE_FAIL screen_read_window");
    report_read(count_mismatches(shared_pixels));
    puts("NATIVE_IMAGE_PRODUCER_PATH_OK; no EGLImage receiver was called");
    puts("NATIVE_IMAGE_HOLD; diagnostic window remains visible for 30 guest seconds");
    sleep(30);

    munlock(shared_pixels, PIXEL_BYTES);
    munmap(shared_pixels, PIXEL_BYTES);
    close(descriptor);
    shm_unlink(shm_name);
    _exit(0);
}

/*
 * QNX Screen presentation probe backed by QEMU's file-shared guest RAM.
 *
 * The host fills two physically contiguous Screen buffers through QEMU's
 * shared RAM file. This client then posts those buffers through Screen. The
 * default build uses CPU-readable buffers; IDRIVE_SCREEN_HMI_GLES2_POST
 * selects an HMI-shaped GLES2 allocation. Neither uses EGL/GLES or represents
 * a BMW HMI frame.
 */
typedef long long int64_t;
typedef unsigned long long uint64_t;

extern int screen_create_context(void **, int);
extern int screen_create_window(void **, void *);
extern int screen_set_window_property_iv(void *, int, const int *);
extern int screen_set_window_property_cv(void *, int, int, const char *);
extern int screen_create_window_buffers(void *, int);
extern int screen_get_window_property_iv(void *, int, int *);
extern int screen_get_window_property_pv(void *, int, void **);
extern int screen_get_buffer_property_iv(void *, int, int *);
extern int screen_get_buffer_property_llv(void *, int, int64_t *);
extern int screen_post_window(void *, void *, int, const int *, int);
extern int screen_destroy_window_buffers(void *);
extern int screen_destroy_window(void *);
extern int screen_destroy_context(void *);
extern int puts(const char *);
extern unsigned sleep(unsigned);
extern void _exit(int);

enum {
    SCREEN_PROPERTY_BUFFER_SIZE = 5,
    SCREEN_PROPERTY_FORMAT = 14,
    SCREEN_PROPERTY_ID_STRING = 20,
    SCREEN_PROPERTY_PHYSICALLY_CONTIGUOUS = 32,
    SCREEN_PROPERTY_POSITION = 35,
    SCREEN_PROPERTY_RENDER_BUFFERS = 37,
    SCREEN_PROPERTY_SIZE = 40,
    SCREEN_PROPERTY_STRIDE = 44,
    SCREEN_PROPERTY_USAGE = 48,
    SCREEN_PROPERTY_VISIBLE = 51,
    SCREEN_PROPERTY_RENDER_BUFFER_COUNT = 53,
    SCREEN_PROPERTY_PHYSICAL_ADDRESS = 55,
    SCREEN_PROPERTY_ZORDER = 54,
    SCREEN_FORMAT_RGBA8888 = 8,
    SCREEN_USAGE_READ_WRITE = 6,
#if defined(IDRIVE_SCREEN_HMI_GLES2_POST)
    SCREEN_USAGE_OPENGL_ES2 = 1 << 5,
    WIDTH = 1440,
    HEIGHT = 540,
#else
    WIDTH = 1280,
    HEIGHT = 480,
#endif
    BUFFER_COUNT = 2,
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

static void report_buffer(unsigned int index, int64_t physical_address,
                          int stride, int width, int height, int format,
                          int contiguous)
{
    char out[192];
    unsigned int length = 0;
    append_text(out, &length, "SCREEN_RAM_BUFFER index=");
    append_unsigned(out, &length, index);
    append_text(out, &length, " pa=0x");
    append_hex64(out, &length, (uint64_t)physical_address);
    append_text(out, &length, " stride=");
    append_unsigned(out, &length, (unsigned int)stride);
    append_text(out, &length, " width=");
    append_unsigned(out, &length, (unsigned int)width);
    append_text(out, &length, " height=");
    append_unsigned(out, &length, (unsigned int)height);
    append_text(out, &length, " format=");
    append_unsigned(out, &length, (unsigned int)format);
    append_text(out, &length, " contiguous=");
    append_unsigned(out, &length, (unsigned int)contiguous);
    out[length] = '\0';
    puts(out);
}

static void fail(const char *message, void *window, void *context)
{
    puts(message);
    if (window) {
        screen_destroy_window_buffers(window);
        screen_destroy_window(window);
    }
    if (context) screen_destroy_context(context);
    _exit(2);
}

void _start(void)
{
    void *context = 0, *window = 0;
    void *buffers[BUFFER_COUNT] = { 0, 0 };
    int dimensions[2] = { WIDTH, HEIGHT };
    int position[2] = { 0, 0 };
    int damage[4] = { 0, 0, WIDTH, HEIGHT };
    int format = SCREEN_FORMAT_RGBA8888;
    int id_string_result = 0;
#if defined(IDRIVE_SCREEN_HMI_GLES2_POST)
    int usage = SCREEN_USAGE_OPENGL_ES2;
#else
    int usage = SCREEN_USAGE_READ_WRITE;
#endif
    int visible = 1, zorder = 2000, render_count = 0;

#if defined(IDRIVE_SCREEN_HMI_GLES2_POST)
    puts("QNX Screen HMI-style GLES2 shared-RAM post probe; diagnostic output, not BMW HMI");
#else
    puts("QNX Screen shared-RAM post probe: host-provided pixels, not BMW HMI output");
#endif
    if (screen_create_context(&context, 0) ||
        screen_create_window(&window, context)) {
        fail("SCREEN_RAM_SETUP_ERROR context/window creation failed", window, context);
    }
#if defined(IDRIVE_SCREEN_HMI_GLES2_POST)
    id_string_result = screen_set_window_property_cv(
        window, SCREEN_PROPERTY_ID_STRING, 5, "65535");
#endif
    if (id_string_result ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_FORMAT, &format) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_USAGE, &usage) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_BUFFER_SIZE, dimensions) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_SIZE, dimensions) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_POSITION, position) ||
#if !defined(IDRIVE_SCREEN_HMI_GLES2_POST)
        screen_set_window_property_iv(window, SCREEN_PROPERTY_ZORDER, &zorder) ||
#endif
        screen_set_window_property_iv(window, SCREEN_PROPERTY_VISIBLE, &visible) ||
        screen_create_window_buffers(window, BUFFER_COUNT)) {
        fail("SCREEN_RAM_SETUP_ERROR window properties/buffer allocation failed", window, context);
    }
    puts(
#if defined(IDRIVE_SCREEN_HMI_GLES2_POST)
        "SCREEN_RAM_LAYOUT mode=hmi-gles2 width=1440 height=540 usage=32 visible=1"
#else
        "SCREEN_RAM_LAYOUT mode=read-write width=1280 height=480 usage=6 visible=1"
#endif
    );
    if (screen_get_window_property_iv(window, SCREEN_PROPERTY_RENDER_BUFFER_COUNT,
                                      &render_count) ||
        render_count != BUFFER_COUNT ||
        screen_get_window_property_pv(window, SCREEN_PROPERTY_RENDER_BUFFERS,
                                      buffers)) {
        fail("SCREEN_RAM_SETUP_ERROR could not retrieve both render buffers", window, context);
    }

    for (unsigned int index = 0; index < BUFFER_COUNT; index++) {
        int size[2] = { 0, 0 }, stride = 0, actual_format = -1, contiguous = 0;
        int64_t physical_address = 0;
        void *buffer = buffers[index];
        if (!buffer ||
            screen_get_buffer_property_iv(buffer, SCREEN_PROPERTY_FORMAT,
                                          &actual_format) ||
            screen_get_buffer_property_iv(buffer, SCREEN_PROPERTY_BUFFER_SIZE,
                                          size) ||
            screen_get_buffer_property_iv(buffer, SCREEN_PROPERTY_STRIDE,
                                          &stride) ||
            screen_get_buffer_property_iv(buffer,
                                          SCREEN_PROPERTY_PHYSICALLY_CONTIGUOUS,
                                          &contiguous) ||
            screen_get_buffer_property_llv(buffer,
                                           SCREEN_PROPERTY_PHYSICAL_ADDRESS,
                                           &physical_address)) {
            fail("SCREEN_RAM_SETUP_ERROR buffer metadata query failed", window, context);
        }
        report_buffer(index, physical_address, stride, size[0], size[1],
                      actual_format, contiguous);
        if (actual_format != SCREEN_FORMAT_RGBA8888 || size[0] != WIDTH ||
            size[1] != HEIGHT || stride < WIDTH * 4 || contiguous != 1 ||
            physical_address <= 0) {
            fail("SCREEN_RAM_UNSUPPORTED buffer must be contiguous RGBA8888 with expected dimensions",
                 window, context);
        }
    }

    if (buffers[0] == buffers[1]) {
        fail("SCREEN_RAM_UNSUPPORTED Screen returned duplicate render-buffer handles",
             window, context);
    }

    puts("SCREEN_RAM_READY; host may fill both Screen buffers in shared QEMU RAM");
    sleep(12);

    for (unsigned int index = 0; index < BUFFER_COUNT; index++) {
        int result = screen_post_window(window, buffers[index], 1, damage, 0);
        if (result) {
            puts(index == 0 ? "SCREEN_RAM_POSTED frame=0 rc=-1" :
                              "SCREEN_RAM_POSTED frame=1 rc=-1");
            fail("SCREEN_RAM_POST_ERROR screen_post_window failed", window, context);
        }
        puts(index == 0 ? "SCREEN_RAM_POSTED frame=0 rc=0" :
                          "SCREEN_RAM_POSTED frame=1 rc=0");
        sleep(2);
    }

    puts("SCREEN_RAM_HOLD window remains visible; press Ctrl-C to stop QEMU");
    sleep(36000);
    _exit(0);
}

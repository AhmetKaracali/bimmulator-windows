/*
 * Screen-side probe for the HmiMain3D CWal3dNBTevo::createWindow path.
 *
 * This intentionally stops before eglCreateWindowSurface. It creates the
 * same kind of hidden GLES2 Screen window and reports the buffers that QNX
 * actually allocates; it does not render or claim to display HMI pixels.
 * Property values are from the QNX Screen 6.5 SP1 API used by this runtime.
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
extern int screen_get_buffer_property_pv(void *, int, void **);
extern int screen_get_buffer_property_llv(void *, int, int64_t *);
extern int screen_destroy_window_buffers(void *);
extern int screen_destroy_window(void *);
extern int screen_destroy_context(void *);
extern int puts(const char *);
extern unsigned sleep(unsigned);
extern void _exit(int);

enum {
    SCREEN_PROPERTY_BUFFER_COUNT = 4,
    SCREEN_PROPERTY_BUFFER_SIZE = 5,
    SCREEN_PROPERTY_FORMAT = 14,
    SCREEN_PROPERTY_PHYSICALLY_CONTIGUOUS = 32,
    SCREEN_PROPERTY_POINTER = 34,
    SCREEN_PROPERTY_POSITION = 35,
    SCREEN_PROPERTY_RENDER_BUFFERS = 37,
    SCREEN_PROPERTY_SIZE = 40,
    SCREEN_PROPERTY_STRIDE = 44,
    SCREEN_PROPERTY_USAGE = 48,
    SCREEN_PROPERTY_VISIBLE = 51,
    SCREEN_PROPERTY_RENDER_BUFFER_COUNT = 53,
    SCREEN_PROPERTY_PHYSICAL_ADDRESS = 55,
    SCREEN_PROPERTY_ID_STRING = 20,
    SCREEN_FORMAT_RGBA8888 = 8,
    SCREEN_USAGE_OPENGL_ES2 = 1 << 5,
    HMI_WIDTH = 1440,
    HMI_HEIGHT = 540,
    HMI_RENDER_BUFFER_COUNT = 2,
};

static void print_number(const char *label, int value)
{
    char out[80];
    char digits[16];
    int length = 0, count = 0;
    while (label[length] && length < 55) {
        out[length] = label[length];
        length++;
    }
    out[length++] = '=';
    if (value < 0) {
        out[length++] = '-';
        value = -value;
    }
    do {
        digits[count++] = (char)('0' + (value % 10));
        value /= 10;
    } while (value && count < (int)sizeof(digits));
    while (count) out[length++] = digits[--count];
    out[length] = '\0';
    puts(out);
}

static void print_hex64(const char *label, uint64_t value)
{
    static const char digits[] = "0123456789abcdef";
    char out[80];
    int length = 0;
    while (label[length] && length < 55) {
        out[length] = label[length];
        length++;
    }
    out[length++] = '=';
    out[length++] = '0';
    out[length++] = 'x';
    int started = 0;
    for (int shift = 60; shift >= 0; shift -= 4) {
        unsigned nibble = (unsigned)((value >> shift) & 0xf);
        if (nibble || started || shift == 0) {
            out[length++] = digits[nibble];
            started = 1;
        }
    }
    out[length] = '\0';
    puts(out);
}

static int set_iv(void *window, const char *label, int property,
                  const int *value)
{
    int result = screen_set_window_property_iv(window, property, value);
    print_number(label, result);
    return result;
}

static void report_buffer(int index, void *buffer)
{
    int value = -1;
    int size[2] = { -1, -1 };
    void *pointer = 0;
    int rc;

    print_number("buffer index", index);
    print_number("buffer handle present", buffer != 0);

    rc = screen_get_buffer_property_iv(buffer, SCREEN_PROPERTY_FORMAT, &value);
    print_number("buffer format query rc", rc);
    print_number("buffer format", value);

    value = -1;
    rc = screen_get_buffer_property_iv(buffer, SCREEN_PROPERTY_USAGE, &value);
    print_number("buffer usage query rc", rc);
    print_number("buffer usage", value);

    rc = screen_get_buffer_property_iv(buffer, SCREEN_PROPERTY_BUFFER_SIZE, size);
    print_number("buffer size query rc", rc);
    print_number("buffer width", size[0]);
    print_number("buffer height", size[1]);

    value = -1;
    rc = screen_get_buffer_property_iv(buffer, SCREEN_PROPERTY_STRIDE, &value);
    print_number("buffer stride query rc", rc);
    print_number("buffer stride bytes", value);

    value = -1;
    rc = screen_get_buffer_property_iv(
        buffer, SCREEN_PROPERTY_PHYSICALLY_CONTIGUOUS, &value);
    print_number("buffer contiguous query rc", rc);
    print_number("buffer physically contiguous", value);

    rc = screen_get_buffer_property_pv(buffer, SCREEN_PROPERTY_POINTER, &pointer);
    print_number("buffer pointer query rc", rc);
    print_number("buffer pointer present", pointer != 0);

    int64_t physical_address = 0;
    rc = screen_get_buffer_property_llv(
        buffer, SCREEN_PROPERTY_PHYSICAL_ADDRESS, &physical_address);
    print_number("buffer physical address query rc", rc);
    if (!rc) print_hex64("buffer physical address", (uint64_t)physical_address);

}

void _start(void)
{
    void *context = 0, *window = 0;
    void *buffers[HMI_RENDER_BUFFER_COUNT] = { 0, 0 };
    const char native_id_string[] = "65535"; /* 0xffff fallback from HMI ID map */
    int native_id_string_length = sizeof(native_id_string) - 1;
    int dimensions[2] = { HMI_WIDTH, HMI_HEIGHT };
    int position[2] = { 0, 0 };
    int format = SCREEN_FORMAT_RGBA8888;
    int usage = SCREEN_USAGE_OPENGL_ES2;
    int visible = 0;
    int render_count = -1;
    int buffer_count = -1;

    puts("HMI Screen contract probe: hidden GLES2 window; no EGL or drawing");
    print_number("requested width", HMI_WIDTH);
    print_number("requested height", HMI_HEIGHT);
    print_number("requested Screen buffers", HMI_RENDER_BUFFER_COUNT);

    int result = screen_create_context(&context, 0);
    print_number("screen_create_context rc", result);
    if (result) _exit(1);
    result = screen_create_window(&window, context);
    print_number("screen_create_window rc", result);
    if (result) {
        screen_destroy_context(context);
        _exit(2);
    }

    result = screen_set_window_property_cv(
        window, SCREEN_PROPERTY_ID_STRING, native_id_string_length,
        native_id_string);
    print_number("set decimal HMI ID string rc", result);
    if (result) goto failed;
    if (set_iv(window, "set RGBA8888 format rc", SCREEN_PROPERTY_FORMAT, &format))
        goto failed;
    if (set_iv(window, "set GLES2 usage rc", SCREEN_PROPERTY_USAGE, &usage))
        goto failed;
    if (set_iv(window, "set initially hidden rc", SCREEN_PROPERTY_VISIBLE, &visible))
        goto failed;
    if (set_iv(window, "set HMI buffer size rc", SCREEN_PROPERTY_BUFFER_SIZE, dimensions))
        goto failed;
    if (set_iv(window, "set HMI window size rc", SCREEN_PROPERTY_SIZE, dimensions))
        goto failed;
    if (set_iv(window, "set HMI window position rc", SCREEN_PROPERTY_POSITION, position))
        goto failed;

    result = screen_create_window_buffers(window, HMI_RENDER_BUFFER_COUNT);
    print_number("screen_create_window_buffers rc", result);
    if (result) goto failed;

    result = screen_get_window_property_iv(
        window, SCREEN_PROPERTY_RENDER_BUFFER_COUNT, &render_count);
    print_number("render buffer count query rc", result);
    print_number("render buffer count", render_count);
    result = screen_get_window_property_iv(
        window, SCREEN_PROPERTY_BUFFER_COUNT, &buffer_count);
    print_number("buffer count query rc", result);
    print_number("buffer count", buffer_count);
    if (result || render_count < 0 || render_count > HMI_RENDER_BUFFER_COUNT) {
        puts("Screen returned an unexpected render-buffer count; handles not queried");
        goto failed;
    }

    result = screen_get_window_property_pv(
        window, SCREEN_PROPERTY_RENDER_BUFFERS, buffers);
    print_number("render buffer handles query rc", result);
    if (result) goto failed;
    for (int i = 0; i < render_count; ++i) report_buffer(i, buffers[i]);

    puts("Holding the hidden Screen allocation for 15 seconds for host RAM inspection");
    sleep(15);

    puts("HMI Screen contract probe complete; this is not an HMI frame");
    screen_destroy_window_buffers(window);
    screen_destroy_window(window);
    screen_destroy_context(context);
    _exit(0);

failed:
    puts("HMI Screen contract probe stopped at the first failed Screen operation");
    if (window) {
        screen_destroy_window_buffers(window);
        screen_destroy_window(window);
    }
    if (context) screen_destroy_context(context);
    _exit(3);
}

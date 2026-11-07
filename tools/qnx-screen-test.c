/*
 * Minimal QNX 6.5 Screen diagnostic, built without a QNX SDK. The property
 * numbers and usage flags are from QNX's Screen 6.5 SP1 API documentation.
 * This tests software window presentation, not PowerVR/GC320 rendering.
 */
typedef unsigned int uint32_t;
extern int screen_create_context(void **, int);
extern int screen_create_window(void **, void *);
extern int screen_set_window_property_iv(void *, int, const int *);
extern int screen_create_window_buffers(void *, int);
extern int screen_get_window_property_pv(void *, int, void **);
extern int screen_get_buffer_property_pv(void *, int, void **);
extern int screen_get_buffer_property_iv(void *, int, int *);
extern int screen_post_window(void *, void *, int, const int *, int);
extern int puts(const char *);
extern unsigned sleep(unsigned);
extern void _exit(int);

enum {
    PROP_BUFFER_SIZE = 5,
    PROP_POINTER = 34,
    PROP_RENDER_BUFFERS = 37,
    PROP_SIZE = 40,
    PROP_STRIDE = 44,
    PROP_USAGE = 48,
    PROP_VISIBLE = 51,
    USAGE_READ_WRITE = 6,
    WIDTH = 1280,
    HEIGHT = 480,
};

void _start(void)
{
    void *context = 0, *window = 0, *buffer = 0, *pixels = 0;
    int size[2] = { WIDTH, HEIGHT }, damage[4] = { 0, 0, WIDTH, HEIGHT };
    int usage = USAGE_READ_WRITE, visible = 1, stride = 0;

    if (screen_create_context(&context, 0) || screen_create_window(&window, context)) {
        puts("Screen context or window creation failed");
        _exit(1);
    }
    if (screen_set_window_property_iv(window, PROP_USAGE, &usage) ||
        screen_set_window_property_iv(window, PROP_BUFFER_SIZE, size) ||
        screen_set_window_property_iv(window, PROP_SIZE, size) ||
        screen_set_window_property_iv(window, PROP_VISIBLE, &visible) ||
        screen_create_window_buffers(window, 1)) {
        puts("Screen window buffer setup failed");
        _exit(2);
    }
    if (screen_get_window_property_pv(window, PROP_RENDER_BUFFERS, &buffer) ||
        screen_get_buffer_property_pv(buffer, PROP_POINTER, &pixels) ||
        screen_get_buffer_property_iv(buffer, PROP_STRIDE, &stride) ||
        !pixels || stride < WIDTH * 4) {
        puts("Screen buffer mapping failed");
        _exit(3);
    }
    for (int y = 0; y < HEIGHT; y++) {
        uint32_t *row = (uint32_t *)((char *)pixels + y * stride);
        for (int x = 0; x < WIDTH; x++) {
            row[x] = x < 426 ? 0xff0000ff : (x < 853 ? 0xff00ff00 : 0xffff0000);
        }
    }
    if (screen_post_window(window, buffer, 1, damage, 0)) {
        puts("Screen window post failed");
        _exit(4);
    }
    puts("Posted blue, green, and red test bands. Interrupt to exit.");
    sleep(36000);
    _exit(0);
}

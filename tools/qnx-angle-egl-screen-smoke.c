/* Exercise a QNX Screen window surface through BMW's public EGL/GLES path. */
#ifndef IDRIVE_SCREEN_SMOKE_HOLD_SECONDS
#define IDRIVE_SCREEN_SMOKE_HOLD_SECONDS 30
#endif
typedef long long int64_t;
typedef unsigned long long uint64_t;
typedef int EGLint;
typedef unsigned int EGLBoolean;
typedef unsigned int EGLenum;
typedef void *EGLDisplay;
typedef void *EGLConfig;
typedef void *EGLSurface;
typedef void *EGLContext;

extern int screen_create_context(void **, int);
extern int screen_create_window(void **, void *);
extern int screen_set_window_property_iv(void *, int, const int *);
extern int screen_set_window_property_cv(void *, int, int, const char *);
extern int screen_create_window_buffers(void *, int);
extern int screen_get_window_property_iv(void *, int, int *);
extern int screen_get_window_property_pv(void *, int, void **);
extern int screen_get_buffer_property_iv(void *, int, int *);
extern int screen_get_buffer_property_llv(void *, int, int64_t *);
extern int screen_destroy_window_buffers(void *);
extern int screen_destroy_window(void *);
extern int screen_destroy_context(void *);
extern EGLDisplay eglGetDisplay(void *);
extern EGLBoolean eglInitialize(EGLDisplay, EGLint *, EGLint *);
extern EGLBoolean eglTerminate(EGLDisplay);
extern EGLBoolean eglChooseConfig(EGLDisplay, const EGLint *, EGLConfig *, EGLint, EGLint *);
extern EGLBoolean eglBindAPI(EGLenum);
extern EGLSurface eglCreateWindowSurface(EGLDisplay, EGLConfig, void *, const EGLint *);
extern EGLBoolean eglDestroySurface(EGLDisplay, EGLSurface);
extern EGLContext eglCreateContext(EGLDisplay, EGLConfig, EGLContext, const EGLint *);
extern EGLBoolean eglDestroyContext(EGLDisplay, EGLContext);
extern EGLBoolean eglMakeCurrent(EGLDisplay, EGLSurface, EGLSurface, EGLContext);
extern EGLBoolean eglQuerySurface(EGLDisplay, EGLSurface, EGLint, EGLint *);
extern EGLBoolean eglSwapBuffers(EGLDisplay, EGLSurface);
extern EGLint eglGetError(void);
extern void glViewport(int, int, int, int);
extern void glScissor(int, int, int, int);
extern void glEnable(unsigned int);
extern void glDisable(unsigned int);
extern void glClearColor(float, float, float, float);
extern void glClear(unsigned int);
extern unsigned int glGetError(void);
extern int puts(const char *);
extern int fflush(void *);
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
    SCREEN_USAGE_OPENGL_ES2 = 1 << 5,
    EGL_FALSE = 0,
    EGL_TRUE = 1,
    EGL_SURFACE_TYPE = 0x3033,
    EGL_WINDOW_BIT = 0x0004,
    EGL_OPENGL_ES2_BIT = 0x0004,
    EGL_RENDERABLE_TYPE = 0x3040,
    EGL_RED_SIZE = 0x3024,
    EGL_GREEN_SIZE = 0x3023,
    EGL_BLUE_SIZE = 0x3022,
    EGL_ALPHA_SIZE = 0x3021,
    EGL_DEPTH_SIZE = 0x3025,
    EGL_RENDER_BUFFER = 0x3086,
    EGL_BACK_BUFFER = 0x3084,
    EGL_CONTEXT_CLIENT_VERSION = 0x3098,
    EGL_WIDTH = 0x3057,
    EGL_HEIGHT = 0x3056,
    EGL_OPENGL_ES_API = 0x30a0,
    EGL_NONE = 0x3038,
    GL_SCISSOR_TEST = 0x0c11,
    GL_COLOR_BUFFER_BIT = 0x00004000,
    GL_NO_ERROR = 0
};

static const int width = 1440;
static const int height = 540;

static void print_number(const char *label, int value)
{
    char output[96];
    char digits[16];
    unsigned int length = 0, count = 0;
    while (label[length] && length < 64) {
        output[length] = label[length];
        ++length;
    }
    output[length++] = '=';
    if (value < 0) {
        output[length++] = '-';
        value = -value;
    }
    do {
        digits[count++] = (char)('0' + value % 10);
        value /= 10;
    } while (value && count < sizeof(digits));
    while (count) output[length++] = digits[--count];
    output[length] = '\0';
    puts(output);
}

static void print_hex64(const char *label, uint64_t value)
{
    static const char digits[] = "0123456789abcdef";
    char output[96];
    unsigned int length = 0;
    int started = 0;
    while (label[length] && length < 64) {
        output[length] = label[length];
        ++length;
    }
    output[length++] = '=';
    output[length++] = '0';
    output[length++] = 'x';
    for (int shift = 60; shift >= 0; shift -= 4) {
        const unsigned int nibble = (unsigned int)((value >> shift) & 15u);
        if (nibble || started || shift == 0) {
            output[length++] = digits[nibble];
            started = 1;
        }
    }
    output[length] = '\0';
    puts(output);
}

static void fail(const char *stage, void *window, void *screen_context,
                 EGLDisplay display, EGLSurface surface, EGLContext context)
{
    puts(stage);
    print_number("EGL error", eglGetError());
    if (display && context) (void)eglMakeCurrent(display, 0, 0, 0);
    if (display && context) (void)eglDestroyContext(display, context);
    if (display && surface) (void)eglDestroySurface(display, surface);
    if (display) (void)eglTerminate(display);
    if (window) (void)screen_destroy_window_buffers(window);
    if (window) (void)screen_destroy_window(window);
    if (screen_context) (void)screen_destroy_context(screen_context);
    fflush((void *)0);
    _exit(1);
}

static void draw_quadrants(unsigned int frame, int x, int y, int w, int h)
{
    static const float colors[2][4][4] = {
        {
            { 1.f, 0.f, 0.f, 1.f }, { 0.f, 1.f, 0.f, 1.f },
            { 0.f, 0.f, 1.f, 1.f }, { 1.f, 1.f, 1.f, 1.f }
        },
        {
            { 1.f, 1.f, 0.f, 1.f }, { 0.f, 1.f, 1.f, 1.f },
            { 1.f, 0.f, 1.f, 1.f }, { 0.f, 0.f, 0.f, 1.f }
        }
    };
    const int half_width = w / 2;
    const int half_height = h / 2;
    const int rectangles[4][4] = {
        { x, y + half_height, half_width, h - half_height },
        { x + half_width, y + half_height, w - half_width, h - half_height },
        { x, y, half_width, half_height },
        { x + half_width, y, w - half_width, half_height }
    };
    glEnable(GL_SCISSOR_TEST);
    for (unsigned int i = 0; i < 4; ++i) {
        glScissor(rectangles[i][0], rectangles[i][1],
                  rectangles[i][2], rectangles[i][3]);
        glClearColor(colors[frame][i][0], colors[frame][i][1],
                     colors[frame][i][2], colors[frame][i][3]);
        glClear(GL_COLOR_BUFFER_BIT);
        if (glGetError() != GL_NO_ERROR) {
            puts("ANGLE_SCREEN_SMOKE_FAIL quadrant draw GL error");
            fflush((void *)0);
            _exit(2);
        }
    }
    glDisable(GL_SCISSOR_TEST);
    if (glGetError() != GL_NO_ERROR) {
        puts("ANGLE_SCREEN_SMOKE_FAIL scissor disable GL error");
        fflush((void *)0);
        _exit(3);
    }
}

void _start(void)
{
    void *screen_context = 0, *window = 0;
    EGLDisplay display = (EGLDisplay)0;
    EGLSurface surface = (EGLSurface)0;
    EGLContext context = (EGLContext)0;
    EGLConfig config = (EGLConfig)0;
    EGLint major = 0, minor = 0, count = 0, actual_width = 0, actual_height = 0;
    int dimensions[2] = { width, height };
    int position[2] = { 0, 0 };
    int actual_position[2] = { -1, -1 }, actual_size[2] = { 0, 0 };
    int actual_format = -1, actual_usage = 0, actual_zorder = 0;
    int format = SCREEN_FORMAT_RGBA8888;
    int usage = SCREEN_USAGE_OPENGL_ES2;
    int visible = 1, actual_visible = 0;
    int buffer_count = 0;
    void *buffers[2] = { 0, 0 };

    puts("ANGLE_SCREEN_SMOKE_BEGIN: QNX Screen window via the ID6 EGL provider");
    if (screen_create_context(&screen_context, 0) ||
        screen_create_window(&window, screen_context))
        fail("ANGLE_SCREEN_SMOKE_FAIL Screen context/window", window,
             screen_context, display, surface, context);
    if (screen_set_window_property_iv(window, SCREEN_PROPERTY_FORMAT, &format) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_USAGE, &usage) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_VISIBLE, &visible) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_BUFFER_SIZE, dimensions) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_SIZE, dimensions) ||
        screen_set_window_property_iv(window, SCREEN_PROPERTY_POSITION, position) ||
        screen_set_window_property_cv(window, SCREEN_PROPERTY_ID_STRING,
                                      5, "65535") ||
        screen_create_window_buffers(window, 2) ||
        screen_get_window_property_iv(window, SCREEN_PROPERTY_RENDER_BUFFER_COUNT,
                                      &buffer_count) ||
        buffer_count != 2 ||
        screen_get_window_property_pv(window, SCREEN_PROPERTY_RENDER_BUFFERS,
                                      buffers))
        fail("ANGLE_SCREEN_SMOKE_FAIL Screen window properties/buffers", window,
             screen_context, display, surface, context);
    if (screen_get_window_property_iv(window, SCREEN_PROPERTY_SIZE, actual_size) ||
        screen_get_window_property_iv(window, SCREEN_PROPERTY_POSITION,
                                      actual_position) ||
        screen_get_window_property_iv(window, SCREEN_PROPERTY_VISIBLE,
                                      &actual_visible) ||
        screen_get_window_property_iv(window, SCREEN_PROPERTY_FORMAT,
                                      &actual_format) ||
        screen_get_window_property_iv(window, SCREEN_PROPERTY_USAGE,
                                      &actual_usage) ||
        screen_get_window_property_iv(window, SCREEN_PROPERTY_ZORDER,
                                      &actual_zorder) ||
        actual_size[0] != width || actual_size[1] != height ||
        actual_position[0] != 0 || actual_position[1] != 0 ||
        actual_visible != 1 || actual_format != format ||
        (actual_usage & usage) != usage || buffer_count != 2)
        fail("ANGLE_SCREEN_SMOKE_FAIL actual window properties", window,
             screen_context, display, surface, context);
    print_number("ANGLE_SCREEN_WINDOW_X", actual_position[0]);
    print_number("ANGLE_SCREEN_WINDOW_Y", actual_position[1]);
    print_number("ANGLE_SCREEN_WINDOW_VISIBLE", actual_visible);
    print_number("ANGLE_SCREEN_WINDOW_FORMAT", actual_format);
    print_number("ANGLE_SCREEN_WINDOW_USAGE", actual_usage);
    print_number("ANGLE_SCREEN_WINDOW_ZORDER", actual_zorder);
    print_number("ANGLE_SCREEN_WINDOW_BUFFER_COUNT", buffer_count);
    for (unsigned int i = 0; i < 2; ++i) {
        int size[2] = { 0, 0 }, stride = 0, buffer_format = -1, contiguous = 0;
        int64_t physical = 0;
        if (!buffers[i] ||
            screen_get_buffer_property_iv(buffers[i], SCREEN_PROPERTY_FORMAT,
                                          &buffer_format) ||
            screen_get_buffer_property_iv(buffers[i], SCREEN_PROPERTY_BUFFER_SIZE,
                                          size) ||
            screen_get_buffer_property_iv(buffers[i], SCREEN_PROPERTY_STRIDE,
                                          &stride) ||
            screen_get_buffer_property_iv(buffers[i],
                                          SCREEN_PROPERTY_PHYSICALLY_CONTIGUOUS,
                                          &contiguous) ||
            screen_get_buffer_property_llv(buffers[i],
                                           SCREEN_PROPERTY_PHYSICAL_ADDRESS,
                                           &physical) ||
            size[0] != width || size[1] != height ||
            buffer_format != SCREEN_FORMAT_RGBA8888 ||
            stride < width * 4 || contiguous != 1 || physical <= 0)
            fail("ANGLE_SCREEN_SMOKE_FAIL Screen buffer metadata", window,
                 screen_context, display, surface, context);
        print_hex64(i == 0 ? "ANGLE_SCREEN_BUFFER0_PHYSICAL" :
                             "ANGLE_SCREEN_BUFFER1_PHYSICAL",
                    (uint64_t)physical);
        print_number(i == 0 ? "ANGLE_SCREEN_BUFFER0_STRIDE" :
                              "ANGLE_SCREEN_BUFFER1_STRIDE", stride);
    }
    puts("ANGLE_SCREEN_STAGE screen-buffers-ready");
    fflush((void *)0);

    display = eglGetDisplay((void *)0);
    puts("ANGLE_SCREEN_STAGE egl-display-returned");
    fflush((void *)0);
    if (!display)
        fail("ANGLE_SCREEN_SMOKE_FAIL EGL display initialization", window,
             screen_context, display, surface, context);
    puts("ANGLE_SCREEN_STAGE egl-initialize-start");
    fflush((void *)0);
    if (!eglInitialize(display, &major, &minor) ||
        !eglBindAPI(EGL_OPENGL_ES_API))
        fail("ANGLE_SCREEN_SMOKE_FAIL EGL display initialization", window,
             screen_context, display, surface, context);
    puts("ANGLE_SCREEN_STAGE egl-initialize-ok");
    fflush((void *)0);
    const EGLint config_attributes[] = {
        EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8,
        EGL_DEPTH_SIZE, 24, EGL_NONE
    };
    if (!eglChooseConfig(display, config_attributes, &config, 1, &count) ||
        count != 1)
        fail("ANGLE_SCREEN_SMOKE_FAIL EGL window config", window,
             screen_context, display, surface, context);
    puts("ANGLE_SCREEN_STAGE egl-config-ok");
    fflush((void *)0);
    const EGLint surface_attributes[] = { EGL_RENDER_BUFFER, EGL_BACK_BUFFER, EGL_NONE };
    surface = eglCreateWindowSurface(display, config, window, surface_attributes);
    if (!surface)
        fail("ANGLE_SCREEN_SMOKE_FAIL eglCreateWindowSurface", window,
             screen_context, display, surface, context);
    puts("ANGLE_SCREEN_STAGE egl-window-surface-ok");
    fflush((void *)0);
    const EGLint context_attributes[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    context = eglCreateContext(display, config, (EGLContext)0, context_attributes);
    if (!context || !eglMakeCurrent(display, surface, surface, context))
        fail("ANGLE_SCREEN_SMOKE_FAIL context/make-current", window,
             screen_context, display, surface, context);
    if (!eglQuerySurface(display, surface, EGL_WIDTH, &actual_width) ||
        !eglQuerySurface(display, surface, EGL_HEIGHT, &actual_height) ||
        actual_width != width || actual_height != height)
        fail("ANGLE_SCREEN_SMOKE_FAIL window surface dimensions", window,
             screen_context, display, surface, context);
    print_number("ANGLE_SCREEN_WIDTH", actual_width);
    print_number("ANGLE_SCREEN_HEIGHT", actual_height);
    glViewport(0, 0, width, height);

    draw_quadrants(0, 0, 0, width, height);
    if (!eglSwapBuffers(display, surface))
        fail("ANGLE_SCREEN_SMOKE_FAIL first window swap", window,
             screen_context, display, surface, context);
    puts("ANGLE_SCREEN_FRAME_OK sequence=0 pattern=red-green-blue-white");
    sleep(5);

    draw_quadrants(1, 0, 0, width, height);
    if (!eglSwapBuffers(display, surface))
        fail("ANGLE_SCREEN_SMOKE_FAIL second window swap", window,
             screen_context, display, surface, context);
    puts("ANGLE_SCREEN_FRAME_OK sequence=1 pattern=yellow-cyan-magenta-black");
    puts("ANGLE_SCREEN_SMOKE_HOLD");
    sleep(IDRIVE_SCREEN_SMOKE_HOLD_SECONDS);

    if (!eglMakeCurrent(display, (EGLSurface)0, (EGLSurface)0, (EGLContext)0) ||
        !eglDestroySurface(display, surface) || !eglDestroyContext(display, context) ||
        !eglTerminate(display))
        fail("ANGLE_SCREEN_SMOKE_FAIL EGL teardown", window,
             screen_context, display, surface, context);
    (void)screen_destroy_window_buffers(window);
    (void)screen_destroy_window(window);
    (void)screen_destroy_context(screen_context);
    puts("ANGLE_SCREEN_BRIDGE_OK egl-window=screen buffers=2 frames=2 cleanup=ok");
    fflush((void *)0);
    _exit(0);
}

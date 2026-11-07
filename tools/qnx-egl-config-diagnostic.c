/* Query the real QNX EGL display/configuration list before launching HmiMain3D. */
typedef int EGLint;
typedef unsigned int EGLBoolean;
typedef void *EGLDisplay;
typedef void *EGLConfig;

extern EGLDisplay eglGetDisplay(void *);
extern EGLBoolean eglInitialize(EGLDisplay, EGLint *, EGLint *);
extern EGLBoolean eglGetConfigs(EGLDisplay, EGLConfig *, EGLint, EGLint *);
extern EGLBoolean eglGetConfigAttrib(EGLDisplay, EGLConfig, EGLint, EGLint *);
extern EGLBoolean eglChooseConfig(EGLDisplay, const EGLint *, EGLConfig *, EGLint, EGLint *);
extern const char *eglQueryString(EGLDisplay, EGLint);
extern EGLint eglGetError(void);
extern EGLBoolean eglTerminate(EGLDisplay);
extern int puts(const char *);
extern int fflush(void *);
extern void _exit(int);
extern int screen_create_context(void **, int);
extern int screen_create_window(void **, void *);
extern int screen_set_window_property_iv(void *, int, const int *);
extern int screen_create_window_buffers(void *, int);

enum {
    EGL_VENDOR = 0x3053,
    EGL_VERSION = 0x3054,
    EGL_EXTENSIONS = 0x3055,
    EGL_CONFIG_ID = 0x3028,
    EGL_RED_SIZE = 0x3024,
    EGL_GREEN_SIZE = 0x3023,
    EGL_BLUE_SIZE = 0x3022,
    EGL_ALPHA_SIZE = 0x3021,
    EGL_DEPTH_SIZE = 0x3025,
    EGL_STENCIL_SIZE = 0x3026,
    EGL_SURFACE_TYPE = 0x3033,
    EGL_RENDERABLE_TYPE = 0x3040,
    EGL_WINDOW_BIT = 0x0004,
    EGL_OPENGL_ES2_BIT = 0x0004,
    EGL_NONE = 0x3038,
};

static void finish(int status)
{
    /* _exit does not flush stdio when diagnostics are redirected to a file. */
    fflush((void *)0);
    _exit(status);
}

static void print_number(const char *label, int value)
{
    char out[64];
    char digits[16];
    int n = 0, i = 0;
    while (label[i] && i < 40) {
        out[i] = label[i];
        i++;
    }
    out[i++] = '=';
    if (value < 0) {
        out[i++] = '-';
        value = -value;
    }
    do {
        digits[n++] = (char)('0' + (value % 10));
        value /= 10;
    } while (value && n < (int)sizeof(digits));
    while (n) out[i++] = digits[--n];
    out[i] = '\0';
    puts(out);
}

static void print_nullable(const char *label, const char *value)
{
    puts(label);
    puts(value ? value : "(null)");
}

static void print_attrib(EGLDisplay display, EGLConfig config, const char *name, EGLint attr)
{
    EGLint value = -1;
    EGLBoolean result = eglGetConfigAttrib(display, config, attr, &value);
    if (!result) value = -(int)eglGetError();
    print_number(name, value);
}

void _start(void)
{
    EGLint major = 0, minor = 0, count = 0, chosen = 0;
    EGLConfig configs[32];
    EGLDisplay display;
    void *screen_context = 0, *screen_window = 0;
    const int usage = 1 << 5; /* SCREEN_USAGE_OPENGL_ES2 */
    const int dimensions[2] = {64, 64};
    const EGLint attributes[] = {
        EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8,
        EGL_NONE
    };

    puts("Native QNX EGL diagnostic: querying the display used by HmiMain3D");
    /* Exercise Screen's GPU allocation path as the native HMI does. Creating
     * only an EGL display can leave the vendor GPU service uninitialized. */
    int result = screen_create_context(&screen_context, 0);
    print_number("Screen create context", result);
    if (result) finish(6);
    result = screen_create_window(&screen_window, screen_context);
    print_number("Screen create window", result);
    if (result) finish(7);
    print_number("Screen GLES2 usage", screen_set_window_property_iv(screen_window, 48, &usage));
    print_number("Screen window size", screen_set_window_property_iv(screen_window, 40, dimensions));
    print_number("Screen buffer size", screen_set_window_property_iv(screen_window, 5, dimensions));
    fflush((void *)0);
    print_number("Screen GLES2 buffers", screen_create_window_buffers(screen_window, 2));
    fflush((void *)0);
    display = eglGetDisplay(0);
    if (!display) {
        puts("eglGetDisplay returned a null handle");
        print_number("eglGetDisplay error", eglGetError());
        finish(1);
    }
    if (!eglInitialize(display, &major, &minor)) {
        print_number("eglInitialize error", eglGetError());
        finish(2);
    }
    print_number("EGL major", major);
    print_number("EGL minor", minor);
    print_nullable("EGL vendor", eglQueryString(display, EGL_VENDOR));
    print_nullable("EGL version", eglQueryString(display, EGL_VERSION));
    print_nullable("EGL extensions", eglQueryString(display, EGL_EXTENSIONS));

    if (!eglGetConfigs(display, 0, 0, &count)) {
        print_number("eglGetConfigs error", eglGetError());
        finish(3);
    }
    print_number("EGL config count", count);
    if (count > (int)(sizeof(configs) / sizeof(configs[0]))) {
        count = sizeof(configs) / sizeof(configs[0]);
    }
    if (count && !eglGetConfigs(display, configs, count, &count)) {
        print_number("eglGetConfigs list error", eglGetError());
        finish(4);
    }
    for (int i = 0; i < count; ++i) {
        print_number("config index", i);
        print_attrib(display, configs[i], "id", EGL_CONFIG_ID);
        print_attrib(display, configs[i], "red", EGL_RED_SIZE);
        print_attrib(display, configs[i], "green", EGL_GREEN_SIZE);
        print_attrib(display, configs[i], "blue", EGL_BLUE_SIZE);
        print_attrib(display, configs[i], "alpha", EGL_ALPHA_SIZE);
        print_attrib(display, configs[i], "depth", EGL_DEPTH_SIZE);
        print_attrib(display, configs[i], "stencil", EGL_STENCIL_SIZE);
        print_attrib(display, configs[i], "surface", EGL_SURFACE_TYPE);
        print_attrib(display, configs[i], "renderable", EGL_RENDERABLE_TYPE);
    }
    if (!eglChooseConfig(display, attributes, configs, 32, &chosen)) {
        print_number("eglChooseConfig error", eglGetError());
        finish(5);
    }
    print_number("matching GLES2 window configs", chosen);
    eglTerminate(display);
    finish(0);
}

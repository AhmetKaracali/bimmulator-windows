/* Transparent QNX EGL provider instrumentation, selected by egl-dlls.
 * The 34-slot ABI and QueryString(NULL, 0x6000) handshake come from the staged
 * libEGL.so.1 (54ad4bb5...) rather than a guessed graphics-driver interface.
 * Vendor calls, output parameters and sticky EGL errors retain their behavior.
 */
typedef unsigned int U32;
typedef __UINTPTR_TYPE__ Word;
typedef void (*Proc)(void);
typedef void *Handle;
extern int write(int, const void *, unsigned int);
extern int getpid(void);
extern int *__get_errno_ptr(void);

#define CORE_PROCS(X) \
 X(eglGetError) X(eglGetDisplay) X(eglInitialize) X(eglTerminate) \
 X(eglQueryString) X(eglGetConfigs) X(eglChooseConfig) X(eglGetConfigAttrib) \
 X(eglCreateWindowSurface) X(eglCreatePbufferSurface) X(eglCreatePixmapSurface) \
 X(eglDestroySurface) X(eglQuerySurface) X(eglBindAPI) X(eglQueryAPI) \
 X(eglWaitClient) X(eglReleaseThread) X(eglCreatePbufferFromClientBuffer) \
 X(eglSurfaceAttrib) X(eglBindTexImage) X(eglReleaseTexImage) X(eglSwapInterval) \
 X(eglCreateContext) X(eglDestroyContext) X(eglMakeCurrent) \
 X(eglGetCurrentContext) X(eglGetCurrentSurface) X(eglGetCurrentDisplay) \
 X(eglQueryContext) X(eglWaitGL) X(eglWaitNative) X(eglSwapBuffers) \
 X(eglCopyBuffers) X(eglGetProcAddress)
extern U32 IMGeglGetError(void);
extern Handle IMGeglGetDisplay(Handle);
extern U32 IMGeglInitialize(Handle, int *, int *);
extern U32 IMGeglTerminate(Handle);
extern const char *IMGeglQueryString(Handle, int);
extern U32 IMGeglGetConfigs(Handle, Handle *, int, int *);
extern U32 IMGeglChooseConfig(Handle, const int *, Handle *, int, int *);
extern U32 IMGeglGetConfigAttrib(Handle, Handle, int, int *);
extern Handle IMGeglCreateWindowSurface(Handle, Handle, Handle, const int *);
extern Handle IMGeglCreatePbufferSurface(Handle, Handle, const int *);
extern Handle IMGeglCreatePixmapSurface(Handle, Handle, Handle, const int *);
extern U32 IMGeglDestroySurface(Handle, Handle);
extern U32 IMGeglQuerySurface(Handle, Handle, int, int *);
extern U32 IMGeglBindAPI(U32);
extern U32 IMGeglQueryAPI(void);
extern U32 IMGeglWaitClient(void);
extern U32 IMGeglReleaseThread(void);
extern Handle IMGeglCreatePbufferFromClientBuffer(Handle, U32, Handle, Handle, const int *);
extern U32 IMGeglSurfaceAttrib(Handle, Handle, int, int);
extern U32 IMGeglBindTexImage(Handle, Handle, int);
extern U32 IMGeglReleaseTexImage(Handle, Handle, int);
extern U32 IMGeglSwapInterval(Handle, int);
extern Handle IMGeglCreateContext(Handle, Handle, Handle, const int *);
extern U32 IMGeglDestroyContext(Handle, Handle);
extern U32 IMGeglMakeCurrent(Handle, Handle, Handle, Handle);
extern Handle IMGeglGetCurrentContext(void);
extern Handle IMGeglGetCurrentSurface(int);
extern Handle IMGeglGetCurrentDisplay(void);
extern U32 IMGeglQueryContext(Handle, Handle, int, int *);
extern U32 IMGeglWaitGL(void);
extern U32 IMGeglWaitNative(int);
extern U32 IMGeglSwapBuffers(Handle, Handle);
extern U32 IMGeglCopyBuffers(Handle, Handle, Handle);
extern Proc IMGeglGetProcAddress(const char *);
#define REAL(name, signature) ((signature)IMG##name)

struct Line { char bytes[320]; unsigned int used; };
static U32 sequence;

static void text(struct Line *line, const char *value)
{
    while (*value && line->used < sizeof(line->bytes) - 2)
        line->bytes[line->used++] = *value++;
}

static void hex(struct Line *line, Word value)
{
    static const char digits[] = "0123456789abcdef";
    text(line, "0x");
    for (int shift = (int)(sizeof(value) * 8) - 4; shift >= 0; shift -= 4)
        if (line->used < sizeof(line->bytes) - 2)
            line->bytes[line->used++] = digits[(value >> shift) & 15];
}

static void field(struct Line *line, const char *name, Word value)
{
    text(line, " "); text(line, name); text(line, "="); hex(line, value);
}

static void begin(struct Line *line, U32 id, const char *operation)
{
    line->used = 0;
    text(line, "ID6EGL"); field(line, "pid", (Word)getpid());
    field(line, "call", id); text(line, " "); text(line, operation);
}

static void emit(struct Line *line)
{
    int saved_errno = *__get_errno_ptr();
    line->bytes[line->used++] = '\n';
    /* No stdio buffering, allocations, or EGL calls while emitting a record. */
    (void)write(2, line->bytes, line->used);
    *__get_errno_ptr() = saved_errno;
}

static U32 next(void) { return __atomic_add_fetch(&sequence, 1, __ATOMIC_RELAXED); }

static void attributes(U32 id, const char *operation, const int *values)
{
    struct Line line; begin(&line, id, operation);
    field(&line, "attributes", (Word)values); emit(&line);
    if (!values) return;
    for (unsigned int i = 0; i < 64; i++) {
        int key = values[i * 2];
        begin(&line, id, operation); field(&line, "index", i);
        field(&line, "key", (U32)key);
        if (key == 0x3038) { text(&line, " END"); emit(&line); return; }
        field(&line, "value", (U32)values[i * 2 + 1]); emit(&line);
    }
    begin(&line, id, operation); text(&line, " ATTRIBUTE_LIMIT"); emit(&line);
}

static U32 trace_error(void)
{
    U32 value = REAL(eglGetError, U32 (*)(void))();
    struct Line line; begin(&line, next(), "eglGetError");
    field(&line, "result", value); emit(&line); return value;
}

static Handle trace_display(Handle native)
{
    Handle result = REAL(eglGetDisplay, Handle (*)(Handle))(native);
    struct Line line; begin(&line, next(), "eglGetDisplay");
    field(&line, "native", (Word)native); field(&line, "result", (Word)result);
    emit(&line); return result;
}

static U32 trace_initialize(Handle display, int *major, int *minor)
{
    U32 result = REAL(eglInitialize, U32 (*)(Handle, int *, int *))(display, major, minor);
    struct Line line; begin(&line, next(), "eglInitialize");
    field(&line, "display", (Word)display); field(&line, "result", result);
    if (result && major) field(&line, "major", (U32)*major);
    if (result && minor) field(&line, "minor", (U32)*minor);
    emit(&line); return result;
}

static U32 trace_configs(Handle display, Handle *configs, int capacity, int *count)
{
    U32 result = REAL(eglGetConfigs, U32 (*)(Handle, Handle *, int, int *))
        (display, configs, capacity, count);
    struct Line line; begin(&line, next(), "eglGetConfigs");
    field(&line, "display", (Word)display); field(&line, "result", result);
    field(&line, "capacity", (U32)capacity);
    if (result && count) field(&line, "count", (U32)*count);
    emit(&line); return result;
}

static U32 trace_choose(Handle display, const int *attrs, Handle *configs,
                        int capacity, int *count)
{
    U32 id = next();
    attributes(id, "eglChooseConfig.attr", attrs);
    U32 result = REAL(eglChooseConfig, U32 (*)(Handle, const int *, Handle *, int, int *))
        (display, attrs, configs, capacity, count);
    struct Line line; begin(&line, id, "eglChooseConfig");
    field(&line, "display", (Word)display); field(&line, "result", result);
    field(&line, "capacity", (U32)capacity);
    if (result && count) field(&line, "count", (U32)*count);
    if (result && count && *count > 0 && capacity > 0 && configs)
        field(&line, "config0", (Word)configs[0]);
    emit(&line); return result;
}

static Handle trace_context(Handle display, Handle config, Handle share, const int *attrs)
{
    U32 id = next(); attributes(id, "eglCreateContext.attr", attrs);
    Handle result = REAL(eglCreateContext, Handle (*)(Handle, Handle, Handle, const int *))
        (display, config, share, attrs);
    struct Line line; begin(&line, id, "eglCreateContext");
    field(&line, "display", (Word)display); field(&line, "config", (Word)config);
    field(&line, "share", (Word)share); field(&line, "result", (Word)result);
    emit(&line); return result;
}

static Handle trace_window(Handle display, Handle config, Handle native, const int *attrs)
{
    U32 id = next(); attributes(id, "eglCreateWindowSurface.attr", attrs);
    Handle result = REAL(eglCreateWindowSurface, Handle (*)(Handle, Handle, Handle, const int *))
        (display, config, native, attrs);
    struct Line line; begin(&line, id, "eglCreateWindowSurface");
    field(&line, "display", (Word)display); field(&line, "config", (Word)config);
    field(&line, "native_window", (Word)native); field(&line, "result", (Word)result);
    emit(&line); return result;
}

static U32 trace_current(Handle display, Handle draw, Handle read, Handle context)
{
    U32 result = REAL(eglMakeCurrent, U32 (*)(Handle, Handle, Handle, Handle))
        (display, draw, read, context);
    struct Line line; begin(&line, next(), "eglMakeCurrent");
    field(&line, "display", (Word)display); field(&line, "draw", (Word)draw);
    field(&line, "read", (Word)read); field(&line, "context", (Word)context);
    field(&line, "result", result); emit(&line); return result;
}

static U32 trace_swap(Handle display, Handle surface)
{
    U32 result = REAL(eglSwapBuffers, U32 (*)(Handle, Handle))(display, surface);
    struct Line line; begin(&line, next(), "eglSwapBuffers");
    field(&line, "display", (Word)display); field(&line, "surface", (Word)surface);
    field(&line, "result", result); emit(&line); return result;
}

/* Exact order read from libEGL.so.1's core-name table at ELF VA 0xa6c8. */
#define ADDRESS(name) (Proc)IMG##name,
static Proc dispatch[34] = { CORE_PROCS(ADDRESS) };
#undef ADDRESS

const char *ID6eglQueryString(Handle display, int name)
{
    const char *value = REAL(eglQueryString, const char *(*)(Handle, int))(display, name);
    if (display || name != 0x6000) return value;
    struct Line line; begin(&line, next(), "provider-table");
    if (value) { text(&line, " vendor-native-table; tracing unavailable"); emit(&line); return value; }
    dispatch[0] = (Proc)trace_error;
    dispatch[1] = (Proc)trace_display;
    dispatch[2] = (Proc)trace_initialize;
    dispatch[5] = (Proc)trace_configs;
    dispatch[6] = (Proc)trace_choose;
    dispatch[8] = (Proc)trace_window;
    dispatch[22] = (Proc)trace_context;
    dispatch[24] = (Proc)trace_current;
    dispatch[31] = (Proc)trace_swap;
    field(&line, "slots", 34); text(&line, " forwarded-vendor-IMG"); emit(&line);
    return (const char *)dispatch;
}

/* Optional slots are resolved by prefixed symbol name outside the core table.
 * Tail branches preserve every argument register and stack slot, including
 * 64-bit EGLTimeKHR alignment. Leave the three absent vendor exports absent.
 */
#if defined(__arm__)
#define FORWARD_EXTENSION(name) \
    __asm__(".text\n.align 2\n.global ID6" #name "\n" \
            ".type ID6" #name ",%function\nID6" #name ":\n" \
            "b IMG" #name "\n.size ID6" #name ", .-ID6" #name "\n");
FORWARD_EXTENSION(eglCreateImageKHR)
FORWARD_EXTENSION(eglDestroyImageKHR)
FORWARD_EXTENSION(eglCreateSyncKHR)
FORWARD_EXTENSION(eglDestroySyncKHR)
FORWARD_EXTENSION(eglClientWaitSyncKHR)
FORWARD_EXTENSION(eglGetSyncAttribKHR)
FORWARD_EXTENSION(eglSwapBuffersRegionEXT)
FORWARD_EXTENSION(eglPostSubBufferNV)
#undef FORWARD_EXTENSION
#endif

/* Controller producer for the hash-checked HmiMain3D of HU 006.027.001 (ID5_1811),
 * ported from X20511I 007.030.001 by code matching (vendor/port-hmi.py).
 * The two pop wrappers observe the native main queue without changing its wait
 * arguments. A worker submits authentic BMW interaction events, which wake
 * that queue through libhmicom's existing mutex and condition variable. */
#include "angle-egl-rpc.h"

#include <stdint.h>
#include <stddef.h>

extern void *dlopen(const char *, int);
extern void *dlsym(void *, const char *);
extern int pthread_create(unsigned int *, const void *, void *(*)(void *), void *);
extern int pthread_join(unsigned int, void **);
extern int usleep(unsigned int);
extern void *mmap_device_memory(void *, size_t, int, int, uint64_t);
extern int munmap(void *, size_t);
extern int printf(const char *, ...);
extern int fflush(void *);
extern void _exit(int);

typedef void *(*PopEvent)(void *, unsigned int);
typedef void (*ProcUnitMethod)(void *);
typedef int (*SubmitEvent)(void *, void *);
typedef void *(*NewControllerEvent)(void);
typedef void **(*GetDisplayServiceCache)(void);
typedef void (*EnableDisplay)(void *, int);

enum {
    kAppQueueOffset = 0x114,
    kAppVtable = 0x029cf520,
    kEventVtable = 0x03747ee0,
    kAllocateEvent = 0x00247c4c,
    kGetDisplayServiceCache = 0x0024eeb8,
    kDisplayServiceVtable = 0x029e7780,
    kEnableDisplay = 0x002d9a70,
    kDisplayHardwareOn = 0x30,
    kDisplayBackend = 0x34,
    kDisplayEnabled = 0x3d,
    kInteractionSlot = 0x1c / sizeof(void *),
    kReadWrite = 0x300,
    kResolveNow = 2,
    kPageSize = 4096,
};

static PopEvent pop_wait;
static PopEvent pop_timed;
static ProcUnitMethod destroy_proc;
static SubmitEvent submit_event;
static void *app_proc;
static unsigned int worker;
static unsigned int stopping;
static unsigned int worker_started;
static unsigned int panel_requested;
static unsigned int panel_announced;

__attribute__((constructor)) static void resolve_native_queue(void)
{
    void *lib = dlopen("/opt/hmi/ID5/lib/libhmicom.so", kResolveNow);
    if (lib) {
        pop_wait = (PopEvent)dlsym(lib, "_ZN14CHmiEventQueue3popEb");
        pop_timed = (PopEvent)dlsym(lib, "_ZN14CHmiEventQueue3popEj");
        destroy_proc = (ProcUnitMethod)dlsym(lib, "_ZN12CHmiProcUnitD2Ev");
        submit_event = (SubmitEvent)dlsym(
            lib, "_ZN12CHmiProcUnit19internalPushIaEventEP9CHmiEvent");
    }
    if (!pop_wait || !pop_timed || !destroy_proc || !submit_event) {
        printf("IDRIVE_HMI_CONTROLLER_FAIL stage=resolve\n");
        fflush(0);
        _exit(1);
    }
    printf("IDRIVE_HMI_CONTROLLER_LOADED\n");
    fflush(0);
}

static void *controller_worker(void *proc)
{
    struct idrive_hmi_controller_ring *ring = mmap_device_memory(
        0, kPageSize, kReadWrite, 0,
        IDRIVE_ANGLE_MAILBOX_PHYS + IDRIVE_HMI_CONTROLLER_OFFSET);
    if (!ring || ring == (void *)-1) {
        printf("IDRIVE_HMI_CONTROLLER_FAIL stage=map\n");
        return 0;
    }
    unsigned int read_index = __atomic_load_n(&ring->write_index, __ATOMIC_ACQUIRE);
    __atomic_store_n(&ring->read_index, read_index, __ATOMIC_RELEASE);
    printf("IDRIVE_HMI_CONTROLLER_READY proc=%p\n", proc);
    fflush(0);
    __atomic_store_n(&ring->ready, 1, __ATOMIC_RELEASE);
    while (!__atomic_load_n(&stopping, __ATOMIC_ACQUIRE)) {
        const unsigned int end = __atomic_load_n(&ring->write_index, __ATOMIC_ACQUIRE);
        if (end == read_index) {
            (void)usleep(10000);
            continue;
        }
        if (end - read_index > IDRIVE_HMI_CONTROLLER_SLOTS) {
            printf("IDRIVE_HMI_CONTROLLER_FAIL stage=ring\n");
            break;
        }
        const unsigned int input = ring->events[read_index % IDRIVE_HMI_CONTROLLER_SLOTS];
        const unsigned int key = input & 255u;
        const unsigned int pressed = input >> 8;
        if (idrive_hmi_controller_valid(key, pressed)) {
            unsigned char *event = ((NewControllerEvent)kAllocateEvent)();
            if (!event || *(uintptr_t *)event != kEventVtable) {
                printf("IDRIVE_HMI_CONTROLLER_FAIL stage=event\n");
                break;
            }
            *(unsigned int *)(event + 0x18) = key;
            event[0x1c] = (unsigned char)pressed;
            /* Constructor supplies one detent, zero long-press and zero refs. */
            __atomic_store_n(&panel_requested, 1, __ATOMIC_RELEASE);
            const int submitted = submit_event(proc, event);
            printf("IDRIVE_HMI_CONTROLLER_SUBMIT key=%u pressed=%u result=%d\n",
                   key, pressed, submitted);
            fflush(0);
        }
        __atomic_store_n(&ring->read_index, ++read_index, __ATOMIC_RELEASE);
    }
    __atomic_store_n(&ring->ready, 0, __ATOMIC_RELEASE);
    (void)munmap(ring, kPageSize);
    return 0;
}

static void announce_bench_panel(void)
{
    void **cache = ((GetDisplayServiceCache)kGetDisplayServiceCache)();
    unsigned char *display = cache ? cache[2] : 0;
    if (!display || *(uintptr_t *)display != kDisplayServiceVtable ||
        !*(void **)(display + kDisplayBackend))
        return;
    /* The emulated CID has no external monitor-status publisher. Seed the
     * panel's hardware status once and let BMW notify its subscribers. */
    display[kDisplayHardwareOn] = 1;
    ((EnableDisplay)kEnableDisplay)(display, 1);
    if (!display[kDisplayEnabled])
        return;
    panel_announced = 1;
    printf("IDRIVE_HMI_CONTROLLER_PANEL_READY\n");
    fflush(0);
}

static void observe_app_queue(void *proc)
{
    if (__atomic_load_n(&worker_started, __ATOMIC_ACQUIRE) ||
        *(uintptr_t *)proc != kAppVtable)
        return;
    const uintptr_t *vtable = *(const uintptr_t **)proc;
    if (vtable[kInteractionSlot] != 0x0020f0a0u &&
        vtable[kInteractionSlot] != (uintptr_t)submit_event)
        return;
    app_proc = proc;
    __atomic_store_n(&stopping, 0, __ATOMIC_RELEASE);
    if (pthread_create(&worker, 0, controller_worker, proc) == 0)
        __atomic_store_n(&worker_started, 1, __ATOMIC_RELEASE);
    else
        printf("IDRIVE_HMI_CONTROLLER_FAIL stage=thread\n");
}

static void *pop_from_queue(PopEvent pop, void *queue, unsigned int mode,
                            uintptr_t caller)
{
    if (caller != 0x00214b44u && caller != 0x00214b78u && caller != 0x00215d74u)
        return pop(queue, mode);
    void *proc = (unsigned char *)queue - kAppQueueOffset;
    observe_app_queue(proc);
    void *event = pop(queue, mode);
    if (event && proc == app_proc && !panel_announced &&
        __atomic_load_n(&panel_requested, __ATOMIC_ACQUIRE))
        announce_bench_panel();
    return event;
}

void *_ZN14CHmiEventQueue3popEb(void *queue, unsigned int block)
{
    return pop_from_queue(pop_wait, queue, block, (uintptr_t)__builtin_return_address(0));
}

void *_ZN14CHmiEventQueue3popEj(void *queue, unsigned int timeout)
{
    return pop_from_queue(pop_timed, queue, timeout, (uintptr_t)__builtin_return_address(0));
}

void _ZN12CHmiProcUnitD2Ev(void *proc)
{
    if (__atomic_load_n(&worker_started, __ATOMIC_ACQUIRE) && proc == app_proc) {
        __atomic_store_n(&stopping, 1, __ATOMIC_RELEASE);
        (void)pthread_join(worker, 0);
        panel_announced = 0;
        __atomic_store_n(&panel_requested, 0, __ATOMIC_RELEASE);
        app_proc = 0;
        __atomic_store_n(&worker_started, 0, __ATOMIC_RELEASE);
    }
    destroy_proc(proc);
}

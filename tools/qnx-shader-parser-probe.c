/*
 * Call the IMG driver's CPU-side glShaderBinary parser directly, without
 * creating EGL or touching the SGX device. The two authentic BMW shader files
 * are embedded by build-qnx-shader-parser-probe.sh.
 */
#include <stdint.h>

typedef int (*shader_parser_fn)(void *, const void *, unsigned int, int,
                                void *, void *, void **);
typedef void *(*allocate_fn)(unsigned int);
typedef void (*release_fn)(void *);

typedef struct {
    allocate_fn allocate;
    release_fn release;
    uint32_t reserved[0x100 / sizeof(uint32_t)];
} parser_context;

extern void glShaderBinary(int, const unsigned int *, unsigned int,
                           const void *, int);
extern int puts(const char *);
extern int fflush(void *);
extern void _exit(int);

void __aeabi_memclr(void *destination, unsigned int size)
{
    uint8_t *bytes = (uint8_t *)destination;
    while (size--) *bytes++ = 0;
}

void __aeabi_memclr4(void *destination, unsigned int size)
{
    __aeabi_memclr(destination, size);
}

void __aeabi_memclr8(void *destination, unsigned int size)
{
    __aeabi_memclr(destination, size);
}

void *__aeabi_memcpy(void *destination, const void *source, unsigned int size)
{
    uint8_t *out = (uint8_t *)destination;
    const uint8_t *in = (const uint8_t *)source;
    while (size--) *out++ = *in++;
    return destination;
}

void *__aeabi_memcpy4(void *destination, const void *source, unsigned int size)
{
    return __aeabi_memcpy(destination, source, size);
}

void *__aeabi_memcpy8(void *destination, const void *source, unsigned int size)
{
    return __aeabi_memcpy(destination, source, size);
}

extern const uint8_t shader_vertex[];
extern const uint32_t shader_vertex_size;
extern const uint8_t shader_fragment[];
extern const uint32_t shader_fragment_size;
extern const uint32_t shader_vertex_payload0_offset;
extern const uint32_t shader_vertex_payload0_size;
extern const uint32_t shader_fragment_payload0_offset;
extern const uint32_t shader_fragment_payload0_size;
extern const uint32_t shader_fragment_payload1_offset;
extern const uint32_t shader_fragment_payload1_size;

/* The native parser reached 254 KiB for mat_list_bg.frag and then requested
 * another 13.5 KiB. Keep a bounded 4 MiB arena so the probe does not mistake
 * its own bookkeeping limit for a rejected BMW shader. */
static uint8_t allocation_arena[4 * 1024 * 1024];
static uint32_t allocation_cursor;
static uint32_t allocation_count;
static uint32_t allocation_bytes;
#define MAX_ALLOCATION_RECORDS 4096
typedef struct {
    uint32_t offset;
    uint32_t size;
} allocation_record;
static allocation_record allocation_records[MAX_ALLOCATION_RECORDS];
static parser_context symbol_context;

static uint32_t parser_debug_count;
static uint32_t allocation_failure_count;

static void print_word(const char *label, uint32_t value);

void PVRSRVDebugPrintf(int level, const char *file, int line,
                       const char *format, ...)
{
    /* Interpose the driver's diagnostic import in this standalone probe.
     * The binary supplies format strings for the exact parser branches; do
     * not guess variadic argument types or consume untrusted format strings. */
    if (level <= 4 && parser_debug_count < 128) {
        parser_debug_count++;
        puts("IMG_UNIPATCH_DIAGNOSTIC");
        puts(file);
        print_word("driver-line", (uint32_t)line);
        puts(format);
    }
}

static void append_hex(char *out, uint32_t value)
{
    static const char digits[] = "0123456789abcdef";
    int i;
    for (i = 0; i < 8; ++i) {
        out[9 - i] = digits[value & 0xf];
        value >>= 4;
    }
}

static const char *hex_digits = "0123456789abcdef";

static void *probe_allocate(unsigned int size)
{
    uint32_t start = (allocation_cursor + 7u) & ~7u;
    uint32_t end = start + size;
    uint32_t i;
    if (end < start || end > sizeof(allocation_arena)) {
        allocation_failure_count++;
        if (allocation_failure_count <= 8) {
            puts("IMG_UNIPATCH_ALLOCATION_LIMIT");
            print_word("requested-bytes", size);
            print_word("arena-cursor", allocation_cursor);
            print_word("arena-capacity", sizeof(allocation_arena));
        }
        return 0;
    }
    for (i = start; i < end; ++i) allocation_arena[i] = 0;
    allocation_cursor = end;
    allocation_count++;
    allocation_bytes += size;
    if (allocation_count <= MAX_ALLOCATION_RECORDS) {
        allocation_records[allocation_count - 1].offset = start;
        allocation_records[allocation_count - 1].size = size;
    }
    return allocation_arena + start;
}

static void probe_release(void *pointer)
{
    (void)pointer;
}

static void print_word(const char *label, uint32_t value)
{
    char out[64];
    int i = 0;
    while (label[i] && i < 38) {
        out[i] = label[i];
        ++i;
    }
    out[i++] = '=';
    out[i++] = '0';
    out[i++] = 'x';
    append_hex(out + i - 2, value);
    i += 8;
    out[i] = '\0';
    puts(out);
}

static void print_hex_bytes(const char *label, const uint8_t *bytes,
                            uint32_t size)
{
    static const char digits[] = "0123456789abcdef";
    char out[160];
    uint32_t offset = 0;
    while (offset < size) {
        uint32_t count = size - offset;
        uint32_t i = 0;
        uint32_t j;
        if (count > 64) count = 64;
        while (label[i] && i < 12) {
            out[i] = label[i];
            ++i;
        }
        out[i++] = '+';
        out[i++] = '0';
        out[i++] = 'x';
        append_hex(out + i - 2, offset);
        i += 8;
        out[i++] = '=';
        for (j = 0; j < count; ++j) {
            out[i++] = digits[bytes[offset + j] >> 4];
            out[i++] = digits[bytes[offset + j] & 0xf];
        }
        out[i] = '\0';
        puts(out);
        offset += count;
    }
}

static int parse_one(const char *name, const uint8_t *bytes, uint32_t size,
                     int stage_flag, uintptr_t parser_address)
{
    uint32_t context[0x600 / sizeof(uint32_t)] = {0};
    void *parsed = 0;
    shader_parser_fn parser = (shader_parser_fn)parser_address;
    int result;
    uint32_t offset;

    allocation_cursor = 0;
    allocation_count = 0;
    allocation_bytes = 0;
    parser_debug_count = 0;
    allocation_failure_count = 0;
    for (offset = 0; offset < MAX_ALLOCATION_RECORDS; ++offset) {
        allocation_records[offset].offset = 0;
        allocation_records[offset].size = 0;
    }
    symbol_context.allocate = probe_allocate;
    symbol_context.release = probe_release;

    puts(name);
    print_word("length", size);
    print_word("stage-flag", (uint32_t)stage_flag);
    print_word("input-address", (uint32_t)(uintptr_t)bytes);
    print_word("allocation-arena", (uint32_t)(uintptr_t)allocation_arena);
    result = parser(context, bytes, size, stage_flag, 0, &symbol_context, &parsed);
    print_word("parser-result", (uint32_t)result);
    print_word("parsed-pointer", (uint32_t)(uintptr_t)parsed);
    print_word("symbol-alloc-count", allocation_count);
    print_word("symbol-alloc-bytes", allocation_bytes);
    print_word("symbol-alloc-cursor", allocation_cursor);
    print_word("symbol-alloc-failures", allocation_failure_count);
    if (parsed) {
        /* The parser's allocation helper creates a 0x98-byte record. */
        for (offset = 0; offset < 0x98; offset += 4) {
            char label[12] = "rec+0x00";
            label[6] = hex_digits[(offset >> 4) & 0xf];
            label[7] = hex_digits[offset & 0xf];
            print_word(label, *(const uint32_t *)((const uint8_t *)parsed + offset));
        }
        print_hex_bytes("record", (const uint8_t *)parsed, 0x98);
    }
    if (allocation_count > MAX_ALLOCATION_RECORDS) {
        print_word("allocation-records-truncated", allocation_count);
    }
    for (offset = 0; offset < allocation_count &&
                     offset < MAX_ALLOCATION_RECORDS; ++offset) {
        uint32_t prefix = allocation_records[offset].size;
        char label[24] = "alloc0000";
        label[5] = hex_digits[(offset >> 12) & 0xf];
        label[6] = hex_digits[(offset >> 8) & 0xf];
        label[7] = hex_digits[(offset >> 4) & 0xf];
        label[8] = hex_digits[offset & 0xf];
        print_word(label, allocation_records[offset].offset);
        label[9] = '-';
        label[10] = 's';
        label[11] = 'i';
        label[12] = 'z';
        label[13] = 'e';
        label[14] = '\0';
        print_word(label, allocation_records[offset].size);
        label[9] = '\0';
        /* Small PSU records contain the pointers to their child objects. */
        if (prefix > 256) prefix = 256;
        if (prefix) {
            print_hex_bytes(label,
                            allocation_arena + allocation_records[offset].offset,
                            prefix);
        }
    }
    return result;
}

void _start(void)
{
    uintptr_t entry = (uintptr_t)glShaderBinary;
    uintptr_t image_base = entry - 0x2c9fc;
    uintptr_t parser = image_base + 0xc7c8;
    int vertex_result;
    int fragment_result;
    int vertex_payload_result;
    int fragment_payload0_result;
    int fragment_payload1_result;

    puts("QNX IMG shader parser probe: no EGL/Screen/GPU initialization");
    print_word("glShaderBinary", (uint32_t)entry);
    print_word("driver-base", (uint32_t)image_base);
    print_word("parser-address", (uint32_t)parser);

    /* The IMG driver maps GL_VERTEX_SHADER to 1 and GL_FRAGMENT_SHADER to 0. */
    vertex_result = parse_one("BMW mat_cover_bg vertex, IMG stage=1",
                              shader_vertex, shader_vertex_size, 1, parser);
    fragment_result = parse_one("BMW mat_cover_bg fragment, IMG stage=0",
                                shader_fragment, shader_fragment_size, 0, parser);
    if (vertex_result != 0 || fragment_result != 0) {
        (void)parse_one("BMW mat_cover_bg vertex, alternate IMG stage=0",
                        shader_vertex, shader_vertex_size, 0, parser);
        (void)parse_one("BMW mat_cover_bg fragment, alternate IMG stage=1",
                        shader_fragment, shader_fragment_size, 1, parser);
        vertex_payload_result = parse_one(
            "BMW mat_cover_bg vertex PSU payload, IMG stage=1",
            shader_vertex + shader_vertex_payload0_offset,
            shader_vertex_payload0_size, 1, parser);
        fragment_payload0_result = parse_one(
            "BMW mat_cover_bg fragment PSU payload 0, IMG stage=0",
            shader_fragment + shader_fragment_payload0_offset,
            shader_fragment_payload0_size, 0, parser);
        fragment_payload1_result = parse_one(
            "BMW mat_cover_bg fragment PSU payload 1, IMG stage=0",
            shader_fragment + shader_fragment_payload1_offset,
            shader_fragment_payload1_size, 0, parser);
    } else {
        vertex_payload_result = 0;
        fragment_payload0_result = 0;
        fragment_payload1_result = 0;
    }
    if (vertex_result == 0 && fragment_result == 0 &&
        vertex_payload_result == 0 && fragment_payload0_result == 0 &&
        fragment_payload1_result == 0) {
        puts("Authentic BMW shader parser gate: PASS");
        fflush((void *)0);
        _exit(0);
    }
    puts("Authentic BMW shader parser gate: FAIL");
    fflush((void *)0);
    _exit(1);
}

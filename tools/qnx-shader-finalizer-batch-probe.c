/* Batch CPU-only finalization through the actual X20511I UniPatch code.
 * Shader assets are embedded into this probe at build time. It does not use
 * EGL, Screen, or the SGX device. */
#define _start original_parser_probe_start
#include "qnx-shader-parser-probe.c"
#undef _start

typedef void (*diagnostic_fn)(const char *, ...);
typedef void *(*create_context_fn)(allocate_fn, release_fn, diagnostic_fn);
typedef int (*set_output_count_fn)(void *, unsigned int);
typedef void (*set_texture_format_fn)(void *, unsigned int, const uint32_t *, uint32_t, uint32_t);
typedef void (*set_fragment_flags_fn)(void *, uint32_t);
typedef void *(*finalize_fn)(void *, void *);

typedef struct {
    const char *name;
    const uint8_t *bytes;
    uint32_t size;
    uint32_t vertex;
} batch_shader;

extern const batch_shader shader_batch[];
extern const uint32_t shader_batch_count;

static void diagnostic(const char *format, ...)
{
    puts("UniPatch diagnostic format:");
    puts(format);
}

static uint32_t allocation_size(const void *pointer)
{
    uintptr_t address = (uintptr_t)pointer;
    uintptr_t base = (uintptr_t)allocation_arena;
    if (address < base || address >= base + sizeof(allocation_arena)) return 0;
    for (uint32_t i = 0; i < allocation_count && i < MAX_ALLOCATION_RECORDS; i++)
        if (allocation_records[i].offset == address - base)
            return allocation_records[i].size;
    return 0;
}

static int run_shader(const batch_shader *shader, uintptr_t driver_base)
{
    create_context_fn create_context = (create_context_fn)(driver_base + 0x52268);
    set_output_count_fn set_output_count = (set_output_count_fn)(driver_base + 0x51f28);
    set_texture_format_fn set_texture_format = (set_texture_format_fn)(driver_base + 0x51e40);
    set_fragment_flags_fn set_fragment_flags = (set_fragment_flags_fn)(driver_base + 0x51f20);
    shader_parser_fn parse = (shader_parser_fn)(driver_base + 0xc7c8);
    finalize_fn finalize = (finalize_fn)(driver_base + 0x51f80);
    uint32_t parser_state[0x600 / sizeof(uint32_t)] = {0};
    void *record = 0;
    void *output = 0;
    void *context;
    uint32_t size;
    int result;

    puts("BMW-UNIPATCH-BATCH-BEGIN");
    puts(shader->name);
    print_word("input-size", shader->size);
    allocation_cursor = allocation_count = allocation_bytes = 0;
    parser_debug_count = allocation_failure_count = 0;
    for (uint32_t i = 0; i < MAX_ALLOCATION_RECORDS; ++i) {
        allocation_records[i].offset = 0;
        allocation_records[i].size = 0;
    }

    context = create_context(probe_allocate, probe_release, diagnostic);
    if (!context || allocation_size(context) != 0x314) {
        puts("BMW-UNIPATCH-BATCH-FAIL context");
        return 1;
    }
    result = parse(parser_state, shader->bytes, shader->size, shader->vertex, 0,
                   context, &record);
    print_word("parse-result", (uint32_t)result);
    print_word("parse-allocation-count", allocation_count);
    print_word("parse-allocation-bytes", allocation_bytes);
    print_word("parse-allocation-cursor", allocation_cursor);
    print_word("parse-allocation-failures", allocation_failure_count);
    if (result || !record) {
        puts("BMW-UNIPATCH-BATCH-FAIL parse");
        return 1;
    }
    void *input = (void *)(uintptr_t)*(uint32_t *)((uint8_t *)record + 0x88);
    if (!input || !set_output_count(context, 1)) {
        puts("BMW-UNIPATCH-BATCH-FAIL output-count");
        return 1;
    }
    if (!shader->vertex) {
        /* Match the verified HMI fragment finalizer setup: sampler zero uses
         * the native GL_RGBA/GL_UNSIGNED_BYTE format descriptor and fragment
         * flag 1. The vertex path leaves both settings untouched. */
        static const uint32_t rgba8_format[5] = {4, 0, 1, 2, 3};
        set_texture_format(context, 0, rgba8_format, 0, 0);
        set_fragment_flags(context, 1);
    }
    output = finalize(context, input);
    size = allocation_size(output);
    print_word("final-pointer", (uint32_t)(uintptr_t)output);
    print_word("final-size", size);
    print_word("arena-used", allocation_bytes);
    if (!output || size < 0xa4 || size > 2 * 1024 * 1024) {
        puts("BMW-UNIPATCH-BATCH-FAIL finalize");
        return 1;
    }
    uint32_t count = *(uint16_t *)((uint8_t *)output + 0x0c);
    uint32_t code = *(uint32_t *)((uint8_t *)output + 0x10);
    uintptr_t end = (uintptr_t)output + size;
    print_word("instruction-count", count);
    print_word("instruction-pointer", code);
    if (!count || count > 4096 || code < (uintptr_t)output ||
        (uintptr_t)code > end || count * 8 > end - (uintptr_t)code) {
        puts("BMW-UNIPATCH-BATCH-FAIL descriptor");
        return 1;
    }
    print_hex_bytes("final", output, size);
    print_hex_bytes("code", (const uint8_t *)(uintptr_t)code, count * 8);
    puts("BMW-UNIPATCH-BATCH-PASS");
    return 0;
}

void _start(void)
{
    uintptr_t driver_base = (uintptr_t)glShaderBinary - 0x2c9fc;
    uint32_t passed = 0;
    uint32_t failed = 0;
    puts("Authentic BMW UniPatch batch finalization: CPU-only");
    print_word("shader-count", shader_batch_count);
    print_word("driver-base", (uint32_t)driver_base);
    for (uint32_t i = 0; i < shader_batch_count; ++i) {
        if (run_shader(&shader_batch[i], driver_base)) ++failed;
        else ++passed;
    }
    print_word("batch-passed", passed);
    print_word("batch-failed", failed);
    fflush((void *)0);
    _exit(failed ? 1 : 0);
}

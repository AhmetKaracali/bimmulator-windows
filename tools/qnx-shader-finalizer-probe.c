/* CPU-only control experiment using the actual X20511I UniPatch functions.
 * No EGL context, Screen window, GPU service, or fabricated completion.
 * Function coordinates and output fields are recorded in the Ghidra evidence.
 */
#define _start original_parser_probe_start
#include "qnx-shader-parser-probe.c"
#undef _start

typedef void (*diagnostic_fn)(const char *, ...);
typedef void *(*create_context_fn)(allocate_fn, release_fn, diagnostic_fn);
typedef int (*set_output_count_fn)(void *, unsigned int);
typedef void (*set_texture_format_fn)(void *, unsigned int, const uint32_t *, uint32_t, uint32_t);
typedef void (*set_fragment_flags_fn)(void *, uint32_t);
typedef void *(*finalize_fn)(void *, void *);

static void diagnostic(const char *format, ...)
{
    /* The format string still identifies the native failure branch. Do not
     * guess a variadic argument layout or consume unmatched format arguments. */
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

static int run_stage(int vertex)
{
    uintptr_t base = (uintptr_t)glShaderBinary - 0x2c9fc;
    create_context_fn create_context = (create_context_fn)(base + 0x52268);
    set_output_count_fn set_output_count = (set_output_count_fn)(base + 0x51f28);
    shader_parser_fn parse = (shader_parser_fn)(base + 0xc7c8);
    finalize_fn finalize = (finalize_fn)(base + 0x51f80);
    set_texture_format_fn set_texture_format = (set_texture_format_fn)(base + 0x51e40);
    set_fragment_flags_fn set_fragment_flags = (set_fragment_flags_fn)(base + 0x51f20);
    uint32_t parser_state[0x600 / sizeof(uint32_t)] = {0};
    void *record = 0;

    puts(vertex ? "BMW-UNIPATCH-BEGIN vertex" : "BMW-UNIPATCH-BEGIN fragment");
    print_word("driver-base", (uint32_t)base);
    allocation_cursor = allocation_count = allocation_bytes = 0;
    void *context = create_context(probe_allocate, probe_release, diagnostic);
    print_word("context", (uint32_t)(uintptr_t)context);
    if (!context || allocation_size(context) != 0x314) goto failed;

    int result = parse(parser_state, vertex ? shader_vertex : shader_fragment,
                       vertex ? shader_vertex_size : shader_fragment_size,
                       vertex, 0, context, &record);
    print_word("parse-result", (uint32_t)result);
    print_word("parsed-record", (uint32_t)(uintptr_t)record);
    if (result || !record) goto failed;
    void *input = (void *)(uintptr_t)*(uint32_t *)((uint8_t *)record + 0x88);
    print_word("parsed-PSU", (uint32_t)(uintptr_t)input);
    if (!input || !set_output_count(context, 1)) goto failed;

    if (!vertex) {
        /* Native GL_RGBA/GL_UNSIGNED_BYTE descriptor at raw VA 0x802b4,
         * words +0x0c..+0x1c. glTexImage2D selects it and texture validation
         * places that pointer at GLES-context +0xe6c. SetupUSEFragmentShader
         * forwards these five words to UniPatch for sampler zero.
         * Flag 1 is the native no-alpha-test/full-color-mask path. */
        static const uint32_t rgba8_format[5] = {4, 0, 1, 2, 3};
        set_texture_format(context, 0, rgba8_format, 0, 0);
        set_fragment_flags(context, 1);
    }

    /* Matches SetupUSEVertexShader's no-texture control path: the selected
     * vertex shader declares attributes/MVP/varying but no texture samplers. */
    void *output = finalize(context, input);
    uint32_t size = allocation_size(output);
    print_word("final-pointer", (uint32_t)(uintptr_t)output);
    print_word("final-size", size);
    print_word("arena-used", allocation_bytes);
    if (!output || size < 0xa4) goto failed;
    uint32_t count = *(uint16_t *)((uint8_t *)output + 0x0c);
    uint32_t code = *(uint32_t *)((uint8_t *)output + 0x10);
    uintptr_t end = (uintptr_t)output + size;
    print_word("instruction-count", count);
    print_word("instruction-pointer", code);
    if (!count || count > 4096 || code < (uintptr_t)output ||
        (uintptr_t)code > end || count * 8 > end - (uintptr_t)code) goto failed;
    print_hex_bytes("final", output, size);
    print_hex_bytes("code", (const uint8_t *)(uintptr_t)code, count * 8);
    puts(vertex ? "BMW-UNIPATCH-PASS vertex" : "BMW-UNIPATCH-PASS fragment");
    return 0;

failed:
    puts(vertex ? "BMW-UNIPATCH-FAIL vertex" : "BMW-UNIPATCH-FAIL fragment");
    return 1;
}

void _start(void)
{
    puts("Authentic BMW UniPatch finalization: CPU-only, no EGL/Screen/GPU initialization");
    int status = run_stage(1);
    if (!status) status = run_stage(0);
    fflush((void *)0);
    _exit(status);
}

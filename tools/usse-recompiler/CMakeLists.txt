cmake_minimum_required(VERSION 3.20)
project(idrive_usse_recompiler LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT VITA3K_ROOT OR NOT DEFINED ENV{IDRIVE_GLSLANG_INCLUDE})
  message(FATAL_ERROR "Set VITA3K_ROOT and enter nix develop path:.#shader")
endif()
find_package(Vulkan REQUIRED)
add_executable(idrive-vulkan-compute vulkan-run.cpp)
target_compile_options(idrive-vulkan-compute PRIVATE -include "${CMAKE_CURRENT_SOURCE_DIR}/common.h")
target_link_libraries(idrive-vulkan-compute PRIVATE Vulkan::Vulkan)
add_executable(idrive-vulkan-graphics vulkan-graphics-run.cpp)
target_compile_options(idrive-vulkan-graphics PRIVATE -include "${CMAKE_CURRENT_SOURCE_DIR}/common.h")
target_link_libraries(idrive-vulkan-graphics PRIVATE Vulkan::Vulkan)
find_package(fmt REQUIRED)
set(GLSLANG_ROOT "$ENV{IDRIVE_GLSLANG_INCLUDE}")
set(SHADER "${VITA3K_ROOT}/vita3k/shader")
file(GLOB TRANSLATORS CONFIGURE_DEPENDS "${SHADER}/src/translator/*.cpp")
file(READ "${SHADER}/src/usse_translator_entry.cpp" ENTRY_CODE)
string(FIND "${ENTRY_CODE}" "decoder->call(visitor, cur_instr);" CHECKED_CALL)
string(FIND "${ENTRY_CODE}" "LOG_DISASM(\"{:016x}: error: instruction unmatched\", cur_instr);" CHECKED_UNKNOWN)
if(CHECKED_CALL EQUAL -1 OR CHECKED_UNKNOWN EQUAL -1)
  message(FATAL_ERROR "Upstream instruction-dispatch contract changed")
endif()
string(REPLACE "decoder->call(visitor, cur_instr);"
  "{ if (!decoder->call(visitor, cur_instr)) throw std::runtime_error(\"USSE visitor rejected instruction\"); }"
  ENTRY_CODE "${ENTRY_CODE}")
string(REPLACE "LOG_DISASM(\"{:016x}: error: instruction unmatched\", cur_instr);"
  "throw std::runtime_error(fmt::format(\"Unmatched USSE instruction {:016x}\", cur_instr));"
  ENTRY_CODE "${ENTRY_CODE}")
string(FIND "${ENTRY_CODE}" "count = _count;" CHECKED_RESET)
if(CHECKED_RESET EQUAL -1)
  message(FATAL_ERROR "Upstream program-reset contract changed")
endif()
set(CHECKED_RESET_CODE [=[count = _count;
    // This computational harness has no texture/memory/task adapter. Admit
    // only the families explicitly examined so far, before CFG analysis could
    // consume a branch/task opcode. Aggregate every unsupported family in this
    // stage so one run identifies the complete current translation boundary.
    const std::array<const char *, 10> allowed = {
        "VMOV ()", "VMAD2 ()", "VPCK ()", "V32NMAD ()", "V16NMAD ()",
        "VMAD ()", "SOP2 ()", "SOP2M ()", "NOP ()", "VBW ()"};
    // These exact opcodes were found in X20511I shaders captured from the real
    // HMI and matched by SHA-256 to staged .shd assets. The matching native
    // finalizer records are in the hmi-angle-draw-v37 vertex input manifest
    // and unipatch-hmi-fragment-batch-v32c manifest. Their visitors are
    // implemented in the pinned Vita3K translator. Keep admission at the
    // observed instruction encoding; do not enable whole VDP/VTSTMSK/VCOMP
    // families without new native evidence.
    const std::array<std::uint64_t, 31> observed_runtime_shader_words = {
        0x788189229033808cULL, // VTSTMSK in mat_list_gloss.vert.shd
        0x18918081c17da20fULL, // VDP in mat_list_mirrored.vert.shd
        0x18918081c1fda20dULL, // VDP in mat_list_bg.vert.shd
        0x3080080202003e02ULL, // VCOMP in mat_list_gloss.vert.shd
        0x30a0008a80000001ULL, // VCOMP in mat_frame/shadow/frame_inner fragments
        0x30a0008280800484ULL, // VCOMP in mat_bg.frag.shd
        0x30a0008280c00384ULL, // VCOMP in mat_list_edge_l.frag.shd
        // Exact additional words from V51 X20511I captures, SHA-256 matched
        // to the staged assets in hmi-id6l-v50-failed-unipatch-batch.json.
        // Their visitors exist in the pinned translator; admission is limited
        // to these observed words until each opcode family's IMG semantics
        // are independently established.
        0xfca3f1f1001fffffULL, // LIMM mat_highlight_main.frag.shd
        0x3080000201a03e01ULL, // VCOMP mat_frame.vert.shd
        0x20a44106e01d138aULL, // VDUAL mat_bg.frag.shd
        0x20a03d0600090880ULL, // VDUAL mat_bg.frag.shd
        0xe001c404e0000300ULL, // SMP mat_subline.frag.shd
        0xf920000000000000ULL, // SPEC/WDF following SMP in mat_subline.frag.shd
        // These exact words were captured from V54 HmiMain3D, matched by
        // full SHA-256 to their staged X20511I assets, and passed through the
        // shipped QNX finalizer. Admission remains limited to these words.
        0x30a0008280800384ULL, // VCOMP in mat_list_mirrored.frag.shd
        0x20e02042a01c0482ULL, // VDUAL in mat_highlight.frag.shd
        0x18918080cf119093ULL, // VDP in Text_ColorFading_vertex_fadeVertical.shd
        0x78800920e0138300ULL, // VTSTMSK in mat_list_mirrored.frag.shd
        // Exact native-finalized X20511I mat_list_bg.frag.shd words. The pinned
        // visitors map these to F32 VRCP/VLOG/VEXP, dual FRCP/VMOV, VSSQ/FMUL,
        // FEXP/FADD, FLOG/FMUL, VMUL/VMOV, and VTSTMSK(VSUB). Their source
        // layouts and operation selectors were checked against the pinned
        // decoder grammar and visitor tables. All other encodings remain out.
        0x3080000281200481ULL, // VCOMP: VRCP, source/destination X
        0x78808922e0338384ULL, // VTSTMSK: F32 VSUB, four-component mask
        0x2085704290350087ULL, // VDUAL: FRCP + VMOV
        0x20c02800df882492ULL, // VDUAL: VSSQ + FMUL
        0x3080080a00203f01ULL, // VCOMP: VRCP, source Y
        0x30800c400fa03e01ULL, // VCOMP: VLOG with decoded source modifier
        0x20c0cc0290452491ULL, // VDUAL: FEXP + FADD
        0x20c0580290085881ULL, // VDUAL: FLOG + FMUL
        0x30800e000fc03e81ULL, // VCOMP: VEXP
        0x28843080df961085ULL, // VDUAL: VMUL + VMOV
        // Exact V84 native-finalized X20511I mat_pad_bg.frag.shd words.
        // The pinned decoder grammar selects F16 VRCP from source Z to dest X,
        // then F16 VRCP from source W to dest Z. Both use temp bank 2, no
        // source modifier, no repeat, no extended bank, and a single write bit.
        0x30a0009281400501ULL,
        0x30a0009a80800504ULL,
        // Exact V84 native-finalized X20511I mat_pad_bg.frag.shd samples.
        // The pinned SMP visitor decodes 2D F16 coordinates from PA0, writes
        // F16 results to temp registers 0 and 2, and selects sampler register
        // keys 10 and 14. Sampler interfaces are supplied only for this exact
        // finalized fragment fixture in graphics-recompile.cpp.
        0xe001840ce0000280ULL,
        0xe001840ce0400380ULL
    };
    std::vector<std::string> unsupported_instructions;
    for (std::size_t i = 0; i < _count; ++i) {
        auto decoded = DecodeUSSE<USSETranslatorVisitor>(_inst[i]);
        if (!decoded) throw std::runtime_error(fmt::format("Unmatched USSE instruction {:016x}", _inst[i]));
        const std::string name = decoded->GetName();
        // Captured X20511I secondary programs use only this narrow VCOMP
        // candidate: F32 VRCP of source component X, writing F32 to bank 2,
        // with no modifiers, repeats, predicates, or extended banks. Keep all
        // other VCOMP encodings outside the current translator contract.
        const std::uint64_t word = _inst[i];
        const auto field = [word](unsigned shift, unsigned width) {
            return (word >> shift) & ((std::uint64_t{1} << width) - 1);
        };
        const std::uint64_t source_bank = field(30, 2);
        const std::uint64_t write_mask = field(0, 4);
        const bool observed_vrcp = name == "VCOMP ()" &&
            field(56, 3) == 0 && field(55, 1) == 1 &&
            field(53, 2) == 0 && field(52, 1) == 0 &&
            field(51, 1) == 0 && field(50, 1) == 0 &&
            field(49, 1) == 0 && field(44, 4) == 0 &&
            field(43, 1) == 1 && field(41, 2) == 0 &&
            field(39, 2) == 0 && field(37, 2) == 0 &&
            field(35, 2) == 0 && field(32, 2) == 2 &&
            (source_bank == 0 || source_bank == 2) &&
            (write_mask == 1 || write_mask == 2);
        if (!std::any_of(allowed.begin(), allowed.end(), [&](const char *s) { return name == s; }) &&
            !observed_vrcp &&
            std::find(observed_runtime_shader_words.begin(), observed_runtime_shader_words.end(), word) == observed_runtime_shader_words.end()) {
            const auto detail = fmt::format("{} 0x{:016x}", name, word);
            if (std::find(unsupported_instructions.begin(), unsupported_instructions.end(), detail) ==
                unsupported_instructions.end())
                unsupported_instructions.push_back(detail);
        }
    }
    std::string unsupported;
    for (const auto &detail : unsupported_instructions) {
        if (!unsupported.empty()) unsupported += ", ";
        unsupported += detail;
    }
    if (!unsupported.empty())
        throw std::runtime_error("Unvalidated USSE operation encodings in this shader: " + unsupported);
]=])
string(REPLACE "count = _count;" "${CHECKED_RESET_CODE}" ENTRY_CODE "${ENTRY_CODE}")
string(PREPEND ENTRY_CODE "#include <string>\n")
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/checked_usse_entry.cpp" "${ENTRY_CODE}")
set(USSE_CORE_SOURCES
  ${TRANSLATORS}
  "${CMAKE_CURRENT_BINARY_DIR}/checked_usse_entry.cpp"
  "${SHADER}/src/usse_program_analyzer.cpp"
  "${SHADER}/src/usse_decode_helpers.cpp"
  "${SHADER}/src/usse_disasm.cpp"
  "${SHADER}/src/usse_utilities.cpp"
  "${GLSLANG_ROOT}/SPIRV/SpvBuilder.cpp"
  "${GLSLANG_ROOT}/SPIRV/SpvPostProcess.cpp"
  "${GLSLANG_ROOT}/SPIRV/InReadableOrder.cpp"
  "${GLSLANG_ROOT}/SPIRV/Logger.cpp"
  "${GLSLANG_ROOT}/SPIRV/doc.cpp")
add_library(idrive-usse-core STATIC ${USSE_CORE_SOURCES})
target_include_directories(idrive-usse-core PUBLIC
  include "${SHADER}/include" "${VITA3K_ROOT}/vita3k/gxm/include"
  "${VITA3K_ROOT}/vita3k/util/include" "${VITA3K_ROOT}/vita3k/features/include"
  "${GLSLANG_ROOT}")
target_compile_options(idrive-usse-core PRIVATE -include "${CMAKE_CURRENT_SOURCE_DIR}/common.h"
  -ffunction-sections -UNDEBUG -Werror=dangling-else)
target_link_libraries(idrive-usse-core PUBLIC fmt::fmt)
add_executable(idrive-usse-recompile main.cpp)
target_compile_options(idrive-usse-recompile PRIVATE -include "${CMAKE_CURRENT_SOURCE_DIR}/common.h")
target_link_libraries(idrive-usse-recompile PRIVATE idrive-usse-core)
add_executable(idrive-usse-graphics graphics-recompile.cpp)
target_compile_options(idrive-usse-graphics PRIVATE -include "${CMAKE_CURRENT_SOURCE_DIR}/common.h")
target_link_libraries(idrive-usse-graphics PRIVATE idrive-usse-core)
if(APPLE)
  target_link_options(idrive-usse-recompile PRIVATE -Wl,-dead_strip)
  target_link_options(idrive-usse-graphics PRIVATE -Wl,-dead_strip)
else()
  target_link_options(idrive-usse-recompile PRIVATE -Wl,--gc-sections)
  target_link_options(idrive-usse-graphics PRIVATE -Wl,--gc-sections)
endif()

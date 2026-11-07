/*
 * Offline regression for the small USSE prefix shared with QEMU. This replays
 * only supported TEMP LIMM/NOP effects and checks that unresolved VLDST/BR
 * candidates leave register state untouched.
 */
#include "../hw/display/omap5430_sgx_usse.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(condition, message) do { \
    if (!(condition)) { \
        fprintf(stderr, "fixture replay failed: %s\n", message); \
        return 1; \
    } \
} while (0)

static uint64_t read_le64(const uint8_t *data)
{
    uint64_t value = 0;
    unsigned i;

    for (i = 0; i < 8; i++) {
        value |= (uint64_t)data[i] << (i * 8);
    }
    return value;
}

static uint64_t fixture_word(const uint8_t *image, size_t image_size,
                             size_t offset)
{
    if (offset > image_size || image_size - offset < sizeof(uint64_t)) {
        return 0;
    }
    return read_le64(image + offset);
}

int main(int argc, char **argv)
{
    uint32_t temp[SGX_USSE_TEMP_COUNT] = { 0 };
    bool temp_valid[SGX_USSE_TEMP_COUNT] = { false };
    uint32_t temp_before[SGX_USSE_TEMP_COUNT];
    bool valid_before[SGX_USSE_TEMP_COUNT];
    SGXUSSEPrefixFields fields;
    SGXUSSEVldstPrimaryLoadCandidate load_candidate;
    SGXUSSEVBWFields vbw_fields;
    SGXUSSEVBWDecodedCandidate vbw_candidate;
    SGXUSSEEmitFields emit_fields;
    SGXUSSEPrefixResult result;
    uint8_t *image;
    size_t image_size;
    FILE *stream;
    unsigned executed = 0;
    size_t offset;
    uint64_t instruction;

    CHECK(argc == 2, "usage: usse-fixture-replay USE_IMAGE.bin");
    stream = fopen(argv[1], "rb");
    CHECK(stream != NULL, "cannot open USE image");
    CHECK(fseek(stream, 0, SEEK_END) == 0, "cannot seek USE image");
    {
        long length = ftell(stream);
        CHECK(length > 0, "empty USE image");
        image_size = (size_t)length;
    }
    CHECK(fseek(stream, 0, SEEK_SET) == 0, "cannot rewind USE image");
    image = malloc(image_size);
    CHECK(image != NULL, "cannot allocate USE image buffer");
    CHECK(fread(image, 1, image_size, stream) == image_size,
          "short USE image read");
    CHECK(fclose(stream) == 0, "cannot close USE image");

    /* Replay the captured entry until its first unresolved memory operation. */
    for (offset = 0x1ec0; offset <= 0x1ee0; offset += 8) {
        instruction = fixture_word(image, image_size, offset);
        memcpy(temp_before, temp, sizeof(temp));
        memcpy(valid_before, temp_valid, sizeof(temp_valid));
        result = sgx_usse_step_prefix(instruction, temp, temp_valid, &fields);

        if (offset < 0x1ee0) {
            if (result == SGX_USSE_PREFIX_APPLIED_LIMM) {
                printf("%08zx: LIMM TEMP[%u]=%#010x\n", offset,
                       fields.limm.destination, fields.limm.immediate);
                executed++;
                continue;
            }
            if (result == SGX_USSE_PREFIX_ADVANCED_NOP) {
                printf("%08zx: NOP\n", offset);
                executed++;
                continue;
            }
            free(image);
            CHECK(false, "unexpected prefix instruction class");
        }

        CHECK(result == SGX_USSE_PREFIX_STOP_UNRESOLVED_VLDST,
              "first memory instruction was not left unresolved");
        CHECK(memcmp(temp_before, temp, sizeof(temp)) == 0,
              "unresolved VLDST changed TEMP values");
        CHECK(memcmp(valid_before, temp_valid, sizeof(temp_valid)) == 0,
              "unresolved VLDST changed TEMP validity");
        CHECK(fields.vldst.dest_bank_primattr == 0 &&
              fields.vldst.destination == 4 &&
              fields.vldst.src0_bank_ext == 0 &&
              fields.vldst.src0_bank == 0 && fields.vldst.src0_n == 4 &&
              fields.vldst.src1_bank_ext == 1 &&
              fields.vldst.src1_bank == 2 && fields.vldst.src1_n == 1 &&
              fields.vldst.src2_bank_ext == 1 &&
              fields.vldst.src2_bank == 2 && fields.vldst.src2_n == 0,
              "unexpected SGX543 VLDST destination fields");
        CHECK(fields.vldst.moe_expand == 1 &&
              sgx_usse_vldst_primary_load_candidate(
                  &fields.vldst, temp, temp_valid, &load_candidate),
              "captured LDR did not match the limited primary-load candidate");
        CHECK(load_candidate.address == 0xf4003004 &&
              load_candidate.destination == 4 &&
              load_candidate.byte_width == 4,
              "SGX543 reference load candidate changed");
        CHECK(temp_valid[4] && temp[4] == 0xf4003000,
              "entry base TEMP4 did not come from the captured LIMM");
        printf("%08zx: VLDST candidate dest-bank-primattr=%u dest=%u "
               "src0=%u/%u:%u src1=%u/%u:%u src2=%u/%u:%u "
               "moe-expand=%u primary-LDR-address-candidate=%#010x "
               "width=%u base-TEMP4=%#010x state=unchanged\n",
               offset, fields.vldst.dest_bank_primattr,
               fields.vldst.destination,
               fields.vldst.src0_bank_ext, fields.vldst.src0_bank,
               fields.vldst.src0_n,
               fields.vldst.src1_bank_ext, fields.vldst.src1_bank,
               fields.vldst.src1_n,
               fields.vldst.src2_bank_ext, fields.vldst.src2_bank,
               fields.vldst.src2_n, fields.vldst.moe_expand,
               load_candidate.address, load_candidate.byte_width, temp[4]);
    }
    CHECK(executed == 4, "unexpected supported prefix instruction count");
    CHECK(temp_valid[0] && temp[0] == 0x01000800 &&
          temp_valid[2] && temp[2] == 0x0f20138c,
          "captured LIMM state differs from QEMU's prefix state");

    /* Decode the next captured word without applying an ALU effect. */
    instruction = fixture_word(image, image_size, 0x1f00);
    memcpy(temp_before, temp, sizeof(temp));
    memcpy(valid_before, temp_valid, sizeof(temp_valid));
    CHECK(instruction == UINT64_C(0x5001000020800201),
          "captured VBW instruction changed");
    CHECK(sgx_usse_decode_vbw(instruction, &vbw_fields),
          "captured VBW instruction did not match the pinned grammar");
    CHECK(vbw_fields.op1 == 2 && vbw_fields.op2 == 0 &&
          vbw_fields.predicate == 0 && vbw_fields.skip_invalid == 0 &&
          vbw_fields.no_schedule == 0 && vbw_fields.repeat_select == 0 &&
          vbw_fields.sync_start == 0 && vbw_fields.destination_ext == 0 &&
          vbw_fields.end == 0 && vbw_fields.src1_ext == 0 &&
          vbw_fields.src2_ext == 1 && vbw_fields.repeat_count == 0 &&
          vbw_fields.src2_invert == 0 && vbw_fields.src2_rotate == 0 &&
          vbw_fields.src2_ext_high == 0 && vbw_fields.partial_16bit == 0 &&
          vbw_fields.destination_bank == 0 && vbw_fields.src1_bank == 0 &&
          vbw_fields.src2_bank == 2 && vbw_fields.destination == 4 &&
          vbw_fields.src2_select == 0 && vbw_fields.src1 == 4 &&
          vbw_fields.src2 == 1,
          "captured VBW fields differ from the pinned grammar");
    CHECK(sgx_usse_vbw_operation_candidate(&vbw_fields, &vbw_candidate) &&
          vbw_candidate.operation == SGX_USSE_VBW_AND_CANDIDATE &&
          vbw_candidate.byte_width == 4,
          "captured VBW operation candidate differs from Vita3K reference");
    CHECK(memcmp(temp_before, temp, sizeof(temp)) == 0 &&
          memcmp(valid_before, temp_valid, sizeof(temp_valid)) == 0,
          "VBW field decode or candidate classification changed TEMP state");
    printf("001f00: VBW candidate op1=%u op2=%u dst-bank=%u dst=%u "
           "src1-bank=%u src1=%u src2-ext=%u src2-bank=%u src2=%u "
           "operation=AND width=%u state=unchanged\n",
           vbw_fields.op1, vbw_fields.op2, vbw_fields.destination_bank,
           vbw_fields.destination, vbw_fields.src1_bank, vbw_fields.src1,
           vbw_fields.src2_ext, vbw_fields.src2_bank, vbw_fields.src2,
           vbw_candidate.byte_width);

    /* Decode all four captured EMIT words as fields only; apply no effects. */
    {
        const size_t emit_offsets[] = { 0x1f08, 0x1f30, 0x113e8, 0x152d8 };
        const uint64_t emit_words[] = {
            UINT64_C(0xfb20b18800c00082),
            UINT64_C(0xfb20b10800c00082),
            UINT64_C(0xfb20b10800c28488),
            UINT64_C(0xfb20b10800c28488),
        };
        const uint32_t sideband_mid[] = { 0x31, 0x21, 0x21, 0x21 };
        const uint32_t expected_src0[] = { 0, 0, 10, 10 };
        const uint32_t expected_src1[] = { 1, 1, 9, 9 };
        const uint32_t expected_src2[] = { 2, 2, 8, 8 };
        size_t i;

        for (i = 0; i < sizeof(emit_offsets) / sizeof(emit_offsets[0]);
             i++) {
            offset = emit_offsets[i];
            instruction = fixture_word(image, image_size, offset);
            memcpy(temp_before, temp, sizeof(temp));
            memcpy(valid_before, temp_valid, sizeof(temp_valid));
            CHECK(instruction == emit_words[i],
                  "captured EMIT instruction changed");
            CHECK(sgx_usse_decode_emit(instruction, &emit_fields),
                  "captured EMIT did not match the SGX544 table layout");
            CHECK(emit_fields.sideband_high == 0 && emit_fields.opcat == 2 &&
                  emit_fields.src0_bank_ext == 0 && emit_fields.end == 0 &&
                  emit_fields.src1_bank_ext == 0 &&
                  emit_fields.src2_bank_ext == 0 && emit_fields.target == 2 &&
                  emit_fields.task_start_or_mte_hi == 1 &&
                  emit_fields.task_end_or_mte_lo == 1 &&
                  emit_fields.no_schedule == 0 &&
                  emit_fields.sideband_mid == sideband_mid[i] &&
                  emit_fields.src0_bank == 0 && emit_fields.incp == 0 &&
                  emit_fields.src1_bank == 0 && emit_fields.src2_bank == 0 &&
                  emit_fields.sideband_low == 3 && emit_fields.freep == 0 &&
                  emit_fields.src0 == expected_src0[i] &&
                  emit_fields.src1 == expected_src1[i] &&
                  emit_fields.src2 == expected_src2[i],
                  "captured EMIT fields differ from the published table");
            CHECK(memcmp(temp_before, temp, sizeof(temp)) == 0 &&
                  memcmp(valid_before, temp_valid, sizeof(temp_valid)) == 0,
                  "EMIT field decode changed TEMP state");
            printf("%08zx: EMIT field-candidate target=%u "
                   "task-start-or-mte-hi=%u task-end-or-mte-lo=%u "
                   "sideband=%u:%#x:%#x src0=%u/%u:%u src1=%u/%u:%u "
                   "src2=%u/%u:%u effects=unmodeled state=unchanged\n",
                   offset, emit_fields.target,
                   emit_fields.task_start_or_mte_hi,
                   emit_fields.task_end_or_mte_lo,
                   emit_fields.sideband_high, emit_fields.sideband_mid,
                   emit_fields.sideband_low, emit_fields.src0_bank_ext,
                   emit_fields.src0_bank, emit_fields.src0,
                   emit_fields.src1_bank_ext, emit_fields.src1_bank,
                   emit_fields.src1, emit_fields.src2_bank_ext,
                   emit_fields.src2_bank, emit_fields.src2);
        }
    }

    /* Decode later branch words as candidates without mutating any registers. */
    {
        const size_t branches[] = { 0x1fc8, 0x43b8 };
        const uint32_t expected_offsets[] = { 0x47e, 0x258d };
        size_t i;

        for (i = 0; i < sizeof(branches) / sizeof(branches[0]); i++) {
            offset = branches[i];
            instruction = fixture_word(image, image_size, offset);
            memcpy(temp_before, temp, sizeof(temp));
            memcpy(valid_before, temp_valid, sizeof(temp_valid));
            result = sgx_usse_step_prefix(instruction, temp, temp_valid,
                                          &fields);
            CHECK(result == SGX_USSE_PREFIX_STOP_UNRESOLVED_BRANCH,
                  "branch candidate was not left unresolved");
            CHECK(fields.branch.offset20 == expected_offsets[i],
                  "branch field extraction lost high offset bits");
            CHECK(memcmp(temp_before, temp, sizeof(temp)) == 0 &&
                  memcmp(valid_before, temp_valid, sizeof(temp_valid)) == 0,
                  "unresolved branch changed TEMP state");
            printf("%08zx: BR candidate save-link=%u offset20=%#x "
                   "low12=%#x state=unchanged\n",
                   offset, fields.branch.save_link, fields.branch.offset20,
                   fields.branch.offset20 & 0xfff);
        }
    }

    instruction = UINT64_C(0x123456789abcdef0);
    memcpy(temp_before, temp, sizeof(temp));
    memcpy(valid_before, temp_valid, sizeof(temp_valid));
    result = sgx_usse_step_prefix(instruction, temp, temp_valid, &fields);
    CHECK(result == SGX_USSE_PREFIX_NOT_HANDLED,
          "unknown instruction was treated as supported");
    CHECK(memcmp(temp_before, temp, sizeof(temp)) == 0 &&
          memcmp(valid_before, temp_valid, sizeof(temp_valid)) == 0,
          "unknown instruction changed TEMP state");

    free(image);
    printf("fixture replay passed: four prefix effects, VLDST/BR stop, VBW "
           "candidate, EMIT fields, unknown input unchanged\n");
    return 0;
}

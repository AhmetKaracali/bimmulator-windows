// Emits candidate graphics-stage SPIR-V wrappers around finalized BMW USSE.
// Native attribute/sampler/output bindings remain explicit candidates.
#include <shader/usse_translator.h>
#include <filesystem>
#include <fstream>
#include <iostream>

static std::vector<uint8_t> readBytes(const std::filesystem::path &path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("Cannot read " + path.string());
    return {std::istreambuf_iterator<char>(in), {}};
}

static uint16_t readU16(const std::vector<uint8_t> &bytes, size_t offset) {
    if (offset + 2 > bytes.size()) throw std::runtime_error("Truncated native descriptor");
    return bytes[offset] | (uint16_t(bytes[offset + 1]) << 8);
}

static std::vector<uint64_t> readCode(const std::filesystem::path &path, size_t count) {
    auto bytes = readBytes(path);
    if (bytes.size() != count * 8) throw std::runtime_error("Code length disagrees with descriptor");
    std::vector<uint64_t> words(count);
    for (size_t i = 0; i < bytes.size(); ++i) words[i / 8] |= uint64_t(bytes[i]) << (8 * (i % 8));
    return words;
}

static spv::Id access(spv::Builder &builder, spv::StorageClass storage,
                      spv::Id variable, std::initializer_list<spv::Id> indexes) {
    if (variable == spv::NoResult) throw std::runtime_error("Access chain received an unset variable id");
    return shader::usse::utils::create_access_chain(
        builder, storage, variable, std::vector<spv::Id>(indexes));
}

static spv::Id zeroArray(spv::Builder &builder, spv::Id element_type,
                         spv::Id zero_element, uint32_t count, const char *name) {
    auto array_type = builder.makeArrayType(element_type, builder.makeUintConstant(count), 0);
    std::vector<spv::Id> values(count, zero_element);
    auto initializer = builder.makeCompositeConstant(array_type, values);
    return builder.createVariable(spv::NoPrecision, spv::StorageClassPrivate,
                                  array_type, name, initializer);
}

static void emitModule(const std::filesystem::path &fixture, const std::string &stage,
                       const std::filesystem::path &output,
                       bool native_register_interface) {
    const bool is_mat_pad_bg = stage == "fragment" &&
        fixture.filename() == "726bf332014cfe9a";
    const auto prefix = fixture / stage;
    auto final = readBytes(prefix.string() + ".final.bin");
    if (final.size() < 0xa4) throw std::runtime_error("Truncated native descriptor");
    auto primary = readCode(prefix.string() + ".primary.usse.bin", readU16(final, 0x0c));
    auto secondary = readCode(prefix.string() + ".secondary.usse.bin", readU16(final, 0x1c));
    if (primary.size() < 2 || readU16(final, 0x14) != 0 || primary[0] != 0)
        throw std::runtime_error("Unmapped native phase layout; leading placeholder is not verified");

    spv::SpvBuildLogger logger;
    spv::Builder builder(spv::Spv_1_0, 0, &logger);
    builder.setMemoryModel(spv::AddressingModelLogical, spv::MemoryModelGLSL450);
    builder.addCapability(spv::CapabilityShader);
    shader::usse::utils::SpirvUtilFunctions utils;
    utils.std_builtins = builder.import("GLSL.std.450");
    const auto execution_model = stage == "vertex" ? spv::ExecutionModelVertex : spv::ExecutionModelFragment;
    auto main = builder.makeEntryPoint("main");
    auto *entry_point = builder.addEntryPoint(execution_model, main, "main");
    if (stage == "fragment") builder.addExecutionMode(main, spv::ExecutionModeOriginUpperLeft);

    auto f32 = builder.makeFloatType(32);
    auto u32 = builder.makeUintType(32);
    auto i32 = builder.makeIntType(32);
    auto vec2 = builder.makeVectorType(f32, 2);
    auto vec4 = builder.makeVectorType(f32, 4);
    auto zero = builder.makeFloatConstant(0.0f);
    auto zero4 = builder.makeCompositeConstant(vec4, {zero, zero, zero, zero});

    // The host-side uniform file is exactly 32 vec4 values: the fragment or
    // vertex secondary-attribute bank in the compute harness's register order.
    auto uniforms_array = builder.makeArrayType(vec4, builder.makeUintConstant(32), 16);
    builder.addDecoration(uniforms_array, spv::DecorationArrayStride, 16);
    auto uniforms_block = builder.makeStructType({uniforms_array}, "BMWSecondaryAttributes");
    builder.addDecoration(uniforms_block, spv::DecorationBlock);
    builder.addMemberDecoration(uniforms_block, 0, spv::DecorationOffset, 0);
    auto uniforms_buffer = builder.createVariable(spv::NoPrecision, spv::StorageClassUniform,
        uniforms_block, "secondary_attributes");
    if (uniforms_buffer == spv::NoResult) throw std::runtime_error("Could not create SA uniform descriptor variable");
    builder.addDecoration(uniforms_buffer, spv::DecorationDescriptorSet, 0);
    // Vertex and fragment secondary-attribute banks are independent in GXM.
    // The host harness mirrors that separation with set 0 bindings 0 and 2.
    builder.addDecoration(uniforms_buffer, spv::DecorationBinding, stage == "vertex" ? 0 : 2);

    spv::Id position_input = 0, uv_input = 0, position_output = 0;
    spv::Id uv_output = 0, texture_sampler = 0, texture_sampler_rse = 0,
            color_output = 0;
    std::vector<spv::Id> native_attribute_inputs;
    std::vector<spv::Id> native_varying_outputs;
    if (stage == "vertex") {
        if (native_register_interface) {
            // This interface exposes the register banks to a later ESSL
            // adapter. It deliberately does not guess BMW attribute names or
            // varyings; those come from each exact .shd symbol table.
            for (unsigned i = 0; i < 16; ++i) {
                const auto name = "attribute_register_" + std::to_string(i);
                const auto input = builder.createVariable(
                    spv::NoPrecision, spv::StorageClassInput, vec4, name.c_str());
                builder.addDecoration(input, spv::DecorationLocation, i);
                entry_point->addIdOperand(input);
                native_attribute_inputs.push_back(input);
            }
        } else {
            position_input = builder.createVariable(spv::NoPrecision, spv::StorageClassInput, vec4, "a_Position_candidate");
            builder.addDecoration(position_input, spv::DecorationLocation, 0);
            uv_input = builder.createVariable(spv::NoPrecision, spv::StorageClassInput, vec2, "a_TextureCoordinate_candidate");
            builder.addDecoration(uv_input, spv::DecorationLocation, 1);
            entry_point->addIdOperand(position_input);
            entry_point->addIdOperand(uv_input);
        }
        position_output = builder.createVariable(spv::NoPrecision, spv::StorageClassOutput, vec4, "gl_Position_candidate");
        builder.addDecoration(position_output, spv::DecorationBuiltIn, spv::BuiltInPosition);
        entry_point->addIdOperand(position_output);
        if (native_register_interface) {
            for (unsigned i = 1; i < 16; ++i) {
                const auto name = "output_register_" + std::to_string(i);
                const auto output_variable = builder.createVariable(
                    spv::NoPrecision, spv::StorageClassOutput, vec4, name.c_str());
                builder.addDecoration(output_variable, spv::DecorationLocation, i - 1);
                entry_point->addIdOperand(output_variable);
                native_varying_outputs.push_back(output_variable);
            }
        } else {
            uv_output = builder.createVariable(spv::NoPrecision, spv::StorageClassOutput, vec2, "varCoord_candidate");
            builder.addDecoration(uv_output, spv::DecorationLocation, 0);
            entry_point->addIdOperand(uv_output);
        }
    } else {
        uv_input = builder.createVariable(spv::NoPrecision, spv::StorageClassInput, vec2, "varCoord_candidate");
        builder.addDecoration(uv_input, spv::DecorationLocation, 0);
        color_output = builder.createVariable(spv::NoPrecision, spv::StorageClassOutput, vec4, "gl_FragColor_candidate");
        builder.addDecoration(color_output, spv::DecorationLocation, 0);
        auto image_type = builder.makeImageType(f32, spv::Dim2D, false, false, false, 1, spv::ImageFormatUnknown);
        auto sampled_image_type = builder.makeSampledImageType(image_type);
        texture_sampler = builder.createVariable(spv::NoPrecision, spv::StorageClassUniformConstant,
            sampled_image_type, is_mat_pad_bg ? "t" : "tex0_candidate");
        builder.addDecoration(texture_sampler, spv::DecorationDescriptorSet, 0);
        builder.addDecoration(texture_sampler, spv::DecorationBinding, 1);
        if (is_mat_pad_bg) {
            // mat_pad_bg has two native sampler symbols and exact SMP source
            // keys 10/14. Keep both as separate uniforms so the HMI's t and
            // t_rse assignments survive the ESSL adapter.
            texture_sampler_rse = builder.createVariable(
                spv::NoPrecision, spv::StorageClassUniformConstant,
                sampled_image_type, "t_rse");
            builder.addDecoration(texture_sampler_rse, spv::DecorationDescriptorSet, 0);
            builder.addDecoration(texture_sampler_rse, spv::DecorationBinding, 2);
        }
        entry_point->addIdOperand(uv_input);
        entry_point->addIdOperand(color_output);
    }

    struct Bank { spv::Id *id; const char *name; uint32_t size; };
    shader::usse::SpirvShaderParameters parameters{};
    Bank banks[] = {{&parameters.ins, "pa", 32}, {&parameters.uniforms, "sa", 32},
                    {&parameters.temps, "temp", 32}, {&parameters.internals, "internal", 4},
                    {&parameters.outs, "output", 32}};
    for (auto &bank : banks) {
        *bank.id = zeroArray(builder, vec4, zero4, bank.size, bank.name);
        if (*bank.id == spv::NoResult) throw std::runtime_error(std::string("Could not create register bank ") + bank.name);
    }
    if (stage == "fragment") {
        // mat_subline.frag.shd's captured SMP word e001c404e0000300 encodes
        // src1_n=6 in sampler bank 3. The pinned Vita3K decoder doubles
        // sampler registers, so its SamplerMap key is 12. Its exact .shd
        // declares one sampler symbol (t), mapped here to the wrapper's only
        // candidate texture descriptor. This does not infer other HMI
        // sampler indices or texture formats.
        if (is_mat_pad_bg) {
            parameters.samplers.emplace(10u, shader::usse::SamplerInfo{
                texture_sampler, 0u, shader::usse::DataType::F32, 4u, false});
            parameters.samplers.emplace(14u, shader::usse::SamplerInfo{
                texture_sampler_rse, 0u, shader::usse::DataType::F32, 4u, false});
        } else {
            parameters.samplers.emplace(12u, shader::usse::SamplerInfo{
                texture_sampler, 0u, shader::usse::DataType::F32, 4u, false});
        }
    }
    parameters.indexes = zeroArray(builder, i32, builder.makeIntConstant(0), 4, "index");
    parameters.predicates = zeroArray(builder, builder.makeBoolType(), builder.makeBoolConstant(false), 4, "predicate");

    // Candidate stage interface: vertex PA0=UV, PA1=position; fragment PA0.y
    // receives the selected sampled component. These bindings are experiments,
    // not recovered native attribute or SGX sampler contracts.
    if (stage == "vertex") {
        if (native_register_interface) {
            for (unsigned i = 0; i < native_attribute_inputs.size(); ++i) {
                const auto destination = access(
                    builder, spv::StorageClassPrivate, parameters.ins,
                    {builder.makeIntConstant(static_cast<int>(i))});
                builder.createStore(
                    builder.createLoad(native_attribute_inputs[i], spv::NoPrecision),
                    destination);
            }
        } else {
            auto uv = builder.createLoad(uv_input, spv::NoPrecision);
            auto u = builder.createCompositeExtract(uv, f32, 0);
            auto v = builder.createCompositeExtract(uv, f32, 1);
            builder.createStore(builder.createCompositeConstruct(vec4, {u, v, zero, zero}),
                                access(builder, spv::StorageClassPrivate, parameters.ins, {builder.makeIntConstant(0)}));
            builder.createStore(builder.createLoad(position_input, spv::NoPrecision),
                                access(builder, spv::StorageClassPrivate, parameters.ins, {builder.makeIntConstant(1)}));
        }
    } else {
        auto image = builder.createLoad(texture_sampler, spv::NoPrecision);
        spv::Builder::TextureParameters texture{};
        texture.sampler = image;
        texture.coords = builder.createLoad(uv_input, spv::NoPrecision);
        auto sampled = builder.createTextureCall(spv::NoPrecision, vec4, false, false, false, false,
                                                  false, texture, spv::ImageOperandsMaskNone);
        builder.createStore(sampled,
                            access(builder, spv::StorageClassPrivate, parameters.ins, {builder.makeIntConstant(0)}));
    }

    // Load all 32 SA vectors from the UBO using the native harness bank layout.
    for (int i = 0; i < 32; ++i) {
        auto from = access(builder, spv::StorageClassUniform, uniforms_buffer,
                           {builder.makeIntConstant(0), builder.makeIntConstant(i)});
        auto to = access(builder, spv::StorageClassPrivate, parameters.uniforms,
                         {builder.makeIntConstant(i)});
        builder.createStore(builder.createLoad(from, spv::NoPrecision), to);
    }

    auto main_block = builder.getBuildPoint();
    spv::Block *end_block = nullptr;
    auto end = builder.makeFunctionEntry(spv::NoPrecision, builder.makeVoidType(), "end", {}, {}, {}, &end_block);
    builder.leaveFunction();
    builder.setBuildPoint(main_block);
    SceGxmProgram program{};
    FeatureState features{};
    shader::usse::NonDependentTextureQueryCallInfos queries;
    shader::usse::USSERecompiler recomp(builder, program, features, parameters, utils, end, queries, 0);
    if (!secondary.empty()) {
        recomp.visitor.set_secondary_program(true);
        recomp.reset(secondary.data(), secondary.size());
        builder.createFunctionCall(recomp.compile_program_function(), {});
    }
    recomp.visitor.set_secondary_program(false);
    recomp.reset(primary.data() + 1, primary.size() - 1);
    builder.createFunctionCall(recomp.compile_program_function(), {});

    if (stage == "vertex") {
        auto position = builder.createLoad(access(builder, spv::StorageClassPrivate,
            parameters.outs, {builder.makeIntConstant(0)}), spv::NoPrecision);
        builder.createStore(position, position_output);
        if (native_register_interface) {
            for (unsigned i = 1; i < native_varying_outputs.size() + 1; ++i) {
                const auto value = builder.createLoad(access(
                    builder, spv::StorageClassPrivate, parameters.outs,
                    {builder.makeIntConstant(static_cast<int>(i))}), spv::NoPrecision);
                builder.createStore(value, native_varying_outputs[i - 1]);
            }
        } else {
            auto uv4 = builder.createLoad(access(builder, spv::StorageClassPrivate,
                parameters.outs, {builder.makeIntConstant(1)}), spv::NoPrecision);
            auto u = builder.createCompositeExtract(uv4, f32, 0);
            auto v = builder.createCompositeExtract(uv4, f32, 1);
            builder.createStore(builder.createCompositeConstruct(vec2, {u, v}), uv_output);
        }
    } else {
        auto packed = builder.createLoad(access(builder, spv::StorageClassPrivate,
            parameters.outs, {builder.makeIntConstant(0)}), spv::NoPrecision);
        auto packed_scalar = builder.createCompositeExtract(packed, f32, 0);
        auto packed_u32 = builder.createUnaryOp(spv::OpBitcast, u32, packed_scalar);
        auto byte_at = [&](unsigned shift) {
            auto shifted = builder.createBinOp(spv::OpShiftRightLogical, u32,
                packed_u32, builder.makeUintConstant(shift));
            auto byte = builder.createBinOp(spv::OpBitwiseAnd, u32, shifted, builder.makeUintConstant(255));
            auto as_float = builder.createUnaryOp(spv::OpConvertUToF, f32, byte);
            return builder.createBinOp(spv::OpFDiv, f32, as_float, builder.makeFloatConstant(255.0f));
        };
        // Candidate byte order: packed LSB -> R, then G, B, MSB -> A.
        // VPCKU8F16 packs the source components into successive low-to-high
        // bytes. Mapping those bytes to RGBA follows the observed little-endian
        // RGBA8 host/Screen path; the native IMG output lane is still unverified.
        auto color = builder.createCompositeConstruct(vec4,
            {byte_at(0), byte_at(8), byte_at(16), byte_at(24)});
        builder.createStore(color, color_output);
    }
    builder.leaveFunction();

    std::vector<unsigned> words;
    builder.dump(words);
    if (!logger.getAllMessages().empty()) throw std::runtime_error(logger.getAllMessages());
    std::ofstream out(output, std::ios::binary);
    out.write(reinterpret_cast<const char *>(words.data()), words.size() * 4);
    if (!out) throw std::runtime_error("Cannot write SPIR-V");
    std::cout << "Emitted candidate " << stage << " graphics stage: "
              << primary.size() - 1 << " primary + " << secondary.size()
              << " secondary slots, full RGBA sampled result; native linkage and packing remain unproven\n";
}

int main(int argc, char **argv) try {
    if (argc < 4 || argc > 5)
        throw std::runtime_error("Usage: idrive-usse-graphics FIXTURE_DIR vertex|fragment OUTPUT.spv [--native-register-interface]");
    std::string stage = argv[2];
    if (stage != "vertex" && stage != "fragment") throw std::runtime_error("Unknown shader stage");
    const bool native_register_interface = argc == 5 &&
        std::string(argv[4]) == "--native-register-interface";
    if (native_register_interface && stage != "vertex")
        throw std::runtime_error("--native-register-interface is supported for vertex stage only");
    if (argc == 5 && !native_register_interface)
        throw std::runtime_error("Unknown optional interface argument");
    emitModule(argv[1], stage, argv[3], native_register_interface);
} catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
}


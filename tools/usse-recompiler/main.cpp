// Computational feasibility harness, not an EGL/GLES provider or renderer.
// Recompiles genuine finalized arithmetic via Vita3K's existing USSE visitor.
#include <shader/usse_translator.h>
#include <fstream>
#include <iostream>
#include <filesystem>

static std::vector<uint8_t> bytes(const std::filesystem::path &path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) throw std::runtime_error("Cannot read " + path.string());
    return {std::istreambuf_iterator<char>(f), {}};
}
static uint16_t u16(const std::vector<uint8_t> &b, size_t off) {
    if (off + 2 > b.size()) throw std::runtime_error("Truncated descriptor");
    return b[off] | (uint16_t(b[off+1]) << 8);
}
static std::vector<uint64_t> code(const std::filesystem::path &path, size_t count) {
    auto b = bytes(path);
    if (b.size() != count * 8) throw std::runtime_error("Code length disagrees with descriptor");
    std::vector<uint64_t> words(count);
    for (size_t i=0;i<b.size();i++) words[i/8] |= uint64_t(b[i]) << (8*(i%8));
    return words;
}

int main(int argc, char **argv) try {
    if (argc != 4) throw std::runtime_error("Usage: idrive-usse-recompile EXTRACTED_DIR vertex|fragment OUTPUT.spv");
    std::string stage=argv[2];
    if (stage!="vertex" && stage!="fragment") throw std::runtime_error("Unknown stage");
    std::filesystem::path prefix=std::filesystem::path(argv[1])/stage;
    auto final=bytes(prefix.string()+".final.bin");
    if(final.size()<0xa4) throw std::runtime_error("Truncated native descriptor");
    auto primary=code(prefix.string()+".primary.usse.bin",u16(final,0x0c));
    auto secondary=code(prefix.string()+".secondary.usse.bin",u16(final,0x1c));
    // Supported control fixture: the driver patches slot zero to scheduling
    // glue. Do not silently classify that zero placeholder as arithmetic.
    if(primary.size()<2 || u16(final,0x14)!=0 || primary[0]!=0)
        throw std::runtime_error("Unmapped native phase layout; only the verified leading placeholder is supported");

    spv::SpvBuildLogger logger;
    spv::Builder b(spv::Spv_1_0, 0, &logger);
    b.setMemoryModel(spv::AddressingModelLogical,spv::MemoryModelGLSL450);
    b.addCapability(spv::CapabilityShader);
    shader::usse::utils::SpirvUtilFunctions utils;
    utils.std_builtins=b.import("GLSL.std.450");
    auto main=b.makeEntryPoint("main");
    b.addEntryPoint(spv::ExecutionModelGLCompute,main,"main");
    b.addExecutionMode(main,spv::ExecutionModeLocalSize,1,1,1);
    auto f32=b.makeFloatType(32), vec4=b.makeVectorType(f32,4);
    auto state_array=b.makeArrayType(vec4,b.makeUintConstant(132),16);
    b.addDecoration(state_array,spv::DecorationArrayStride,16);
    auto state_type=b.makeStructType({state_array},"RegisterState");
    b.addDecoration(state_type,spv::DecorationBufferBlock);
    b.addMemberDecoration(state_type,0,spv::DecorationOffset,0);
    auto state=b.createVariable(spv::NoPrecision,spv::StorageClassUniform,state_type,"state");
    b.addDecoration(state,spv::DecorationBinding,0);
    b.addDecoration(state,spv::DecorationDescriptorSet,0);

    shader::usse::SpirvShaderParameters p{};
    struct Bank {spv::Id *id;const char *name;int size;};
    Bank banks[]={{&p.ins,"pa",32},{&p.uniforms,"sa",32},{&p.temps,"temp",32},
                  {&p.internals,"internal",4},{&p.outs,"output",32}};
    int offset=0;
    auto access=[&](spv::StorageClass sc,spv::Id v,std::vector<spv::Id> indexes){
        return shader::usse::utils::create_access_chain(b,sc,v,indexes);
    };
    for(auto &bank:banks) {
        auto type=b.makeArrayType(vec4,b.makeUintConstant(bank.size),0);
        *bank.id=b.createVariable(spv::NoPrecision,spv::StorageClassPrivate,type,bank.name);
        for(int i=0;i<bank.size;i++) {
            auto from=access(spv::StorageClassUniform,state,{b.makeIntConstant(0),b.makeIntConstant(offset+i)});
            auto to=access(spv::StorageClassPrivate,*bank.id,{b.makeIntConstant(i)});
            b.createStore(b.createLoad(from,spv::NoPrecision),to);
        }
        offset+=bank.size;
    }
    auto make_zero_bank=[&](spv::Id type,spv::Id zero,const char *name) {
        auto arr=b.makeArrayType(type,b.makeUintConstant(4),0);
        return b.createVariable(spv::NoPrecision,spv::StorageClassPrivate,arr,name,
                                b.makeCompositeConstant(arr,{zero,zero,zero,zero}));
    };
    p.indexes=make_zero_bank(b.makeIntType(32),b.makeIntConstant(0),"index");
    p.predicates=make_zero_bank(b.makeBoolType(),b.makeBoolConstant(false),"predicate");
    auto main_block=b.getBuildPoint();
    spv::Block *end_block=nullptr;
    auto end=b.makeFunctionEntry(spv::NoPrecision,b.makeVoidType(),"end",{},{},{},&end_block);
    b.leaveFunction(); b.setBuildPoint(main_block);
    SceGxmProgram program{}; // No GXP input, texture metadata or literals used by this harness.
    FeatureState features{};
    shader::usse::NonDependentTextureQueryCallInfos queries;
    shader::usse::USSERecompiler recomp(b,program,features,p,utils,end,queries,0);
    if(!secondary.empty()) {
        recomp.visitor.set_secondary_program(true);
        recomp.reset(secondary.data(),secondary.size());
        b.createFunctionCall(recomp.compile_program_function(),{});
    }
    recomp.visitor.set_secondary_program(false);
    recomp.reset(primary.data()+1,primary.size()-1);
    b.createFunctionCall(recomp.compile_program_function(),{});
    offset=0;
    for(auto &bank:banks) {
        for(int i=0;i<bank.size;i++) {
            auto from=access(spv::StorageClassPrivate,*bank.id,{b.makeIntConstant(i)});
            auto to=access(spv::StorageClassUniform,state,{b.makeIntConstant(0),b.makeIntConstant(offset+i)});
            b.createStore(b.createLoad(from,spv::NoPrecision),to);
        }
        offset+=bank.size;
    }
    b.leaveFunction();
    std::vector<unsigned> spirv; b.dump(spirv);
    if(!logger.getAllMessages().empty()) throw std::runtime_error(logger.getAllMessages());
    std::ofstream out(argv[3],std::ios::binary);
    out.write(reinterpret_cast<const char*>(spirv.data()),spirv.size()*4);
    if(!out) throw std::runtime_error("Cannot write SPIR-V");
    std::cout<<"Translated "<<stage<<": "<<primary.size()-1<<" primary + "<<secondary.size()<<" secondary slots; "<<spirv.size()*4<<" SPIR-V bytes\n";
} catch(const std::exception &e) {std::cerr<<e.what()<<'\n';return 1;}

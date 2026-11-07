#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: c4324ac0edffdf3b4af3ed532c8fe071793fd7a253319bf3069814ab211b9991
// Candidate module sha256: 914edba0a6a897e57cee085497731bb7e5fd0584c8100b248989af31abed86ef
// Native input table sha256: 16034715ad68ad87037e9e5fc1b795d5e7fd56ac07d8131cc805ebf7bf13b103
// Constant-copy table sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Native shader has no sampler symbol; no sample is injected.
in highp vec3 fd;
in highp vec4 shd;
precision mediump float;
precision highp int;

const vec4 _34[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 sa[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 temp[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 _output[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));

highp vec2 unpack2xF16(highp float _198)
{
    return unpackHalf2x16(floatBitsToUint(_198));
}

highp float pack2xF16(highp vec2 _232)
{
    return uintBitsToFloat(packHalf2x16(_232));
}

highp float pack4xU8(uvec4 _520)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_520.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_520.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_520.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_520.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _204 = unpack2xF16(pa[0].x);
    highp vec2 _215 = vec2(pa[0].x, pa[0].y);
    highp vec2 _223 = (vec2(0.0) - vec2(_204.x, _204.x)) + vec2(unpack2xF16(_215.x).y, unpack2xF16(_215.y).x);
    highp vec2 _247 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x, _223.x)), pack2xF16(vec2(_223.y, unpack2xF16(pa[0].y).y)));
    pa[0] = vec4(_247.x, _247.y, pa[0].z, pa[0].w);
    highp vec2 _269 = unpack2xF16(pa[0].y);
    highp vec2 _274 = vec2(pack2xF16(vec2(1.0 / unpack2xF16(pa[0].x).y, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_269.x, _269.y)));
    pa[0] = vec4(_274.x, _274.y, pa[0].z, pa[0].w);
    highp vec2 _303 = unpack2xF16(pa[0].y);
    highp vec2 _308 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[0].y).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_303.x, _303.y)));
    pa[0] = vec4(_308.x, _308.y, pa[0].z, pa[0].w);
    highp vec2 _330 = unpack2xF16(pa[0].y);
    highp vec2 _335 = vec2(pack2xF16(vec2(max(unpack2xF16(pa[0].x).x, 0.0), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_330.x, _330.y)));
    pa[0] = vec4(_335.x, _335.y, pa[0].z, pa[0].w);
    highp vec2 _357 = unpack2xF16(pa[0].y);
    highp vec2 _362 = vec2(pack2xF16(vec2(min(unpack2xF16(pa[0].x).x, 1.0), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_357.x, _357.y)));
    pa[0] = vec4(_362.x, _362.y, pa[0].z, pa[0].w);
    highp vec2 _371 = unpack2xF16(pa[0].x);
    highp vec2 _376 = vec2(0.0) - vec2(2.0);
    highp vec2 _379 = vec2(_371.x, _371.x) * _376 + vec2(3.0);
    highp vec2 _387 = unpack2xF16(temp[0].y);
    highp vec2 _392 = vec2(pack2xF16(vec2(_379.x, _379.y)), pack2xF16(vec2(_387.x, _387.y)));
    temp[0] = vec4(_392.x, _392.y, temp[0].z, temp[0].w);
    highp vec2 _421 = unpack2xF16(pa[0].y);
    highp vec2 _426 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_421.x, _421.y)));
    pa[0] = vec4(_426.x, _426.y, pa[0].z, pa[0].w);
    highp vec2 _455 = unpack2xF16(pa[0].y);
    highp vec2 _460 = vec2(pack2xF16(vec2(unpack2xF16(temp[0].x).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_455.x, _455.y)));
    pa[0] = vec4(_460.x, _460.y, pa[0].z, pa[0].w);
    highp vec4 _488 = pa[0];
    _488.w = pack2xF16(vec2(unpack2xF16(pa[0].w).x, unpack2xF16(pa[0].w).y * unpack2xF16(pa[0].x).x));
    pa[0] = _488;
    highp vec2 _495 = vec2(pa[0].z, pa[0].w);
    highp vec2 _497 = unpack2xF16(_495.x);
    highp vec2 _499 = unpack2xF16(_495.y);
    uvec4 _513 = uvec4(round(clamp(vec4(_497.x, _497.y, _499.x, _499.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _537 = _output[0];
    _537.x = pack4xU8(uvec4(_513.x, _513.y, _513.z, _513.w));
    _output[0] = _537;
}

void main()
{
    pa[1].x = fd.x;
    pa[1].y = fd.y;
    pa[1].z = fd.z;
    pa[0].x = shd.x;
    pa[0].y = shd.y;
    pa[0].z = shd.z;
    pa[0].w = shd.w;
    primary_program();
    uint _542 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_542 >> 0u) & 255u) / 255.0, float((_542 >> 8u) & 255u) / 255.0, float((_542 >> 16u) & 255u) / 255.0, float((_542 >> 24u) & 255u) / 255.0);
}

#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 94607d87c4120580a4b7f51328c66c25cf759e884ebe69e252ee2c700fef343b
// Candidate module sha256: 4aab9a2d1774f52bd57e77d369186bcb438096a0e3b9845fb4a842b9e022fa0a
// Native input table sha256: e2f0ef87e5b44b3ce59858ccce4064dc914fc052748ff39d3a7270a5991c39cb
// Constant-copy table sha256: bfc7d9458c8811be75cb3490640b96ad7195b67442e290fa08f6436d79ee4f9c
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Host interface adapter: cm is encoded as packed F16 varying words.
// Native shader has no sampler symbol; no sample is injected.
in highp vec3 cm;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _27[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const vec4 _34[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = _27;
highp vec4 sa[32] = _27;
highp vec4 _output[32] = _27;

highp vec2 unpack2xF16(highp float _198)
{
    return unpackHalf2x16(floatBitsToUint(_198));
}

uvec4 unpack4xU8(highp float _216)
{
    uint _219 = floatBitsToUint(_216);
    return uvec4((((_219) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_219) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_219) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_219) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _236)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_236.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_236.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_236.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_236.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void secondary_program()
{
    uvec4 _230 = unpack4xU8(sa[2].y);
    highp vec4 _252 = sa[2];
    _252.y = pack4xU8(uvec4(_230.x, _230.y, _230.z, uint(round(clamp(unpack2xF16(sa[2].y).y, 0.0, 1.0) * 255.0))));
    sa[2] = _252;
}

void primary_program()
{
    highp vec2 _262 = vec2(pa[0].x, pa[0].y);
    highp vec2 _264 = unpack2xF16(_262.x);
    uvec3 _278 = uvec3(round(clamp(vec3(_264.x, _264.y, unpack2xF16(_262.y).x), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _291 = pa[0];
    _291.x = pack4xU8(uvec4(_278.x, _278.y, _278.z, unpack4xU8(pa[0].x).w));
    pa[0] = _291;
    uvec4 _297 = unpack4xU8(pa[0].x);
    uvec4 _307 = unpack4xU8(sa[2].y);
    highp vec3 _337 = vec3(1.0) - vec3(0.0);
    highp float _338 = 1.0 - 0.0;
    uvec3 _351 = uvec3(round(clamp((_337 * (vec3(uvec3(_297.x, _297.y, _297.z)) / vec3(255.0))) + (vec3(0.0) * (vec3(uvec3(_307.x, _307.y, _307.z)) / vec3(255.0))), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _368 = _output[0];
    _368.x = pack4xU8(uvec4(_351.x, _351.y, _351.z, unpack4xU8(_output[0].x).w));
    _output[0] = _368;
    uvec4 _372 = unpack4xU8(_output[0].x);
    highp vec4 _380 = _output[0];
    _380.x = pack4xU8(uvec4(_372.x, _372.y, _372.z, uint(round(clamp((0.0 * (float(unpack4xU8(pa[0].x).w) / 255.0)) + (_338 * (float(unpack4xU8(sa[2].y).w) / 255.0)), 0.0, 1.0) * 255.0))));
    _output[0] = _380;
}

void main()
{
    pa[0].x = uintBitsToFloat(packHalf2x16(cm.xy));
    pa[0].y = uintBitsToFloat(packHalf2x16(vec2(cm.z, 0.0)));
    pa[0].z = 0.0;
    sa[2].y = uintBitsToFloat(0x3f800000u);
    secondary_program();
    primary_program();
    uint _385 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_385 >> 0u) & 255u) / 255.0, float((_385 >> 8u) & 255u) / 255.0, float((_385 >> 16u) & 255u) / 255.0, float((_385 >> 24u) & 255u) / 255.0);
}

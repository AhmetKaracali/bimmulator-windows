#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 6c12160f3c05b9e3987bc96bea23c024eeb65039d31edd4d583d172d946f24ae
// Candidate module sha256: a65a5c40423904c4a542502641739fb61bb4fea242ecb0d4735e5971d0afa052
// Native input table sha256: 76fe9a9254904d69b229fa365924cc49009a35cc2b0a77ca815abb1a811cba74
// Constant-copy table sha256: 9b844435caa57bcea771b81dd8165f9f0f05808f105ae365b1e033f5d8e6abc5
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t0 using UV uv at native base 0; lane mapping is unverified.
uniform highp float intensity;
uniform highp vec3 CO_HL;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _27[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const vec4 _34[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t0;
in highp vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = _27;
highp vec4 sa[32] = _27;
highp vec4 _output[32] = _27;

uvec4 unpack4xU8(highp float _249)
{
    uint _252 = floatBitsToUint(_249);
    return uvec4((((_252) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_252) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_252) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_252) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _267)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_267.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_267.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_267.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_267.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void secondary_program()
{
    highp vec4 _205 = sa[3];
    _205.x = sa[3].x * sa[3].y;
    sa[3] = _205;
    highp vec2 _227 = vec2(sa[2].z, sa[2].w);
    uvec3 _240 = uvec3(round(clamp(vec3(vec2(sa[2].x, sa[2].y).y, _227.x, _227.y), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _283 = sa[2];
    _283.y = pack4xU8(uvec4(_240.x, _240.y, _240.z, unpack4xU8(sa[2].y).w));
    sa[2] = _283;
}

void primary_program()
{
    highp vec4 _300 = pa[0];
    _300.z = sa[3].x * pa[0].y;
    pa[0] = _300;
    highp vec4 _311 = vec4(uvec4(0u));
    highp vec4 _315 = vec4(1.0) - vec4(0.0);
    uvec4 _325 = uvec4(round(clamp((_315 * (vec4(unpack4xU8(sa[2].y)) / vec4(255.0))) + (vec4(0.0) * (_311 / vec4(255.0))), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _338 = _output[0];
    _338.x = pack4xU8(uvec4(_325.x, _325.y, _325.z, unpack4xU8(_output[0].x).w));
    _output[0] = _338;
    uvec4 _351 = unpack4xU8(_output[0].x);
    highp vec4 _359 = _output[0];
    _359.x = pack4xU8(uvec4(_351.x, _351.y, _351.z, uint(round(clamp(pa[0].z, 0.0, 1.0) * 255.0))));
    _output[0] = _359;
}

void main()
{
pa[0] = texture(t0, uv);
    sa[2].y = CO_HL.x;
    sa[2].z = CO_HL.y;
    sa[2].w = CO_HL.z;
    sa[3].x = opacity;
    sa[3].y = intensity;
    secondary_program();
    primary_program();
    uint _364 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_364 >> 0u) & 255u) / 255.0, float((_364 >> 8u) & 255u) / 255.0, float((_364 >> 16u) & 255u) / 255.0, float((_364 >> 24u) & 255u) / 255.0);
}

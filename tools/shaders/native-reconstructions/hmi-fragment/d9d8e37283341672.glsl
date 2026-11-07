#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: d9d8e3728334167293b09859d596ef463cd8137e8f4f85958ba3a957355b269f
// Candidate module sha256: b2423c99ecc430e505b46c7603b12331c1bebe2ba2c213226b65414993535e27
// Native input table sha256: 76fe9a9254904d69b229fa365924cc49009a35cc2b0a77ca815abb1a811cba74
// Constant-copy table sha256: f709c9244697f85c9b2e1a726a84101e3836a787cac7d59899ddd1087688966b
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t0 using UV uv at native base 0; lane mapping is unverified.
uniform highp vec3 CO;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _27[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t0;
in highp vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = _27;
highp vec4 sa[32] = _27;
highp vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 _output[32] = _27;

highp float pack4xU8(uvec4 _277)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_277.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_277.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_277.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_277.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _213 = vec2(sa[2].z, sa[2].w);
    highp vec3 _217 = vec3(vec2(sa[2].x, sa[2].y).y, _213.x, _213.y);
    internal[0] = vec4(_217.x, _217.y, _217.z, internal[0].w);
    highp vec4 _228 = internal[0];
    _228.w = pa[0].z;
    internal[0] = _228;
    internal[0] += vec4(pa[0].y, pa[0].y, pa[0].y, pa[0].y);
    highp vec4 _257 = internal[0];
    _257.w = internal[0].w * sa[3].x;
    internal[0] = _257;
    uvec4 _270 = uvec4(round(clamp(internal[0], vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _294 = _output[0];
    _294.x = pack4xU8(uvec4(_270.x, _270.y, _270.z, _270.w));
    _output[0] = _294;
}

void main()
{
pa[0] = texture(t0, uv);
    sa[2].y = CO.x;
    sa[2].z = CO.y;
    sa[2].w = CO.z;
    sa[3].x = opacity;
    primary_program();
    uint _299 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_299 >> 0u) & 255u) / 255.0, float((_299 >> 8u) & 255u) / 255.0, float((_299 >> 16u) & 255u) / 255.0, float((_299 >> 24u) & 255u) / 255.0);
}

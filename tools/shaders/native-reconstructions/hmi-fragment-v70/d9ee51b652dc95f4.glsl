#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: d9ee51b652dc95f4bb5c41428a3e64013bc03ddb6157641d994c663c98329353
// Candidate module sha256: 7eae7f8b1667fad56c73a8af6c5fb3d07dde68067cd7c21be30adf488790866d
// Native input table sha256: 76fe9a9254904d69b229fa365924cc49009a35cc2b0a77ca815abb1a811cba74
// Constant-copy table sha256: f709c9244697f85c9b2e1a726a84101e3836a787cac7d59899ddd1087688966b
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t0 using UV uv at native base 0; lane mapping is unverified.
uniform highp vec3 CO;
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

uvec4 unpack4xU8(highp float _235)
{
    uint _238 = floatBitsToUint(_235);
    return uvec4((((_238) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_238) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_238) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_238) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _253)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_253.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_253.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_253.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_253.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void secondary_program()
{
    highp vec2 _213 = vec2(sa[2].z, sa[2].w);
    uvec3 _226 = uvec3(round(clamp(vec3(vec2(sa[2].x, sa[2].y).y, _213.x, _213.y), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _269 = sa[2];
    _269.y = pack4xU8(uvec4(_226.x, _226.y, _226.z, unpack4xU8(sa[2].y).w));
    sa[2] = _269;
}

void primary_program()
{
    highp vec4 _286 = pa[0];
    _286.z = pa[0].z * sa[3].x;
    pa[0] = _286;
    highp vec4 _297 = vec4(uvec4(0u));
    highp vec4 _301 = vec4(1.0) - vec4(0.0);
    uvec4 _311 = uvec4(round(clamp((_301 * (vec4(unpack4xU8(sa[2].y)) / vec4(255.0))) + (vec4(0.0) * (_297 / vec4(255.0))), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _324 = _output[0];
    _324.x = pack4xU8(uvec4(_311.x, _311.y, _311.z, unpack4xU8(_output[0].x).w));
    _output[0] = _324;
    uvec4 _337 = unpack4xU8(_output[0].x);
    highp vec4 _345 = _output[0];
    _345.x = pack4xU8(uvec4(_337.x, _337.y, _337.z, uint(round(clamp(pa[0].z, 0.0, 1.0) * 255.0))));
    _output[0] = _345;
}

void main()
{
pa[0] = texture(t0, uv);
    sa[2].y = CO.x;
    sa[2].z = CO.y;
    sa[2].w = CO.z;
    sa[3].x = opacity;
    secondary_program();
    primary_program();
    uint _350 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_350 >> 0u) & 255u) / 255.0, float((_350 >> 8u) & 255u) / 255.0, float((_350 >> 16u) & 255u) / 255.0, float((_350 >> 24u) & 255u) / 255.0);
}

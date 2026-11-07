#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 97c1c6620721dd924eb601633826d20b2575201e584978c57c88ef2924375ce1
// Candidate module sha256: 996173780ffb057c14e705be58e2e38472ee42d40066e2a7ad9c04032355e6d5
// Native input table sha256: 4d78ece692dc75bafda8f2a9534767b3dd2c99132bdc668d29871cf784902dea
// Constant-copy table sha256: e909a9b6fd004628835745f1c4c45648f5e0f9fa9078241861775ca81c24b05e
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t using UV uv at native base 0; lane mapping is unverified.
in highp float v_main_menu;
uniform highp vec3 CO;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _34[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t;
in highp vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 sa[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 temp[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 _output[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));

highp vec2 unpack2xF16(highp float _201)
{
    return unpackHalf2x16(floatBitsToUint(_201));
}

uvec4 unpack4xU8(highp float _231)
{
    uint _234 = floatBitsToUint(_231);
    return uvec4((((_234) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_234) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_234) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_234) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _249)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_249.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_249.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_249.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_249.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void secondary_program()
{
    highp vec2 _198 = vec2(sa[2].z, sa[2].w);
    highp vec2 _207 = unpack2xF16(_198.x);
    uvec3 _222 = uvec3(round(clamp(vec3(_207.x, _207.y, unpack2xF16(_198.y).x), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _265 = sa[2];
    _265.z = pack4xU8(uvec4(_222.x, _222.y, _222.z, unpack4xU8(sa[2].z).w));
    sa[2] = _265;
}

highp float pack2xF16(highp vec2 _301)
{
    return uintBitsToFloat(packHalf2x16(_301));
}

void primary_program()
{
    highp vec2 _274 = unpack2xF16(pa[0].z);
    highp vec2 _283 = unpack2xF16(pa[0].y);
    highp vec2 _292 = unpack2xF16(pa[0].x);
    highp vec2 _296 = vec2(_274.x, _274.x) * vec2(_283.x, _283.x) + vec2(_292.y, _292.y);
    highp vec2 _311 = unpack2xF16(temp[0].y);
    highp vec2 _316 = vec2(pack2xF16(vec2(_296.x, _296.y)), pack2xF16(vec2(_311.x, _311.y)));
    temp[0] = vec4(_316.x, _316.y, temp[0].z, temp[0].w);
    highp vec2 _325 = unpack2xF16(pa[0].x);
    highp vec2 _334 = unpack2xF16(pa[0].z);
    highp vec2 _344 = unpack2xF16(temp[0].x);
    highp vec2 _348 = vec2(_325.y, _325.y) * (vec2(0.0) - vec2(_334.x, _334.x)) + vec2(_344.x, _344.x);
    highp vec2 _356 = unpack2xF16(pa[0].y);
    highp vec2 _361 = vec2(pack2xF16(vec2(_348.x, _348.y)), pack2xF16(vec2(_356.x, _356.y)));
    pa[0] = vec4(_361.x, _361.y, pa[0].z, pa[0].w);
    highp vec2 _390 = unpack2xF16(pa[0].w);
    highp vec2 _395 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(sa[2].w).y, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_390.x, _390.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _395.x, _395.y);
    highp vec4 _409 = vec4(uvec4(0u));
    highp vec4 _413 = vec4(1.0) - vec4(0.0);
    uvec4 _423 = uvec4(round(clamp((_413 * (vec4(unpack4xU8(sa[2].z)) / vec4(255.0))) + (vec4(0.0) * (_409 / vec4(255.0))), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _436 = _output[0];
    _436.x = pack4xU8(uvec4(_423.x, _423.y, _423.z, unpack4xU8(_output[0].x).w));
    _output[0] = _436;
    uvec4 _451 = unpack4xU8(_output[0].x);
    highp vec4 _459 = _output[0];
    _459.x = pack4xU8(uvec4(_451.x, _451.y, _451.z, uint(round(clamp(unpack2xF16(pa[0].z).x, 0.0, 1.0) * 255.0))));
    _output[0] = _459;
}

void main()
{
pa[0] = texture(t, uv);
    pa[1].x = v_main_menu;
    sa[2].z = CO.x;
    sa[2].w = CO.z;
    secondary_program();
    primary_program();
    uint _464 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_464 >> 0u) & 255u) / 255.0, float((_464 >> 8u) & 255u) / 255.0, float((_464 >> 16u) & 255u) / 255.0, float((_464 >> 24u) & 255u) / 255.0);
}

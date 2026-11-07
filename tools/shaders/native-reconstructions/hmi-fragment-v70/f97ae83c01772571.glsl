#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: f97ae83c017725712d59e91955527bc37939f83621d75c1f96b9cdf4db70fd93
// Candidate module sha256: e9ee1ce87ce6368cb7d254bd2adc80f499b60c4a2c785f475685f5e631c49359
// Native input table sha256: 92bb06f0e0933822dddb5bb4ed9192d0eda14e377d5b64b6612f53692d96ac3d
// Constant-copy table sha256: 2a706559566620a9c3e90243e2863c17da5ca5fd93e2bb1aefcbddeb630456b8
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA1 from t0 using UV uv at native base 4; lane mapping is unverified.
in highp vec3 mc;
uniform highp float pressed;
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
    uvec4 _230 = unpack4xU8(sa[2].z);
    highp vec4 _252 = sa[2];
    _252.z = pack4xU8(uvec4(_230.x, _230.y, _230.z, uint(round(clamp(unpack2xF16(sa[2].z).x, 0.0, 1.0) * 255.0))));
    sa[2] = _252;
}

highp float pack2xF16(highp vec2 _278)
{
    return uintBitsToFloat(packHalf2x16(_278));
}

void primary_program()
{
    highp vec2 _288 = unpack2xF16(pa[0].w);
    highp vec2 _293 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].w).x + unpack2xF16(sa[2].y).y, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_288.x, _288.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _293.x, _293.y);
    highp vec2 _302 = unpack2xF16(pa[0].w);
    highp vec2 _311 = unpack2xF16(sa[2].y);
    highp vec2 _321 = unpack2xF16(pa[0].z);
    highp vec2 _325 = vec2(_302.x, _302.x) * (vec2(0.0) - vec2(_311.y, _311.y)) + vec2(_321.x, _321.x);
    highp vec2 _333 = unpack2xF16(pa[0].w);
    highp vec2 _338 = vec2(pack2xF16(vec2(_325.x, _325.y)), pack2xF16(vec2(_333.x, _333.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _338.x, _338.y);
    highp vec2 _348 = vec2(pa[0].x, pa[0].y);
    highp vec2 _350 = unpack2xF16(_348.x);
    highp vec2 _362 = unpack2xF16(pa[0].z);
    highp vec3 _367 = vec3(_350.x, _350.y, unpack2xF16(_348.y).x) * vec3(_362.x, _362.x, _362.x);
    highp vec2 _380 = vec2(pack2xF16(vec2(_367.x, _367.y)), pack2xF16(vec2(_367.z, unpack2xF16(pa[0].y).y)));
    pa[0] = vec4(_380.x, _380.y, pa[0].z, pa[0].w);
    highp vec2 _390 = vec2(pa[0].x, pa[0].y);
    highp vec2 _392 = unpack2xF16(_390.x);
    uvec3 _406 = uvec3(round(clamp(vec3(_392.x, _392.y, unpack2xF16(_390.y).x), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _419 = pa[0];
    _419.x = pack4xU8(uvec4(_406.x, _406.y, _406.z, unpack4xU8(pa[0].x).w));
    pa[0] = _419;
    uvec4 _425 = unpack4xU8(pa[0].x);
    uvec4 _435 = unpack4xU8(sa[2].z);
    highp vec3 _465 = vec3(1.0) - vec3(0.0);
    highp float _466 = 1.0 - 0.0;
    uvec3 _479 = uvec3(round(clamp((_465 * (vec3(uvec3(_425.x, _425.y, _425.z)) / vec3(255.0))) + (vec3(0.0) * (vec3(uvec3(_435.x, _435.y, _435.z)) / vec3(255.0))), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _496 = _output[0];
    _496.x = pack4xU8(uvec4(_479.x, _479.y, _479.z, unpack4xU8(_output[0].x).w));
    _output[0] = _496;
    uvec4 _500 = unpack4xU8(_output[0].x);
    highp vec4 _508 = _output[0];
    _508.x = pack4xU8(uvec4(_500.x, _500.y, _500.z, uint(round(clamp((0.0 * (float(unpack4xU8(pa[0].x).w) / 255.0)) + (_466 * (float(unpack4xU8(sa[2].z).w) / 255.0)), 0.0, 1.0) * 255.0))));
    _output[0] = _508;
}

void main()
{
pa[1] = texture(t0, uv);
    pa[0].x = mc.x;
    pa[0].y = mc.y;
    pa[0].z = mc.z;
    sa[2].y = uintBitsToFloat(0x3f800000u);
    sa[2].z = opacity;
    secondary_program();
    primary_program();
    uint _513 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_513 >> 0u) & 255u) / 255.0, float((_513 >> 8u) & 255u) / 255.0, float((_513 >> 16u) & 255u) / 255.0, float((_513 >> 24u) & 255u) / 255.0);
}

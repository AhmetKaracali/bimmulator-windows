#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 7bb56fa7eb34d1994110de7ab97b86f28ceab7e24f4fd21e3eea8b3a472b6853
// Candidate module sha256: 0d1aa212043c8b44a935e7b8c586bb6e2f85715ac50cc21d8a82a4bc501dac0b
// Native input table sha256: 7c8aca12935c605a60b75266e610798766ed03eb189be36a2590441c7e51453f
// Constant-copy table sha256: d906d03287508396b8ff5dd0f301f17e709bfc2698a5cd4105ceb1a7c0b05bc3
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t0 using UV uv at native base 0; lane mapping is unverified.
uniform highp float usr_modality;
uniform highp vec3 CO_ORANGE;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _34[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t0;
uniform highp sampler2D t1;
in highp vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 sa[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 temp[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 _output[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));

highp vec2 unpack2xF16(highp float _198)
{
    return unpackHalf2x16(floatBitsToUint(_198));
}

highp float pack2xF16(highp vec2 _215)
{
    return uintBitsToFloat(packHalf2x16(_215));
}

void secondary_program()
{
    highp vec2 _225 = unpack2xF16(sa[3].y);
    highp vec2 _230 = vec2(pack2xF16(vec2((0.0 - unpack2xF16(sa[3].x).y) + 1.0, unpack2xF16(sa[3].x).y)), pack2xF16(vec2(_225.x, _225.y)));
    sa[3] = vec4(_230.x, _230.y, sa[3].z, sa[3].w);
}

highp float pack4xU8(uvec4 _473)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_473.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_473.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_473.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_473.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _242 = unpack2xF16(pa[0].y);
    highp vec2 _251 = unpack2xF16(sa[3].x);
    highp vec2 _260 = unpack2xF16(pa[0].x);
    highp vec2 _264 = vec2(_242.x, _242.x) * vec2(_251.y, _251.y) + vec2(_260.y, _260.y);
    highp vec2 _272 = unpack2xF16(temp[0].y);
    highp vec2 _277 = vec2(pack2xF16(vec2(_264.x, _264.y)), pack2xF16(vec2(_272.x, _272.y)));
    temp[0] = vec4(_277.x, _277.y, temp[0].z, temp[0].w);
    highp vec2 _286 = unpack2xF16(pa[0].x);
    highp vec2 _295 = unpack2xF16(sa[3].x);
    highp vec2 _305 = unpack2xF16(temp[0].x);
    highp vec2 _309 = vec2(_286.y, _286.y) * (vec2(0.0) - vec2(_295.y, _295.y)) + vec2(_305.x, _305.x);
    highp vec2 _317 = unpack2xF16(temp[0].y);
    highp vec2 _322 = vec2(pack2xF16(vec2(_309.x, _309.y)), pack2xF16(vec2(_317.x, _317.y)));
    temp[0] = vec4(_322.x, _322.y, temp[0].z, temp[0].w);
    highp vec2 _351 = unpack2xF16(pa[0].y);
    highp vec2 _356 = vec2(pack2xF16(vec2(unpack2xF16(sa[3].x).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_351.x, _351.y)));
    pa[0] = vec4(_356.x, _356.y, pa[0].z, pa[0].w);
    highp vec2 _365 = unpack2xF16(pa[0].x);
    highp vec2 _377 = vec2(sa[2].z, sa[2].w);
    highp vec2 _379 = unpack2xF16(_377.x);
    highp vec2 _381 = unpack2xF16(_377.y);
    highp vec2 _394 = vec2(sa[2].z, sa[2].w);
    highp vec2 _396 = unpack2xF16(_394.x);
    highp vec2 _398 = unpack2xF16(_394.y);
    highp vec4 _404 = vec4(_365.x, _365.x, _365.x, _365.x) * (vec4(0.0) - vec4(_379.x, _379.y, _381.x, _381.y)) + vec4(_396.x, _396.y, _398.x, _398.y);
    highp vec2 _413 = vec2(pack2xF16(vec2(_404.x, _404.y)), pack2xF16(vec2(_404.z, _404.w)));
    pa[0] = vec4(_413.x, _413.y, pa[0].z, pa[0].w);
    highp vec4 _441 = pa[0];
    _441.y = pack2xF16(vec2(unpack2xF16(pa[0].y).x, unpack2xF16(temp[0].x).x * unpack2xF16(sa[2].y).y));
    pa[0] = _441;
    highp vec2 _448 = vec2(pa[0].x, pa[0].y);
    highp vec2 _450 = unpack2xF16(_448.x);
    highp vec2 _452 = unpack2xF16(_448.y);
    uvec4 _466 = uvec4(round(clamp(vec4(_450.x, _450.y, _452.x, _452.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _490 = _output[0];
    _490.x = pack4xU8(uvec4(_466.x, _466.y, _466.z, _466.w));
    _output[0] = _490;
}

void main()
{
pa[0] = texture(t0, uv);
    sa[2].y = uintBitsToFloat(0x00000000u);
    sa[2].z = CO_ORANGE.x;
    sa[2].w = CO_ORANGE.z;
    sa[3].x = uintBitsToFloat(0x00000000u);
    secondary_program();
    primary_program();
    uint _495 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_495 >> 0u) & 255u) / 255.0, float((_495 >> 8u) & 255u) / 255.0, float((_495 >> 16u) & 255u) / 255.0, float((_495 >> 24u) & 255u) / 255.0);
}

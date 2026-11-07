#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 28d0404d6155198ca1756afa9e3cdea12c0060573af523559e09cc78ba724ff3
// Candidate module sha256: 1b4355ae2a083487b3b843bc97b81b172831719228815a2c1fa223d4fb46a647
// Native input table sha256: 7c8aca12935c605a60b75266e610798766ed03eb189be36a2590441c7e51453f
// Constant-copy table sha256: 89fda6b1ce9281d6377414335a6dd626e1574feecc21031fcd42a4da6e022638
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t using UV uv at native base 0; lane mapping is unverified.
uniform highp vec3 CO_EDGE;
uniform highp float intensity;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _27[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const vec4 _34[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t;
in highp vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = _27;
highp vec4 sa[32] = _27;
highp vec4 _output[32] = _27;

highp vec2 unpack2xF16(highp float _198)
{
    return unpackHalf2x16(floatBitsToUint(_198));
}

highp float pack2xF16(highp vec2 _229)
{
    return uintBitsToFloat(packHalf2x16(_229));
}

void secondary_program()
{
    highp vec2 _204 = unpack2xF16(sa[2].y);
    highp vec2 _215 = vec2(sa[2].z, sa[2].w);
    highp vec2 _219 = unpack2xF16(_215.y);
    highp vec3 _224 = vec3(_204.x, _204.x, _204.x) * vec3(unpack2xF16(_215.x).y, _219.x, _219.y);
    highp vec2 _244 = vec2(pack2xF16(vec2(_224.x, _224.y)), pack2xF16(vec2(_224.z, unpack2xF16(sa[2].w).y)));
    sa[2] = vec4(sa[2].x, sa[2].y, _244.x, _244.y);
    highp vec4 _264 = sa[2];
    _264.w = pack2xF16(vec2(unpack2xF16(sa[2].w).x, unpack2xF16(sa[2].y).y));
    sa[2] = _264;
}

highp float pack4xU8(uvec4 _339)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_339.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_339.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_339.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_339.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _273 = unpack2xF16(pa[0].x);
    highp vec2 _285 = vec2(sa[2].z, sa[2].w);
    highp vec2 _287 = unpack2xF16(_285.x);
    highp vec2 _289 = unpack2xF16(_285.y);
    highp vec4 _295 = vec4(_273.x, _273.x, _273.x, _273.y) * vec4(_287.x, _287.y, _289.x, _289.y);
    highp vec2 _304 = vec2(pack2xF16(vec2(_295.x, _295.y)), pack2xF16(vec2(_295.z, _295.w)));
    pa[0] = vec4(_304.x, _304.y, pa[0].z, pa[0].w);
    highp vec2 _314 = vec2(pa[0].x, pa[0].y);
    highp vec2 _316 = unpack2xF16(_314.x);
    highp vec2 _318 = unpack2xF16(_314.y);
    uvec4 _332 = uvec4(round(clamp(vec4(_316.x, _316.y, _318.x, _318.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _356 = _output[0];
    _356.x = pack4xU8(uvec4(_332.x, _332.y, _332.z, _332.w));
    _output[0] = _356;
}

void main()
{
pa[0] = texture(t, uv);
    sa[2].y = intensity;
    sa[2].z = uintBitsToFloat(0x00000000u);
    sa[2].w = CO_EDGE.y;
    secondary_program();
    primary_program();
    uint _361 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_361 >> 0u) & 255u) / 255.0, float((_361 >> 8u) & 255u) / 255.0, float((_361 >> 16u) & 255u) / 255.0, float((_361 >> 24u) & 255u) / 255.0);
}

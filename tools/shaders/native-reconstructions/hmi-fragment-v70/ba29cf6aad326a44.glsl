#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: ba29cf6aad326a4459b43a3a8013908221ff5c1921372d65c19b9b0b5ba8c7ca
// Candidate module sha256: a707e6c35cba4ca43c6517ec9ac8b6cef34d51094f7cc16f5b96831c9598cf21
// Native input table sha256: 7c8aca12935c605a60b75266e610798766ed03eb189be36a2590441c7e51453f
// Constant-copy table sha256: bfc7d9458c8811be75cb3490640b96ad7195b67442e290fa08f6436d79ee4f9c
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t using UV uv at native base 0; lane mapping is unverified.
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

highp float pack2xF16(highp vec2 _221)
{
    return uintBitsToFloat(packHalf2x16(_221));
}

highp float pack4xU8(uvec4 _262)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_262.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_262.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_262.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_262.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec4 _230 = pa[0];
    _230.y = pack2xF16(vec2(unpack2xF16(pa[0].y).x, unpack2xF16(sa[2].y).x * unpack2xF16(pa[0].y).y));
    pa[0] = _230;
    highp vec2 _237 = vec2(pa[0].x, pa[0].y);
    highp vec2 _239 = unpack2xF16(_237.x);
    highp vec2 _241 = unpack2xF16(_237.y);
    uvec4 _255 = uvec4(round(clamp(vec4(_239.x, _239.y, _241.x, _241.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _279 = _output[0];
    _279.x = pack4xU8(uvec4(_255.x, _255.y, _255.z, _255.w));
    _output[0] = _279;
}

void main()
{
pa[0] = texture(t, uv);
    sa[2].y = opacity;
    primary_program();
    uint _284 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_284 >> 0u) & 255u) / 255.0, float((_284 >> 8u) & 255u) / 255.0, float((_284 >> 16u) & 255u) / 255.0, float((_284 >> 24u) & 255u) / 255.0);
}

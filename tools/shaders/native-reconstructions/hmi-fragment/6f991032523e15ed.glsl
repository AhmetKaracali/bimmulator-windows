#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 6f991032523e15edf141037b5636cb1ae888da29e90b731da94481afad13c750
// Candidate module sha256: ab0d06c5a5697a3b3b0edd6853d0c0794b88281f8abbc4b5f88277304c5d2ce4
// Native input table sha256: 7c8aca12935c605a60b75266e610798766ed03eb189be36a2590441c7e51453f
// Constant-copy table sha256: bfc7d9458c8811be75cb3490640b96ad7195b67442e290fa08f6436d79ee4f9c
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from tex0 using UV uv at native base 0; lane mapping is unverified.
uniform highp float bright;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _27[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const vec4 _34[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D tex0;
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

void secondary_program()
{
    highp vec2 _231 = unpack2xF16(sa[2].w);
    highp vec2 _236 = vec2(pack2xF16(vec2(unpack2xF16(sa[2].y).x * unpack2xF16(sa[2].y).y, unpack2xF16(sa[2].z).y)), pack2xF16(vec2(_231.x, _231.y)));
    sa[2] = vec4(sa[2].x, sa[2].y, _236.x, _236.y);
}

highp float pack4xU8(uvec4 _312)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_312.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_312.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_312.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_312.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _248 = unpack2xF16(sa[2].z);
    highp vec2 _259 = vec2(pa[0].x, pa[0].y);
    highp vec2 _261 = unpack2xF16(_259.x);
    highp vec4 _268 = vec4(_248.x, _248.x, _248.x, 1.0) * vec4(_261.x, _261.y, unpack2xF16(_259.y).x, 1.0);
    highp vec2 _277 = vec2(pack2xF16(vec2(_268.x, _268.y)), pack2xF16(vec2(_268.z, _268.w)));
    pa[0] = vec4(_277.x, _277.y, pa[0].z, pa[0].w);
    highp vec2 _287 = vec2(pa[0].x, pa[0].y);
    highp vec2 _289 = unpack2xF16(_287.x);
    highp vec2 _291 = unpack2xF16(_287.y);
    uvec4 _305 = uvec4(round(clamp(vec4(_289.x, _289.y, _291.x, _291.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _329 = _output[0];
    _329.x = pack4xU8(uvec4(_305.x, _305.y, _305.z, _305.w));
    _output[0] = _329;
}

void main()
{
pa[0] = texture(tex0, uv);
    sa[2].y = bright;
    secondary_program();
    primary_program();
    uint _334 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_334 >> 0u) & 255u) / 255.0, float((_334 >> 8u) & 255u) / 255.0, float((_334 >> 16u) & 255u) / 255.0, float((_334 >> 24u) & 255u) / 255.0);
}

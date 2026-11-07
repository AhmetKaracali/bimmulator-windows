#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 14f74983d4621b9b1f0d51d666cf8189129afc151e596e79e81a1746442cb3c8
// Candidate module sha256: 6a32ca094d7c474d038a8928f9ee4aadd7c96ffee4c3b55ec8a1e992d22caeb6
// Native input table sha256: 7c8aca12935c605a60b75266e610798766ed03eb189be36a2590441c7e51453f
// Constant-copy table sha256: bfc7d9458c8811be75cb3490640b96ad7195b67442e290fa08f6436d79ee4f9c
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t0 using UV uv at native base 0; lane mapping is unverified.
uniform highp float intensity;
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

highp float pack2xF16(highp vec2 _231)
{
    return uintBitsToFloat(packHalf2x16(_231));
}

highp float pack4xU8(uvec4 _277)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_277.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_277.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_277.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_277.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _204 = unpack2xF16(sa[2].y);
    highp vec2 _216 = vec2(pa[0].x, pa[0].y);
    highp vec2 _218 = unpack2xF16(_216.x);
    highp vec2 _220 = unpack2xF16(_216.y);
    highp vec4 _226 = vec4(_204.x, _204.x, _204.x, _204.y) * vec4(_218.x, _218.y, _220.x, _220.y);
    highp vec2 _242 = vec2(pack2xF16(vec2(_226.x, _226.y)), pack2xF16(vec2(_226.z, _226.w)));
    pa[0] = vec4(_242.x, _242.y, pa[0].z, pa[0].w);
    highp vec2 _252 = vec2(pa[0].x, pa[0].y);
    highp vec2 _254 = unpack2xF16(_252.x);
    highp vec2 _256 = unpack2xF16(_252.y);
    uvec4 _270 = uvec4(round(clamp(vec4(_254.x, _254.y, _256.x, _256.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _294 = _output[0];
    _294.x = pack4xU8(uvec4(_270.x, _270.y, _270.z, _270.w));
    _output[0] = _294;
}

void main()
{
pa[0] = texture(t0, uv);
    sa[2].y = intensity;
    primary_program();
    uint _299 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_299 >> 0u) & 255u) / 255.0, float((_299 >> 8u) & 255u) / 255.0, float((_299 >> 16u) & 255u) / 255.0, float((_299 >> 24u) & 255u) / 255.0);
}

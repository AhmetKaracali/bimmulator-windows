#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 97fc77bf116044ef91afe8c9d93390a24802d6b20ca91ff0879b6c5b4a1e820b
// Candidate module sha256: 36c9730e9d8f169b5420efedac7077aee961a9793ecaab0d32b946b87ad41638
// Native input table sha256: 9dddd2f16d7da75e5938727a12380267fce1945b18ac8428508cc8a066fa4aae
// Constant-copy table sha256: 6f17e207be0c1e25e1c3893d21a25dab2e3f6289b34705159bbb072b5841502e
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA2 from t0 using UV uv at native base 8; lane mapping is unverified.
in highp vec3 fd;
in highp vec3 mixed_co;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _34[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t0;
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

highp float pack2xF16(highp vec2 _232)
{
    return uintBitsToFloat(packHalf2x16(_232));
}

highp float pack4xU8(uvec4 _554)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_554.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_554.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_554.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_554.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _204 = unpack2xF16(pa[0].x);
    highp vec2 _215 = vec2(pa[0].x, pa[0].y);
    highp vec2 _223 = (vec2(0.0) - vec2(_204.x, _204.x)) + vec2(unpack2xF16(_215.x).y, unpack2xF16(_215.y).x);
    highp vec2 _247 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x, _223.x)), pack2xF16(vec2(_223.y, unpack2xF16(pa[0].y).y)));
    pa[0] = vec4(_247.x, _247.y, pa[0].z, pa[0].w);
    highp vec2 _269 = unpack2xF16(pa[0].y);
    highp vec2 _274 = vec2(pack2xF16(vec2(1.0 / unpack2xF16(pa[0].x).y, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_269.x, _269.y)));
    pa[0] = vec4(_274.x, _274.y, pa[0].z, pa[0].w);
    highp vec2 _303 = unpack2xF16(pa[0].y);
    highp vec2 _308 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[0].y).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_303.x, _303.y)));
    pa[0] = vec4(_308.x, _308.y, pa[0].z, pa[0].w);
    highp vec2 _330 = unpack2xF16(pa[0].y);
    highp vec2 _335 = vec2(pack2xF16(vec2(max(unpack2xF16(pa[0].x).x, 0.0), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_330.x, _330.y)));
    pa[0] = vec4(_335.x, _335.y, pa[0].z, pa[0].w);
    highp vec2 _357 = unpack2xF16(pa[0].y);
    highp vec2 _362 = vec2(pack2xF16(vec2(min(unpack2xF16(pa[0].x).x, 1.0), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_357.x, _357.y)));
    pa[0] = vec4(_362.x, _362.y, pa[0].z, pa[0].w);
    highp vec2 _371 = unpack2xF16(pa[0].x);
    highp vec2 _376 = vec2(0.0) - vec2(2.0);
    highp vec2 _379 = vec2(_371.x, _371.x) * _376 + vec2(3.0);
    highp vec2 _387 = unpack2xF16(temp[0].y);
    highp vec2 _392 = vec2(pack2xF16(vec2(_379.x, _379.y)), pack2xF16(vec2(_387.x, _387.y)));
    temp[0] = vec4(_392.x, _392.y, temp[0].z, temp[0].w);
    highp vec2 _421 = unpack2xF16(pa[0].y);
    highp vec2 _426 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_421.x, _421.y)));
    pa[0] = vec4(_426.x, _426.y, pa[0].z, pa[0].w);
    highp vec2 _455 = unpack2xF16(pa[0].y);
    highp vec2 _460 = vec2(pack2xF16(vec2(unpack2xF16(temp[0].x).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_455.x, _455.y)));
    pa[0] = vec4(_460.x, _460.y, pa[0].z, pa[0].w);
    highp vec2 _489 = unpack2xF16(pa[0].y);
    highp vec2 _494 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].z).y * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_489.x, _489.y)));
    pa[0] = vec4(_494.x, _494.y, pa[0].z, pa[0].w);
    highp vec4 _522 = pa[1];
    _522.y = pack2xF16(vec2(unpack2xF16(pa[1].y).x, unpack2xF16(pa[0].x).x * unpack2xF16(sa[2].y).x));
    pa[1] = _522;
    highp vec2 _529 = vec2(pa[1].x, pa[1].y);
    highp vec2 _531 = unpack2xF16(_529.x);
    highp vec2 _533 = unpack2xF16(_529.y);
    uvec4 _547 = uvec4(round(clamp(vec4(_531.x, _531.y, _533.x, _533.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _571 = _output[0];
    _571.x = pack4xU8(uvec4(_547.x, _547.y, _547.z, _547.w));
    _output[0] = _571;
}

void main()
{
pa[2] = texture(t0, uv);
    pa[0].x = fd.x;
    pa[0].y = fd.y;
    pa[0].z = fd.z;
    pa[1].x = mixed_co.x;
    pa[1].y = mixed_co.y;
    pa[1].z = mixed_co.z;
    sa[2].y = opacity;
    primary_program();
    uint _576 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_576 >> 0u) & 255u) / 255.0, float((_576 >> 8u) & 255u) / 255.0, float((_576 >> 16u) & 255u) / 255.0, float((_576 >> 24u) & 255u) / 255.0);
}

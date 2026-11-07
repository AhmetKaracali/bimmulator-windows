#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: ad5dde505415813072f598d1e990758eb85493b23de8d54d72c427a59328dd87
// Candidate module sha256: 8ed065fb8e53f61a9631a93c39a524c4a6fa1865f5e79e1af3cfcb0309250326
// Native input table sha256: e2f0ef87e5b44b3ce59858ccce4064dc914fc052748ff39d3a7270a5991c39cb
// Constant-copy table sha256: 6f17e207be0c1e25e1c3893d21a25dab2e3f6289b34705159bbb072b5841502e
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Native shader has no sampler symbol; no sample is injected.
in highp vec3 fd;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _34[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

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

uvec4 unpack4xU8(highp float _527)
{
    uint _530 = floatBitsToUint(_527);
    return uvec4((((_530) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_530) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_530) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_530) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _544)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_544.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_544.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_544.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_544.w) & ((1u << uint(8)) - 1u)) << uint(24))));
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
    highp vec2 _489 = unpack2xF16(temp[0].w);
    highp vec2 _494 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(sa[2].y).y, unpack2xF16(temp[0].z).y)), pack2xF16(vec2(_489.x, _489.y)));
    temp[0] = vec4(temp[0].x, temp[0].y, _494.x, _494.y);
    highp vec4 _501 = vec4(uvec4(0u));
    highp vec4 _505 = vec4(uvec4(0u));
    highp vec4 _509 = vec4(1.0) - vec4(0.0);
    uvec4 _519 = uvec4(round(clamp((_509 * (_501 / vec4(255.0))) + (vec4(0.0) * (_505 / vec4(255.0))), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _560 = _output[0];
    _560.x = pack4xU8(uvec4(_519.x, _519.y, _519.z, unpack4xU8(_output[0].x).w));
    _output[0] = _560;
    uvec4 _575 = unpack4xU8(_output[0].x);
    highp vec4 _583 = _output[0];
    _583.x = pack4xU8(uvec4(_575.x, _575.y, _575.z, uint(round(clamp(unpack2xF16(temp[0].z).x, 0.0, 1.0) * 255.0))));
    _output[0] = _583;
}

void main()
{
    pa[0].x = fd.x;
    pa[0].y = fd.y;
    pa[0].z = fd.z;
    sa[2].y = uintBitsToFloat(0x00000000u);
    primary_program();
    uint _588 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_588 >> 0u) & 255u) / 255.0, float((_588 >> 8u) & 255u) / 255.0, float((_588 >> 16u) & 255u) / 255.0, float((_588 >> 24u) & 255u) / 255.0);
}

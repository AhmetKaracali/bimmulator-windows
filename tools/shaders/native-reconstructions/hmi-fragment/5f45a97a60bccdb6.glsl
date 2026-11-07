#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 5f45a97a60bccdb66297b2328f8a10f9e114170c47b825006dd8e020bd13cf1c
// Candidate module sha256: ed52ae60b1b7f806022db4ad8d173e877cdf95dbab2322454bef3d7c5217f871
// Native input table sha256: 0cf1f73093131706cf980889d6854cd3d9f5c90d1dcbc741b0d50c9817734183
// Constant-copy table sha256: 6f17e207be0c1e25e1c3893d21a25dab2e3f6289b34705159bbb072b5841502e
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA2 from t0 using UV uv at native base 8; lane mapping is unverified.
in highp float v_cursor_link;
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

highp float pack2xF16(highp vec2 _231)
{
    return uintBitsToFloat(packHalf2x16(_231));
}

highp float pack4xU8(uvec4 _643)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_643.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_643.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_643.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_643.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _204 = unpack2xF16(pa[1].z);
    highp vec2 _213 = unpack2xF16(pa[0].w);
    highp vec2 _222 = unpack2xF16(pa[0].z);
    highp vec2 _226 = vec2(_204.x, _204.x) * vec2(_213.x, _213.x) + vec2(_222.x, _222.x);
    highp vec2 _241 = unpack2xF16(temp[0].y);
    highp vec2 _246 = vec2(pack2xF16(vec2(_226.x, _226.y)), pack2xF16(vec2(_241.x, _241.y)));
    temp[0] = vec4(_246.x, _246.y, temp[0].z, temp[0].w);
    highp vec2 _255 = unpack2xF16(pa[0].z);
    highp vec2 _264 = unpack2xF16(pa[1].z);
    highp vec2 _274 = unpack2xF16(temp[0].x);
    highp vec2 _278 = vec2(_255.x, _255.x) * (vec2(0.0) - vec2(_264.x, _264.x)) + vec2(_274.x, _274.x);
    highp vec2 _286 = unpack2xF16(pa[1].w);
    highp vec2 _291 = vec2(pack2xF16(vec2(_278.x, _278.y)), pack2xF16(vec2(_286.x, _286.y)));
    pa[1] = vec4(pa[1].x, pa[1].y, _291.x, _291.y);
    highp vec2 _300 = unpack2xF16(pa[0].x);
    highp vec2 _311 = vec2(pa[0].x, pa[0].y);
    highp vec2 _319 = (vec2(0.0) - vec2(_300.x, _300.x)) + vec2(unpack2xF16(_311.x).y, unpack2xF16(_311.y).x);
    highp vec2 _336 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x, _319.x)), pack2xF16(vec2(_319.y, unpack2xF16(pa[0].y).y)));
    pa[0] = vec4(_336.x, _336.y, pa[0].z, pa[0].w);
    highp vec2 _358 = unpack2xF16(pa[0].y);
    highp vec2 _363 = vec2(pack2xF16(vec2(1.0 / unpack2xF16(pa[0].x).y, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_358.x, _358.y)));
    pa[0] = vec4(_363.x, _363.y, pa[0].z, pa[0].w);
    highp vec2 _392 = unpack2xF16(pa[0].y);
    highp vec2 _397 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[0].y).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_392.x, _392.y)));
    pa[0] = vec4(_397.x, _397.y, pa[0].z, pa[0].w);
    highp vec2 _419 = unpack2xF16(pa[0].y);
    highp vec2 _424 = vec2(pack2xF16(vec2(max(unpack2xF16(pa[0].x).x, 0.0), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_419.x, _419.y)));
    pa[0] = vec4(_424.x, _424.y, pa[0].z, pa[0].w);
    highp vec2 _446 = unpack2xF16(pa[0].y);
    highp vec2 _451 = vec2(pack2xF16(vec2(min(unpack2xF16(pa[0].x).x, 1.0), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_446.x, _446.y)));
    pa[0] = vec4(_451.x, _451.y, pa[0].z, pa[0].w);
    highp vec2 _460 = unpack2xF16(pa[0].x);
    highp vec2 _465 = vec2(0.0) - vec2(2.0);
    highp vec2 _468 = vec2(_460.x, _460.x) * _465 + vec2(3.0);
    highp vec2 _476 = unpack2xF16(pa[0].w);
    highp vec2 _481 = vec2(pack2xF16(vec2(_468.x, _468.y)), pack2xF16(vec2(_476.x, _476.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _481.x, _481.y);
    highp vec2 _510 = unpack2xF16(pa[0].y);
    highp vec2 _515 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_510.x, _510.y)));
    pa[0] = vec4(_515.x, _515.y, pa[0].z, pa[0].w);
    highp vec2 _544 = unpack2xF16(pa[0].y);
    highp vec2 _549 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].z).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_544.x, _544.y)));
    pa[0] = vec4(_549.x, _549.y, pa[0].z, pa[0].w);
    highp vec2 _578 = unpack2xF16(pa[0].y);
    highp vec2 _583 = vec2(pack2xF16(vec2(unpack2xF16(pa[1].z).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_578.x, _578.y)));
    pa[0] = vec4(_583.x, _583.y, pa[0].z, pa[0].w);
    highp vec4 _611 = pa[1];
    _611.y = pack2xF16(vec2(unpack2xF16(pa[1].y).x, unpack2xF16(pa[0].x).x * unpack2xF16(sa[2].y).x));
    pa[1] = _611;
    highp vec2 _618 = vec2(pa[1].x, pa[1].y);
    highp vec2 _620 = unpack2xF16(_618.x);
    highp vec2 _622 = unpack2xF16(_618.y);
    uvec4 _636 = uvec4(round(clamp(vec4(_620.x, _620.y, _622.x, _622.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _660 = _output[0];
    _660.x = pack4xU8(uvec4(_636.x, _636.y, _636.z, _636.w));
    _output[0] = _660;
}

void main()
{
pa[2] = texture(t0, uv);
    pa[3].x = v_cursor_link;
    pa[0].x = fd.x;
    pa[0].y = fd.y;
    pa[0].z = fd.z;
    pa[1].x = mixed_co.x;
    pa[1].y = mixed_co.y;
    pa[1].z = mixed_co.z;
    sa[2].y = opacity;
    primary_program();
    uint _665 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_665 >> 0u) & 255u) / 255.0, float((_665 >> 8u) & 255u) / 255.0, float((_665 >> 16u) & 255u) / 255.0, float((_665 >> 24u) & 255u) / 255.0);
}

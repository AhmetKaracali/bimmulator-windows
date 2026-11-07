#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: fe143e10ad56d53f8507acfa3d70466831e5add28b4c6dcea86a7bfc1dbfdd50
// Candidate module sha256: b6b67adebd8f158b11adbfb9a2e3a22b1d251a3c6e44f6685786d4c28855b038
// Native input table sha256: 71ef53162bca87adc40065697b3c9d73dcf22d0ee4ea6642f3af1ff940e2003d
// Constant-copy table sha256: a0d51350d7903fb714361ef71e34dd9cce4ba45e1d0160eac995a7eb27a8e9cf
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t using UV uv at native base 0; lane mapping is unverified.
in highp float px;
in highp float am_inner_stack;
in highp float am_outer_stack;
uniform highp float late_stack;
uniform highp float early_stack;
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

highp vec2 unpack2xF16(highp float _198)
{
    return unpackHalf2x16(floatBitsToUint(_198));
}

highp float pack2xF16(highp vec2 _222)
{
    return uintBitsToFloat(packHalf2x16(_222));
}

void secondary_program()
{
    highp vec2 _232 = unpack2xF16(sa[3].w);
    highp vec2 _237 = vec2(pack2xF16(vec2((0.0 - unpack2xF16(sa[3].y).x) + unpack2xF16(sa[3].y).y, unpack2xF16(sa[3].z).y)), pack2xF16(vec2(_232.x, _232.y)));
    sa[3] = vec4(sa[3].x, sa[3].y, _237.x, _237.y);
    highp vec4 _260 = sa[2];
    _260.y = pack2xF16(vec2(vec3(1.0 / unpack2xF16(sa[3].z).x).x, unpack2xF16(sa[2].y).y));
    sa[2] = _260;
}

highp float pack4xU8(uvec4 _868)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_868.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_868.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_868.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_868.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _290 = unpack2xF16(pa[0].w);
    highp vec2 _295 = vec2(pack2xF16(vec2((0.0 - unpack2xF16(sa[3].y).x) + unpack2xF16(pa[0].y).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_290.x, _290.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _295.x, _295.y);
    highp vec2 _324 = unpack2xF16(pa[0].w);
    highp vec2 _329 = vec2(pack2xF16(vec2(unpack2xF16(sa[2].y).x * unpack2xF16(pa[0].z).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_324.x, _324.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _329.x, _329.y);
    highp vec2 _351 = unpack2xF16(pa[0].w);
    highp vec2 _356 = vec2(pack2xF16(vec2(max(unpack2xF16(pa[0].z).x, 0.0), unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_351.x, _351.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _356.x, _356.y);
    highp vec2 _378 = unpack2xF16(pa[0].w);
    highp vec2 _383 = vec2(pack2xF16(vec2(min(unpack2xF16(pa[0].z).x, 1.0), unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_378.x, _378.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _383.x, _383.y);
    highp vec2 _392 = unpack2xF16(pa[0].z);
    highp vec2 _397 = vec2(0.0) - vec2(2.0);
    highp vec2 _400 = vec2(_392.x, _392.x) * _397 + vec2(3.0);
    highp vec2 _408 = unpack2xF16(temp[0].y);
    highp vec2 _413 = vec2(pack2xF16(vec2(_400.x, _400.y)), pack2xF16(vec2(_408.x, _408.y)));
    temp[0] = vec4(_413.x, _413.y, temp[0].z, temp[0].w);
    highp vec2 _442 = unpack2xF16(pa[0].w);
    highp vec2 _447 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].z).x * unpack2xF16(pa[0].z).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_442.x, _442.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _447.x, _447.y);
    highp vec2 _476 = unpack2xF16(pa[0].w);
    highp vec2 _481 = vec2(pack2xF16(vec2(unpack2xF16(temp[0].x).x * unpack2xF16(pa[0].z).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_476.x, _476.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _481.x, _481.y);
    highp vec2 _490 = unpack2xF16(pa[0].z);
    highp vec2 _499 = unpack2xF16(sa[2].y);
    highp vec2 _504 = vec2(_490.x, _490.x) * vec2(_499.y, _499.y) + vec2(1.0);
    highp vec2 _512 = unpack2xF16(pa[0].w);
    highp vec2 _517 = vec2(pack2xF16(vec2(_504.x, _504.y)), pack2xF16(vec2(_512.x, _512.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _517.x, _517.y);
    highp vec2 _547 = unpack2xF16(pa[0].w);
    highp vec2 _552 = vec2(pack2xF16(vec2((0.0 - unpack2xF16(sa[2].y).y) + unpack2xF16(pa[0].z).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_547.x, _547.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _552.x, _552.y);
    highp vec2 _563 = vec2(sa[3].x, sa[3].y);
    highp vec2 _565 = unpack2xF16(_563.x);
    highp vec2 _567 = unpack2xF16(_563.y);
    highp vec2 _579 = vec2(pa[0].x, pa[0].y);
    highp vec2 _581 = unpack2xF16(_579.x);
    highp vec2 _583 = unpack2xF16(_579.y);
    highp vec4 _591 = vec4(greaterThanEqual(vec4(_565.x, _565.y, _567.x, _567.y), vec4(_581.x, _581.y, _583.x, _583.y)));
    highp vec2 _600 = vec2(pack2xF16(vec2(_591.x, _591.y)), pack2xF16(vec2(_591.z, _591.w)));
    temp[0] = vec4(_600.x, _600.y, temp[0].z, temp[0].w);
    highp vec2 _609 = unpack2xF16(pa[1].x);
    highp vec2 _618 = unpack2xF16(temp[0].x);
    highp vec2 _627 = unpack2xF16(pa[1].y);
    highp vec2 _631 = vec2(_609.x, _609.x) * vec2(_618.x, _618.x) + vec2(_627.x, _627.x);
    highp vec2 _639 = unpack2xF16(pa[0].y);
    highp vec2 _644 = vec2(pack2xF16(vec2(_631.x, _631.y)), pack2xF16(vec2(_639.x, _639.y)));
    pa[0] = vec4(_644.x, _644.y, pa[0].z, pa[0].w);
    highp vec2 _653 = unpack2xF16(pa[1].y);
    highp vec2 _662 = unpack2xF16(temp[0].x);
    highp vec2 _672 = unpack2xF16(pa[0].x);
    highp vec2 _676 = vec2(_653.x, _653.x) * (vec2(0.0) - vec2(_662.x, _662.x)) + vec2(_672.x, _672.x);
    highp vec2 _684 = unpack2xF16(pa[0].y);
    highp vec2 _689 = vec2(pack2xF16(vec2(_676.x, _676.y)), pack2xF16(vec2(_684.x, _684.y)));
    pa[0] = vec4(_689.x, _689.y, pa[0].z, pa[0].w);
    highp vec2 _698 = unpack2xF16(pa[0].x);
    highp vec2 _707 = unpack2xF16(sa[3].x);
    highp vec2 _711 = vec2(_698.x, _698.x) * vec2(_707.y, _707.y) + vec2(1.0);
    highp vec2 _719 = unpack2xF16(pa[0].y);
    highp vec2 _724 = vec2(pack2xF16(vec2(_711.x, _711.y)), pack2xF16(vec2(_719.x, _719.y)));
    pa[0] = vec4(_724.x, _724.y, pa[0].z, pa[0].w);
    highp vec2 _754 = unpack2xF16(pa[0].y);
    highp vec2 _759 = vec2(pack2xF16(vec2((0.0 - unpack2xF16(sa[3].x).y) + unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_754.x, _754.y)));
    pa[0] = vec4(_759.x, _759.y, pa[0].z, pa[0].w);
    highp vec2 _788 = unpack2xF16(pa[0].w);
    highp vec2 _793 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].z).x, unpack2xF16(pa[0].w).x * unpack2xF16(pa[0].x).x)), pack2xF16(vec2(_788.x, _788.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _793.x, _793.y);
    highp vec2 _802 = unpack2xF16(pa[0].z);
    highp vec2 _814 = vec2(sa[2].z, sa[2].w);
    highp vec2 _816 = unpack2xF16(_814.x);
    highp vec2 _818 = unpack2xF16(_814.y);
    highp vec4 _824 = vec4(_802.x, _802.x, _802.x, _802.y) * vec4(_816.x, _816.y, _818.x, _818.y);
    highp vec2 _833 = vec2(pack2xF16(vec2(_824.x, _824.y)), pack2xF16(vec2(_824.z, _824.w)));
    pa[0] = vec4(_833.x, _833.y, pa[0].z, pa[0].w);
    highp vec2 _843 = vec2(pa[0].x, pa[0].y);
    highp vec2 _845 = unpack2xF16(_843.x);
    highp vec2 _847 = unpack2xF16(_843.y);
    uvec4 _861 = uvec4(round(clamp(vec4(_845.x, _845.y, _847.x, _847.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _885 = _output[0];
    _885.x = pack4xU8(uvec4(_861.x, _861.y, _861.z, _861.w));
    _output[0] = _885;
}

void main()
{
pa[0] = texture(t, uv);
    pa[1].x = px;
    pa[2].x = am_inner_stack;
    pa[3].x = am_outer_stack;
    sa[2].y = uintBitsToFloat(0x3f800000u);
    sa[2].z = CO.x;
    sa[2].w = CO.z;
    sa[3].x = uintBitsToFloat(0xc4358000u);
    sa[3].y = uintBitsToFloat(0x3d4ccccdu);
    secondary_program();
    primary_program();
    uint _890 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_890 >> 0u) & 255u) / 255.0, float((_890 >> 8u) & 255u) / 255.0, float((_890 >> 16u) & 255u) / 255.0, float((_890 >> 24u) & 255u) / 255.0);
}

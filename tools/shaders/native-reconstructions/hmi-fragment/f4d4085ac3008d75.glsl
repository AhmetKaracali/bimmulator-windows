#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: f4d4085ac3008d75d4fcc68df42345f907802be0a6a3ac7e40849a69aa626349
// Candidate module sha256: 4949b08adbece5898718810f7ccabe6b6acb7ffdc455f00116b9b70c5cbd52ed
// Native input table sha256: 3b7b8d5b505735a217e29fe5931185dd4d09e71b8378d540e410014f2805982b
// Constant-copy table sha256: 393c516c697450eb02dd9c1f8ad7f113640ab921250645ae6f3ab8cad89ee517
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t using UV uv at native base 0; lane mapping is unverified.
uniform highp float selection;
uniform highp float is_stack;
uniform highp vec3 CO_EDGE;
uniform highp float intensity;
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
    highp vec2 _237 = vec2(pack2xF16(vec2((0.0 - unpack2xF16(sa[3].x).y) + unpack2xF16(sa[3].y).x, unpack2xF16(sa[3].z).y)), pack2xF16(vec2(_232.x, _232.y)));
    sa[3] = vec4(sa[3].x, sa[3].y, _237.x, _237.y);
    highp vec4 _260 = sa[3];
    _260.y = pack2xF16(vec2(vec3(1.0 / unpack2xF16(sa[3].z).x).x, unpack2xF16(sa[3].y).y));
    sa[3] = _260;
    highp vec2 _266 = unpack2xF16(sa[2].y);
    highp vec2 _277 = vec2(sa[2].z, sa[2].w);
    highp vec2 _281 = unpack2xF16(_277.y);
    highp vec3 _286 = vec3(_266.x, _266.x, _266.x) * vec3(unpack2xF16(_277.x).y, _281.x, _281.y);
    highp vec2 _299 = vec2(pack2xF16(vec2(_286.x, _286.y)), pack2xF16(vec2(_286.z, unpack2xF16(sa[3].w).y)));
    sa[3] = vec4(sa[3].x, sa[3].y, _299.x, _299.y);
}

highp float pack4xU8(uvec4 _819)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_819.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_819.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_819.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_819.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _311 = unpack2xF16(pa[0].y);
    highp vec2 _320 = unpack2xF16(sa[3].x);
    highp vec2 _329 = unpack2xF16(pa[0].x);
    highp vec2 _333 = vec2(_311.x, _311.x) * vec2(_320.x, _320.x) + vec2(_329.x, _329.x);
    highp vec2 _341 = unpack2xF16(temp[0].y);
    highp vec2 _346 = vec2(pack2xF16(vec2(_333.x, _333.y)), pack2xF16(vec2(_341.x, _341.y)));
    temp[0] = vec4(_346.x, _346.y, temp[0].z, temp[0].w);
    highp vec2 _355 = unpack2xF16(pa[0].x);
    highp vec2 _364 = unpack2xF16(sa[3].x);
    highp vec2 _374 = unpack2xF16(temp[0].x);
    highp vec2 _378 = vec2(_355.x, _355.x) * (vec2(0.0) - vec2(_364.x, _364.x)) + vec2(_374.x, _374.x);
    highp vec2 _386 = unpack2xF16(temp[0].y);
    highp vec2 _391 = vec2(pack2xF16(vec2(_378.x, _378.y)), pack2xF16(vec2(_386.x, _386.y)));
    temp[0] = vec4(_391.x, _391.y, temp[0].z, temp[0].w);
    highp vec2 _421 = unpack2xF16(pa[0].y);
    highp vec2 _426 = vec2(pack2xF16(vec2((0.0 - unpack2xF16(sa[3].x).y) + unpack2xF16(pa[0].z).y, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_421.x, _421.y)));
    pa[0] = vec4(_426.x, _426.y, pa[0].z, pa[0].w);
    highp vec2 _455 = unpack2xF16(pa[0].y);
    highp vec2 _460 = vec2(pack2xF16(vec2(unpack2xF16(sa[3].y).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_455.x, _455.y)));
    pa[0] = vec4(_460.x, _460.y, pa[0].z, pa[0].w);
    highp vec2 _482 = unpack2xF16(pa[0].y);
    highp vec2 _487 = vec2(pack2xF16(vec2(max(unpack2xF16(pa[0].x).x, 0.0), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_482.x, _482.y)));
    pa[0] = vec4(_487.x, _487.y, pa[0].z, pa[0].w);
    highp vec2 _509 = unpack2xF16(pa[0].y);
    highp vec2 _514 = vec2(pack2xF16(vec2(min(unpack2xF16(pa[0].x).x, 1.0), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_509.x, _509.y)));
    pa[0] = vec4(_514.x, _514.y, pa[0].z, pa[0].w);
    highp vec2 _523 = unpack2xF16(pa[0].x);
    highp vec2 _528 = vec2(0.0) - vec2(2.0);
    highp vec2 _531 = vec2(_523.x, _523.x) * _528 + vec2(3.0);
    highp vec2 _539 = unpack2xF16(pa[0].w);
    highp vec2 _544 = vec2(pack2xF16(vec2(_531.x, _531.y)), pack2xF16(vec2(_539.x, _539.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _544.x, _544.y);
    highp vec2 _573 = unpack2xF16(pa[0].y);
    highp vec2 _578 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_573.x, _573.y)));
    pa[0] = vec4(_578.x, _578.y, pa[0].z, pa[0].w);
    highp vec2 _607 = unpack2xF16(pa[0].y);
    highp vec2 _612 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].z).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_607.x, _607.y)));
    pa[0] = vec4(_612.x, _612.y, pa[0].z, pa[0].w);
    highp vec2 _621 = unpack2xF16(pa[0].x);
    highp vec2 _630 = unpack2xF16(sa[2].z);
    highp vec2 _635 = vec2(_621.x, _621.x) * vec2(_630.x, _630.x) + vec2(1.0);
    highp vec2 _643 = unpack2xF16(pa[0].w);
    highp vec2 _648 = vec2(pack2xF16(vec2(_635.x, _635.y)), pack2xF16(vec2(_643.x, _643.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _648.x, _648.y);
    highp vec2 _678 = unpack2xF16(pa[0].y);
    highp vec2 _683 = vec2(pack2xF16(vec2((0.0 - unpack2xF16(sa[2].z).x) + unpack2xF16(pa[0].z).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_678.x, _678.y)));
    pa[0] = vec4(_683.x, _683.y, pa[0].z, pa[0].w);
    highp vec2 _712 = unpack2xF16(pa[0].y);
    highp vec2 _717 = vec2(pack2xF16(vec2(unpack2xF16(temp[0].x).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_712.x, _712.y)));
    pa[0] = vec4(_717.x, _717.y, pa[0].z, pa[0].w);
    highp vec2 _727 = vec2(sa[3].z, sa[3].w);
    highp vec2 _729 = unpack2xF16(_727.x);
    highp vec2 _741 = unpack2xF16(pa[0].x);
    highp vec3 _746 = vec3(_729.x, _729.y, unpack2xF16(_727.y).x) * vec3(_741.x, _741.x, _741.x);
    highp vec2 _759 = vec2(pack2xF16(vec2(_746.x, _746.y)), pack2xF16(vec2(_746.z, unpack2xF16(temp[0].y).y)));
    temp[0] = vec4(_759.x, _759.y, temp[0].z, temp[0].w);
    highp vec4 _787 = temp[0];
    _787.y = pack2xF16(vec2(unpack2xF16(temp[0].y).x, unpack2xF16(sa[2].y).y * unpack2xF16(pa[0].x).y));
    temp[0] = _787;
    highp vec2 _794 = vec2(temp[0].x, temp[0].y);
    highp vec2 _796 = unpack2xF16(_794.x);
    highp vec2 _798 = unpack2xF16(_794.y);
    uvec4 _812 = uvec4(round(clamp(vec4(_796.x, _796.y, _798.x, _798.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _836 = _output[0];
    _836.x = pack4xU8(uvec4(_812.x, _812.y, _812.z, _812.w));
    _output[0] = _836;
}

void main()
{
pa[0] = texture(t, uv);
    sa[2].y = intensity;
    sa[2].z = is_stack;
    sa[2].w = CO_EDGE.y;
    sa[3].x = selection;
    sa[3].y = uintBitsToFloat(0x3f59999au);
    secondary_program();
    primary_program();
    uint _841 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_841 >> 0u) & 255u) / 255.0, float((_841 >> 8u) & 255u) / 255.0, float((_841 >> 16u) & 255u) / 255.0, float((_841 >> 24u) & 255u) / 255.0);
}

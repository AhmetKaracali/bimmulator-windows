#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 7559af48f921868efb22902ac0dfdcf5d29d0e188d3554cca806c029fcf19260
// Candidate module sha256: ab69e0450aa552559f52aaba674ab3780a91a5fbbd04ade03d7ec50f45cd7a0a
// Native input table sha256: 92bb06f0e0933822dddb5bb4ed9192d0eda14e377d5b64b6612f53692d96ac3d
// Constant-copy table sha256: 4a6430b009e4cf3835931bf211c7be94db2b972268dba161cad55a4e4d1377e6
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA1 from t0 using UV uv at native base 4; lane mapping is unverified.
in highp vec3 fd;
uniform highp float pressed;
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

uvec4 unpack4xU8(highp float _650)
{
    uint _653 = floatBitsToUint(_650);
    return uvec4((((_653) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_653) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_653) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_653) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _667)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_667.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_667.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_667.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_667.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _204 = unpack2xF16(pa[0].z);
    highp vec2 _213 = unpack2xF16(sa[2].z);
    highp vec2 _222 = unpack2xF16(pa[0].w);
    highp vec2 _226 = vec2(_204.x, _204.x) * vec2(_213.x, _213.x) + vec2(_222.x, _222.x);
    highp vec2 _241 = unpack2xF16(pa[0].w);
    highp vec2 _246 = vec2(pack2xF16(vec2(_226.x, _226.y)), pack2xF16(vec2(_241.x, _241.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _246.x, _246.y);
    highp vec2 _255 = unpack2xF16(pa[0].w);
    highp vec2 _264 = unpack2xF16(sa[2].z);
    highp vec2 _274 = unpack2xF16(pa[0].z);
    highp vec2 _278 = vec2(_255.x, _255.x) * (vec2(0.0) - vec2(_264.x, _264.x)) + vec2(_274.x, _274.x);
    highp vec2 _286 = unpack2xF16(temp[0].y);
    highp vec2 _291 = vec2(pack2xF16(vec2(_278.x, _278.y)), pack2xF16(vec2(_286.x, _286.y)));
    temp[0] = vec4(_291.x, _291.y, temp[0].z, temp[0].w);
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
    highp vec2 _583 = vec2(pack2xF16(vec2(unpack2xF16(temp[0].x).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_578.x, _578.y)));
    pa[0] = vec4(_583.x, _583.y, pa[0].z, pa[0].w);
    highp vec2 _612 = unpack2xF16(pa[0].w);
    highp vec2 _617 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(sa[2].y).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_612.x, _612.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _617.x, _617.y);
    highp vec4 _624 = vec4(uvec4(0u));
    highp vec4 _628 = vec4(uvec4(0u));
    highp vec4 _632 = vec4(1.0) - vec4(0.0);
    uvec4 _642 = uvec4(round(clamp((_632 * (_624 / vec4(255.0))) + (vec4(0.0) * (_628 / vec4(255.0))), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _683 = _output[0];
    _683.x = pack4xU8(uvec4(_642.x, _642.y, _642.z, unpack4xU8(_output[0].x).w));
    _output[0] = _683;
    uvec4 _698 = unpack4xU8(_output[0].x);
    highp vec4 _706 = _output[0];
    _706.x = pack4xU8(uvec4(_698.x, _698.y, _698.z, uint(round(clamp(unpack2xF16(pa[0].z).x, 0.0, 1.0) * 255.0))));
    _output[0] = _706;
}

void main()
{
pa[1] = texture(t0, uv);
    pa[0].x = fd.x;
    pa[0].y = fd.y;
    pa[0].z = fd.z;
    sa[2].y = opacity;
    sa[2].z = pressed;
    primary_program();
    uint _711 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_711 >> 0u) & 255u) / 255.0, float((_711 >> 8u) & 255u) / 255.0, float((_711 >> 16u) & 255u) / 255.0, float((_711 >> 24u) & 255u) / 255.0);
}

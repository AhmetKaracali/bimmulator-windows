#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 82c1e1c65498546013b074e710a0b6e3b7bad499d2f28f853d389f3968f95da3
// Candidate module sha256: 981c99e2605ed0d4111e5baed29eecc9d8603857546c270604e8c882b3275d9d
// Native input table sha256: 4d78ece692dc75bafda8f2a9534767b3dd2c99132bdc668d29871cf784902dea
// Constant-copy table sha256: 87f529240a8780cbc53d232b30aa9267ae6a47b3b7edd947429183879c46d094
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t using UV uv at native base 0; lane mapping is unverified.
in highp float v_main_menu;
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

highp vec2 unpack2xF16(highp float _202)
{
    return unpackHalf2x16(floatBitsToUint(_202));
}

highp float pack2xF16(highp vec2 _220)
{
    return uintBitsToFloat(packHalf2x16(_220));
}

uvec4 unpack4xU8(highp float _256)
{
    uint _259 = floatBitsToUint(_256);
    return uvec4((((_259) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_259) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_259) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_259) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _276)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_276.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_276.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_276.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_276.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void secondary_program()
{
    highp vec2 _199 = vec2(sa[2].z, sa[2].w);
    highp vec2 _210 = unpack2xF16(_199.y);
    highp vec3 _215 = vec3(0.5) * vec3(unpack2xF16(_199.x).y, _210.x, _210.y);
    highp vec2 _235 = vec2(pack2xF16(vec2(_215.x, _215.y)), pack2xF16(vec2(_215.z, unpack2xF16(sa[2].w).y)));
    sa[2] = vec4(sa[2].x, sa[2].y, _235.x, _235.y);
    uvec4 _270 = unpack4xU8(sa[2].y);
    highp vec4 _292 = sa[2];
    _292.y = pack4xU8(uvec4(_270.x, _270.y, _270.z, uint(round(clamp(unpack2xF16(sa[2].y).x, 0.0, 1.0) * 255.0))));
    sa[2] = _292;
}

void primary_program()
{
    highp vec2 _301 = unpack2xF16(pa[0].z);
    highp vec2 _310 = unpack2xF16(pa[0].x);
    highp vec2 _319 = unpack2xF16(pa[0].x);
    highp vec2 _323 = vec2(_301.x, _301.x) * vec2(_310.x, _310.x) + vec2(_319.y, _319.y);
    highp vec2 _331 = unpack2xF16(temp[0].y);
    highp vec2 _336 = vec2(pack2xF16(vec2(_323.x, _323.y)), pack2xF16(vec2(_331.x, _331.y)));
    temp[0] = vec4(_336.x, _336.y, temp[0].z, temp[0].w);
    highp vec2 _345 = unpack2xF16(pa[0].x);
    highp vec2 _354 = unpack2xF16(pa[0].z);
    highp vec2 _364 = unpack2xF16(temp[0].x);
    highp vec2 _368 = vec2(_345.y, _345.y) * (vec2(0.0) - vec2(_354.x, _354.x)) + vec2(_364.x, _364.x);
    highp vec2 _376 = unpack2xF16(pa[0].y);
    highp vec2 _381 = vec2(pack2xF16(vec2(_368.x, _368.y)), pack2xF16(vec2(_376.x, _376.y)));
    pa[0] = vec4(_381.x, _381.y, pa[0].z, pa[0].w);
    highp vec2 _390 = unpack2xF16(pa[0].x);
    highp vec2 _401 = vec2(sa[2].z, sa[2].w);
    highp vec2 _403 = unpack2xF16(_401.x);
    highp vec3 _410 = vec3(_390.x, _390.x, _390.x) * vec3(_403.x, _403.y, unpack2xF16(_401.y).x);
    highp vec2 _423 = vec2(pack2xF16(vec2(_410.x, _410.y)), pack2xF16(vec2(_410.z, unpack2xF16(pa[0].y).y)));
    pa[0] = vec4(_423.x, _423.y, pa[0].z, pa[0].w);
    highp vec2 _433 = vec2(pa[0].x, pa[0].y);
    highp vec2 _435 = unpack2xF16(_433.x);
    uvec3 _449 = uvec3(round(clamp(vec3(_435.x, _435.y, unpack2xF16(_433.y).x), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _462 = pa[0];
    _462.x = pack4xU8(uvec4(_449.x, _449.y, _449.z, unpack4xU8(pa[0].x).w));
    pa[0] = _462;
    uvec4 _468 = unpack4xU8(pa[0].x);
    uvec4 _478 = unpack4xU8(sa[2].y);
    highp vec3 _508 = vec3(1.0) - vec3(0.0);
    highp float _509 = 1.0 - 0.0;
    uvec3 _522 = uvec3(round(clamp((_508 * (vec3(uvec3(_468.x, _468.y, _468.z)) / vec3(255.0))) + (vec3(0.0) * (vec3(uvec3(_478.x, _478.y, _478.z)) / vec3(255.0))), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _539 = _output[0];
    _539.x = pack4xU8(uvec4(_522.x, _522.y, _522.z, unpack4xU8(_output[0].x).w));
    _output[0] = _539;
    uvec4 _543 = unpack4xU8(_output[0].x);
    highp vec4 _551 = _output[0];
    _551.x = pack4xU8(uvec4(_543.x, _543.y, _543.z, uint(round(clamp((0.0 * (float(unpack4xU8(pa[0].x).w) / 255.0)) + (_509 * (float(unpack4xU8(sa[2].y).w) / 255.0)), 0.0, 1.0) * 255.0))));
    _output[0] = _551;
}

void main()
{
pa[0] = texture(t, uv);
    pa[1].x = v_main_menu;
    sa[2].y = opacity;
    sa[2].z = uintBitsToFloat(0x3f000000u);
    sa[2].w = CO.y;
    secondary_program();
    primary_program();
    uint _556 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_556 >> 0u) & 255u) / 255.0, float((_556 >> 8u) & 255u) / 255.0, float((_556 >> 16u) & 255u) / 255.0, float((_556 >> 24u) & 255u) / 255.0);
}

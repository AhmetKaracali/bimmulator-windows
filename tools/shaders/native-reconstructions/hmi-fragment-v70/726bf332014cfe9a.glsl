#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 726bf332014cfe9aa86842c3b7d4fa2682bccaa0aff75b915578ae270ddb5c9f
// Candidate module sha256: 6694661dc1ebb4960ab6a8bb337389aaba6df8922bef72611ef6e5f5ce0be750
// Native input table sha256: 632e8a829b94f9c927341becfcb933ff4142deb9759cceccfa7c7cef0a3f1f54
// Constant-copy table sha256: 9fc9d83b7169fd9ff4e604a97c825e3d54243e5a84d67640f8e1a3d7c44445be
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Host interface adapter: base_co is encoded as packed F16 varying words.
// Native SMP operations remain bound to their exact .shd samplers.
// IDRIVE_UNIFORM_ALIAS native=gl_PMXPosAdjust host=bmw_PMXPosAdjust
in highp vec3 base_co;
uniform highp float rse_switch;
uniform highp vec3 CO_FES;
uniform highp float opacity;
uniform highp vec4 bmw_PMXPosAdjust;
precision mediump float;
precision highp int;

const vec4 _35[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _41[4] = int[](0, 0, 0, 0);
const bool _47[4] = bool[](false, false, false, false);

uniform highp sampler2D t;
uniform highp sampler2D t_rse;

layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 sa[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 temp[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 _output[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));

highp vec2 unpack2xF16(highp float _199)
{
    return unpackHalf2x16(floatBitsToUint(_199));
}

highp float pack2xF16(highp vec2 _215)
{
    return uintBitsToFloat(packHalf2x16(_215));
}

uvec4 unpack4xU8(highp float _313)
{
    uint _316 = floatBitsToUint(_313);
    return uvec4((((_316) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_316) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_316) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_316) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _333)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_333.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_333.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_333.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_333.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void secondary_program()
{
    highp vec2 _225 = unpack2xF16(sa[5].y);
    highp vec2 _230 = vec2(pack2xF16(vec2(1.0 / unpack2xF16(sa[5].y).x, unpack2xF16(sa[5].x).y)), pack2xF16(vec2(_225.x, _225.y)));
    sa[5] = vec4(_230.x, _230.y, sa[5].z, sa[5].w);
    highp vec4 _253 = sa[2];
    _253.y = pack2xF16(vec2(vec3(1.0 / unpack2xF16(sa[5].y).y).x, unpack2xF16(sa[2].y).y));
    sa[2] = _253;
    highp vec2 _259 = unpack2xF16(sa[5].z);
    highp vec2 _270 = vec2(sa[4].z, sa[4].w);
    highp vec2 _274 = unpack2xF16(_270.y);
    highp vec3 _279 = vec3(_259.y, _259.y, _259.y) * vec3(unpack2xF16(_270.x).y, _274.x, _274.y);
    highp vec2 _292 = vec2(pack2xF16(vec2(_279.x, _279.y)), pack2xF16(vec2(_279.z, unpack2xF16(sa[6].y).y)));
    sa[6] = vec4(_292.x, _292.y, sa[6].z, sa[6].w);
    uvec4 _327 = unpack4xU8(sa[4].z);
    highp vec4 _349 = sa[4];
    _349.z = pack4xU8(uvec4(_327.x, _327.y, _327.z, uint(round(clamp(unpack2xF16(sa[5].x).y, 0.0, 1.0) * 255.0))));
    sa[4] = _349;
}

void primary_program()
{
    highp vec2 _359 = vec2(pa[0].x, pa[0].y);
    highp vec2 _367 = unpack2xF16(pa[0].y);
    highp vec2 _372 = vec2(pack2xF16(vec2(_359.x, _359.y)), pack2xF16(vec2(_367.x, _367.y)));
    pa[0] = vec4(_372.x, _372.y, pa[0].z, pa[0].w);
    highp vec2 _402 = unpack2xF16(temp[0].y);
    highp vec2 _407 = vec2(pack2xF16(vec2((0.0 - unpack2xF16(pa[0].x).y) + unpack2xF16(sa[2].y).y, unpack2xF16(temp[0].x).y)), pack2xF16(vec2(_402.x, _402.y)));
    temp[0] = vec4(_407.x, _407.y, temp[0].z, temp[0].w);
    highp vec2 _437 = unpack2xF16(pa[0].y);
    highp vec2 _442 = vec2(pack2xF16(vec2(unpack2xF16(sa[5].x).x * abs(unpack2xF16(pa[0].x).x), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_437.x, _437.y)));
    pa[0] = vec4(_442.x, _442.y, pa[0].z, pa[0].w);
    highp vec2 _472 = unpack2xF16(pa[0].y);
    highp vec2 _477 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x, unpack2xF16(sa[2].y).x * abs(unpack2xF16(temp[0].x).x))), pack2xF16(vec2(_472.x, _472.y)));
    pa[0] = vec4(_477.x, _477.y, pa[0].z, pa[0].w);
    highp vec2 _486 = unpack2xF16(pa[0].x);
    vec4 _491 = texture(t, vec2(_486.x, _486.y));
    highp vec2 _500 = vec2(pack2xF16(vec2(_491.x, _491.y)), pack2xF16(vec2(_491.z, _491.w)));
    temp[0] = vec4(_500.x, _500.y, temp[0].z, temp[0].w);
    highp vec2 _509 = unpack2xF16(pa[0].x);
    vec4 _514 = texture(t_rse, vec2(_509.x, _509.y));
    highp vec2 _523 = vec2(pack2xF16(vec2(_514.x, _514.y)), pack2xF16(vec2(_514.z, _514.w)));
    temp[0] = vec4(temp[0].x, temp[0].y, _523.x, _523.y);
    highp vec2 _532 = unpack2xF16(temp[0].z);
    highp vec2 _535 = vec2(_532.x, _532.x);
    highp vec2 _552 = vec2(pack2xF16(vec2(_535.x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_535.y, unpack2xF16(pa[0].y).y)));
    pa[0] = vec4(_552.x, _552.y, pa[0].z, pa[0].w);
    highp vec2 _562 = vec2(pa[0].x, pa[0].y);
    highp vec2 _564 = unpack2xF16(_562.x);
    highp vec2 _566 = unpack2xF16(_562.y);
    highp vec2 _577 = unpack2xF16(sa[5].z);
    highp vec2 _589 = vec2(temp[0].x, temp[0].y);
    highp vec2 _591 = unpack2xF16(_589.x);
    highp vec2 _593 = unpack2xF16(_589.y);
    highp vec4 _599 = vec4(_564.x, _564.y, _566.x, _566.y) * vec4(_577.x, _577.x, _577.x, _577.x) + vec4(_591.x, _591.y, _593.x, _593.y);
    highp vec2 _608 = vec2(pack2xF16(vec2(_599.x, _599.y)), pack2xF16(vec2(_599.z, _599.w)));
    pa[0] = vec4(_608.x, _608.y, pa[0].z, pa[0].w);
    highp vec2 _618 = vec2(temp[0].x, temp[0].y);
    highp vec2 _620 = unpack2xF16(_618.x);
    highp vec2 _622 = unpack2xF16(_618.y);
    highp vec2 _633 = unpack2xF16(sa[5].z);
    highp vec2 _646 = vec2(pa[0].x, pa[0].y);
    highp vec2 _648 = unpack2xF16(_646.x);
    highp vec2 _650 = unpack2xF16(_646.y);
    highp vec4 _656 = vec4(_620.x, _620.y, _622.x, _622.y) * (vec4(0.0) - vec4(_633.x, _633.x, _633.x, _633.x)) + vec4(_648.x, _648.y, _650.x, _650.y);
    highp vec2 _665 = vec2(pack2xF16(vec2(_656.x, _656.y)), pack2xF16(vec2(_656.z, _656.w)));
    temp[0] = vec4(_665.x, _665.y, temp[0].z, temp[0].w);
    highp vec2 _694 = unpack2xF16(pa[0].y);
    highp vec2 _699 = vec2(pack2xF16(vec2(unpack2xF16(temp[0].y).x * unpack2xF16(sa[4].z).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_694.x, _694.y)));
    pa[0] = vec4(_699.x, _699.y, pa[0].z, pa[0].w);
    highp vec2 _709 = vec2(pa[0].z, pa[0].w);
    highp vec2 _711 = unpack2xF16(_709.x);
    highp vec2 _723 = unpack2xF16(pa[0].x);
    highp vec3 _728 = vec3(_711.x, _711.y, unpack2xF16(_709.y).x) * vec3(_723.x, _723.x, _723.x);
    highp vec2 _741 = vec2(pack2xF16(vec2(_728.x, _728.y)), pack2xF16(vec2(_728.z, unpack2xF16(pa[0].y).y)));
    pa[0] = vec4(_741.x, _741.y, pa[0].z, pa[0].w);
    highp vec2 _750 = unpack2xF16(temp[0].x);
    highp vec2 _762 = vec2(sa[6].x, sa[6].y);
    highp vec2 _764 = unpack2xF16(_762.x);
    highp vec2 _766 = unpack2xF16(_762.y);
    highp vec2 _778 = vec2(pa[0].x, pa[0].y);
    highp vec2 _780 = unpack2xF16(_778.x);
    highp vec2 _782 = unpack2xF16(_778.y);
    highp vec4 _788 = vec4(_750.x, _750.x, _750.x, _750.x) * vec4(_764.x, _764.y, _766.x, _766.y) + vec4(_780.x, _780.y, _782.x, _782.y);
    highp vec2 _797 = vec2(pack2xF16(vec2(_788.x, _788.y)), pack2xF16(vec2(_788.z, _788.w)));
    pa[0] = vec4(_797.x, _797.y, pa[0].z, pa[0].w);
    highp vec2 _807 = vec2(pa[0].x, pa[0].y);
    highp vec2 _809 = unpack2xF16(_807.x);
    uvec3 _823 = uvec3(round(clamp(vec3(_809.x, _809.y, unpack2xF16(_807.y).x), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _836 = pa[0];
    _836.x = pack4xU8(uvec4(_823.x, _823.y, _823.z, unpack4xU8(pa[0].x).w));
    pa[0] = _836;
    uvec4 _842 = unpack4xU8(pa[0].x);
    uvec4 _852 = unpack4xU8(sa[4].z);
    highp vec3 _882 = vec3(1.0) - vec3(0.0);
    highp float _883 = 1.0 - 0.0;
    uvec3 _896 = uvec3(round(clamp((_882 * (vec3(uvec3(_842.x, _842.y, _842.z)) / vec3(255.0))) + (vec3(0.0) * (vec3(uvec3(_852.x, _852.y, _852.z)) / vec3(255.0))), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _913 = _output[0];
    _913.x = pack4xU8(uvec4(_896.x, _896.y, _896.z, unpack4xU8(_output[0].x).w));
    _output[0] = _913;
    uvec4 _917 = unpack4xU8(_output[0].x);
    highp vec4 _925 = _output[0];
    _925.x = pack4xU8(uvec4(_917.x, _917.y, _917.z, uint(round(clamp((0.0 * (float(unpack4xU8(pa[0].x).w) / 255.0)) + (_883 * (float(unpack4xU8(sa[4].z).w) / 255.0)), 0.0, 1.0) * 255.0))));
    _output[0] = _925;
}

void main()
{
    pa[0].x = uintBitsToFloat(packHalf2x16(base_co.xy));
    pa[0].y = uintBitsToFloat(packHalf2x16(vec2(base_co.z, 0.0)));
    pa[0].z = 0.0;
    sa[2].y = bmw_PMXPosAdjust.x;
    sa[4].z = uintBitsToFloat(0x3fa66666u);
    sa[4].w = CO_FES.y;
    sa[5].x = uintBitsToFloat(0x3f800000u);
    sa[5].y = uintBitsToFloat(0x44b40000u);
    sa[5].z = rse_switch;
    secondary_program();
    primary_program();
    uint _930 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_930 >> 0u) & 255u) / 255.0, float((_930 >> 8u) & 255u) / 255.0, float((_930 >> 16u) & 255u) / 255.0, float((_930 >> 24u) & 255u) / 255.0);
}

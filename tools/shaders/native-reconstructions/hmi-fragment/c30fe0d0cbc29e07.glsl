#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: c30fe0d0cbc29e076d1db22e54949e38854172748a3e29babf66dd85dc295558
// Candidate module sha256: a66629511d937fcf0ae133e413027128d91f83f967f7e3c705b18a518ce1a485
// Native input table sha256: 612ca97aca1de4363db91bc7fc8af33b2c3b4445b25e0164bb813d4cc1b196df
// Constant-copy table sha256: c0065468e0d461a5a9113286ddc45debdcb68bc1c6fedfca58b973102a42ef1f
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA1 from t1 using UV uv at native base 4; lane mapping is unverified.
in highp float v_am;
in highp float v_usr_modality;
in highp vec3 fd;
in highp float birth;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _27[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t1;
in highp vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = _27;
highp vec4 sa[32] = _27;
highp vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 _output[32] = _27;

highp vec2 unpack2xF16(highp float _198)
{
    return unpackHalf2x16(floatBitsToUint(_198));
}

highp float pack2xF16(highp vec2 _221)
{
    return uintBitsToFloat(packHalf2x16(_221));
}

uvec4 unpack4xU8(highp float _661)
{
    uint _664 = floatBitsToUint(_661);
    return uvec4((((_664) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_664) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_664) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_664) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _681)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_681.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_681.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_681.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_681.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _231 = unpack2xF16(pa[0].w);
    highp vec2 _236 = vec2(pack2xF16(vec2(unpack2xF16(pa[1].x).x * unpack2xF16(pa[0].w).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_231.x, _231.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _236.x, _236.y);
    highp vec2 _245 = unpack2xF16(pa[1].y);
    highp vec2 _252 = vec2(_245.x, _245.x) * vec2(0.75) + vec2(1.0);
    highp vec2 _260 = unpack2xF16(pa[1].y);
    highp vec2 _265 = vec2(pack2xF16(vec2(_252.x, _252.y)), pack2xF16(vec2(_260.x, _260.y)));
    pa[1] = vec4(_265.x, _265.y, pa[1].z, pa[1].w);
    highp vec4 _287 = internal[0];
    _287.x = (0.0 - unpack2xF16(pa[1].y).x) + unpack2xF16(pa[1].x).x;
    internal[0] = _287;
    highp vec2 _293 = unpack2xF16(pa[0].x);
    highp vec2 _304 = vec2(pa[0].x, pa[0].y);
    highp vec2 _312 = (vec2(0.0) - vec2(_293.x, _293.x)) + vec2(unpack2xF16(_304.x).y, unpack2xF16(_304.y).x);
    internal[1] = vec4(internal[1].x, _312.x, _312.y, internal[1].w);
    highp vec4 _331 = internal[1];
    highp vec2 _335 = vec2(1.0 / _331.y);
    highp vec4 _338 = internal[2];
    _338.x = unpack2xF16(pa[0].z).x * internal[0].x;
    internal[2] = _338;
    highp vec2 _346 = unpack2xF16(pa[0].y);
    highp vec2 _351 = vec2(pack2xF16(vec2(_335.x, _335.y)), pack2xF16(vec2(_346.x, _346.y)));
    pa[0] = vec4(_351.x, _351.y, pa[0].z, pa[0].w);
    highp vec2 _378 = unpack2xF16(pa[0].y);
    highp vec2 _383 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * internal[1].z, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_378.x, _378.y)));
    pa[0] = vec4(_383.x, _383.y, pa[0].z, pa[0].w);
    highp vec2 _405 = unpack2xF16(pa[0].y);
    highp vec2 _410 = vec2(pack2xF16(vec2(max(unpack2xF16(pa[0].x).x, 0.0), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_405.x, _405.y)));
    pa[0] = vec4(_410.x, _410.y, pa[0].z, pa[0].w);
    highp vec2 _432 = unpack2xF16(pa[0].y);
    highp vec2 _437 = vec2(pack2xF16(vec2(min(unpack2xF16(pa[0].x).x, 1.0), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_432.x, _432.y)));
    pa[0] = vec4(_437.x, _437.y, pa[0].z, pa[0].w);
    highp vec2 _446 = unpack2xF16(pa[0].x);
    highp vec2 _451 = vec2(0.0) - vec2(2.0);
    highp vec2 _454 = vec2(_446.x, _446.x) * _451 + vec2(3.0);
    highp vec2 _462 = unpack2xF16(pa[0].w);
    highp vec2 _467 = vec2(pack2xF16(vec2(_454.x, _454.y)), pack2xF16(vec2(_462.x, _462.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _467.x, _467.y);
    highp vec2 _496 = unpack2xF16(pa[0].y);
    highp vec2 _501 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_496.x, _496.y)));
    pa[0] = vec4(_501.x, _501.y, pa[0].z, pa[0].w);
    highp vec2 _530 = unpack2xF16(pa[0].y);
    highp vec2 _535 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].z).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_530.x, _530.y)));
    pa[0] = vec4(_535.x, _535.y, pa[0].z, pa[0].w);
    highp vec2 _564 = unpack2xF16(pa[0].y);
    highp vec2 _569 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[1].z).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_564.x, _564.y)));
    pa[0] = vec4(_569.x, _569.y, pa[0].z, pa[0].w);
    highp vec2 _596 = unpack2xF16(pa[0].y);
    highp vec2 _601 = vec2(pack2xF16(vec2(internal[2].x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_596.x, _596.y)));
    pa[0] = vec4(_601.x, _601.y, pa[0].z, pa[0].w);
    highp vec2 _630 = unpack2xF16(pa[0].w);
    highp vec2 _635 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(sa[2].y).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_630.x, _630.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _635.x, _635.y);
    highp vec4 _643 = _output[0];
    _643.x = uintBitsToFloat(4294967295u);
    _output[0] = _643;
    uvec4 _675 = unpack4xU8(_output[0].x);
    highp vec4 _697 = _output[0];
    _697.x = pack4xU8(uvec4(_675.x, _675.y, _675.z, uint(round(clamp(unpack2xF16(pa[0].z).x, 0.0, 1.0) * 255.0))));
    _output[0] = _697;
}

void main()
{
pa[1] = texture(t1, uv);
    pa[2].x = v_am;
    pa[3].x = v_usr_modality;
    pa[0].x = fd.x;
    pa[0].y = fd.y;
    pa[0].z = fd.z;
    pa[4].x = birth;
    sa[2].y = opacity;
    primary_program();
    uint _702 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_702 >> 0u) & 255u) / 255.0, float((_702 >> 8u) & 255u) / 255.0, float((_702 >> 16u) & 255u) / 255.0, float((_702 >> 24u) & 255u) / 255.0);
}

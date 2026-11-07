#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: cd02bf138fc0ca859e3f171fd8922d4b3e0523f0c5a971e191d32893c4126ec6
// Candidate module sha256: c7ba84e85b637f4eac22aeae96a0aea6e33facbbe52ed5e2b3cf6b31a3432596
// Native input table sha256: 9dddd2f16d7da75e5938727a12380267fce1945b18ac8428508cc8a066fa4aae
// Constant-copy table sha256: 3f990f258046174a55d96937ed43e1b2c81db3c24dd573e518c0797286856b78
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA2 from t using UV uv at native base 8; lane mapping is unverified.
in highp vec3 fd;
in highp vec3 mixed_co;
uniform highp float usr_modality;
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

highp vec2 unpack2xF16(highp float _199)
{
    return unpackHalf2x16(floatBitsToUint(_199));
}

highp float pack2xF16(highp vec2 _215)
{
    return uintBitsToFloat(packHalf2x16(_215));
}

void secondary_program()
{
    highp vec2 _225 = unpack2xF16(sa[3].y);
    highp vec2 _230 = vec2(pack2xF16(vec2(0.75 * unpack2xF16(sa[2].y).y, unpack2xF16(sa[3].x).y)), pack2xF16(vec2(_225.x, _225.y)));
    sa[3] = vec4(_230.x, _230.y, sa[3].z, sa[3].w);
}

highp float pack4xU8(uvec4 _674)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_674.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_674.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_674.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_674.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _242 = unpack2xF16(pa[0].z);
    highp vec2 _251 = unpack2xF16(sa[2].z);
    highp vec2 _260 = unpack2xF16(pa[0].w);
    highp vec2 _264 = vec2(_242.x, _242.x) * vec2(_251.x, _251.x) + vec2(_260.x, _260.x);
    highp vec2 _272 = unpack2xF16(pa[0].w);
    highp vec2 _277 = vec2(pack2xF16(vec2(_264.x, _264.y)), pack2xF16(vec2(_272.x, _272.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _277.x, _277.y);
    highp vec2 _286 = unpack2xF16(pa[0].w);
    highp vec2 _295 = unpack2xF16(sa[2].z);
    highp vec2 _305 = unpack2xF16(pa[0].z);
    highp vec2 _309 = vec2(_286.x, _286.x) * (vec2(0.0) - vec2(_295.x, _295.x)) + vec2(_305.x, _305.x);
    highp vec2 _317 = unpack2xF16(temp[0].y);
    highp vec2 _322 = vec2(pack2xF16(vec2(_309.x, _309.y)), pack2xF16(vec2(_317.x, _317.y)));
    temp[0] = vec4(_322.x, _322.y, temp[0].z, temp[0].w);
    highp vec2 _331 = unpack2xF16(pa[0].x);
    highp vec2 _342 = vec2(pa[0].x, pa[0].y);
    highp vec2 _350 = (vec2(0.0) - vec2(_331.x, _331.x)) + vec2(unpack2xF16(_342.x).y, unpack2xF16(_342.y).x);
    highp vec2 _367 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x, _350.x)), pack2xF16(vec2(_350.y, unpack2xF16(pa[0].y).y)));
    pa[0] = vec4(_367.x, _367.y, pa[0].z, pa[0].w);
    highp vec2 _389 = unpack2xF16(pa[0].y);
    highp vec2 _394 = vec2(pack2xF16(vec2(1.0 / unpack2xF16(pa[0].x).y, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_389.x, _389.y)));
    pa[0] = vec4(_394.x, _394.y, pa[0].z, pa[0].w);
    highp vec2 _423 = unpack2xF16(pa[0].y);
    highp vec2 _428 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[0].y).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_423.x, _423.y)));
    pa[0] = vec4(_428.x, _428.y, pa[0].z, pa[0].w);
    highp vec2 _450 = unpack2xF16(pa[0].y);
    highp vec2 _455 = vec2(pack2xF16(vec2(max(unpack2xF16(pa[0].x).x, 0.0), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_450.x, _450.y)));
    pa[0] = vec4(_455.x, _455.y, pa[0].z, pa[0].w);
    highp vec2 _477 = unpack2xF16(pa[0].y);
    highp vec2 _482 = vec2(pack2xF16(vec2(min(unpack2xF16(pa[0].x).x, 1.0), unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_477.x, _477.y)));
    pa[0] = vec4(_482.x, _482.y, pa[0].z, pa[0].w);
    highp vec2 _491 = unpack2xF16(pa[0].x);
    highp vec2 _496 = vec2(0.0) - vec2(2.0);
    highp vec2 _499 = vec2(_491.x, _491.x) * _496 + vec2(3.0);
    highp vec2 _507 = unpack2xF16(pa[0].w);
    highp vec2 _512 = vec2(pack2xF16(vec2(_499.x, _499.y)), pack2xF16(vec2(_507.x, _507.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _512.x, _512.y);
    highp vec2 _541 = unpack2xF16(pa[0].y);
    highp vec2 _546 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_541.x, _541.y)));
    pa[0] = vec4(_546.x, _546.y, pa[0].z, pa[0].w);
    highp vec2 _575 = unpack2xF16(pa[0].y);
    highp vec2 _580 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].z).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_575.x, _575.y)));
    pa[0] = vec4(_580.x, _580.y, pa[0].z, pa[0].w);
    highp vec2 _609 = unpack2xF16(pa[0].y);
    highp vec2 _614 = vec2(pack2xF16(vec2(unpack2xF16(temp[0].x).x * unpack2xF16(pa[0].x).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_609.x, _609.y)));
    pa[0] = vec4(_614.x, _614.y, pa[0].z, pa[0].w);
    highp vec4 _642 = pa[1];
    _642.y = pack2xF16(vec2(unpack2xF16(pa[1].y).x, unpack2xF16(pa[0].x).x * unpack2xF16(sa[3].x).x));
    pa[1] = _642;
    highp vec2 _649 = vec2(pa[1].x, pa[1].y);
    highp vec2 _651 = unpack2xF16(_649.x);
    highp vec2 _653 = unpack2xF16(_649.y);
    uvec4 _667 = uvec4(round(clamp(vec4(_651.x, _651.y, _653.x, _653.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _691 = _output[0];
    _691.x = pack4xU8(uvec4(_667.x, _667.y, _667.z, _667.w));
    _output[0] = _691;
}

void main()
{
pa[2] = texture(t, uv);
    pa[0].x = fd.x;
    pa[0].y = fd.y;
    pa[0].z = fd.z;
    pa[1].x = mixed_co.x;
    pa[1].y = mixed_co.y;
    pa[1].z = mixed_co.z;
    sa[2].y = uintBitsToFloat(0x40400000u);
    sa[2].z = usr_modality;
    secondary_program();
    primary_program();
    uint _696 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_696 >> 0u) & 255u) / 255.0, float((_696 >> 8u) & 255u) / 255.0, float((_696 >> 16u) & 255u) / 255.0, float((_696 >> 24u) & 255u) / 255.0);
}

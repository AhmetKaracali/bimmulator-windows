#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: cf69532a3d1177d0f00bac883c933d1a3b3afb6703647f1ebe93c6109e1f36e6
// Candidate module sha256: 22361361709c5f58442b028720d05711eb5872d6ac530b1fe4d4f8504569f77b
// Native input table sha256: 4d78ece692dc75bafda8f2a9534767b3dd2c99132bdc668d29871cf784902dea
// Constant-copy table sha256: 3f990f258046174a55d96937ed43e1b2c81db3c24dd573e518c0797286856b78
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t using UV uv at native base 0; lane mapping is unverified.
in highp float v_am;
uniform highp float late_stack;
uniform highp float intensity;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _27[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const vec4 _34[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t;
in highp vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = _27;
highp vec4 sa[32] = _27;
highp vec4 _output[32] = _27;

highp vec2 unpack2xF16(highp float _198)
{
    return unpackHalf2x16(floatBitsToUint(_198));
}

highp float pack2xF16(highp vec2 _231)
{
    return uintBitsToFloat(packHalf2x16(_231));
}

uvec4 unpack4xU8(highp float _426)
{
    uint _429 = floatBitsToUint(_426);
    return uvec4((((_429) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_429) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_429) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_429) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _443)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_443.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_443.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_443.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_443.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _204 = unpack2xF16(pa[0].x);
    highp vec2 _213 = unpack2xF16(sa[2].z);
    highp vec2 _222 = unpack2xF16(pa[0].y);
    highp vec2 _226 = vec2(_204.x, _204.x) * vec2(_213.x, _213.x) + vec2(_222.x, _222.x);
    highp vec2 _241 = unpack2xF16(pa[0].y);
    highp vec2 _246 = vec2(pack2xF16(vec2(_226.x, _226.y)), pack2xF16(vec2(_241.x, _241.y)));
    pa[0] = vec4(_246.x, _246.y, pa[0].z, pa[0].w);
    highp vec2 _255 = unpack2xF16(pa[0].y);
    highp vec2 _264 = unpack2xF16(sa[2].z);
    highp vec2 _274 = unpack2xF16(pa[0].x);
    highp vec2 _278 = vec2(_255.x, _255.x) * (vec2(0.0) - vec2(_264.x, _264.x)) + vec2(_274.x, _274.x);
    highp vec2 _286 = unpack2xF16(pa[0].y);
    highp vec2 _291 = vec2(pack2xF16(vec2(_278.x, _278.y)), pack2xF16(vec2(_286.x, _286.y)));
    pa[0] = vec4(_291.x, _291.y, pa[0].z, pa[0].w);
    highp vec2 _320 = unpack2xF16(pa[0].y);
    highp vec2 _325 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(sa[2].y).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_320.x, _320.y)));
    pa[0] = vec4(_325.x, _325.y, pa[0].z, pa[0].w);
    highp vec2 _354 = unpack2xF16(pa[0].y);
    highp vec2 _359 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[0].z).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_354.x, _354.y)));
    pa[0] = vec4(_359.x, _359.y, pa[0].z, pa[0].w);
    highp vec2 _388 = unpack2xF16(pa[0].w);
    highp vec2 _393 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(sa[2].y).y, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_388.x, _388.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _393.x, _393.y);
    highp vec4 _400 = vec4(uvec4(0u));
    highp vec4 _404 = vec4(uvec4(0u));
    highp vec4 _408 = vec4(1.0) - vec4(0.0);
    uvec4 _418 = uvec4(round(clamp((_408 * (_400 / vec4(255.0))) + (vec4(0.0) * (_404 / vec4(255.0))), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _459 = _output[0];
    _459.x = pack4xU8(uvec4(_418.x, _418.y, _418.z, unpack4xU8(_output[0].x).w));
    _output[0] = _459;
    uvec4 _474 = unpack4xU8(_output[0].x);
    highp vec4 _482 = _output[0];
    _482.x = pack4xU8(uvec4(_474.x, _474.y, _474.z, uint(round(clamp(unpack2xF16(pa[0].z).x, 0.0, 1.0) * 255.0))));
    _output[0] = _482;
}

void main()
{
pa[0] = texture(t, uv);
    pa[1].x = v_am;
    sa[2].y = intensity;
    sa[2].z = late_stack;
    primary_program();
    uint _487 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_487 >> 0u) & 255u) / 255.0, float((_487 >> 8u) & 255u) / 255.0, float((_487 >> 16u) & 255u) / 255.0, float((_487 >> 24u) & 255u) / 255.0);
}

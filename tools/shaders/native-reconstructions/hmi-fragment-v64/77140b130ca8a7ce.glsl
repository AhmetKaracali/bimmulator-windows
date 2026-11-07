#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 77140b130ca8a7cee0aab7ea128babdcb43afe8e8818e5b21c5e36695054b6e4
// Candidate module sha256: e98323787cf155c7883c4ffb614895fefb4bd7098c84974fda9ae1a4ccc61945
// Native input table sha256: 9c06a396e257c6928cccf1dc0c76ef294250c3cc1c169f97b6d22d49514cf3b6
// Constant-copy table sha256: 8b795201ad9699db7cdb56f5f45810d1b56a0876a225ea3b79d9e550942077ea
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA2 from tex0 using UV vTexCoord at native base 8; lane mapping is unverified.
in highp vec3 vFading;
in highp vec4 vColor;
uniform highp float u_opacity;
precision mediump float;
precision highp int;

const vec4 _27[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D tex0;
in highp vec2 vTexCoord;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = _27;
highp vec4 sa[32] = _27;
highp vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 _output[32] = _27;

highp vec2 unpack2xF16(highp float _232)
{
    return unpackHalf2x16(floatBitsToUint(_232));
}

highp float pack2xF16(highp vec2 _242)
{
    return uintBitsToFloat(packHalf2x16(_242));
}

highp float pack4xU8(uvec4 _383)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_383.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_383.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_383.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_383.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec3 _200 = max(vec3(pa[1].x, pa[1].y, pa[1].z), vec3(0.0));
    internal[0] = vec4(_200.x, _200.y, _200.z, internal[0].w);
    highp vec3 _213 = min(vec3(internal[0].x, internal[0].y, internal[0].z), vec3(1.0));
    internal[0] = vec4(_213.x, _213.y, _213.z, internal[0].w);
    highp vec2 _252 = unpack2xF16(pa[1].y);
    highp vec2 _257 = vec2(pack2xF16(vec2(internal[0].x * internal[0].y, unpack2xF16(pa[1].x).y)), pack2xF16(vec2(_252.x, _252.y)));
    pa[1] = vec4(_257.x, _257.y, pa[1].z, pa[1].w);
    highp vec2 _284 = unpack2xF16(pa[1].y);
    highp vec2 _289 = vec2(pack2xF16(vec2(unpack2xF16(pa[1].x).x * internal[0].z, unpack2xF16(pa[1].x).y)), pack2xF16(vec2(_284.x, _284.y)));
    pa[1] = vec4(_289.x, _289.y, pa[1].z, pa[1].w);
    highp vec2 _318 = unpack2xF16(pa[0].w);
    highp vec2 _323 = vec2(pack2xF16(vec2(unpack2xF16(sa[2].y).y * unpack2xF16(pa[0].z).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_318.x, _318.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _323.x, _323.y);
    highp vec4 _351 = pa[0];
    _351.y = pack2xF16(vec2(unpack2xF16(pa[0].y).x, unpack2xF16(pa[0].z).x * unpack2xF16(pa[1].x).x));
    pa[0] = _351;
    highp vec2 _358 = vec2(pa[0].x, pa[0].y);
    highp vec2 _360 = unpack2xF16(_358.x);
    highp vec2 _362 = unpack2xF16(_358.y);
    uvec4 _376 = uvec4(round(clamp(vec4(_360.x, _360.y, _362.x, _362.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _400 = _output[0];
    _400.x = pack4xU8(uvec4(_376.x, _376.y, _376.z, _376.w));
    _output[0] = _400;
}

void main()
{
pa[2] = texture(tex0, vTexCoord);
    pa[1].x = vFading.x;
    pa[1].y = vFading.y;
    pa[1].z = vFading.z;
    pa[0].x = vColor.x;
    pa[0].y = vColor.y;
    pa[0].z = vColor.z;
    pa[0].w = vColor.w;
    sa[2].y = uintBitsToFloat(0x00000000u);
    primary_program();
    uint _405 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_405 >> 0u) & 255u) / 255.0, float((_405 >> 8u) & 255u) / 255.0, float((_405 >> 16u) & 255u) / 255.0, float((_405 >> 24u) & 255u) / 255.0);
}

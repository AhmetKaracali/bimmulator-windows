#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: d071d981e4ee3d9228a526688d55d7177ab1b63cded0c703c5e18c36bbfafa5c
// Candidate module sha256: 70d8ab9ce2e08aae0c4e279647c028ba3c9b904619d9306e450173abc0820b75
// Native input table sha256: 171496b07b5ce47352e8d4df25408bff5eac3ab32f892476b6664368ee936564
// Constant-copy table sha256: 8c9e64907ee37db199f45e3b0511e881b9e665326b12631c4335d98646255852
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t using UV uv at native base 0; lane mapping is unverified.
uniform highp float sub;
uniform highp vec3 CO;
uniform highp float opacity;
precision mediump float;
precision highp int;

const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t;
in highp vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 sa[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 temp[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 _output[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));

uvec4 unpack4xU8(highp float _262)
{
    uint _265 = floatBitsToUint(_262);
    return uvec4((((_265) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_265) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_265) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_265) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _280)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_280.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_280.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_280.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_280.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void secondary_program()
{
    highp vec4 _206 = sa[5];
    _206.z = (0.0 - sa[4].z) + sa[4].w;
    sa[5] = _206;
    sa[4] = vec4(sa[4].x, sa[4].y, sa[4].z, vec2(1.0 / sa[5].z).x);
    highp vec3 _233 = vec3(sa[2].y, sa[2].z, sa[2].w) * vec3(sa[5].y, sa[5].y, sa[5].y);
    internal[0] = vec4(_233.x, _233.y, _233.z, internal[0].w);
    uvec3 _253 = uvec3(round(clamp(vec3(internal[0].x, internal[0].y, internal[0].z), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _296 = sa[2];
    _296.y = pack4xU8(uvec4(_253.x, _253.y, _253.z, unpack4xU8(sa[2].y).w));
    sa[2] = _296;
}

void primary_program()
{
    highp vec4 _314 = temp[0];
    _314.x = (0.0 - sa[4].z) + pa[0].x;
    temp[0] = _314;
    highp vec4 _328 = internal[0];
    _328.x = sa[4].w * temp[0].x;
    internal[0] = _328;
    highp vec4 _337 = internal[0];
    _337.x = max(internal[0].x, 0.0);
    internal[0] = _337;
    highp vec4 _346 = internal[0];
    _346.x = min(internal[0].x, 1.0);
    internal[0] = _346;
    highp float _352 = 0.0 - 2.0;
    highp vec4 _361 = internal[1];
    _361.x = internal[0].x * _352 + sa[4].x;
    internal[1] = _361;
    highp vec4 _375 = internal[0];
    _375.x = internal[0].x * internal[0].x + 0.0;
    internal[0] = _375;
    highp vec4 _389 = internal[0];
    _389.x = internal[0].x * internal[1].x + 0.0;
    internal[0] = _389;
    highp vec4 _408 = internal[0];
    _408.x = internal[0].x * sa[4].y + pa[0].x;
    internal[0] = _408;
    highp vec4 _428 = pa[0];
    _428.x = pa[0].x * (0.0 - sa[4].y) + internal[0].x;
    pa[0] = _428;
    temp[0] = texture(t, vec2(pa[0].x, pa[0].y));
    highp vec4 _452 = temp[0];
    _452.z = temp[0].y * sa[5].x;
    temp[0] = _452;
    highp vec4 _463 = vec4(uvec4(0u));
    highp vec4 _467 = vec4(1.0) - vec4(0.0);
    uvec4 _477 = uvec4(round(clamp((_467 * (vec4(unpack4xU8(sa[2].y)) / vec4(255.0))) + (vec4(0.0) * (_463 / vec4(255.0))), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _490 = _output[0];
    _490.x = pack4xU8(uvec4(_477.x, _477.y, _477.z, unpack4xU8(_output[0].x).w));
    _output[0] = _490;
    uvec4 _503 = unpack4xU8(_output[0].x);
    highp vec4 _511 = _output[0];
    _511.x = pack4xU8(uvec4(_503.x, _503.y, _503.z, uint(round(clamp(temp[0].z, 0.0, 1.0) * 255.0))));
    _output[0] = _511;
}

void main()
{
pa[0] = texture(t, uv);
    sa[2].y = CO.x;
    sa[2].z = CO.y;
    sa[2].w = CO.z;
    sa[4].x = uintBitsToFloat(0x40400000u);
    sa[4].y = sub;
    sa[4].z = uintBitsToFloat(0x3f666666u);
    sa[4].w = uintBitsToFloat(0x3f7ae148u);
    sa[5].x = opacity;
    sa[5].y = uintBitsToFloat(0x3dcccccdu);
    secondary_program();
    primary_program();
    uint _516 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_516 >> 0u) & 255u) / 255.0, float((_516 >> 8u) & 255u) / 255.0, float((_516 >> 16u) & 255u) / 255.0, float((_516 >> 24u) & 255u) / 255.0);
}

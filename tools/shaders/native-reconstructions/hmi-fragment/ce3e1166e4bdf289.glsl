#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: ce3e1166e4bdf28927cc52b1f35db60ed5a95e283d903d8af742a0fd5bb90fbb
// Candidate module sha256: 19670009ff23e983d8653a33ce0513cc8b0a292c4c2df78510cdd7f2008cd2ac
// Native input table sha256: 76fe9a9254904d69b229fa365924cc49009a35cc2b0a77ca815abb1a811cba74
// Constant-copy table sha256: 9b844435caa57bcea771b81dd8165f9f0f05808f105ae365b1e033f5d8e6abc5
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t using UV uv at native base 0; lane mapping is unverified.
uniform highp float main_menu;
uniform highp vec3 CO;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _27[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t;
in highp vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = _27;
highp vec4 sa[32] = _27;
highp vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 _output[32] = _27;

uvec4 unpack4xU8(highp float _235)
{
    uint _238 = floatBitsToUint(_235);
    return uvec4((((_238) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_238) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_238) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_238) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _253)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_253.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_253.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_253.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_253.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void secondary_program()
{
    highp vec2 _213 = vec2(sa[2].z, sa[2].w);
    uvec3 _226 = uvec3(round(clamp(vec3(vec2(sa[2].x, sa[2].y).y, _213.x, _213.y), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _269 = sa[2];
    _269.y = pack4xU8(uvec4(_226.x, _226.y, _226.z, unpack4xU8(sa[2].y).w));
    sa[2] = _269;
}

void primary_program()
{
    highp vec4 _291 = internal[0];
    _291.x = pa[0].y * sa[3].y + pa[0].z;
    internal[0] = _291;
    highp vec4 _311 = internal[0];
    _311.x = pa[0].z * (0.0 - sa[3].y) + internal[0].x;
    internal[0] = _311;
    highp vec4 _325 = internal[0];
    _325.x = internal[0].x * pa[0].x + 0.0;
    internal[0] = _325;
    highp vec4 _339 = pa[0];
    _339.z = internal[0].x * sa[3].x + 0.0;
    pa[0] = _339;
    highp vec4 _350 = vec4(uvec4(0u));
    highp vec4 _354 = vec4(1.0) - vec4(0.0);
    uvec4 _364 = uvec4(round(clamp((_354 * (vec4(unpack4xU8(sa[2].y)) / vec4(255.0))) + (vec4(0.0) * (_350 / vec4(255.0))), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _377 = _output[0];
    _377.x = pack4xU8(uvec4(_364.x, _364.y, _364.z, unpack4xU8(_output[0].x).w));
    _output[0] = _377;
    uvec4 _390 = unpack4xU8(_output[0].x);
    highp vec4 _398 = _output[0];
    _398.x = pack4xU8(uvec4(_390.x, _390.y, _390.z, uint(round(clamp(pa[0].z, 0.0, 1.0) * 255.0))));
    _output[0] = _398;
}

void main()
{
pa[0] = texture(t, uv);
    sa[2].y = CO.x;
    sa[2].z = CO.y;
    sa[2].w = CO.z;
    sa[3].x = opacity;
    sa[3].y = main_menu;
    secondary_program();
    primary_program();
    uint _403 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_403 >> 0u) & 255u) / 255.0, float((_403 >> 8u) & 255u) / 255.0, float((_403 >> 16u) & 255u) / 255.0, float((_403 >> 24u) & 255u) / 255.0);
}

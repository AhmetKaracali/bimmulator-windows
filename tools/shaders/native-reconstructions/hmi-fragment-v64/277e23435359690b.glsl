#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 277e23435359690bf18af136fbc862ca228d05307a2a0715d72c5353560340fd
// Candidate module sha256: 5332d09be59b2e13708c38262d77b2ac586bf2f275862f257323efa65179050c
// Native input table sha256: a81c2c237084197d17bd15e10c47941af4076816f7e951533598cd6618756fa9
// Constant-copy table sha256: 677c1bbfaf8c3277712d0715fcd55fc432d9f0d5032d029077236eaf8b10234d
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA2 from t using UV uv at native base 8; lane mapping is unverified.
in highp float px;
in highp vec3 p_grd;
in highp float v_stack;
in highp float v_cm;
in highp vec3 p_fd;
in highp float ant;
uniform highp vec3 CO;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _27[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t;
uniform highp sampler2D tn;
in highp vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = _27;
highp vec4 sa[32] = _27;
highp vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 _output[32] = _27;

void secondary_program()
{
    highp vec4 _206 = sa[4];
    _206.z = (0.0 - sa[4].y) + sa[4].z;
    sa[4] = _206;
    highp vec4 _215 = sa[4];
    _215.z = 1.0 / sa[4].z;
    sa[4] = _215;
}

highp float pack4xU8(uvec4 _796)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_796.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_796.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_796.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_796.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec4 _231 = pa[2];
    highp vec4 _235 = vec4(greaterThanEqual(vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y), _231));
    pa[0] = vec4(pa[0].x, pa[0].y, _235.x, _235.y);
    pa[1] = vec4(_235.z, _235.w, pa[1].z, pa[1].w);
    highp vec4 _261 = pa[0];
    _261.z = pa[0].w * (0.0 - sa[4].x) + pa[2].x;
    pa[0] = _261;
    highp vec4 _272 = pa[0];
    _272.w = uintBitsToFloat(floatBitsToUint(pa[1].w));
    pa[0] = _272;
    highp vec2 _288 = (vec2(0.0) - vec2(pa[1].z, pa[1].z)) + vec2(pa[0].z, pa[0].w);
    internal[0] = vec4(_288.x, _288.y, internal[0].z, internal[0].w);
    highp vec2 _304 = vec2(pa[3].w, pa[4].x);
    highp vec4 _307 = internal[1];
    _307.x = 1.0 / internal[0].y;
    internal[1] = _307;
    pa[0] = vec4(pa[0].x, pa[0].y, _304.x, _304.y);
    highp vec4 _325 = internal[2];
    _325.x = (0.0 - sa[4].y) + pa[0].y;
    internal[2] = _325;
    highp vec4 _339 = internal[1];
    highp vec4 _344 = internal[0];
    highp vec3 _348 = vec3(_339.x * _344.x);
    highp vec4 _351 = internal[1];
    _351.x = sa[4].z * internal[2].x;
    internal[1] = _351;
    internal[0] = vec4(_348.x, _348.y, _348.z, internal[0].w);
    highp vec2 _370 = (vec2(0.0) - vec2(pa[3].z, pa[3].z)) + vec2(pa[0].z, pa[0].w);
    internal[2] = vec4(internal[2].x, _370.x, _370.y, internal[2].w);
    highp vec4 _382 = pa[0];
    _382.z = 1.0 / internal[2].y;
    pa[0] = _382;
    highp vec4 _396 = internal[1];
    _396.y = internal[2].z * pa[0].z + 0.0;
    internal[1] = _396;
    highp vec2 _403 = vec2(internal[1].x, internal[1].y);
    internal[0] = vec4(internal[0].x, _403.x, _403.y, internal[0].w);
    highp vec3 _415 = max(vec3(internal[0].x, internal[0].y, internal[0].z), vec3(0.0));
    internal[0] = vec4(_415.x, _415.y, _415.z, internal[0].w);
    highp vec3 _428 = min(vec3(internal[0].x, internal[0].y, internal[0].z), vec3(1.0));
    internal[0] = vec4(_428.x, _428.y, _428.z, internal[0].w);
    highp vec3 _441 = vec3(0.0) - vec3(2.0);
    highp vec3 _450 = vec3(internal[0].x, internal[0].y, internal[0].z) * _441 + vec3(sa[2].y, sa[2].y, sa[2].y);
    internal[1] = vec4(_450.x, _450.y, _450.z, internal[1].w);
    highp vec3 _470 = vec3(internal[0].x, internal[0].y, internal[0].z) * vec3(internal[0].x, internal[0].y, internal[0].z) + vec3(0.0);
    internal[0] = vec4(_470.x, _470.y, _470.z, internal[0].w);
    highp vec3 _490 = vec3(internal[0].x, internal[0].y, internal[0].z) * vec3(internal[1].x, internal[1].y, internal[1].z) + vec3(0.0);
    internal[0] = vec4(_490.x, _490.y, _490.z, internal[0].w);
    highp vec4 _503 = internal[1];
    _503.x = log2(abs(internal[0].x));
    internal[1] = _503;
    highp vec4 _517 = internal[1];
    _517.x = internal[1].x * sa[3].z + 0.0;
    internal[1] = _517;
    highp vec4 _531 = internal[2];
    _531.x = internal[0].y * pa[4].y + 1.0;
    internal[2] = _531;
    highp float _537 = exp2(internal[1].x);
    highp vec4 _542 = pa[4];
    highp vec4 _554 = pa[0];
    _554.z = isnan(_537) ? 1.0 : _537;
    pa[0] = _554;
    highp vec4 _557 = internal[1];
    _557.x = (0.0 - _542.y) + internal[2].x;
    internal[1] = _557;
    highp vec4 _565 = pa[0];
    _565.y = internal[0].z;
    pa[0] = _565;
    highp vec2 _575 = (vec2(0.0) - vec2(pa[0].x, pa[0].y)) + vec2(1.0);
    pa[0] = vec4(_575.x, _575.y, pa[0].z, pa[0].w);
    highp vec4 _597 = internal[2];
    _597.x = pa[0].z * pa[4].y + pa[0].x;
    internal[2] = _597;
    highp vec4 _617 = internal[2];
    _617.x = pa[0].x * (0.0 - pa[4].y) + internal[2].x;
    internal[2] = _617;
    highp vec4 _631 = internal[2];
    _631.x = internal[2].x * pa[1].x + 0.0;
    internal[2] = _631;
    highp vec4 _645 = internal[2];
    _645.x = internal[2].x * pa[4].z + 0.0;
    internal[2] = _645;
    highp vec4 _655 = internal[2];
    highp vec4 _660 = internal[1];
    highp vec4 _666 = internal[1];
    _666.x = log2(abs(pa[0].y));
    internal[1] = _666;
    highp vec4 _669 = pa[0];
    _669.x = _655.x * _660.x;
    pa[0] = _669;
    highp vec4 _683 = internal[1];
    _683.x = internal[1].x * sa[4].w + 0.0;
    internal[1] = _683;
    highp float _688 = internal[1].x;
    highp vec4 _694 = internal[2];
    _694.x = isnan(_688) ? 1.0 : exp2(_688);
    internal[2] = _694;
    highp vec4 _708 = internal[1];
    _708.x = internal[2].x * pa[2].z + 1.0;
    internal[1] = _708;
    highp vec4 _723 = internal[1];
    _723.x = (0.0 - internal[2].x) + internal[1].x;
    internal[1] = _723;
    highp vec4 _746 = internal[1];
    _746.x = internal[0].z * internal[1].x;
    internal[1] = _746;
    internal[0] = vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y);
    highp vec4 _761 = pa[0];
    _761.y = internal[1].x * pa[4].w + 0.0;
    pa[0] = _761;
    internal[0] = vec4(pa[0].x, pa[0].x, pa[0].x, pa[0].y) * internal[0];
    uvec4 _789 = uvec4(round(clamp(internal[0], vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _812 = _output[0];
    _812.x = pack4xU8(uvec4(_789.x, _789.y, _789.z, _789.w));
    _output[0] = _812;
}

void main()
{
pa[2] = texture(t, uv);
    pa[3].x = px;
    pa[0].x = p_grd.x;
    pa[0].y = p_grd.y;
    pa[0].z = p_grd.z;
    pa[4].x = v_stack;
    pa[5].x = v_cm;
    pa[1].x = p_fd.x;
    pa[1].y = p_fd.y;
    pa[1].z = p_fd.z;
    pa[6].x = ant;
    sa[2].y = uintBitsToFloat(0x40400000u);
    sa[2].z = CO.x;
    sa[2].w = CO.y;
    sa[3].x = CO.z;
    sa[3].y = opacity;
    sa[3].z = uintBitsToFloat(0x40c00000u);
    sa[3].w = uintBitsToFloat(0xc4358000u);
    sa[4].x = uintBitsToFloat(0x3be56042u);
    sa[4].y = uintBitsToFloat(0x3f8ccccdu);
    sa[4].z = uintBitsToFloat(0x3f4ccccdu);
    sa[4].w = uintBitsToFloat(0x3eb33333u);
    secondary_program();
    primary_program();
    uint _817 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_817 >> 0u) & 255u) / 255.0, float((_817 >> 8u) & 255u) / 255.0, float((_817 >> 16u) & 255u) / 255.0, float((_817 >> 24u) & 255u) / 255.0);
}

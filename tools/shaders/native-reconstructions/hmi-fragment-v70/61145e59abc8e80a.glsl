#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 61145e59abc8e80a8e97022962b9372379407f38fc08185d190dd165a38f8014
// Candidate module sha256: 55a0409e428ae50b9ef436b38cd6e0993b4366429de4bb417b8af4d3f3ffb1e0
// Native input table sha256: cbd80d4174afb22a2e0eece97f094d501b2834b556f4a956fb2c06136e6818c1
// Constant-copy table sha256: d184627eafcedabb718c348f97d931c9a95a6a755923b87acd350f0ff5cab2cf
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA0 from t1 using UV uv at native base 0; lane mapping is unverified.
in highp float v_am;
in highp float v_usr_modality;
uniform highp float opacity;
precision mediump float;
precision highp int;

const vec4 _27[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const vec4 _34[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t1;
in highp vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = _27;
highp vec4 sa[32] = _27;
highp vec4 _output[32] = _27;

highp vec2 unpack2xF16(highp float _198)
{
    return unpackHalf2x16(floatBitsToUint(_198));
}

highp float pack2xF16(highp vec2 _221)
{
    return uintBitsToFloat(packHalf2x16(_221));
}

uvec4 unpack4xU8(highp float _394)
{
    uint _397 = floatBitsToUint(_394);
    return uvec4((((_397) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_397) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_397) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_397) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _414)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_414.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_414.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_414.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_414.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _231 = unpack2xF16(pa[0].y);
    highp vec2 _236 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].z).x * unpack2xF16(pa[0].y).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_231.x, _231.y)));
    pa[0] = vec4(_236.x, _236.y, pa[0].z, pa[0].w);
    highp vec2 _245 = unpack2xF16(pa[0].w);
    highp vec2 _252 = vec2(_245.x, _245.x) * vec2(0.75) + vec2(1.0);
    highp vec2 _260 = unpack2xF16(pa[0].w);
    highp vec2 _265 = vec2(pack2xF16(vec2(_252.x, _252.y)), pack2xF16(vec2(_260.x, _260.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _265.x, _265.y);
    highp vec2 _295 = unpack2xF16(pa[0].w);
    highp vec2 _300 = vec2(pack2xF16(vec2((0.0 - unpack2xF16(pa[0].w).x) + unpack2xF16(pa[0].z).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_295.x, _295.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _300.x, _300.y);
    highp vec2 _329 = unpack2xF16(pa[0].y);
    highp vec2 _334 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(pa[0].z).x, unpack2xF16(pa[0].x).y)), pack2xF16(vec2(_329.x, _329.y)));
    pa[0] = vec4(_334.x, _334.y, pa[0].z, pa[0].w);
    highp vec2 _363 = unpack2xF16(pa[0].w);
    highp vec2 _368 = vec2(pack2xF16(vec2(unpack2xF16(pa[0].x).x * unpack2xF16(sa[2].y).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_363.x, _363.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _368.x, _368.y);
    highp vec4 _376 = _output[0];
    _376.x = uintBitsToFloat(4294967295u);
    _output[0] = _376;
    uvec4 _408 = unpack4xU8(_output[0].x);
    highp vec4 _430 = _output[0];
    _430.x = pack4xU8(uvec4(_408.x, _408.y, _408.z, uint(round(clamp(unpack2xF16(pa[0].z).x, 0.0, 1.0) * 255.0))));
    _output[0] = _430;
}

void main()
{
pa[0] = texture(t1, uv);
    pa[1].x = v_am;
    pa[2].x = v_usr_modality;
    sa[2].y = opacity;
    primary_program();
    uint _435 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_435 >> 0u) & 255u) / 255.0, float((_435 >> 8u) & 255u) / 255.0, float((_435 >> 16u) & 255u) / 255.0, float((_435 >> 24u) & 255u) / 255.0);
}

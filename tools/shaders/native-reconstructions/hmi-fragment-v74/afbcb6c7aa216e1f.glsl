#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: afbcb6c7aa216e1f273960a0fb3f566a55fd4fe8d02ff737f8f1ae53e2d36b2c
// Candidate module sha256: 63a574485ac9c8ea2cb32c819ad09ba208da7138a59dfce66c49b613878f8ac9
// Native input table sha256: 7ce70318fcad82a261361b8c4baf411f45f981bb7cef8ae6e8908b19bfe132b2
// Constant-copy table sha256: d184627eafcedabb718c348f97d931c9a95a6a755923b87acd350f0ff5cab2cf
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Host interface adapter: vColor is encoded as packed F16 varying words.
// Host uniform adapter: exact-hash scalar u_opacity is packed into the high F16 lane of SA2.y; runtime candidate.
// Sample result candidate: texture a maps to native PA1.x for GL_ALPHA (0x1909), V89 font-atlas upload; native lane mapping is not independently verified.
in highp float fFading;
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

highp vec2 unpack2xF16(highp float _198)
{
    return unpackHalf2x16(floatBitsToUint(_198));
}

highp float pack2xF16(highp vec2 _221)
{
    return uintBitsToFloat(packHalf2x16(_221));
}

uvec4 unpack4xU8(highp float _306)
{
    uint _309 = floatBitsToUint(_306);
    return uvec4((((_309) >> uint(int(0u))) & ((1u << uint(int(8u))) - 1u)), (((_309) >> uint(int(8u))) & ((1u << uint(int(8u))) - 1u)), (((_309) >> uint(int(16u))) & ((1u << uint(int(8u))) - 1u)), (((_309) >> uint(int(24u))) & ((1u << uint(int(8u))) - 1u)));
}

highp float pack4xU8(uvec4 _324)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_324.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_324.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_324.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_324.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _231 = unpack2xF16(pa[0].w);
    highp vec2 _236 = vec2(pack2xF16(vec2(unpack2xF16(sa[2].y).y * unpack2xF16(pa[0].z).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_231.x, _231.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _236.x, _236.y);
    highp vec4 _248 = internal[0];
    _248.x = max(pa[1].x, 0.0);
    internal[0] = _248;
    highp vec4 _257 = internal[1];
    _257.x = min(internal[0].x, 1.0);
    internal[1] = _257;
    highp vec4 _273 = internal[0];
    _273.x = unpack2xF16(pa[0].z).x * internal[1].x;
    internal[0] = _273;
    highp vec2 _280 = vec2(pa[0].x, pa[0].y);
    highp vec2 _282 = unpack2xF16(_280.x);
    uvec3 _297 = uvec3(round(clamp(vec3(_282.x, _282.y, unpack2xF16(_280.y).x), vec3(0.0), vec3(1.0)) * vec3(255.0)));
    highp vec4 _340 = _output[0];
    _340.x = pack4xU8(uvec4(_297.x, _297.y, _297.z, unpack4xU8(_output[0].x).w));
    _output[0] = _340;
    uvec4 _353 = unpack4xU8(_output[0].x);
    highp vec4 _361 = _output[0];
    _361.x = pack4xU8(uvec4(_353.x, _353.y, _353.z, uint(round(clamp(internal[0].x, 0.0, 1.0) * 255.0))));
    _output[0] = _361;
}

void main()
{
pa[1].x = texture(tex0, vTexCoord).a;
    pa[2].x = fFading;
    pa[0].x = uintBitsToFloat(packHalf2x16(vColor.xy));
    pa[0].y = uintBitsToFloat(packHalf2x16(vec2(vColor.z, 0.0)));
    pa[0].z = uintBitsToFloat(packHalf2x16(vec2(vColor.w, 0.0)));
    pa[0].w = 0.0;
    sa[2].y = uintBitsToFloat(packHalf2x16(vec2(0.0, u_opacity)));
    primary_program();
    uint _366 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_366 >> 0u) & 255u) / 255.0, float((_366 >> 8u) & 255u) / 255.0, float((_366 >> 16u) & 255u) / 255.0, float((_366 >> 24u) & 255u) / 255.0);
}

#version 300 es
// Reconstructed host ESSL from the exact BMW fragment .shd and finalized USSE.
// .shd sha256: 9af0a57ef55d32dd32464f117c5d692b60c63e2d87e7986b733c7ac74eb4457e
// Candidate module sha256: da6e2992f5f606caf01938f8f6d3b93fddd0ce200f51043a4c7ab8b3fa38bca7
// Native input table sha256: 56cd27d7ae3f097b38f884fc71b7796a4b534364189abeb34a0cea373a63d7c0
// Constant-copy table sha256: b95d127348a44ddb0727a5bd03c1e8ab3de0b9e37b636dfafb68585feef31f15
// Packed U8 output candidate: low byte -> R, then G, B, high byte -> A; native IMG lane unverified.
// Sample result candidate: full RGBA in PA1 from t0 using UV uv at native base 4; lane mapping is unverified.
in highp vec3 fd;
uniform highp float pressed;
uniform highp vec3 CO_BG_L;
uniform highp vec3 CO_BG_R;
uniform highp vec3 CO_BG_TOUCH;
uniform highp float usr_modality;
uniform highp float composition;
uniform highp float opacity;
precision mediump float;
precision highp int;

const int _40[4] = int[](0, 0, 0, 0);
const bool _46[4] = bool[](false, false, false, false);

uniform highp sampler2D t0;
in highp vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
highp vec4 pa[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 sa[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 temp[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
highp vec4 _output[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));

highp vec2 unpack2xF16(highp float _198)
{
    return unpackHalf2x16(floatBitsToUint(_198));
}

highp float pack2xF16(highp vec2 _224)
{
    return uintBitsToFloat(packHalf2x16(_224));
}

void secondary_program()
{
    highp vec2 _204 = unpack2xF16(sa[4].y);
    highp vec2 _214 = unpack2xF16(sa[4].x);
    highp vec3 _219 = vec3(_204.x, _204.y, _204.y) * vec3(_214.y, _214.y, _214.y);
    highp vec2 _239 = vec2(pack2xF16(vec2(_219.x, _219.y)), pack2xF16(vec2(_219.z, unpack2xF16(sa[5].y).y)));
    sa[5] = vec4(_239.x, _239.y, sa[5].z, sa[5].w);
    highp vec2 _261 = unpack2xF16(sa[4].y);
    highp vec2 _266 = vec2(pack2xF16(vec2(unpack2xF16(sa[4].z).y + 1.0, unpack2xF16(sa[4].x).y)), pack2xF16(vec2(_261.x, _261.y)));
    sa[4] = vec4(_266.x, _266.y, sa[4].z, sa[4].w);
    highp vec2 _296 = unpack2xF16(sa[4].w);
    highp vec2 _301 = vec2(pack2xF16(vec2((0.0 - unpack2xF16(sa[4].x).x) + unpack2xF16(sa[4].z).y, unpack2xF16(sa[4].z).y)), pack2xF16(vec2(_296.x, _296.y)));
    sa[4] = vec4(sa[4].x, sa[4].y, _301.x, _301.y);
    highp vec4 _324 = sa[2];
    _324.y = pack2xF16(vec2(vec3(1.0 / unpack2xF16(sa[4].z).x).x, unpack2xF16(sa[2].y).y));
    sa[2] = _324;
}

highp float pack4xU8(uvec4 _1062)
{
    return uintBitsToFloat(((((((((((((0u) & ~(((1u << uint(8)) - 1u) << uint(0))) | (((_1062.x) & ((1u << uint(8)) - 1u)) << uint(0)))) & ~(((1u << uint(8)) - 1u) << uint(8))) | (((_1062.y) & ((1u << uint(8)) - 1u)) << uint(8)))) & ~(((1u << uint(8)) - 1u) << uint(16))) | (((_1062.z) & ((1u << uint(8)) - 1u)) << uint(16)))) & ~(((1u << uint(8)) - 1u) << uint(24))) | (((_1062.w) & ((1u << uint(8)) - 1u)) << uint(24))));
}

void primary_program()
{
    highp vec2 _333 = unpack2xF16(pa[0].z);
    highp vec2 _345 = vec2(sa[3].x, sa[3].y);
    highp vec2 _347 = unpack2xF16(_345.x);
    highp vec2 _349 = unpack2xF16(_345.y);
    highp vec2 _361 = vec2(sa[3].z, sa[3].w);
    highp vec2 _363 = unpack2xF16(_361.x);
    highp vec2 _365 = unpack2xF16(_361.y);
    highp vec4 _371 = vec4(_333.x, _333.x, _333.x, _333.x) * vec4(_347.x, _347.y, _349.x, _349.y) + vec4(_363.x, _363.y, _365.x, _365.y);
    highp vec2 _380 = vec2(pack2xF16(vec2(_371.x, _371.y)), pack2xF16(vec2(_371.z, _371.w)));
    temp[0] = vec4(_380.x, _380.y, temp[0].z, temp[0].w);
    highp vec2 _389 = unpack2xF16(pa[0].z);
    highp vec2 _401 = vec2(sa[3].z, sa[3].w);
    highp vec2 _403 = unpack2xF16(_401.x);
    highp vec2 _405 = unpack2xF16(_401.y);
    highp vec2 _418 = vec2(temp[0].x, temp[0].y);
    highp vec2 _420 = unpack2xF16(_418.x);
    highp vec2 _422 = unpack2xF16(_418.y);
    highp vec4 _428 = vec4(_389.x, _389.x, _389.x, _389.x) * (vec4(0.0) - vec4(_403.x, _403.y, _405.x, _405.y)) + vec4(_420.x, _420.y, _422.x, _422.y);
    highp vec2 _437 = vec2(pack2xF16(vec2(_428.x, _428.y)), pack2xF16(vec2(_428.z, _428.w)));
    temp[0] = vec4(temp[0].x, temp[0].y, _437.x, _437.y);
    highp vec4 _451 = temp[0];
    _451.x = uintBitsToFloat(floatBitsToUint(sa[2].w));
    temp[0] = _451;
    highp vec2 _457 = unpack2xF16(temp[0].x);
    highp vec2 _469 = vec2(sa[2].z, sa[2].w);
    highp vec2 _471 = unpack2xF16(_469.x);
    highp vec2 _473 = unpack2xF16(_469.y);
    highp vec2 _485 = vec2(temp[0].z, temp[0].w);
    highp vec2 _487 = unpack2xF16(_485.x);
    highp vec2 _489 = unpack2xF16(_485.y);
    highp vec4 _495 = vec4(_457.y, _457.y, _457.y, _457.y) * vec4(_471.x, _471.y, _473.x, _473.y) + vec4(_487.x, _487.y, _489.x, _489.y);
    highp vec2 _504 = vec2(pack2xF16(vec2(_495.x, _495.y)), pack2xF16(vec2(_495.z, _495.w)));
    temp[0] = vec4(_504.x, _504.y, temp[0].z, temp[0].w);
    highp vec2 _514 = vec2(temp[0].z, temp[0].w);
    highp vec2 _516 = unpack2xF16(_514.x);
    highp vec2 _528 = unpack2xF16(sa[2].w);
    highp vec2 _540 = vec2(temp[0].x, temp[0].y);
    highp vec2 _542 = unpack2xF16(_540.x);
    highp vec3 _549 = vec3(_516.x, _516.y, unpack2xF16(_514.y).x) * (vec3(0.0) - vec3(_528.y, _528.y, _528.y)) + vec3(_542.x, _542.y, unpack2xF16(_540.y).x);
    internal[0] = vec4(_549.x, _549.y, _549.z, internal[0].w);
    highp vec2 _579 = unpack2xF16(pa[0].w);
    highp vec2 _584 = vec2(pack2xF16(vec2((0.0 - unpack2xF16(sa[4].x).x) + unpack2xF16(pa[1].x).x, unpack2xF16(pa[0].z).y)), pack2xF16(vec2(_579.x, _579.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _584.x, _584.y);
    highp vec2 _613 = unpack2xF16(pa[1].y);
    highp vec2 _618 = vec2(pack2xF16(vec2(unpack2xF16(sa[2].y).x * unpack2xF16(pa[0].z).x, unpack2xF16(pa[1].x).y)), pack2xF16(vec2(_613.x, _613.y)));
    pa[1] = vec4(_618.x, _618.y, pa[1].z, pa[1].w);
    highp vec2 _627 = unpack2xF16(pa[0].z);
    highp vec2 _636 = unpack2xF16(sa[2].w);
    highp vec2 _645 = unpack2xF16(pa[0].w);
    highp vec2 _649 = vec2(_627.y, _627.y) * vec2(_636.y, _636.y) + vec2(_645.x, _645.x);
    highp vec2 _657 = unpack2xF16(pa[0].w);
    highp vec2 _662 = vec2(pack2xF16(vec2(_649.x, _649.y)), pack2xF16(vec2(_657.x, _657.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _662.x, _662.y);
    highp vec2 _671 = unpack2xF16(pa[0].w);
    highp vec2 _680 = unpack2xF16(sa[2].w);
    highp vec2 _690 = unpack2xF16(pa[0].z);
    highp vec2 _694 = vec2(_671.x, _671.x) * (vec2(0.0) - vec2(_680.y, _680.y)) + vec2(_690.x, _690.x);
    highp vec2 _702 = unpack2xF16(temp[0].y);
    highp vec2 _707 = vec2(pack2xF16(vec2(_694.x, _694.y)), pack2xF16(vec2(_702.x, _702.y)));
    temp[0] = vec4(_707.x, _707.y, temp[0].z, temp[0].w);
    highp vec2 _716 = unpack2xF16(pa[0].x);
    highp vec2 _727 = vec2(pa[0].x, pa[0].y);
    highp vec2 _735 = (vec2(0.0) - vec2(_716.x, _716.x)) + vec2(unpack2xF16(_727.x).y, unpack2xF16(_727.y).x);
    internal[1] = vec4(internal[1].x, _735.x, _735.y, internal[1].w);
    highp vec2 _753 = vec2(sa[5].x, sa[5].y);
    highp vec2 _755 = unpack2xF16(_753.x);
    highp vec3 _762 = vec3(internal[0].x, internal[0].y, internal[0].z) + vec3(_755.x, _755.y, unpack2xF16(_753.y).x);
    highp vec4 _765 = internal[1];
    highp vec2 _769 = vec2(1.0 / _765.y);
    internal[2] = vec4(_762.x, _762.y, _762.z, internal[2].w);
    highp vec2 _780 = unpack2xF16(pa[0].y);
    highp vec2 _785 = vec2(pack2xF16(vec2(_769.x, _769.y)), pack2xF16(vec2(_780.x, _780.y)));
    pa[0] = vec4(_785.x, _785.y, pa[0].z, pa[0].w);
    highp vec2 _812 = unpack2xF16(pa[1].y);
    highp vec2 _817 = vec2(pack2xF16(vec2(unpack2xF16(pa[1].x).x, unpack2xF16(pa[0].x).x * internal[1].z)), pack2xF16(vec2(_812.x, _812.y)));
    pa[1] = vec4(_817.x, _817.y, pa[1].z, pa[1].w);
    highp vec2 _826 = unpack2xF16(pa[1].x);
    highp vec2 _830 = max(vec2(_826.x, _826.y), vec2(0.0));
    highp vec2 _838 = unpack2xF16(pa[0].y);
    highp vec2 _843 = vec2(pack2xF16(vec2(_830.x, _830.y)), pack2xF16(vec2(_838.x, _838.y)));
    pa[0] = vec4(_843.x, _843.y, pa[0].z, pa[0].w);
    highp vec2 _852 = unpack2xF16(pa[0].x);
    highp vec2 _857 = min(vec2(_852.x, _852.y), vec2(1.0));
    highp vec2 _865 = unpack2xF16(pa[0].y);
    highp vec2 _870 = vec2(pack2xF16(vec2(_857.x, _857.y)), pack2xF16(vec2(_865.x, _865.y)));
    pa[0] = vec4(_870.x, _870.y, pa[0].z, pa[0].w);
    highp vec2 _879 = unpack2xF16(pa[0].x);
    highp vec2 _884 = vec2(0.0) - vec2(2.0);
    highp vec2 _887 = vec2(_879.x, _879.y) * _884 + vec2(3.0);
    highp vec2 _895 = unpack2xF16(pa[0].w);
    highp vec2 _900 = vec2(pack2xF16(vec2(_887.x, _887.y)), pack2xF16(vec2(_895.x, _895.y)));
    pa[0] = vec4(pa[0].x, pa[0].y, _900.x, _900.y);
    highp vec2 _909 = unpack2xF16(pa[0].x);
    highp vec2 _918 = unpack2xF16(pa[0].x);
    highp vec2 _922 = vec2(_909.x, _909.y) * vec2(_918.x, _918.y);
    highp vec2 _930 = unpack2xF16(pa[0].y);
    highp vec2 _935 = vec2(pack2xF16(vec2(_922.x, _922.y)), pack2xF16(vec2(_930.x, _930.y)));
    pa[0] = vec4(_935.x, _935.y, pa[0].z, pa[0].w);
    highp vec2 _944 = unpack2xF16(pa[0].z);
    highp vec2 _953 = unpack2xF16(pa[0].x);
    highp vec2 _957 = vec2(_944.x, _944.y) * vec2(_953.x, _953.y);
    internal[0] = vec4(_957.x, _957.y, internal[0].z, internal[0].w);
    highp vec2 _975 = unpack2xF16(temp[0].x);
    highp vec4 _981 = vec4(internal[2].x, internal[2].y, internal[2].z, internal[2].x) * vec4(_975.x, _975.x, _975.x, _975.x);
    highp vec2 _1001 = vec2(pack2xF16(vec2(_981.x, _981.y)), pack2xF16(vec2(_981.z, _981.w)));
    pa[0] = vec4(_1001.x, _1001.y, pa[0].z, pa[0].w);
    highp vec4 _1007 = internal[0];
    _1007.x = internal[0].y * internal[0].x;
    internal[0] = _1007;
    highp vec4 _1030 = pa[0];
    _1030.y = pack2xF16(vec2(unpack2xF16(pa[0].y).x, internal[0].x * unpack2xF16(sa[2].y).y));
    pa[0] = _1030;
    highp vec2 _1037 = vec2(pa[0].x, pa[0].y);
    highp vec2 _1039 = unpack2xF16(_1037.x);
    highp vec2 _1041 = unpack2xF16(_1037.y);
    uvec4 _1055 = uvec4(round(clamp(vec4(_1039.x, _1039.y, _1041.x, _1041.y), vec4(0.0), vec4(1.0)) * vec4(255.0)));
    highp vec4 _1078 = _output[0];
    _1078.x = pack4xU8(uvec4(_1055.x, _1055.y, _1055.z, _1055.w));
    _output[0] = _1078;
}

void main()
{
pa[1] = texture(t0, uv);
    pa[0].x = fd.x;
    pa[0].y = fd.y;
    pa[0].z = fd.z;
    sa[2].y = uintBitsToFloat(0x40400000u);
    sa[2].z = CO_BG_TOUCH.x;
    sa[2].w = CO_BG_TOUCH.z;
    sa[3].x = CO_BG_R.x;
    sa[3].y = CO_BG_R.z;
    sa[3].z = CO_BG_L.x;
    sa[3].w = CO_BG_L.z;
    sa[4].x = uintBitsToFloat(0x3f800000u);
    sa[4].y = uintBitsToFloat(0x3e051eb8u);
    sa[4].z = uintBitsToFloat(0x3cf5c28fu);
    secondary_program();
    primary_program();
    uint _1083 = floatBitsToUint(_output[0].x);
    bmwFragmentColor = vec4(float((_1083 >> 0u) & 255u) / 255.0, float((_1083 >> 8u) & 255u) / 255.0, float((_1083 >> 16u) & 255u) / 255.0, float((_1083 >> 24u) & 255u) / 255.0);
}

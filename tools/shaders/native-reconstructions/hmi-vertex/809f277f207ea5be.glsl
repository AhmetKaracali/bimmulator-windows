#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 809f277f207ea5be31df9ccc4dd380f459c41bad5897da6ed7ac46365aea2967
// Candidate module sha256: bc431d88eafefa7c3292b0caca2907e0ba0a678bef69e88475ba99e22c4721ff
// Constant-copy table sha256: fc086ba4a6ec6bb9c264d5e9c99ac5f5737e116c29a3b4d4cb81855ed364078d
uniform float size_x_rel_tilt;
uniform float size_x;
uniform float size_z;
uniform float composition;
uniform float pressed;
uniform mat4 u_MVPMatrix;
uniform float mppd_composition;
uniform float opacity;
uniform float fade_squeeze;
uniform float fade_out;

const vec4 _53[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _66[4] = int[](0, 0, 0, 0);
const bool _72[4] = bool[](false, false, false, false);

in vec2 a_TextureCoordinate;
in vec4 a_Color;
in vec3 a_Position;
const vec4 attribute_register_3 = vec4(0.0);
const vec4 attribute_register_4 = vec4(0.0);
const vec4 attribute_register_5 = vec4(0.0);
const vec4 attribute_register_6 = vec4(0.0);
const vec4 attribute_register_7 = vec4(0.0);
const vec4 attribute_register_8 = vec4(0.0);
const vec4 attribute_register_9 = vec4(0.0);
const vec4 attribute_register_10 = vec4(0.0);
const vec4 attribute_register_11 = vec4(0.0);
const vec4 attribute_register_12 = vec4(0.0);
const vec4 attribute_register_13 = vec4(0.0);
const vec4 attribute_register_14 = vec4(0.0);
const vec4 attribute_register_15 = vec4(0.0);
out vec4 shd;
out vec3 fd;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void secondary_program()
{
    vec4 _248 = sa[10];
    _248.z = 1.0;
    sa[10] = _248;
    vec4 _270 = sa[10];
    _270.x = sa[8].z * (0.0 - sa[8].y) + sa[8].y;
    sa[10] = _270;
    vec4 _285 = sa[9];
    _285.x = sa[8].w * sa[9].x;
    sa[9] = _285;
    vec4 _300 = sa[8];
    _300.w = sa[9].z * sa[9].y;
    sa[8] = _300;
    vec4 _308 = sa[10];
    _308.w = sa[7].x;
    sa[10] = _308;
    vec4 _316 = sa[8];
    _316.z = sa[7].y;
    sa[8] = _316;
    vec4 _326 = internal[0];
    _326.x = 64.0 + sa[6].w;
    internal[0] = _326;
    sa[8] = vec4(sa[8].x, vec2(1.0 / internal[0].x).x, sa[8].z, sa[8].w);
    vec4 _345 = internal[0];
    _345.x = 1.0 + sa[7].z;
    internal[0] = _345;
    vec4 _365 = sa[7];
    _365.x = sa[7].w * internal[0].x + (0.0 - sa[7].z);
    sa[7] = _365;
    vec4 _379 = sa[7];
    _379.y = sa[7].x + sa[7].z;
    sa[7] = _379;
}

void primary_program()
{
    vec4 _390 = pa[0];
    _390.z = pa[0].y;
    pa[0] = _390;
    vec4 _394 = pa[0];
    vec4 _395 = pa[1];
    vec4 _405 = vec4(greaterThanEqual(vec4(_394.z, _394.w, _395.x, _395.y), vec4(0.5, 0.25, 0.5, 0.5)));
    pa[0] = vec4(pa[0].x, pa[0].y, _405.x, _405.y);
    pa[1] = vec4(_405.z, _405.w, pa[1].z, pa[1].w);
    vec4 _421 = pa[0];
    _421.w = (0.0 - pa[0].z) + 1.0;
    pa[0] = _421;
    vec2 _436 = vec2(sa[6].z, sa[6].z) * vec2(pa[0].z, pa[0].w);
    pa[0] = vec4(pa[0].x, pa[0].y, _436.x, _436.y);
    vec4 _458 = internal[0];
    _458.x = pa[0].w * pa[1].y + pa[0].y;
    internal[0] = _458;
    vec4 _478 = internal[0];
    _478.x = pa[0].z * (0.0 - pa[1].y) + internal[0].x;
    internal[0] = _478;
    vec2 _493 = vec2(pa[2].x, pa[2].y);
    vec3 _504 = vec3(_493.x, _493.y, vec2(pa[2].z, pa[2].w).x);
    internal[1] = vec4(_504.x, _504.y, _504.z, internal[1].w);
    vec4 _526 = pa[0];
    _526.x = pa[0].x * sa[6].w + internal[1].x;
    pa[0] = _526;
    vec4 _545 = internal[0];
    _545.x = internal[0].x * sa[8].x + internal[1].z;
    internal[0] = _545;
    vec4 _566 = internal[0];
    _566.x = pa[1].x * (0.0 - sa[10].x) + internal[0].x;
    internal[0] = _566;
    vec4 _585 = internal[0];
    _585.x = pa[1].x * sa[9].x + internal[0].x;
    internal[0] = _585;
    internal[2] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(pa[0].x, pa[0].x, pa[0].x, pa[0].x);
    internal[1] = vec4(internal[1].y, internal[1].y, internal[1].y, internal[1].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[2];
    internal[0] = vec4(internal[0].x, internal[0].x, internal[0].x, internal[0].x) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[1];
    vec2 _669 = vec2(1.0) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_669.x, _669.y, _output[0].z, _output[0].w);
    vec2 _687 = vec2(sa[6].x, sa[6].y) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _687.x, _687.y);
    vec4 _701 = _output[1];
    _701.z = uintBitsToFloat(floatBitsToUint(sa[8].z));
    _output[1] = _701;
    vec4 _715 = _output[1];
    _715.w = sa[8].w * pa[1].z;
    _output[1] = _715;
    vec4 _730 = _output[2];
    _730.z = pa[0].x * (0.0 - sa[8].y) + 1.0;
    _output[2] = _730;
    vec2 _738 = vec2(sa[10].z, sa[10].w);
    _output[1] = vec4(_738.x, _738.y, _output[1].z, _output[1].w);
    vec2 _748 = vec2(sa[7].x, sa[7].y);
    _output[2] = vec4(_748.x, _748.y, _output[2].z, _output[2].w);
}

void main()
{
    pa[0] = vec4(a_TextureCoordinate, 0.0, 1.0);
    pa[1] = a_Color;
    pa[2] = vec4(a_Position, 1.0);
    pa[3] = attribute_register_3;
    pa[4] = attribute_register_4;
    pa[5] = attribute_register_5;
    pa[6] = attribute_register_6;
    pa[7] = attribute_register_7;
    pa[8] = attribute_register_8;
    pa[9] = attribute_register_9;
    pa[10] = attribute_register_10;
    pa[11] = attribute_register_11;
    pa[12] = attribute_register_12;
    pa[13] = attribute_register_13;
    pa[14] = attribute_register_14;
    pa[15] = attribute_register_15;
































    // Native uniform/constants copied through the IMG table.
    sa[2].z = u_MVPMatrix[2][0];
    sa[2].w = u_MVPMatrix[2][1];
    sa[3].x = u_MVPMatrix[2][2];
    sa[3].y = u_MVPMatrix[2][3];
    sa[3].z = u_MVPMatrix[1][0];
    sa[3].w = u_MVPMatrix[1][1];
    sa[4].x = u_MVPMatrix[1][2];
    sa[4].y = u_MVPMatrix[1][3];
    sa[4].z = u_MVPMatrix[0][0];
    sa[4].w = u_MVPMatrix[0][1];
    sa[5].x = u_MVPMatrix[0][2];
    sa[5].y = u_MVPMatrix[0][3];
    sa[5].z = u_MVPMatrix[3][0];
    sa[5].w = u_MVPMatrix[3][1];
    sa[6].x = u_MVPMatrix[3][2];
    sa[6].y = u_MVPMatrix[3][3];
    sa[6].z = size_x_rel_tilt;
    sa[6].w = size_x;
    sa[7].x = uintBitsToFloat(0x3ed70a3du);
    sa[7].y = uintBitsToFloat(0x3c23d70au);
    sa[7].z = fade_squeeze;
    sa[7].w = fade_out;
    sa[8].x = size_z;
    sa[8].y = uintBitsToFloat(0xc0a00000u);
    sa[8].z = composition;
    sa[8].w = pressed;
    sa[9].x = uintBitsToFloat(0x40a00000u);
    sa[9].y = mppd_composition;
    sa[9].z = opacity;
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    shd = _output[1];
    fd = _output[2].xyz;

}

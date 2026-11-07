#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 37a553bc52c3d989fb65694998ddfc39a058b67e7f31c245968894f0770809f1
// Candidate module sha256: 3c920b329f410b6d0e751bdf7823b58914946dfe138cb306758bdec249535a4b
// Constant-copy table sha256: 2a41684229b24f598d44a064fc6f9244a266631bad99a5d8656fb0f66840a878
uniform float size_x;
uniform float size_z;
uniform mat4 u_MVPMatrix;
uniform float cursor_link;
uniform float pressed;
uniform float fade_squeeze;
uniform float fade_out;
uniform float composition;

const vec4 _53[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _66[4] = int[](0, 0, 0, 0);
const bool _72[4] = bool[](false, false, false, false);

in vec2 a_TextureCoordinate;
in vec2 a_TextureCoordinate1;
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
out vec3 mixed_co;
out vec3 fd;
out vec2 uv;
out float v_cursor_link;
out float birth;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void secondary_program()
{
    vec4 _257 = sa[9];
    _257.x = uintBitsToFloat(floatBitsToUint(sa[8].y));
    sa[9] = _257;
    vec4 _272 = sa[9];
    _272.y = sa[8].z + sa[8].w;
    sa[9] = _272;
    vec2 _287 = (vec2(0.0) - vec2(1.0, sa[7].x)) * vec2(sa[6].w, sa[6].w);
    sa[11] = vec4(_287.x, _287.y, sa[11].z, sa[11].w);
    vec4 _299 = sa[11];
    _299.z = 0.0 * sa[6].w;
    sa[11] = _299;
    vec2 _313 = vec2(1.0, sa[7].x) * vec2(sa[6].z, sa[6].z);
    sa[10] = vec4(_313.x, _313.y, sa[10].z, sa[10].w);
    vec4 _325 = sa[10];
    _325.z = 0.0 * sa[6].z;
    sa[10] = _325;
    vec4 _340 = internal[0];
    _340.x = sa[7].y + sa[8].y;
    internal[0] = _340;
    sa[7] = vec4(sa[7].x, vec2(1.0 / internal[0].x).x, sa[7].z, sa[7].w);
    vec4 _359 = internal[0];
    _359.x = 1.0 + sa[7].z;
    internal[0] = _359;
    vec4 _379 = sa[9];
    _379.z = sa[7].w * internal[0].x + (0.0 - sa[7].z);
    sa[9] = _379;
    vec4 _394 = sa[9];
    _394.w = sa[9].z + sa[7].z;
    sa[9] = _394;
    vec4 _404 = internal[0];
    _404.x = (0.0 - sa[8].x) + 1.0;
    internal[0] = _404;
    vec4 _419 = sa[8];
    _419.z = (0.0 - sa[8].x) + internal[0].x;
    sa[8] = _419;
    vec2 _427 = vec2(1.0, sa[7].x) * vec2(1.0);
    sa[7] = vec4(sa[7].x, sa[7].y, _427.x, _427.y);
    float _431 = 0.0 * 1.0;
    vec4 _434 = sa[8];
    _434.x = _431;
    sa[8] = _434;
}

void primary_program()
{
    vec2 _452 = vec2(pa[2].x, pa[2].y);
    vec3 _463 = vec3(_452.x, _452.y, vec2(pa[2].z, pa[2].w).x);
    internal[0] = vec4(_463.x, _463.y, _463.z, internal[0].w);
    vec2 _489 = vec2(pa[1].x, pa[1].y) * vec2(sa[9].x, sa[9].y) + vec2(internal[0].x, internal[0].z);
    internal[1] = vec4(_489.x, _489.y, internal[1].z, internal[1].w);
    internal[2] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[1].x, internal[1].x, internal[1].x, internal[1].x);
    internal[0] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[2];
    internal[0] = vec4(internal[1].y, internal[1].y, internal[1].y, internal[1].y) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[0];
    vec2 _575 = vec2(1.0) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_575.x, _575.y, _output[0].z, _output[0].w);
    vec2 _593 = vec2(sa[6].x, sa[6].y) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _593.x, _593.y);
    vec2 _611 = vec2(sa[7].z, sa[7].w);
    vec3 _622 = vec3(_611.x, _611.y, vec2(sa[8].x, sa[8].y).x);
    internal[0] = vec4(_622.x, _622.y, _622.z, internal[0].w);
    vec3 _650 = vec3(internal[0].x, internal[0].y, internal[0].z) * vec3(pa[0].x, pa[0].x, pa[0].x) + vec3(internal[0].x, internal[0].y, internal[0].z);
    internal[2] = vec4(_650.x, _650.y, _650.z, internal[2].w);
    vec3 _679 = vec3(internal[0].x, internal[0].y, internal[0].z) * (vec3(0.0) - vec3(pa[0].x, pa[0].x, pa[0].x)) + vec3(internal[2].x, internal[2].y, internal[2].z);
    internal[2] = vec4(_679.x, _679.y, _679.z, internal[2].w);
    vec3 _707 = vec3(internal[2].x, internal[2].y, internal[2].z) * vec3(sa[6].w, sa[6].w, sa[6].w) + vec3(internal[0].x, internal[0].y, internal[0].z);
    internal[0] = vec4(_707.x, _707.y, _707.z, internal[0].w);
    vec3 _729 = vec3(1.0) * vec3(sa[11].x, sa[11].y, sa[11].z) + vec3(internal[0].x, internal[0].y, internal[0].z);
    internal[0] = vec4(_729.x, _729.y, _729.z, internal[0].w);
    vec3 _750 = vec3(1.0) * vec3(sa[10].x, sa[10].y, sa[10].z) + vec3(internal[0].x, internal[0].y, internal[0].z);
    internal[2] = vec4(_750.x, _750.y, _750.z, internal[2].w);
    vec2 _776 = vec2(internal[0].x, internal[0].y) * (vec2(0.0) - vec2(sa[6].z, sa[6].z)) + vec2(internal[2].x, internal[2].y);
    _output[1] = vec4(_776.x, _776.y, _output[1].z, _output[1].w);
    vec4 _799 = _output[1];
    _799.z = internal[0].z * (0.0 - sa[6].z) + internal[2].z;
    _output[1] = _799;
    vec4 _807 = _output[3];
    _807.x = sa[6].w;
    _output[3] = _807;
    vec4 _822 = internal[0];
    _822.x = internal[1].x * (0.0 - sa[7].y) + 1.0;
    internal[0] = _822;
    vec4 _837 = _output[3];
    _837.z = 1.0 * (0.0 - sa[8].z) + internal[0].x;
    _output[3] = _837;
    vec4 _845 = _output[2];
    _845.y = internal[0].x;
    _output[2] = _845;
    vec4 _855 = _output[1];
    _855.w = uintBitsToFloat(floatBitsToUint(sa[9].z));
    _output[1] = _855;
    vec4 _866 = _output[2];
    _866.x = uintBitsToFloat(floatBitsToUint(sa[9].w));
    _output[2] = _866;
    vec2 _873 = vec2(pa[0].x, pa[0].y);
    _output[2] = vec4(_output[2].x, _output[2].y, _873.x, _873.y);
}

void main()
{
    pa[0] = vec4(a_TextureCoordinate, 0.0, 1.0);
    pa[1] = vec4(a_TextureCoordinate1, 0.0, 1.0);
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
    sa[6].z = pressed;
    sa[6].w = cursor_link;
    sa[7].x = uintBitsToFloat(0x3ea4dd2fu);
    sa[7].y = uintBitsToFloat(0x428c0000u);
    sa[7].z = fade_squeeze;
    sa[7].w = fade_out;
    sa[8].x = composition;
    sa[8].y = size_x;
    sa[8].z = size_z;
    sa[8].w = uintBitsToFloat(0x41200000u);
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    mixed_co = _output[1].xyz;
    fd = _output[2].xyz;
    uv = _output[3].xy;
    v_cursor_link = _output[4].x;
    birth = _output[5].x;

}

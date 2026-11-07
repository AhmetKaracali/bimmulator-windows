#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 0bb0e2183547aacbe945cbbb23e97ea85fa7c08348a58b24446733669c781358
// Candidate module sha256: e129b753f080b39f7e1a0d18fe90be2cceeccc3068d061043f0c11b73fd12657
// Constant-copy table sha256: b32dcd865b0218dfed450f1f3f15f7cc15e8b6f1b056b630955e3b0e3f37d50f
uniform float size_x;
uniform float size_z;
uniform mat4 u_MVPMatrix;
uniform vec3 CO_ORANGE;
uniform float fade_squeeze;
uniform float fade_out;

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

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void secondary_program()
{
    vec4 _255 = sa[8];
    _255.z = 64.0 + sa[5].z;
    sa[8] = _255;
    sa[8] = vec4(sa[8].x, vec2(1.0 / sa[8].z).x, sa[8].z, sa[8].w);
    vec4 _275 = internal[0];
    _275.x = 1.0 + sa[7].z;
    internal[0] = _275;
    vec2 _298 = vec2(sa[7].w, sa[7].w) * vec2(internal[0].x, internal[0].x) + (vec2(0.0) - vec2(sa[7].z, sa[7].z));
    sa[7] = vec4(sa[7].x, sa[7].y, _298.x, _298.y);
}

void primary_program()
{
    vec2 _311 = vec2(sa[6].x, sa[6].y);
    _output[1] = vec4(_311.x, _311.y, _output[1].z, _output[1].w);
    vec2 _321 = vec2(pa[0].x, pa[0].y);
    _output[2] = vec4(_output[2].x, _output[2].y, _321.x, _321.y);
    vec2 _339 = vec2(pa[2].x, pa[2].y);
    vec3 _350 = vec3(_339.x, _339.y, vec2(pa[2].z, pa[2].w).x);
    internal[0] = vec4(_350.x, _350.y, _350.z, internal[0].w);
    vec2 _375 = vec2(pa[1].x, pa[1].y) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].z);
    internal[1] = vec4(_375.x, _375.y, internal[1].z, internal[1].w);
    internal[2] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[1].x, internal[1].x, internal[1].x, internal[1].x);
    internal[0] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[2];
    internal[0] = vec4(internal[1].y, internal[1].y, internal[1].y, internal[1].y) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[0];
    vec2 _462 = vec2(1.0) * vec2(sa[6].z, sa[6].w) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_462.x, _462.y, _output[0].z, _output[0].w);
    vec2 _480 = vec2(sa[7].x, sa[7].y) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _480.x, _480.y);
    vec4 _499 = internal[0];
    _499.x = internal[1].x * (0.0 - sa[8].y) + 1.0;
    internal[0] = _499;
    vec4 _507 = _output[2];
    _507.y = internal[0].x;
    _output[2] = _507;
    vec2 _531 = vec2(vec2(sa[8].x, sa[8].y).x, vec2(sa[7].z, sa[7].w).x);
    _output[1] = vec4(_output[1].x, _output[1].y, _531.x, _531.y);
    vec4 _545 = _output[2];
    _545.x = uintBitsToFloat(floatBitsToUint(sa[7].w));
    _output[2] = _545;
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
    sa[5].z = size_x;
    sa[5].w = size_z;
    sa[6].x = CO_ORANGE.x;
    sa[6].y = CO_ORANGE.y;
    sa[6].z = u_MVPMatrix[3][0];
    sa[6].w = u_MVPMatrix[3][1];
    sa[7].x = u_MVPMatrix[3][2];
    sa[7].y = u_MVPMatrix[3][3];
    sa[7].z = fade_squeeze;
    sa[7].w = fade_out;
    sa[8].x = CO_ORANGE.z;
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    mixed_co = _output[1].xyz;
    fd = _output[2].xyz;
    uv = _output[3].xy;

}

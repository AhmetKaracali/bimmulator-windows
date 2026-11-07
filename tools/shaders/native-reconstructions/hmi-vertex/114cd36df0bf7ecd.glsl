#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 114cd36df0bf7ecdaf83574794c30ed68802357d8c35d43e2429ab1520412ef5
// Candidate module sha256: f7310dfb04bd34083e34e4392ef9af8e96cba69c06cd854971f1bcabfb55128c
// Constant-copy table sha256: 5d6b0d6cca2404086ca65a167638e9137f2c84a2a761a445c4238f3b37ea148f
uniform mat4 u_MVPMatrix;
uniform vec4 u_color;

const vec4 _53[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _66[4] = int[](0, 0, 0, 0);
const bool _72[4] = bool[](false, false, false, false);

in vec4 a_Position;
in vec2 a_TextureCoordinate;
in float a_Custom;
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
out vec4 vColor;
out vec2 vTexCoord;
out float fFading;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void primary_program()
{
    vec2 _252 = vec2(sa[5].z, sa[5].w);
    _output[1] = vec4(_252.x, _252.y, _output[1].z, _output[1].w);
    vec2 _262 = vec2(sa[6].x, sa[6].y);
    _output[1] = vec4(_output[1].x, _output[1].y, _262.x, _262.y);
    vec2 _272 = vec2(pa[1].x, pa[1].y);
    _output[2] = vec4(_272.x, _272.y, _output[2].z, _output[2].w);
    vec4 _286 = _output[2];
    _286.z = uintBitsToFloat(floatBitsToUint(pa[2].x));
    _output[2] = _286;
    vec2 _301 = vec2(pa[0].x, pa[0].y);
    vec3 _312 = vec3(_301.x, _301.y, vec2(pa[0].z, pa[0].w).x);
    internal[0] = vec4(_312.x, _312.y, _312.z, internal[0].w);
    internal[1] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[0].x, internal[0].x, internal[0].x, internal[0].x);
    internal[1] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[1];
    internal[0] = vec4(internal[0].z, internal[0].z, internal[0].z, internal[0].z) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[1];
    vec2 _399 = vec2(1.0) * vec2(sa[6].z, sa[6].w) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_399.x, _399.y, _output[0].z, _output[0].w);
    vec2 _417 = vec2(sa[7].x, sa[7].y) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _417.x, _417.y);
}

void main()
{
    pa[0] = a_Position;
    pa[1] = vec4(a_TextureCoordinate, 0.0, 1.0);
    pa[2] = vec4(a_Custom, 0.0, 0.0, 1.0);
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
    sa[5].z = u_color.x;
    sa[5].w = u_color.y;
    sa[6].x = u_color.z;
    sa[6].y = u_color.w;
    sa[6].z = u_MVPMatrix[3][0];
    sa[6].w = u_MVPMatrix[3][1];
    sa[7].x = u_MVPMatrix[3][2];
    sa[7].y = u_MVPMatrix[3][3];
































    primary_program();
    gl_Position = _output[0];
    vColor = _output[1];
    vTexCoord = _output[2].xy;
    fFading = _output[3].x;

}

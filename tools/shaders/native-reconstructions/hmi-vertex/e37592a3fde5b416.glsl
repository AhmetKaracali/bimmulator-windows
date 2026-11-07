#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: e37592a3fde5b4166c38f15400de1fe702700bdcdec46d8ddb811e8dc6acefa6
// Candidate module sha256: e99e88714ecc109b6a1246e8083b542f4680ffe73afd3009eba023a6edccd849
// Constant-copy table sha256: 247d457235a8ba3eea1348efbc34a709dc480a54a048e7c01ec12ba269db81fd
uniform float size_x;
uniform mat4 u_MVPMatrix;
uniform float usr_modality;

const vec4 _53[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _66[4] = int[](0, 0, 0, 0);
const bool _72[4] = bool[](false, false, false, false);

in vec2 a_TextureCoordinate;
in vec3 a_Position;
const vec4 attribute_register_2 = vec4(0.0);
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
out vec2 uv;
out float v_am;
out float v_usr_modality;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void secondary_program()
{
    vec4 _259 = sa[7];
    _259.x = sa[7].x * sa[6].z + 0.5;
    sa[7] = _259;
    float _265 = 0.0 - 0.5;
    vec4 _274 = sa[7];
    _274.x = sa[6].z * _265 + sa[7].x;
    sa[7] = _274;
}

void primary_program()
{
    vec2 _292 = vec2(pa[1].x, pa[1].y);
    vec3 _303 = vec3(_292.x, _292.y, vec2(pa[1].z, pa[1].w).x);
    internal[0] = vec4(_303.x, _303.y, _303.z, internal[0].w);
    vec4 _325 = internal[1];
    _325.x = pa[0].x * sa[6].w + internal[0].x;
    internal[1] = _325;
    internal[1] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[1].x, internal[1].x, internal[1].x, internal[1].x);
    internal[1] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[1];
    internal[0] = vec4(internal[0].z, internal[0].z, internal[0].z, internal[0].z) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[1];
    vec2 _409 = vec2(1.0) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_409.x, _409.y, _output[0].z, _output[0].w);
    vec2 _427 = vec2(sa[6].x, sa[6].y) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _427.x, _427.y);
    vec2 _437 = vec2(pa[0].x, pa[0].y);
    _output[1] = vec4(_437.x, _437.y, _output[1].z, _output[1].w);
    vec4 _451 = _output[1];
    _451.z = uintBitsToFloat(floatBitsToUint(sa[7].x));
    _output[1] = _451;
    vec4 _461 = _output[2];
    _461.x = uintBitsToFloat(floatBitsToUint(sa[6].z));
    _output[2] = _461;
}

void main()
{
    pa[0] = vec4(a_TextureCoordinate, 0.0, 1.0);
    pa[1] = vec4(a_Position, 1.0);
    pa[2] = attribute_register_2;
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
    sa[6].z = usr_modality;
    sa[6].w = size_x;
    sa[7].x = uintBitsToFloat(0x3e99999au);
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    uv = _output[1].xy;
    v_am = _output[2].x;
    v_usr_modality = _output[3].x;

}

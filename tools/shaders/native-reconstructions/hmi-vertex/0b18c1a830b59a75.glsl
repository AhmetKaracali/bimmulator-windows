#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 0b18c1a830b59a75938ffbb3382bdaf39842da05b625b4e43521095929fe5561
// Candidate module sha256: bd7bdb209af0406412799b34a126f453a7fa6ca81cfb92d8b063616b88daf360
// Constant-copy table sha256: 425812f30ef8118de5338e09860b8e4f6fc198057d08813954c0fb811f4562b9
uniform float composition;
uniform float size_z;
uniform mat4 u_MVPMatrix;

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
out vec2 uv;
out float r;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void primary_program()
{
    vec4 _256 = _output[1];
    _256.y = uintBitsToFloat(floatBitsToUint(pa[0].y));
    _output[1] = _256;
    vec4 _270 = _output[1];
    _270.x = pa[0].x * sa[6].z;
    _output[1] = _270;
    vec2 _285 = vec2(pa[2].x, pa[2].y);
    vec3 _296 = vec3(_285.x, _285.y, vec2(pa[2].z, pa[2].w).x);
    internal[0] = vec4(_296.x, _296.y, _296.z, internal[0].w);
    vec4 _318 = internal[1];
    _318.x = pa[1].y * sa[6].w + internal[0].z;
    internal[1] = _318;
    internal[2] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[0].x, internal[0].x, internal[0].x, internal[0].x);
    internal[0] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[2];
    internal[0] = vec4(internal[1].x, internal[1].x, internal[1].x, internal[1].x) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[0];
    vec2 _402 = vec2(1.0) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_402.x, _402.y, _output[0].z, _output[0].w);
    vec2 _420 = vec2(sa[6].x, sa[6].y) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _420.x, _420.y);
    vec4 _433 = _output[1];
    _433.z = uintBitsToFloat(floatBitsToUint(pa[1].x));
    _output[1] = _433;
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
    sa[6].z = composition;
    sa[6].w = size_z;
































    primary_program();
    gl_Position = _output[0];
    uv = _output[1].xy;
    r = _output[2].x;

}

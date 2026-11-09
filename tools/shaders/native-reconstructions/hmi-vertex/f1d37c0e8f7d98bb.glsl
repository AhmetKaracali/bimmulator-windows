#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: f1d37c0e8f7d98bb49d47c2c2c4c2c51d236413e11bc94dcf0a9b7b5e4bf623b
// Candidate module sha256: ee5eafef91e8e0fa6a6af5145bd54e2d9c92c8150f53ba7fca7851e34e96783d
// Constant-copy table sha256: e30d9eedb5a6cb2bf94a233f38c76e52fcfe2a03b1ea92801c5c7222c024435c
uniform float size_x;
uniform float size_z;
uniform mat4 u_MVPMatrix;
uniform float fade_squeeze;
uniform float fade_out;

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
out vec3 fd;
out vec2 uv;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void secondary_program()
{
    vec4 _255 = sa[7];
    _255.z = 64.0 + sa[5].z;
    sa[7] = _255;
    vec4 _264 = sa[8];
    _264.x = 1.0 / sa[7].z;
    sa[8] = _264;
    vec4 _273 = internal[0];
    _273.x = 1.0 + sa[7].x;
    internal[0] = _273;
    vec4 _293 = sa[7];
    _293.z = sa[7].y * internal[0].x + (0.0 - sa[7].x);
    sa[7] = _293;
    vec4 _307 = sa[7];
    _307.w = sa[7].z + sa[7].x;
    sa[7] = _307;
}

void primary_program()
{
    vec2 _325 = vec2(pa[1].x, pa[1].y);
    vec3 _336 = vec3(_325.x, _325.y, vec2(pa[1].z, pa[1].w).x);
    internal[0] = vec4(_336.x, _336.y, _336.z, internal[0].w);
    vec2 _361 = vec2(pa[0].x, pa[0].y) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].z);
    internal[1] = vec4(_361.x, _361.y, internal[1].z, internal[1].w);
    internal[2] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[1].x, internal[1].x, internal[1].x, internal[1].x);
    internal[0] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[2];
    internal[0] = vec4(internal[1].y, internal[1].y, internal[1].y, internal[1].y) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[0];
    vec2 _448 = vec2(1.0) * vec2(sa[6].x, sa[6].y) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_448.x, _448.y, _output[0].z, _output[0].w);
    vec2 _466 = vec2(sa[6].z, sa[6].w) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _466.x, _466.y);
    vec4 _485 = _output[1];
    _485.z = internal[1].x * (0.0 - sa[8].x) + 1.0;
    _output[1] = _485;
    vec2 _492 = vec2(sa[7].z, sa[7].w);
    _output[1] = vec4(_492.x, _492.y, _output[1].z, _output[1].w);
    vec4 _506 = _output[1];
    _506.w = uintBitsToFloat(floatBitsToUint(pa[0].x));
    _output[1] = _506;
    vec4 _516 = _output[2];
    _516.x = uintBitsToFloat(floatBitsToUint(pa[0].y));
    _output[2] = _516;
}

// Varyings read with SGX packing (tools/fix-packed-varyings.py).
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
    sa[5].z = size_x;
    sa[5].w = size_z;
    sa[6].x = u_MVPMatrix[3][0];
    sa[6].y = u_MVPMatrix[3][1];
    sa[6].z = u_MVPMatrix[3][2];
    sa[6].w = u_MVPMatrix[3][3];
    sa[7].x = fade_squeeze;
    sa[7].y = fade_out;
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    fd = vec3(_output[1].x, _output[1].y, _output[1].z);
    uv = vec2(_output[1].w, _output[2].x);
}

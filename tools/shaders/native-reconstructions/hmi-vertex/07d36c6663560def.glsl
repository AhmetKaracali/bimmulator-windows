#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 07d36c6663560def374a837ade6853a077ad5d65422ade3bfd28faeec7a86703
// Candidate module sha256: e2e6afb9658cc22bdb7d99f0a1aaf63093f7cd886943f362b4a98d7accf4c3cb
// Constant-copy table sha256: 334e8a1566d8c0fbc7138e5b3eb2c09397bc6e537d7e17facc763ab3657c2c0f
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
    vec4 _255 = sa[8];
    _255.x = 64.0 + sa[5].z;
    sa[8] = _255;
    sa[7] = vec4(sa[7].x, sa[7].y, sa[7].z, vec2(1.0 / sa[8].x).x);
    vec4 _275 = internal[0];
    _275.x = 1.0 + sa[7].x;
    internal[0] = _275;
    vec4 _295 = sa[8];
    _295.x = sa[7].y * internal[0].x + (0.0 - sa[7].x);
    sa[8] = _295;
    vec4 _309 = sa[8];
    _309.y = sa[8].x + sa[7].x;
    sa[8] = _309;
}

void primary_program()
{
    vec2 _327 = vec2(pa[1].x, pa[1].y);
    vec3 _338 = vec3(_327.x, _327.y, vec2(pa[1].z, pa[1].w).x);
    internal[0] = vec4(_338.x, _338.y, _338.z, internal[0].w);
    vec2 _363 = vec2(pa[0].x, pa[0].y) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].z);
    internal[1] = vec4(_363.x, _363.y, internal[1].z, internal[1].w);
    vec4 _376 = internal[2];
    _376.x = (0.0 - pa[0].x) + 1.0;
    internal[2] = _376;
    vec4 _395 = pa[0];
    _395.z = internal[2].x * sa[7].z + internal[1].x;
    pa[0] = _395;
    internal[2] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(pa[0].z, pa[0].z, pa[0].z, pa[0].z);
    internal[0] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[2];
    internal[0] = vec4(internal[1].y, internal[1].y, internal[1].y, internal[1].y) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[0];
    vec2 _479 = vec2(1.0) * vec2(sa[6].x, sa[6].y) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_479.x, _479.y, _output[0].z, _output[0].w);
    vec2 _497 = vec2(sa[6].z, sa[6].w) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _497.x, _497.y);
    vec4 _515 = _output[1];
    _515.z = pa[0].z * (0.0 - sa[7].w) + 1.0;
    _output[1] = _515;
    vec2 _522 = vec2(sa[8].x, sa[8].y);
    _output[1] = vec4(_522.x, _522.y, _output[1].z, _output[1].w);
    vec4 _536 = _output[1];
    _536.w = uintBitsToFloat(floatBitsToUint(pa[0].x));
    _output[1] = _536;
    vec4 _546 = _output[2];
    _546.x = uintBitsToFloat(floatBitsToUint(pa[0].y));
    _output[2] = _546;
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
    sa[7].z = uintBitsToFloat(0x40400000u);
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    fd = vec3(_output[1].x, _output[1].y, _output[1].z);
    uv = vec2(_output[1].w, _output[2].x);
}

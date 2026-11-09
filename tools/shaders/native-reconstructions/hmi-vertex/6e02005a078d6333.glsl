#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 6e02005a078d63336a621f4b95fe0b59c65ee17dcd0ec25851635e0231537525
// Candidate module sha256: f27099f080634bedb9ca71db24c211c882faaac0d1efe3403ea0218534b8226f
// Constant-copy table sha256: 41e14bb80ce74cc3502a60c96a1bbbde33bd467d07da301a68b0d4133a693940
uniform float size_x;
uniform float size_z;
uniform mat4 u_MVPMatrix;
uniform float cursor_link;
uniform float pressed;

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
    vec4 _256 = sa[9];
    _256.x = uintBitsToFloat(floatBitsToUint(sa[7].w));
    sa[9] = _256;
    vec4 _271 = sa[9];
    _271.y = sa[8].x + sa[8].y;
    sa[9] = _271;
    vec2 _286 = (vec2(0.0) - vec2(1.0, sa[7].x)) * vec2(sa[6].w, sa[6].w);
    sa[11] = vec4(_286.x, _286.y, sa[11].z, sa[11].w);
    vec4 _298 = sa[11];
    _298.z = 0.0 * sa[6].w;
    sa[11] = _298;
    vec2 _312 = vec2(1.0, sa[7].y) * vec2(sa[7].z, sa[7].z);
    sa[10] = vec4(_312.x, _312.y, sa[10].z, sa[10].w);
    vec4 _324 = sa[10];
    _324.z = 0.0 * sa[7].z;
    sa[10] = _324;
    vec4 _338 = internal[0];
    _338.x = sa[6].z + sa[7].w;
    internal[0] = _338;
    vec4 _347 = sa[6];
    _347.z = 1.0 / internal[0].x;
    sa[6] = _347;
    sa[9] = vec4(sa[9].x, sa[9].y, vec2(0.0).x, vec2(0.0).y);
    vec2 _358 = vec2(1.0, sa[7].x) * vec2(1.0);
    sa[8] = vec4(_358.x, _358.y, sa[8].z, sa[8].w);
    float _362 = 0.0 * 1.0;
    vec4 _365 = sa[8];
    _365.z = _362;
    sa[8] = _365;
}

void primary_program()
{
    vec2 _383 = vec2(pa[2].x, pa[2].y);
    vec3 _394 = vec3(_383.x, _383.y, vec2(pa[2].z, pa[2].w).x);
    internal[0] = vec4(_394.x, _394.y, _394.z, internal[0].w);
    vec2 _420 = vec2(pa[1].x, pa[1].y) * vec2(sa[9].x, sa[9].y) + vec2(internal[0].x, internal[0].z);
    internal[1] = vec4(_420.x, _420.y, internal[1].z, internal[1].w);
    internal[2] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[1].x, internal[1].x, internal[1].x, internal[1].x);
    internal[0] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[2];
    internal[0] = vec4(internal[1].y, internal[1].y, internal[1].y, internal[1].y) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[0];
    vec2 _506 = vec2(1.0) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_506.x, _506.y, _output[0].z, _output[0].w);
    vec2 _524 = vec2(sa[6].x, sa[6].y) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _524.x, _524.y);
    vec2 _542 = vec2(sa[8].x, sa[8].y);
    vec3 _554 = vec3(_542.x, _542.y, vec2(sa[8].z, sa[8].w).x);
    internal[0] = vec4(_554.x, _554.y, _554.z, internal[0].w);
    vec3 _582 = vec3(internal[0].x, internal[0].y, internal[0].z) * vec3(pa[0].x, pa[0].x, pa[0].x) + vec3(internal[0].x, internal[0].y, internal[0].z);
    internal[2] = vec4(_582.x, _582.y, _582.z, internal[2].w);
    vec3 _611 = vec3(internal[0].x, internal[0].y, internal[0].z) * (vec3(0.0) - vec3(pa[0].x, pa[0].x, pa[0].x)) + vec3(internal[2].x, internal[2].y, internal[2].z);
    internal[2] = vec4(_611.x, _611.y, _611.z, internal[2].w);
    vec3 _639 = vec3(internal[2].x, internal[2].y, internal[2].z) * vec3(sa[6].w, sa[6].w, sa[6].w) + vec3(internal[0].x, internal[0].y, internal[0].z);
    internal[0] = vec4(_639.x, _639.y, _639.z, internal[0].w);
    vec3 _661 = vec3(1.0) * vec3(sa[11].x, sa[11].y, sa[11].z) + vec3(internal[0].x, internal[0].y, internal[0].z);
    internal[0] = vec4(_661.x, _661.y, _661.z, internal[0].w);
    vec3 _682 = vec3(1.0) * vec3(sa[10].x, sa[10].y, sa[10].z) + vec3(internal[0].x, internal[0].y, internal[0].z);
    internal[2] = vec4(_682.x, _682.y, _682.z, internal[2].w);
    vec2 _708 = vec2(internal[0].x, internal[0].y) * (vec2(0.0) - vec2(sa[7].z, sa[7].z)) + vec2(internal[2].x, internal[2].y);
    _output[1] = vec4(_708.x, _708.y, _output[1].z, _output[1].w);
    vec4 _731 = _output[1];
    _731.z = internal[0].z * (0.0 - sa[7].z) + internal[2].z;
    _output[1] = _731;
    vec4 _739 = _output[3];
    _739.x = sa[6].w;
    _output[3] = _739;
    vec4 _754 = _output[2];
    _754.y = internal[1].x * (0.0 - sa[6].z) + 1.0;
    _output[2] = _754;
    float _755 = 0.0 - 1.0;
    vec4 _764 = _output[3];
    _764.z = _755 + _output[2].y;
    _output[3] = _764;
    vec4 _775 = _output[1];
    _775.w = uintBitsToFloat(floatBitsToUint(sa[9].z));
    _output[1] = _775;
    vec4 _786 = _output[2];
    _786.x = uintBitsToFloat(floatBitsToUint(sa[9].w));
    _output[2] = _786;
    vec2 _793 = vec2(pa[0].x, pa[0].y);
    _output[2] = vec4(_output[2].x, _output[2].y, _793.x, _793.y);
}

// Varyings read with SGX packing (tools/fix-packed-varyings.py).
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
    sa[6].z = uintBitsToFloat(0x428c0000u);
    sa[6].w = cursor_link;
    sa[7].x = uintBitsToFloat(0x3e947ae1u);
    sa[7].y = uintBitsToFloat(0x3e99999au);
    sa[7].z = pressed;
    sa[7].w = size_x;
    sa[8].x = size_z;
    sa[8].y = uintBitsToFloat(0x41200000u);
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    mixed_co = vec3(_output[1].x, _output[1].y, _output[1].z);
    fd = vec3(_output[1].w, _output[2].x, _output[2].y);
    uv = vec2(_output[2].z, _output[2].w);
    v_cursor_link = _output[3].x;
    birth = _output[3].z;
}

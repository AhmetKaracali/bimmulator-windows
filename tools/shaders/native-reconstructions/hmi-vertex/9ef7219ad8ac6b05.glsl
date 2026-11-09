#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 9ef7219ad8ac6b05c81a56b716922b7065ab667363a2f9d5e3326c1439a7ecae
// Candidate module sha256: 0c3df9720f364f1d751a52b96235d4b2c696a175464f287007e1c6baa00cd5dc
// Constant-copy table sha256: 57ca4472a543d1cb5701515f995e5e28687c3e77146cd5d2ed5d0756e89e7b86
uniform mat4 u_MVPMatrix;
uniform mat4 u_MVMatrix;

const vec4 _53[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _66[4] = int[](0, 0, 0, 0);
const bool _72[4] = bool[](false, false, false, false);

in vec2 a_TextureCoordinate;
in vec3 a_Position;
in vec4 a_Color;
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
out float am_inner_stack;
out float am_outer_stack;
out float px;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void secondary_program()
{
    vec4 _256 = sa[7];
    _256.z = uintBitsToFloat(floatBitsToUint(sa[7].y));
    sa[7] = _256;
    vec4 _264 = sa[7];
    _264.w = sa[7].x;
    sa[7] = _264;
    vec4 _272 = sa[8];
    _272.x = sa[6].w;
    sa[8] = _272;
    vec4 _280 = sa[8];
    _280.y = sa[6].z;
    sa[8] = _280;
}

void primary_program()
{
    vec2 _290 = vec2(pa[0].x, pa[0].y);
    _output[1] = vec4(_290.x, _290.y, _output[1].z, _output[1].w);
    vec2 _308 = vec2(pa[1].x, pa[1].y);
    vec3 _319 = vec3(_308.x, _308.y, vec2(pa[1].z, pa[1].w).x);
    internal[0] = vec4(_319.x, _319.y, _319.z, internal[0].w);
    internal[1] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[0].x, internal[0].x, internal[0].x, internal[0].x);
    internal[1] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[1];
    internal[1] = vec4(internal[0].z, internal[0].z, internal[0].z, internal[0].z) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[1];
    vec2 _406 = vec2(1.0) * vec2(sa[5].z, sa[5].w) + vec2(internal[1].x, internal[1].y);
    _output[0] = vec4(_406.x, _406.y, _output[0].z, _output[0].w);
    vec2 _424 = vec2(sa[6].x, sa[6].y) + vec2(internal[1].z, internal[1].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _424.x, _424.y);
    vec4 _435 = _output[2];
    _435.x = pa[2].z;
    _output[2] = _435;
    vec4 _456 = _output[2];
    _456.z = dot(vec4(sa[7].z, sa[7].w, sa[8].x, sa[8].y), vec4(internal[0].x, internal[0].y, internal[0].z, 1.0));
    _output[2] = _456;
    vec4 _466 = _output[1];
    _466.z = uintBitsToFloat(floatBitsToUint(pa[2].x));
    _output[1] = _466;
}

// Varyings read with SGX packing (tools/fix-packed-varyings.py).
void main()
{
    pa[0] = vec4(a_TextureCoordinate, 0.0, 1.0);
    pa[1] = vec4(a_Position, 1.0);
    pa[2] = a_Color;
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
    sa[6].z = u_MVMatrix[3][0];
    sa[6].w = u_MVMatrix[2][0];
    sa[7].x = u_MVMatrix[1][0];
    sa[7].y = u_MVMatrix[0][0];
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    uv = vec2(_output[1].x, _output[1].y);
    am_inner_stack = _output[1].z;
    am_outer_stack = _output[2].x;
    px = _output[2].z;
}

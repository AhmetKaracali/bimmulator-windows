#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: c9163daf462ec5035e40f188c86fbe0ebd0a44a4c43d6534e48512058d7b1680
// Candidate module sha256: 7283a27f8943c6ded13c589003845ed2a967c72dbfe4a8bddfd82fb872e3a548
// Constant-copy table sha256: d68a7867ec70613a21aa7c820c04cff4642f30cf881c801d6148020f73cf91c9
uniform mat4 u_MVPMatrix;
uniform mat4 u_MVMatrix;
uniform float fade_squeeze;
uniform float fade_out;
uniform float early_stack;
uniform float late_stack;
uniform float focused_mppd;
uniform float stack;

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
out vec3 p_fd;
out vec3 p_grd;
out vec2 uv;
out float ant;
out float px;
out float v_cm;
out float v_stack;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void secondary_program()
{
    vec4 _254 = sa[10];
    _254.x = 1.0 + sa[6].z;
    sa[10] = _254;
    vec4 _275 = sa[10];
    _275.z = sa[6].w * sa[10].x + (0.0 - sa[6].z);
    sa[10] = _275;
    vec4 _290 = sa[10];
    _290.w = sa[10].z + sa[6].z;
    sa[10] = _290;
    vec4 _305 = sa[10];
    _305.x = sa[9].x * sa[7].x + 0.5;
    sa[10] = _305;
    vec4 _320 = sa[10];
    _320.y = sa[7].x * (0.0 - sa[9].y) + 0.5;
    sa[10] = _320;
    vec4 _335 = sa[9];
    _335.x = sa[9].y * sa[9].z;
    sa[9] = _335;
    vec4 _351 = sa[8];
    _351.z = sa[8].y * sa[8].z;
    sa[8] = _351;
    vec4 _359 = sa[8];
    _359.y = sa[7].w;
    sa[8] = _359;
    vec2 _383 = vec2(vec2(sa[8].x, sa[8].y).x, vec2(sa[8].x, sa[8].y).y);
    sa[6] = vec4(sa[6].x, sa[6].y, _383.x, _383.y);
    vec4 _397 = sa[7];
    _397.x = uintBitsToFloat(floatBitsToUint(sa[7].z));
    sa[7] = _397;
}

void primary_program()
{
    vec4 _408 = _output[3];
    _408.x = pa[1].y;
    _output[3] = _408;
    vec2 _423 = vec2(pa[2].x, pa[2].y);
    vec3 _434 = vec3(_423.x, _423.y, vec2(pa[2].z, pa[2].w).x);
    internal[0] = vec4(_434.x, _434.y, _434.z, internal[0].w);
    internal[1] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[0].x, internal[0].x, internal[0].x, internal[0].x);
    internal[1] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[1];
    internal[1] = vec4(internal[0].z, internal[0].z, internal[0].z, internal[0].z) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[1];
    vec2 _521 = vec2(1.0) * vec2(sa[5].z, sa[5].w) + vec2(internal[1].x, internal[1].y);
    _output[0] = vec4(_521.x, _521.y, _output[0].z, _output[0].w);
    vec2 _539 = vec2(sa[6].x, sa[6].y) + vec2(internal[1].z, internal[1].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _539.x, _539.y);
    vec4 _563 = _output[3];
    _563.z = dot(vec4(sa[6].z, sa[6].w, sa[7].x, sa[7].y), vec4(internal[0].x, internal[0].y, internal[0].z, 1.0));
    _output[3] = _563;
    vec4 _573 = _output[1];
    _573.z = (0.0 - pa[0].x) + 1.0;
    _output[1] = _573;
    vec4 _587 = _output[2];
    _587.y = sa[9].x + pa[0].x;
    _output[2] = _587;
    vec4 _595 = _output[4];
    _595.z = sa[8].w;
    _output[4] = _595;
    vec2 _602 = vec2(sa[10].z, sa[10].w);
    _output[1] = vec4(_602.x, _602.y, _output[1].z, _output[1].w);
    vec4 _615 = _output[1];
    _615.w = uintBitsToFloat(floatBitsToUint(sa[10].x));
    _output[1] = _615;
    vec4 _626 = _output[2];
    _626.x = uintBitsToFloat(floatBitsToUint(sa[10].y));
    _output[2] = _626;
    vec2 _633 = vec2(pa[0].x, pa[0].y);
    _output[2] = vec4(_output[2].x, _output[2].y, _633.x, _633.y);
    vec4 _646 = _output[4];
    _646.x = uintBitsToFloat(floatBitsToUint(sa[8].z));
    _output[4] = _646;
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
    sa[6].z = fade_squeeze;
    sa[6].w = fade_out;
    sa[7].x = uintBitsToFloat(0x3cf5c28fu);
    sa[7].y = u_MVMatrix[3][0];
    sa[7].z = u_MVMatrix[2][0];
    sa[7].w = u_MVMatrix[1][0];
    sa[8].x = u_MVMatrix[0][0];
    sa[8].y = focused_mppd;
    sa[8].z = uintBitsToFloat(0x3fa66666u);
    sa[8].w = stack;
    sa[9].x = early_stack;
    sa[9].y = late_stack;
    sa[9].z = uintBitsToFloat(0x3ee66666u);
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    p_fd = vec3(_output[1].x, _output[1].y, _output[1].z);
    p_grd = vec3(_output[1].w, _output[2].x, _output[2].y);
    uv = vec2(_output[2].z, _output[2].w);
    ant = _output[3].x;
    px = _output[3].z;
    v_cm = _output[4].x;
    v_stack = _output[4].z;
}

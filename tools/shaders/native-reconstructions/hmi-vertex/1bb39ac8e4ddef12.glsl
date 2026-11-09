#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 1bb39ac8e4ddef12954b18912922af5d84c53fe4a01cac7e35f3216a8416060b
// Candidate module sha256: 2ee12371cda88e4028b70a688b889eadab60df8761ec9e3f16afabdc08833ac0
// Constant-copy table sha256: d3290f0c38eab774836193d188893e4f23698df70b8551ce0ab43630542b2424
uniform mat4 u_MVPMatrix;
uniform vec3 CO_TOP;

const vec4 _53[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _66[4] = int[](0, 0, 0, 0);
const bool _72[4] = bool[](false, false, false, false);

in vec4 a_Color;
in vec3 a_Position;
in vec2 a_TextureCoordinate;
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
out vec3 cm;
out vec2 uv;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void primary_program()
{
    vec2 _252 = vec2(sa[5].z, sa[5].w);
    _output[1] = vec4(_252.x, _252.y, _output[1].z, _output[1].w);
    vec2 _279 = vec2(vec2(sa[7].x, sa[7].y).y, vec2(pa[2].x, pa[2].y).x);
    _output[1] = vec4(_output[1].x, _output[1].y, _279.x, _279.y);
    vec4 _293 = _output[2];
    _293.x = uintBitsToFloat(floatBitsToUint(pa[2].y));
    _output[2] = _293;
    vec2 _308 = vec2(pa[1].x, pa[1].y);
    vec3 _319 = vec3(_308.x, _308.y, vec2(pa[1].z, pa[1].w).x);
    internal[0] = vec4(_319.x, _319.y, _319.z, internal[0].w);
    internal[1] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[0].x, internal[0].x, internal[0].x, internal[0].x);
    internal[1] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[1];
    internal[0] = vec4(internal[0].z, internal[0].z, internal[0].z, internal[0].z) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[1];
    vec2 _406 = vec2(1.0) * vec2(sa[6].x, sa[6].y) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_406.x, _406.y, _output[0].z, _output[0].w);
    vec2 _424 = vec2(sa[6].z, sa[6].w) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _424.x, _424.y);
}

// Varyings read with SGX packing (tools/fix-packed-varyings.py).
void main()
{
    pa[0] = a_Color;
    pa[1] = vec4(a_Position, 1.0);
    pa[2] = vec4(a_TextureCoordinate, 0.0, 1.0);
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
    sa[5].z = CO_TOP.x;
    sa[5].w = CO_TOP.y;
    sa[6].x = u_MVPMatrix[3][0];
    sa[6].y = u_MVPMatrix[3][1];
    sa[6].z = u_MVPMatrix[3][2];
    sa[6].w = u_MVPMatrix[3][3];
    sa[7].x = uintBitsToFloat(0x438b0000u);
    sa[7].y = CO_TOP.z;
































    primary_program();
    gl_Position = _output[0];
    cm = vec3(_output[1].x, _output[1].y, _output[1].z);
    uv = vec2(_output[1].w, _output[2].x);
}

#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 178e9190c72eb45a7fbdf9d6b487113d7a8bdbca94d59fed2a99db7f59625253
// Candidate module sha256: 93165843791fadf17ac26a642de24be7ef9193850849cc78198bfe6f7c2640a6
// Constant-copy table sha256: 4cbad1f66b4bc6fc23d385c046ee773a928acfbbbca97d5b4cc8e96263d2ebfd
uniform float size_x;
uniform float cursor_link;
uniform float size_z;
uniform mat4 u_MVPMatrix;
uniform float pressed;
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
    vec4 _260 = sa[10];
    _260.z = sa[9].x + sa[9].y;
    sa[10] = _260;
    vec4 _271 = internal[0];
    _271.x = (0.0 - sa[9].z) + 1.0;
    internal[0] = _271;
    vec4 _281 = sa[10];
    _281.x = internal[0].x * 4.0 + 0.0;
    sa[10] = _281;
    vec4 _293 = sa[9];
    _293.z = uintBitsToFloat(floatBitsToUint(sa[10].z));
    sa[9] = _293;
    vec4 _308 = sa[9];
    _308.w = sa[7].w + sa[8].x;
    sa[9] = _308;
    vec4 _323 = internal[0];
    _323.x = sa[8].y * sa[8].z + 1.0;
    internal[0] = _323;
    vec2 _338 = vec2(internal[0].x, internal[0].x) * vec2(sa[5].z, sa[5].w) + vec2(0.0);
    sa[11] = vec4(_338.x, _338.y, sa[11].z, sa[11].w);
    vec4 _355 = sa[8];
    _355.x = sa[8].w * internal[0].x;
    sa[8] = _355;
    vec4 _369 = internal[0];
    _369.x = sa[7].x + sa[9].x;
    internal[0] = _369;
    vec4 _378 = sa[7];
    _378.x = 1.0 / internal[0].x;
    sa[7] = _378;
    vec4 _387 = internal[0];
    _387.x = 1.0 + sa[7].y;
    internal[0] = _387;
    vec4 _407 = sa[5];
    _407.z = sa[7].z * internal[0].x + (0.0 - sa[7].y);
    sa[5] = _407;
    vec4 _421 = sa[5];
    _421.w = sa[5].z + sa[7].y;
    sa[5] = _421;
}

void primary_program()
{
    vec2 _431 = vec2(pa[0].x, pa[0].y);
    _output[2] = vec4(_output[2].x, _output[2].y, _431.x, _431.y);
    vec2 _449 = vec2(pa[2].x, pa[2].y);
    vec3 _460 = vec3(_449.x, _449.y, vec2(pa[2].z, pa[2].w).x);
    internal[0] = vec4(_460.x, _460.y, _460.z, internal[0].w);
    vec2 _485 = vec2(pa[1].x, pa[1].y) * vec2(sa[9].z, sa[9].w) + vec2(internal[0].x, internal[0].z);
    internal[1] = vec4(_485.x, _485.y, internal[1].z, internal[1].w);
    vec4 _498 = internal[2];
    _498.x = (0.0 - pa[1].x) + 1.0;
    internal[2] = _498;
    vec4 _519 = pa[0];
    _519.x = internal[2].x * (0.0 - sa[10].x) + internal[1].x;
    pa[0] = _519;
    internal[2] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(pa[0].x, pa[0].x, pa[0].x, pa[0].x);
    internal[0] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[2];
    internal[0] = vec4(internal[1].y, internal[1].y, internal[1].y, internal[1].y) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[0];
    vec2 _603 = vec2(1.0) * vec2(sa[6].x, sa[6].y) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_603.x, _603.y, _output[0].z, _output[0].w);
    vec2 _621 = vec2(sa[6].z, sa[6].w) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _621.x, _621.y);
    vec4 _639 = internal[0];
    _639.x = pa[0].x * (0.0 - sa[7].x) + 1.0;
    internal[0] = _639;
    vec4 _647 = _output[2];
    _647.y = internal[0].x;
    _output[2] = _647;
    vec2 _655 = vec2(sa[11].x, sa[11].y);
    _output[1] = vec4(_655.x, _655.y, _output[1].z, _output[1].w);
    vec2 _682 = vec2(vec2(sa[8].x, sa[8].y).x, vec2(sa[5].z, sa[5].w).x);
    _output[1] = vec4(_output[1].x, _output[1].y, _682.x, _682.y);
    vec4 _695 = _output[2];
    _695.x = uintBitsToFloat(floatBitsToUint(sa[5].w));
    _output[2] = _695;
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
    sa[5].z = uintBitsToFloat(0x3f0a3d71u);
    sa[5].w = uintBitsToFloat(0x3db851ecu);
    sa[6].x = u_MVPMatrix[3][0];
    sa[6].y = u_MVPMatrix[3][1];
    sa[6].z = u_MVPMatrix[3][2];
    sa[6].w = u_MVPMatrix[3][3];
    sa[7].x = uintBitsToFloat(0x428c0000u);
    sa[7].y = fade_squeeze;
    sa[7].z = fade_out;
    sa[7].w = size_z;
    sa[8].x = uintBitsToFloat(0x41200000u);
    sa[8].y = pressed;
    sa[8].z = uintBitsToFloat(0x3f666666u);
    sa[8].w = uintBitsToFloat(0x3cf5c28fu);
    sa[9].x = size_x;
    sa[9].y = uintBitsToFloat(0x41400000u);
    sa[9].z = cursor_link;
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    mixed_co = _output[1].xyz;
    fd = _output[2].xyz;
    uv = _output[3].xy;

}

#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: b8da2966f915fe5ec6f3314d0a4c092b4d8a7da5da1635025d61754eb1a98807
// Candidate module sha256: eb1f63df407cfcd0ea47800f52cd6fda183ef0d22d5a85dc12be804fe6580996
// Constant-copy table sha256: 56979dd4dbecef0c21541a03e43af91c176bc8d26adb9230d4fc611818ee92bb
uniform float early_stack;
uniform mat4 u_MVPMatrix;

const vec4 _53[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _66[4] = int[](0, 0, 0, 0);
const bool _72[4] = bool[](false, false, false, false);

in vec2 a_TextureCoordinate;
in vec4 a_Color;
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
out float v_am;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void primary_program()
{
    vec2 _252 = vec2(pa[0].x, pa[0].y);
    _output[1] = vec4(_252.x, _252.y, _output[1].z, _output[1].w);
    vec4 _269 = internal[0];
    _269.x = pa[1].z * sa[6].z + 1.0;
    internal[0] = _269;
    vec4 _284 = _output[1];
    _284.z = 1.0 * (0.0 - sa[6].z) + internal[0].x;
    _output[1] = _284;
    vec2 _299 = vec2(pa[2].x, pa[2].y);
    vec3 _310 = vec3(_299.x, _299.y, vec2(pa[2].z, pa[2].w).x);
    internal[0] = vec4(_310.x, _310.y, _310.z, internal[0].w);
    internal[1] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[0].x, internal[0].x, internal[0].x, internal[0].x);
    internal[1] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[1];
    internal[0] = vec4(internal[0].z, internal[0].z, internal[0].z, internal[0].z) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[1];
    vec2 _397 = vec2(1.0) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_397.x, _397.y, _output[0].z, _output[0].w);
    vec2 _415 = vec2(sa[6].x, sa[6].y) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _415.x, _415.y);
}

void main()
{
    pa[0] = vec4(a_TextureCoordinate, 0.0, 1.0);
    pa[1] = a_Color;
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
    sa[6].z = early_stack;
































    primary_program();
    gl_Position = _output[0];
    uv = _output[1].xy;
    v_am = _output[2].x;

}

#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 1a37cc86bcb63e31a5d19e72e8a080098e032b118830d719d3ce5372fb9bb1be
// Candidate module sha256: 61851c8c6837060545e57a838283818a4cdcda70acda163582e61e3be12639f4
// Constant-copy table sha256: d3290f0c38eab774836193d188893e4f23698df70b8551ce0ab43630542b2424
uniform float size_z;
uniform mat4 u_MVPMatrix;
uniform vec3 CO;

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
out vec3 mc;
out vec2 uv;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void secondary_program()
{
    vec4 _248 = sa[7];
    _248.z = 1.0;
    sa[7] = _248;
}

void primary_program()
{
    vec2 _258 = vec2(sa[5].z, sa[5].w);
    _output[1] = vec4(_258.x, _258.y, _output[1].z, _output[1].w);
    vec4 _272 = _output[1];
    _272.z = uintBitsToFloat(floatBitsToUint(sa[7].y));
    _output[1] = _272;
    vec4 _282 = _output[1];
    _282.w = uintBitsToFloat(floatBitsToUint(sa[7].z));
    _output[1] = _282;
    vec4 _290 = _output[2];
    _290.x = pa[0].y;
    _output[2] = _290;
    vec2 _305 = vec2(pa[1].x, pa[1].y);
    vec3 _316 = vec3(_305.x, _305.y, vec2(pa[1].z, pa[1].w).x);
    internal[0] = vec4(_316.x, _316.y, _316.z, internal[0].w);
    vec4 _338 = internal[1];
    _338.x = pa[0].y * sa[7].x + internal[0].z;
    internal[1] = _338;
    internal[2] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[0].x, internal[0].x, internal[0].x, internal[0].x);
    internal[0] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[2];
    internal[0] = vec4(internal[1].x, internal[1].x, internal[1].x, internal[1].x) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[0];
    vec2 _422 = vec2(1.0) * vec2(sa[6].x, sa[6].y) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_422.x, _422.y, _output[0].z, _output[0].w);
    vec2 _440 = vec2(sa[6].z, sa[6].w) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _440.x, _440.y);
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
    sa[5].z = CO.x;
    sa[5].w = CO.y;
    sa[6].x = u_MVPMatrix[3][0];
    sa[6].y = u_MVPMatrix[3][1];
    sa[6].z = u_MVPMatrix[3][2];
    sa[6].w = u_MVPMatrix[3][3];
    sa[7].x = size_z;
    sa[7].y = CO.z;
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    mc = _output[1].xyz;
    uv = _output[2].xy;

}

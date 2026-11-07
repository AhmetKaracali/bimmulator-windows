#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: ec0105664ee6202ffa8b692e1e6c63ede8ff169f8a0434cdc3be40d67be219be
// Candidate module sha256: b23f482c8a23e8038b98772b435f1a45819ee9a8365de18b78b0784a342bbe23
// Constant-copy table sha256: f3e9c342c8a37331df176a82c88fafd30f8774195b641238d75e0a75da92cb39
uniform float is_functionbar;
uniform float is_preview;
uniform float mirrored;
uniform mat4 u_MVPMatrix;

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
out vec2 uv;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void secondary_program()
{
    vec4 _259 = sa[7];
    _259.z = sa[7].z * sa[7].w;
    sa[7] = _259;
    vec4 _273 = sa[7];
    _273.z = sa[6].z * sa[7].z;
    sa[7] = _273;
    vec4 _287 = sa[6];
    _287.z = sa[6].w * sa[7].x;
    sa[6] = _287;
}

void primary_program()
{
    vec4 _300 = pa[0];
    _300.z = (0.0 - pa[0].y) + 1.0;
    pa[0] = _300;
    vec4 _314 = internal[0];
    _314.x = sa[7].z * pa[0].z;
    internal[0] = _314;
    vec2 _329 = vec2(pa[1].x, pa[1].y);
    vec3 _340 = vec3(_329.x, _329.y, vec2(pa[1].z, pa[1].w).x);
    internal[1] = vec4(_340.x, _340.y, _340.z, internal[1].w);
    vec4 _362 = internal[0];
    _362.x = internal[1].z * sa[7].y + internal[0].x;
    internal[0] = _362;
    vec4 _377 = internal[0];
    _377.x = (0.0 - sa[6].z) + internal[0].x;
    internal[0] = _377;
    internal[2] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[1].x, internal[1].x, internal[1].x, internal[1].x);
    internal[1] = vec4(internal[1].y, internal[1].y, internal[1].y, internal[1].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[2];
    internal[0] = vec4(internal[0].x, internal[0].x, internal[0].x, internal[0].x) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[1];
    vec2 _461 = vec2(1.0) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_461.x, _461.y, _output[0].z, _output[0].w);
    vec2 _479 = vec2(sa[6].x, sa[6].y) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _479.x, _479.y);
    vec2 _489 = vec2(pa[0].x, pa[0].y);
    _output[1] = vec4(_489.x, _489.y, _output[1].z, _output[1].w);
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
    sa[5].z = u_MVPMatrix[3][0];
    sa[5].w = u_MVPMatrix[3][1];
    sa[6].x = u_MVPMatrix[3][2];
    sa[6].y = u_MVPMatrix[3][3];
    sa[6].z = uintBitsToFloat(0x40e00000u);
    sa[6].w = mirrored;
    sa[7].x = uintBitsToFloat(0x40400000u);
    sa[7].y = uintBitsToFloat(0x3f80624eu);
    sa[7].z = is_functionbar;
    sa[7].w = is_preview;
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    uv = _output[1].xy;

}

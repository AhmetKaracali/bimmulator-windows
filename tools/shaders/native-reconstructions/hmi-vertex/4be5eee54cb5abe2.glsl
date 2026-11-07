#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 4be5eee54cb5abe264fdc91b80296f49c9d0744e203b2a7426d6f07ff0a7d386
// Candidate module sha256: 6388b2846c07ea48a6e471b7440103cc6e51bbed723505dee0bb0f6c5e0fddc2
// Constant-copy table sha256: cdbfc41778d7808abaef8de14465972976186d95e6b3f4bdeffce1e0b0269332
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
out vec3 fd;
out vec2 uv;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void secondary_program()
{
    vec4 _259 = sa[7];
    _259.x = sa[7].x + sa[5].z;
    sa[7] = _259;
    vec4 _268 = sa[8];
    _268.x = 1.0 / sa[7].x;
    sa[8] = _268;
    vec4 _277 = internal[0];
    _277.x = 1.0 + sa[7].y;
    internal[0] = _277;
    vec4 _297 = sa[7];
    _297.x = sa[7].z * internal[0].x + (0.0 - sa[7].y);
    sa[7] = _297;
    vec4 _311 = sa[7];
    _311.y = sa[7].x + sa[7].y;
    sa[7] = _311;
}

void primary_program()
{
    vec4 _325 = _output[1];
    _325.w = uintBitsToFloat(floatBitsToUint(pa[0].x));
    _output[1] = _325;
    vec4 _335 = _output[2];
    _335.x = uintBitsToFloat(floatBitsToUint(pa[0].y));
    _output[2] = _335;
    vec2 _350 = vec2(pa[1].x, pa[1].y);
    vec3 _361 = vec3(_350.x, _350.y, vec2(pa[1].z, pa[1].w).x);
    internal[0] = vec4(_361.x, _361.y, _361.z, internal[0].w);
    vec2 _386 = vec2(pa[2].x, pa[2].y) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].z);
    internal[1] = vec4(_386.x, _386.y, internal[1].z, internal[1].w);
    internal[2] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[1].x, internal[1].x, internal[1].x, internal[1].x);
    internal[0] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[2];
    internal[0] = vec4(internal[1].y, internal[1].y, internal[1].y, internal[1].y) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[0];
    vec2 _473 = vec2(1.0) * vec2(sa[6].x, sa[6].y) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_473.x, _473.y, _output[0].z, _output[0].w);
    vec2 _491 = vec2(sa[6].z, sa[6].w) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _491.x, _491.y);
    vec4 _508 = internal[0];
    _508.x = 1.0 * sa[7].w + internal[1].x;
    internal[0] = _508;
    vec4 _524 = _output[1];
    _524.z = internal[0].x * (0.0 - sa[8].x) + 1.0;
    _output[1] = _524;
    vec2 _531 = vec2(sa[7].x, sa[7].y);
    _output[1] = vec4(_531.x, _531.y, _output[1].z, _output[1].w);
}

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
    sa[5].z = size_x;
    sa[5].w = size_z;
    sa[6].x = u_MVPMatrix[3][0];
    sa[6].y = u_MVPMatrix[3][1];
    sa[6].z = u_MVPMatrix[3][2];
    sa[6].w = u_MVPMatrix[3][3];
    sa[7].x = uintBitsToFloat(0x42be0000u);
    sa[7].y = fade_squeeze;
    sa[7].z = fade_out;
    sa[7].w = uintBitsToFloat(0x41200000u);
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    fd = _output[1].xyz;
    uv = _output[2].xy;

}

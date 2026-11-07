#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 1a9b04c0947ca46a3e64180cb8c32c85862e1b3000c594b0128ecc4ff03d2d4d
// Candidate module sha256: 4a9ee1cd8f53cc845fba1e8dc0fc1e3b5a3c42f0e518a430f0eb6a622eaef02d
// Constant-copy table sha256: f2b22fd5e0a46e313ef9ac399230b2d61e769792e94128548c4398773c5dd04d
uniform float size_x;
uniform mat4 u_MVPMatrix;
uniform float usr_modality;
uniform float fade_squeeze;
uniform float fade_out;
uniform float composition;

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
out float v_am;
out float birth;
out float v_usr_modality;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void secondary_program()
{
    vec4 _259 = sa[8];
    _259.x = sa[7].w * sa[7].x + 0.5;
    sa[8] = _259;
    float _265 = 0.0 - 0.5;
    vec4 _275 = sa[8];
    _275.z = sa[7].x * _265 + sa[8].x;
    sa[8] = _275;
    vec4 _285 = internal[0];
    _285.x = 64.0 + sa[7].z;
    internal[0] = _285;
    sa[7] = vec4(sa[7].x, sa[7].y, sa[7].z, vec2(1.0 / internal[0].x).x);
    vec4 _304 = internal[0];
    _304.x = 1.0 + sa[7].y;
    internal[0] = _304;
    vec4 _324 = sa[8];
    _324.x = sa[6].z * internal[0].x + (0.0 - sa[7].y);
    sa[8] = _324;
    vec4 _338 = sa[8];
    _338.y = sa[8].x + sa[7].y;
    sa[8] = _338;
    vec4 _348 = internal[0];
    _348.x = (0.0 - sa[6].w) + 1.0;
    internal[0] = _348;
    vec4 _363 = sa[6];
    _363.z = (0.0 - sa[6].w) + internal[0].x;
    sa[6] = _363;
}

void primary_program()
{
    vec2 _381 = vec2(pa[1].x, pa[1].y);
    vec3 _392 = vec3(_381.x, _381.y, vec2(pa[1].z, pa[1].w).x);
    internal[0] = vec4(_392.x, _392.y, _392.z, internal[0].w);
    vec4 _414 = internal[1];
    _414.x = pa[0].x * sa[7].z + internal[0].x;
    internal[1] = _414;
    internal[2] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[1].x, internal[1].x, internal[1].x, internal[1].x);
    internal[2] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[2];
    internal[0] = vec4(internal[0].z, internal[0].z, internal[0].z, internal[0].z) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[2];
    vec2 _498 = vec2(1.0) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_498.x, _498.y, _output[0].z, _output[0].w);
    vec2 _516 = vec2(sa[6].x, sa[6].y) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _516.x, _516.y);
    vec4 _534 = _output[1];
    _534.z = internal[1].x * (0.0 - sa[7].w) + 1.0;
    _output[1] = _534;
    vec4 _549 = internal[0];
    _549.x = (0.0 - sa[6].z) + _output[1].z;
    internal[0] = _549;
    vec4 _558 = internal[0];
    _558.x = max(internal[0].x, 0.0);
    internal[0] = _558;
    vec4 _567 = _output[2];
    _567.w = min(internal[0].x, 1.0);
    _output[2] = _567;
    vec2 _574 = vec2(sa[8].x, sa[8].y);
    _output[1] = vec4(_574.x, _574.y, _output[1].z, _output[1].w);
    vec4 _588 = _output[1];
    _588.w = uintBitsToFloat(floatBitsToUint(pa[0].x));
    _output[1] = _588;
    vec2 _613 = vec2(vec2(pa[0].x, pa[0].y).y, vec2(sa[8].z, sa[8].w).x);
    _output[2] = vec4(_613.x, _613.y, _output[2].z, _output[2].w);
    vec4 _626 = _output[3];
    _626.y = uintBitsToFloat(floatBitsToUint(sa[7].x));
    _output[3] = _626;
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
    sa[6].z = fade_out;
    sa[6].w = composition;
    sa[7].x = usr_modality;
    sa[7].y = fade_squeeze;
    sa[7].z = size_x;
    sa[7].w = uintBitsToFloat(0x3e99999au);
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    fd = _output[1].xyz;
    uv = _output[2].xy;
    v_am = _output[3].x;
    birth = _output[4].x;
    v_usr_modality = _output[5].x;

}

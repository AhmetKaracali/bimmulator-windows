#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: ddc68e69ebab4e8423574814fc30728843531e8458de806eb552b76a8d783c3e
// Candidate module sha256: 40c4532f487961d5c6975e7c9b3224d5f7d2f46ce6072b5c35af56a0c6752e61
// Constant-copy table sha256: 07e6513a37d930053f7d452686b43902ec3cc4be3b01def227a8c706b4550677
uniform float size_x;
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
out vec2 varCoord;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

vec2 unpack2xF16(float _276)
{
    return unpackHalf2x16(floatBitsToUint(_276));
}

void secondary_program()
{
    vec4 _255 = sa[6];
    _255.z = (0.0 - sa[6].z) + 1.0;
    sa[6] = _255;
    vec4 _269 = sa[6];
    _269.z = sa[6].z * sa[6].w;
    sa[6] = _269;
    vec4 _286 = sa[6];
    _286.w = unpack2xF16(sa[7].x).y;
    sa[6] = _286;
}

void primary_program()
{
    vec4 _300 = _output[1];
    _300.y = uintBitsToFloat(floatBitsToUint(pa[0].y));
    _output[1] = _300;
    vec4 _315 = internal[0];
    _315.x = (0.0 - sa[6].z) + pa[0].x;
    internal[0] = _315;
    float _316 = 0.0 - 1.0;
    vec4 _325 = internal[0];
    _325.x = _316 + internal[0].x;
    internal[0] = _325;
    vec4 _339 = _output[1];
    _339.x = 1.0 * sa[6].w + internal[0].x;
    _output[1] = _339;
    vec2 _354 = vec2(pa[1].x, pa[1].y);
    vec3 _365 = vec3(_354.x, _354.y, vec2(pa[1].z, pa[1].w).x);
    internal[0] = vec4(_365.x, _365.y, _365.z, internal[0].w);
    internal[1] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[0].x, internal[0].x, internal[0].x, internal[0].x);
    internal[1] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[1];
    internal[0] = vec4(internal[0].z, internal[0].z, internal[0].z, internal[0].z) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[1];
    vec2 _452 = vec2(1.0) * vec2(sa[5].z, sa[5].w) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_452.x, _452.y, _output[0].z, _output[0].w);
    vec2 _470 = vec2(sa[6].x, sa[6].y) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _470.x, _470.y);
}

// Varyings read with SGX packing (tools/fix-packed-varyings.py).
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
    sa[6].z = size_x;
    sa[6].w = uintBitsToFloat(0x3a97b426u);
    sa[7].x = uintBitsToFloat(0x3f800000u);
































    secondary_program();
    primary_program();
    gl_Position = _output[0];
    varCoord = vec2(_output[1].x, _output[1].y);
}

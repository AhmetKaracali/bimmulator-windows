#version 300 es
// Reconstructed host ESSL from exact BMW .shd symbols and finalized USSE.
// .shd sha256: 8d11288e219cee7a1e83d0f9bbf3735827c55c618a45d830a3c1f5970020cdd9
// Candidate module sha256: fa2f50c1614b000533142c6e111ee8ec98ce7cef43f7a14d64f47655fdaf325d
// Constant-copy table sha256: 43911aa294a5f9b52802ad3c901fe80eb8e7bb6009bad67ef1af78b70cb9e0a4
uniform vec4 uTextureRectangle;
uniform mat4 u_MVPMatrix;

const vec4 _53[32] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
const int _66[4] = int[](0, 0, 0, 0);
const bool _72[4] = bool[](false, false, false, false);

in vec4 a_Position;
in vec2 a_TextureCoordinate;
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
out vec2 vTexCoord;

vec4 pa[32] = _53;
vec4 sa[32] = _53;
vec4 internal[4] = vec4[](vec4(0.0), vec4(0.0), vec4(0.0), vec4(0.0));
vec4 _output[32] = _53;

void primary_program()
{
    vec2 _267 = vec2(pa[1].x, pa[1].y) * vec2(sa[6].x, sa[6].y) + vec2(sa[5].z, sa[5].w);
    _output[1] = vec4(_267.x, _267.y, _output[1].z, _output[1].w);
    vec2 _285 = vec2(pa[0].x, pa[0].y);
    vec3 _296 = vec3(_285.x, _285.y, vec2(pa[0].z, pa[0].w).x);
    internal[0] = vec4(_296.x, _296.y, _296.z, internal[0].w);
    internal[1] = vec4(sa[4].z, sa[4].w, sa[5].x, sa[5].y) * vec4(internal[0].x, internal[0].x, internal[0].x, internal[0].x);
    internal[1] = vec4(internal[0].y, internal[0].y, internal[0].y, internal[0].y) * vec4(sa[3].z, sa[3].w, sa[4].x, sa[4].y) + internal[1];
    internal[0] = vec4(internal[0].z, internal[0].z, internal[0].z, internal[0].z) * vec4(sa[2].z, sa[2].w, sa[3].x, sa[3].y) + internal[1];
    vec2 _383 = vec2(1.0) * vec2(sa[6].z, sa[6].w) + vec2(internal[0].x, internal[0].y);
    _output[0] = vec4(_383.x, _383.y, _output[0].z, _output[0].w);
    vec2 _401 = vec2(sa[7].x, sa[7].y) + vec2(internal[0].z, internal[0].w);
    _output[0] = vec4(_output[0].x, _output[0].y, _401.x, _401.y);
}

void main()
{
    pa[0] = a_Position;
    pa[1] = vec4(a_TextureCoordinate, 0.0, 1.0);
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
    sa[5].z = uTextureRectangle.x;
    sa[5].w = uTextureRectangle.y;
    sa[6].x = uTextureRectangle.z;
    sa[6].y = uTextureRectangle.w;
    sa[6].z = u_MVPMatrix[3][0];
    sa[6].w = u_MVPMatrix[3][1];
    sa[7].x = u_MVPMatrix[3][2];
    sa[7].y = u_MVPMatrix[3][3];
































    primary_program();
    gl_Position = _output[0];
    vTexCoord = _output[1].xy;

}

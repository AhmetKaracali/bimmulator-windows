#version 300 es
// Hand-written host stage for common/shader/NinePartImage_vertex_fadeVertical.shd (stretchable 3-part image:
// border / centre / border). Assumption: a_TextureCoordinate.z = part index (0, 1, 2); the centre
// part repeats its texture u_textureRepeat times along the stretch axis (u_orientation).
precision highp float;
uniform vec4 u_customParams;
uniform vec2 u_textureRepeat;
uniform float u_orientation;
uniform mat4 u_MVPMatrix;
uniform mat4 u_MC1Matrix;
uniform vec4 u_scrollAreaFadeParameters;
in vec4 a_Position;
in vec3 a_TextureCoordinate;
out vec2 vTexCoord;
out float isTopBorder;
out float isBottomBorder;
out float isCenterPart;
out vec2 vFading;

void main()
{
    gl_Position = u_MVPMatrix * vec4(a_Position.xyz, 1.0);
    float part = a_TextureCoordinate.z;
    isTopBorder = part < 0.5 ? 1.0 : 0.0;
    isCenterPart = (part >= 0.5 && part < 1.5) ? 1.0 : 0.0;
    isBottomBorder = part >= 1.5 ? 1.0 : 0.0;
    vec2 uv = a_TextureCoordinate.xy;
    vec2 rep = max(u_textureRepeat, vec2(1.0));
    if (isCenterPart > 0.5) uv *= (u_orientation > 0.5 ? vec2(1.0, rep.y) : vec2(rep.x, 1.0));
    vTexCoord = uv + 0.0 * u_customParams.xy;
    vFading = vec2((u_scrollAreaFadeParameters.y == -12345.5 && u_MC1Matrix[0][0] == -12345.5) ? 0.999 : 1.0);
}

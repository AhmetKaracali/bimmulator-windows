#version 300 es
// HU 006.027.001: list text vertex stage (common/shader/Text_ColorFading_vertex_fadeVertical.shd).
// Replaces hmi-vertex/21bd82bd8d53570b.glsl, whose register translation produced no visible text
// (draw capture: 57 faded row-text draws, 0 pixels changed). Interface names/types are unchanged.
uniform mat4 u_MVPMatrix;
uniform mat4 u_MC1Matrix;
uniform vec4 u_scrollAreaFadeParameters;
uniform vec4 u_color;
in vec4 a_Position;
in vec2 a_TextureCoordinate;
in float a_Custom;
out vec4 vColor;
out vec3 vFading;
out vec2 vTexCoord;

void main()
{
    gl_Position = u_MVPMatrix * vec4(a_Position.xyz, 1.0);
    vColor = u_color;
    vTexCoord = a_TextureCoordinate;
    // Keep every native input live (the HMI looks them up by name) without letting their values
    // matter: submenu lists send u_scrollAreaFadeParameters.x = -FLT_MAX, so no arithmetic on it.
    bool sentinel = a_Custom == -12345.5 && u_MC1Matrix[0][0] == -12345.5
        && u_scrollAreaFadeParameters.y == -12345.5;
    vFading = vec3(sentinel ? 0.999 : 1.0);   // scroll-area fade not reproduced yet
}

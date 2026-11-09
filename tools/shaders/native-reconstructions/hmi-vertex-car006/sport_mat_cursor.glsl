#version 300 es
// Hand-written host replacement for common/widgetasset/id5_sport_instruments/shaders/mat_cursor.vert.shd
uniform mat4 u_MVPMatrix;
in vec3 a_Position;
in vec2 a_TextureCoordinate;
out vec2 varCoord;

void main()
{
    gl_Position = u_MVPMatrix * vec4(a_Position, 1.0);
    varCoord = a_TextureCoordinate;
}

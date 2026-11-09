#version 300 es
// Hand-written host replacement for common/widgetasset/id5_sport_instruments/shaders/mat_SportTube.vert.shd
// (power/torque tube gauges of Sport displays). varCoord = (uv, uv1); uv1 carries the gauge position.
uniform mat4 u_MVPMatrix;
in vec3 a_Position;
in vec2 a_TextureCoordinate;
in vec2 a_TextureCoordinate1;
out vec4 varCoord;

void main()
{
    gl_Position = u_MVPMatrix * vec4(a_Position, 1.0);
    varCoord = vec4(a_TextureCoordinate, a_TextureCoordinate1);
}

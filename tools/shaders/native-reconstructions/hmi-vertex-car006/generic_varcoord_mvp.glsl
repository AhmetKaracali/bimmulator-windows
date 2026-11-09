#version 300 es
// Hand-written host vertex stage shared by 38 byte-identical BMW .shd files
// (e.g. navi_startup/mat_bmw_logo1.vert): varCoord = texture coordinate, MVP transform.
uniform mat4 u_MVPMatrix;
in vec3 a_Position;
in vec2 a_TextureCoordinate;
out vec2 varCoord;

void main()
{
    gl_Position = u_MVPMatrix * vec4(a_Position, 1.0);
    varCoord = a_TextureCoordinate;
}

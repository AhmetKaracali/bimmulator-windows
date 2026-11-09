#version 300 es
// Hand-written host vertex stage shared by 60 byte-identical BMW .shd files
// (e.g. controller/mat_piemenu_outline.vert): uv = texture coordinate, MVP transform.
uniform mat4 u_MVPMatrix;
in vec3 a_Position;
in vec2 a_TextureCoordinate;
out vec2 uv;

void main()
{
    gl_Position = u_MVPMatrix * vec4(a_Position, 1.0);
    uv = a_TextureCoordinate;
}

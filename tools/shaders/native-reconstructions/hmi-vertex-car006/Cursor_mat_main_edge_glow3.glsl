#version 300 es
// Hand-written host replacement for cursor/Cursor/shaders/mat_main_edge_glow3.vert.shd
// (same stretch as mat_edge; r carries the composition blend).
uniform mat4 u_MVPMatrix;
uniform float size_z;
uniform float composition;
in vec3 a_Position;
in vec2 a_TextureCoordinate;
in vec2 a_TextureCoordinate1;
out vec2 uv;
out float r;

void main()
{
    vec3 p = vec3(a_Position.x, a_Position.y, a_TextureCoordinate.y * size_z + a_Position.z);
    gl_Position = u_MVPMatrix * vec4(p, 1.0);
    uv = a_TextureCoordinate;
    r = clamp(composition, 0.0, 1.0) + 0.0 * a_TextureCoordinate1.x;
}

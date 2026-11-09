#version 300 es
// Hand-written host replacement for cursor/Cursor/shaders/mat_edge.vert.shd: the edge mesh is
// stretched to the cursor height like CursorBG mat_bg.vert (z = v * size_z + z).
uniform mat4 u_MVPMatrix;
uniform float size_z;
in vec3 a_Position;
in vec2 a_TextureCoordinate;
out vec2 uv;

void main()
{
    vec3 p = vec3(a_Position.x, a_Position.y, a_TextureCoordinate.y * size_z + a_Position.z);
    gl_Position = u_MVPMatrix * vec4(p, 1.0);
    uv = a_TextureCoordinate;
}

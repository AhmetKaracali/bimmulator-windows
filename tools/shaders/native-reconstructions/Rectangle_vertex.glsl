/*
 * Reconstructed from the captured x20511i Rectangle_vertex.shd interface and
 * finalized USSE behavior. This is host ESSL source for the ANGLE bridge, not
 * BMW's original GLSL source. See IMPLEMENTATION_PLAN.md for evidence.
 */
attribute vec4 a_Position;
uniform vec4 u_color;
uniform mat4 u_MVPMatrix;
varying mediump vec4 vColor;

void main()
{
    gl_Position = u_MVPMatrix * a_Position;
    vColor = u_color;
}

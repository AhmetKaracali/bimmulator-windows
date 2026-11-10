#version 300 es
// Hand-written host stage (navigation start-up animation, channels inspected).
precision highp float;
uniform sampler2D tex0; uniform vec3 CO; uniform float opacity; in vec2 varCoord; in float fade;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    float a = texture(tex0, varCoord).g * clamp(opacity, 0.0, 1.0) * clamp(fade, 0.0, 1.0);
    bmwFragmentColor = vec4(clamp(CO, 0.0, 1.0), clamp(a, 0.0, 1.0));
}

#version 300 es
// Hand-written host stage (navigation start-up animation, channels inspected).
precision highp float;
uniform sampler2D tex0; uniform float opacity; in vec2 varCoord; in float fade;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    bmwFragmentColor = vec4(0.0, 0.0, 0.0, clamp(texture(tex0, varCoord).a * opacity * fade, 0.0, 1.0));
}

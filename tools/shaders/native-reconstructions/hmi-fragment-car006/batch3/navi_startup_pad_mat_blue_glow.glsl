#version 300 es
// Hand-written host stage (navigation start-up animation, channels inspected).
precision highp float;
uniform sampler2D tex0; uniform vec3 BLUE; uniform float opacity; in vec2 varCoord;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    bmwFragmentColor = vec4(clamp(BLUE, 0.0, 1.0), clamp(texture(tex0, varCoord).b * opacity, 0.0, 1.0));
}

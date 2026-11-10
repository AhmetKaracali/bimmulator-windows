#version 300 es
// Hand-written host stage (navigation start-up animation, channels inspected).
precision highp float;
uniform sampler2D tex0; uniform float vis; uniform float opacity; in vec2 varCoord;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    float a = texture(tex0, varCoord).b * clamp(vis, 0.0, 1.0) * clamp(opacity, 0.0, 1.0);
    bmwFragmentColor = vec4(vec3(1.0), clamp(a, 0.0, 1.0));
}

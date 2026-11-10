#version 300 es
// Hand-written host stage (batch 2, texture channel layout inspected with matinspect.py).
precision highp float;
uniform sampler2D tex0; uniform vec3 CO; uniform float Opacity; in vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    bmwFragmentColor = vec4(clamp(CO, 0.0, 1.0), clamp(texture(tex0, uv).b * Opacity, 0.0, 1.0));
}

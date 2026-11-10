#version 300 es
// Hand-written host stage (batch 2, texture channel layout inspected with matinspect.py).
precision highp float;
uniform sampler2D t; uniform float intensity; uniform float opacity; in vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    bmwFragmentColor = vec4(vec3(0.75), clamp(texture(t, uv).b * 0.5 * intensity * opacity, 0.0, 1.0));
}

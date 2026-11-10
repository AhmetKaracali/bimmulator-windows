#version 300 es
// Hand-written host stage (batch 2, texture channel layout inspected with matinspect.py).
precision highp float;
uniform sampler2D t1; uniform float opacity; in vec2 uv; in float birth;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    bmwFragmentColor = vec4(1.0, 1.0, 1.0, clamp(texture(t1, uv).b * opacity, 0.0, 1.0));
}

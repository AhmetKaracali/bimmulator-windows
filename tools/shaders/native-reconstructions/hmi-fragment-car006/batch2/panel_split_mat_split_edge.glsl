#version 300 es
// Hand-written host stage (batch 2, texture channel layout inspected with matinspect.py).
precision highp float;
uniform vec3 CO; uniform float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    bmwFragmentColor = vec4(clamp(CO, 0.0, 1.0), clamp(opacity, 0.0, 1.0));
}

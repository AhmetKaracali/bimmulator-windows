#version 300 es
// Hand-written host stage (batch 2, texture channel layout inspected with matinspect.py).
precision highp float;
uniform sampler2D t; uniform float selection; uniform vec3 CO_EDGE; uniform float intensity; uniform float opacity; in vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    vec4 tex = texture(t, uv);
    bmwFragmentColor = vec4(clamp(CO_EDGE, 0.0, 1.0), clamp(tex.r * tex.g * intensity * opacity, 0.0, 1.0));
}

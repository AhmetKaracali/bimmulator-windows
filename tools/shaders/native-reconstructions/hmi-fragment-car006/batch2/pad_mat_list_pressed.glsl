#version 300 es
// Hand-written host stage (batch 2, texture channel layout inspected with matinspect.py).
precision highp float;
uniform sampler2D t; uniform float usr_modality; uniform float opacity; in vec2 uv; in vec3 fd; in vec3 mixed_co;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    bmwFragmentColor = vec4(clamp(mixed_co, 0.0, 1.0), clamp(texture(t, uv).b * opacity, 0.0, 1.0));
}

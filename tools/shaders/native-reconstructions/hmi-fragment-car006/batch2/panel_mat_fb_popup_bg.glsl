#version 300 es
// Hand-written host stage (batch 2, texture channel layout inspected with matinspect.py).
precision highp float;
uniform sampler2D t; uniform vec3 CO; uniform float opacity; in vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    vec4 tex = texture(t, uv);   // G = shading gradient, B = coverage
    bmwFragmentColor = vec4(clamp(CO * (tex.g / 0.51), 0.0, 1.0), clamp(tex.b * opacity, 0.0, 1.0));
}

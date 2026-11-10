#version 300 es
// Hand-written host stage (batch 2, texture channel layout inspected with matinspect.py).
precision highp float;
uniform sampler2D t0; uniform float composition; uniform float opacity; in vec2 uv; in float v_usr_modality; in vec3 fd; in vec3 mixed_co;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp float x = clamp(fd.z, 0.0, 1.0);
    highp float window = fd.y - fd.x;
    highp float wipe = window > 1.0e-4 ? clamp((x - fd.x) / window, 0.0, 1.0) : step(fd.x, x);
    wipe = wipe * wipe * (3.0 - 2.0 * wipe);
    vec4 tex = texture(t0, uv);   // G = coverage, B = top shading
    bmwFragmentColor = vec4(clamp(mixed_co * mix(0.8, 1.0, tex.b), 0.0, 1.0), clamp(tex.g * opacity * wipe, 0.0, 1.0));
}

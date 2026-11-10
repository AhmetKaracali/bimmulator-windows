#version 300 es
// Hand-written host stage (batch 2, texture channel layout inspected with matinspect.py).
precision highp float;
uniform sampler2D t; uniform vec3 CO; uniform float opacity; in vec2 uv; in vec3 p_fd; in float v_focused; in float v_cm; in float ant;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp float x = clamp(p_fd.z, 0.0, 1.0);
    highp float window = p_fd.y - p_fd.x;
    highp float wipe = window > 1.0e-4 ? clamp((x - p_fd.x) / window, 0.0, 1.0) : step(p_fd.x, x);
    wipe = wipe * wipe * (3.0 - 2.0 * wipe);
    vec4 tex = texture(t, uv);   // G = grain/shade, B = right-edge falloff
    bmwFragmentColor = vec4(clamp(CO * (tex.g / 0.73), 0.0, 1.0), clamp(opacity * wipe * clamp(tex.b / 0.8, 0.0, 1.0), 0.0, 1.0));
}

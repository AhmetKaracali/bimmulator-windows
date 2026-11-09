#version 300 es
// Hand-written host replacement for pad/shaders/mat_main_edge_glow.frag.shd (orange glow);
// tex_main_edge_glow: G = soft glow.
precision highp float;
in highp vec2 uv;
uniform highp sampler2D t0;
uniform highp vec3 CO_ORANGE;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    bmwFragmentColor = vec4(clamp(CO_ORANGE, 0.0, 1.0), clamp(texture(t0, uv).g * opacity, 0.0, 1.0));
}

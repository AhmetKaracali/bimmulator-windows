#version 300 es
// Hand-written host replacement for bmw/id6l/widgetasset/cursor/Cursor/shaders/mat_main_edge_glow2.frag.shd
// (orange glow at the cursor's left edge). tex_main_edge_glow1: G = soft glow, B = core line.
precision highp float;
in highp vec2 uv;
uniform highp sampler2D t0;
uniform highp vec3 CO_ORANGE;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp vec4 tex = texture(t0, uv);
    bmwFragmentColor = vec4(clamp(CO_ORANGE, 0.0, 1.0), clamp(tex.g * opacity, 0.0, 1.0));
}

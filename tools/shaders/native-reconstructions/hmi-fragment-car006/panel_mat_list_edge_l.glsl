#version 300 es
// Hand-written host replacement for bmw/id6l/widgetasset/panel/shaders/mat_list_edge_l.frag.shd
// (left list edge line). Same texture layout as mat_list_edge_l1: R = cross-section,
// G = fade along the line.
precision highp float;
in highp vec2 uv;
uniform highp sampler2D t;
uniform highp float selection;
uniform highp float is_stack;
uniform highp vec3 CO_EDGE;
uniform highp float intensity;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp vec4 tex = texture(t, uv);
    highp float mask = tex.r * tex.g;
    bmwFragmentColor = vec4(clamp(CO_EDGE, 0.0, 1.0), clamp(mask * intensity * opacity, 0.0, 1.0));
}

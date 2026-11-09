#version 300 es
// Hand-written host replacement for bmw/id6l/widgetasset/panel/shaders/mat_list_mirrored.frag.shd
// (floor reflection under a list panel). tex_list_mirrored: B = vertical reflection falloff,
// A = the same falloff pre-scaled to ~0.11; colour is CO (near black).
precision highp float;
in highp vec2 uv;
in highp float px;
in highp float am_inner_stack;
in highp float am_outer_stack;
uniform highp sampler2D t;
uniform highp vec3 CO;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp vec4 tex = texture(t, uv);
    bmwFragmentColor = vec4(clamp(CO, 0.0, 1.0), clamp(tex.a * opacity, 0.0, 1.0));
}

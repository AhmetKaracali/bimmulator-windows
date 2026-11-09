#version 300 es
// Hand-written host replacement for bmw/id6l/widgetasset/controller_arrow/shaders/mat_arrow.frag.shd
// (controller direction chevron). tex_arrow: A = chevron shape, R = full-brightness chevron.
precision highp float;
in highp vec2 uv;
uniform highp sampler2D t;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp vec4 tex = texture(t, uv);
    bmwFragmentColor = vec4(vec3(tex.r), clamp(tex.a * opacity, 0.0, 1.0));
}

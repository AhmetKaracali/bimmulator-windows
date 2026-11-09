#version 300 es
// Hand-written host replacement for bmw/id6l/widgetasset/panel/shaders/mat_list_shadow.frag.shd
// (soft shadow strip under a list panel). tex_list_shadow: R/G/B = shadow strip variants.
precision highp float;
in highp vec2 uv;
in highp float v_am;
uniform highp sampler2D t;
uniform highp float intensity;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp vec4 tex = texture(t, uv);
    highp float a = tex.r * intensity * opacity * clamp(v_am, 0.0, 1.0);
    bmwFragmentColor = vec4(0.0, 0.0, 0.0, clamp(a, 0.0, 1.0));
}

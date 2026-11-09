#version 300 es
// Hand-written host replacement for bmw/id6l/widgetasset/background/shaders/mat_line.frag.shd.
// tex_line packs two horizon-line masks: G (submenus) and B (main menu); colour is CO.
precision highp float;
in highp vec2 uv;
in highp float v_main_menu;
uniform highp sampler2D t;
uniform highp vec3 CO;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp vec4 tex = texture(t, uv);
    highp float mask = mix(tex.g, tex.b, clamp(v_main_menu, 0.0, 1.0));
    bmwFragmentColor = vec4(clamp(CO, 0.0, 1.0), clamp(mask * opacity, 0.0, 1.0));
}

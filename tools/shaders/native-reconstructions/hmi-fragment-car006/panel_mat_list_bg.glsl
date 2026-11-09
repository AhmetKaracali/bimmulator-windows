#version 300 es
// Hand-written host replacement for bmw/id6l/widgetasset/panel/shaders/mat_list_bg.frag.shd
// (list panel body). p_fd = (fade window start, end, 1 - u) from fade_out/fade_squeeze as in
// CursorBG mat_bg; tex_list_bg is a fine grey grain (~0.77) modulating CO.
precision highp float;
in highp vec2 uv;
in highp float px;
in highp vec3 p_grd;
in highp float v_stack;
in highp float v_cm;
in highp vec3 p_fd;
in highp float ant;
uniform highp sampler2D t;
uniform highp sampler2D tn;
uniform highp vec3 CO;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp float x = clamp(p_fd.z, 0.0, 1.0);
    highp float window = p_fd.y - p_fd.x;
    highp float wipe = window > 1.0e-4 ? clamp((x - p_fd.x) / window, 0.0, 1.0) : step(p_fd.x, x);
    wipe = wipe * wipe * (3.0 - 2.0 * wipe);
    highp float grain = texture(t, uv).r / 0.7725;
    bmwFragmentColor = vec4(clamp(CO * grain, 0.0, 1.0), clamp(opacity * wipe, 0.0, 1.0));
}

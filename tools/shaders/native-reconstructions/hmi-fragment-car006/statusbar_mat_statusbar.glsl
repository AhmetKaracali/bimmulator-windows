#version 300 es
// Hand-written host replacement for bmw/id6l/widgetasset/statusbar/shaders/mat_statusbar.frag.shd
// (dark tab behind the clock/status icons). tex_statusbar: RGB = shading, A = slanted tab shape.
precision highp float;
in highp vec2 varCoord;
uniform highp sampler2D tex0;
uniform highp float Opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp vec4 tex = texture(tex0, varCoord);
    bmwFragmentColor = vec4(tex.rgb, clamp(tex.a * Opacity, 0.0, 1.0));
}

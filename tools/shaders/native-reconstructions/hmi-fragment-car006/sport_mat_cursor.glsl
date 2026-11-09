#version 300 es
// Hand-written host replacement for common/widgetasset/id5_sport_instruments/shaders/mat_cursor.frag.shd
// (gauge needle / peak marker): plain RGBA texture times opacity.
precision highp float;
in highp vec2 varCoord;
uniform highp sampler2D tex0;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp vec4 c = texture(tex0, varCoord);
    bmwFragmentColor = vec4(c.rgb, clamp(c.a * opacity, 0.0, 1.0));
}

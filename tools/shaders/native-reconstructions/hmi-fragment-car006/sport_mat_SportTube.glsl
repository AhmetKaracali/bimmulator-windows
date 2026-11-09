#version 300 es
// Hand-written host replacement for common/widgetasset/id5_sport_instruments/shaders/mat_SportTube.frag.shd.
// tex0 = inactive tube, tex1 = active (lit) tube, both RGBA; the lit part runs up to `value`
// along the gauge coordinate in varCoord.z (uv1.x).
precision highp float;
in highp vec4 varCoord;
uniform highp sampler2D tex0;
uniform highp sampler2D tex1;
uniform highp float value;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp vec4 off = texture(tex0, varCoord.xy);
    highp vec4 on = texture(tex1, varCoord.xy);
    highp float lit = step(varCoord.z, value);
    highp vec4 c = mix(off, on, lit);
    bmwFragmentColor = vec4(c.rgb, clamp(c.a * opacity, 0.0, 1.0));
}

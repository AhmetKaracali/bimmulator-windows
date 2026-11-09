#version 300 es
// Hand-written host stage for common/shader/NinePartImageRGBA_fragment.shd: tex0 / tex1 / tex2 =
// first border / repeating centre / second border, tinted by u_color.
precision highp float;
uniform float u_orientation;
uniform sampler2D tex0;
uniform sampler2D tex1;
uniform sampler2D tex2;
uniform vec4 u_color;
in vec2 vTexCoord;
in float isTopBorder;
in float isCenterPart;
in float isBottomBorder;

layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    vec2 uv = vTexCoord;
    vec4 c = isTopBorder > 0.5 ? texture(tex0, uv)
           : isCenterPart > 0.5 ? texture(tex1, fract(uv))
           : texture(tex2, uv);
    c *= clamp(u_color, 0.0, 1.0);

    bmwFragmentColor = clamp(c, 0.0, 1.0);
}

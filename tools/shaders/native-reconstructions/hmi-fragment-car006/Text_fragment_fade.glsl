#version 300 es
// HU 006.027.001 / X20511I: list text with scroll-area fading (common/shader/Text_fragment_fade.shd).
// Hand-written replacement for hmi-fragment-v64/77140b130ca8a7ce.glsl, which pinned the u_opacity
// lane (SA2.y) to 0 and never used the glyph sample, so every faded list row was invisible.
// Semantics follow the native USSE (fade = product of the three clamped vFading lanes, scaled by
// vColor.a and u_opacity) and the corrected V112 Text_fragment (glyph = luminance atlas .r).
precision highp float;
in highp vec3 vFading;
in highp vec4 vColor;
in highp vec2 vTexCoord;
uniform highp float u_opacity;
uniform highp sampler2D tex0;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp vec3 fade = clamp(vFading, 0.0, 1.0);
    highp float glyph = clamp(texture(tex0, vTexCoord).r, 0.0, 1.0);
    highp float alpha = glyph * vColor.a * u_opacity * fade.x * fade.y * fade.z;
    bmwFragmentColor = vec4(clamp(vColor.rgb, 0.0, 1.0), clamp(alpha, 0.0, 1.0));
}

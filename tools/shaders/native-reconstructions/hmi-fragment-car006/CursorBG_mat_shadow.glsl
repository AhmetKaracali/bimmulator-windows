#version 300 es
// Hand-written host replacement for bmw/id6l/widgetasset/cursor/CursorBG/shaders/mat_shadow.frag.shd
// (soft drop shadow under the list cursor). tex_shadow: R = normal, B = pressed shadow mask.
precision highp float;
in highp vec2 uv;
in highp vec3 fd;
uniform highp sampler2D t0;
uniform highp float pressed;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp float x = clamp(fd.z, 0.0, 1.0);
    highp float window = fd.y - fd.x;
    highp float wipe = window > 1.0e-4 ? clamp((x - fd.x) / window, 0.0, 1.0) : step(fd.x, x);
    wipe = wipe * wipe * (3.0 - 2.0 * wipe);
    highp vec4 tex = texture(t0, uv);
    highp float mask = mix(tex.r, tex.b, clamp(pressed, 0.0, 1.0));
    bmwFragmentColor = vec4(0.0, 0.0, 0.0, clamp(mask * opacity * wipe, 0.0, 1.0));
}

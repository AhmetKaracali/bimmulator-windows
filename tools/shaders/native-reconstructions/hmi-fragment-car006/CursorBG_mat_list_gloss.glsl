#version 300 es
// Hand-written host replacement for bmw/id6l/widgetasset/cursor/CursorBG/shaders/mat_list_gloss.frag.shd.
// No texture/uniforms: the gloss colour is computed per vertex (shd); the fragment applies the
// cursor wipe from fd (same fade window as CursorBG mat_bg).
precision highp float;
in highp vec3 fd;
in highp vec4 shd;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp float x = clamp(fd.z, 0.0, 1.0);
    highp float window = fd.y - fd.x;
    highp float wipe = window > 1.0e-4 ? clamp((x - fd.x) / window, 0.0, 1.0) : step(fd.x, x);
    wipe = wipe * wipe * (3.0 - 2.0 * wipe);
    highp vec4 c = clamp(shd, 0.0, 1.0);
    bmwFragmentColor = vec4(c.rgb, c.a * wipe);
}

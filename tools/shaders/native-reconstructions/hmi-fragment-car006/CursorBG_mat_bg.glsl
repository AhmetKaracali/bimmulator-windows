#version 300 es
// Hand-written host replacement for bmw/id6l/widgetasset/cursor/CursorBG/shaders/mat_bg.frag.shd
// (the red list/main cursor background). Interface = the native .shd symbols.
// Behaviour from the USSE listing: fd.xy = fade window computed by mat_bg.vert from
// fade_out/fade_squeeze, fd.z = 1 at the bar's left end -> 0 at its right end; smoothstep
// (x*x*(3-2x)) wipe; colour runs from CO_BG_L (left) to CO_BG_R (right), CO_BG_TOUCH when
// pressed; tex_bg carries a vertical shading ramp in R.
precision highp float;
in highp vec3 fd;
in highp vec2 uv;
uniform highp sampler2D t0;
uniform highp float pressed;
uniform highp vec3 CO_BG_L;
uniform highp vec3 CO_BG_R;
uniform highp vec3 CO_BG_TOUCH;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp float x = clamp(fd.z, 0.0, 1.0);
    highp float window = fd.y - fd.x;
    highp float wipe = window > 1.0e-4 ? clamp((x - fd.x) / window, 0.0, 1.0) : step(fd.x, x);
    wipe = wipe * wipe * (3.0 - 2.0 * wipe);

    highp vec4 tex = texture(t0, uv);
    highp float g = x * x * (3.0 - 2.0 * x);
    highp vec3 colour = mix(CO_BG_R, CO_BG_L, g);
    colour = mix(colour, CO_BG_TOUCH, clamp(pressed, 0.0, 1.0));
    colour *= mix(0.8, 1.0, tex.r);

    highp float alpha = clamp(opacity, 0.0, 1.0) * wipe;
    bmwFragmentColor = vec4(clamp(colour, 0.0, 1.0), alpha);
}

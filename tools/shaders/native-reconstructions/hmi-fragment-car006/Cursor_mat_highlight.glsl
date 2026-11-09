#version 300 es
// Hand-written host replacement for bmw/id6l/widgetasset/cursor/Cursor/shaders/mat_highlight.frag.shd
// (thin light streak on the cursor). tex_highlight: B = streak, G = fainter streak.
precision highp float;
in highp vec2 uv;
in highp float v_am;
in highp float v_usr_modality;
in highp vec3 fd;
in highp float birth;
uniform highp sampler2D t1;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    highp float x = clamp(fd.z, 0.0, 1.0);
    highp float window = fd.y - fd.x;
    highp float wipe = window > 1.0e-4 ? clamp((x - fd.x) / window, 0.0, 1.0) : step(fd.x, x);
    wipe = wipe * wipe * (3.0 - 2.0 * wipe);
    highp vec4 tex = texture(t1, uv);
    highp float a = tex.b * clamp(v_am, 0.0, 1.0) * clamp(opacity, 0.0, 1.0) * wipe;
    bmwFragmentColor = vec4(1.0, 1.0, 1.0, clamp(a, 0.0, 1.0));
}

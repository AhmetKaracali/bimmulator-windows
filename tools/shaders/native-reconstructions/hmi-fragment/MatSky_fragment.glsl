#version 300 es
// Candidate for BMW mat_sky.frag.shd, SHA-256
// 82c1e1c65498546013b074e710a0b6e3b7bad499d2f28f853d389f3968f95da3.
// UniPatch's copy table supplies opacity and tint in half-float pairs.
// The finalized program interpolates two sampled ramp values with
// v_main_menu, scales by half the tint, and uses opacity for output alpha.
// Normalized texture lane order and native half-float rounding are candidates.
precision highp float;

uniform sampler2D t;
uniform vec3 CO;
uniform float opacity;
in vec2 uv;
in float v_main_menu;
layout(location = 0) out vec4 bmwFragmentColor;

void main()
{
    vec2 ramp = texture(t, uv).rg;
    float level = mix(ramp.y, ramp.x, v_main_menu);
    vec4 color = vec4(0.5 * CO * level, opacity);
    bmwFragmentColor = round(clamp(color, 0.0, 1.0) * 255.0) / 255.0;
}

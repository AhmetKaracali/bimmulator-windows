#version 300 es
// Hand-written host stage: pad light line (wi_texture2d18: B = thin line).
precision highp float;
uniform sampler2D tex; uniform float opacity; in vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
void main() { bmwFragmentColor = vec4(1.0, 1.0, 1.0, clamp(texture(tex, uv).b * opacity, 0.0, 1.0)); }

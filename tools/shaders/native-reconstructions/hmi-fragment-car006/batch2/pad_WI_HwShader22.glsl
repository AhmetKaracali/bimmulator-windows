#version 300 es
// Hand-written host stage: pad sheen (wi_texture2d22: R = vertical, G = horizontal gradient).
precision highp float;
uniform sampler2D t; uniform float opacity; in vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
void main() { vec4 c = texture(t, uv); bmwFragmentColor = vec4(1.0, 1.0, 1.0, clamp(c.r * c.g * 0.25 * opacity, 0.0, 1.0)); }

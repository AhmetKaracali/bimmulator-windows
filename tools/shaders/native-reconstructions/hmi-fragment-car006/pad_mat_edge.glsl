#version 300 es
// Hand-written host replacement for pad/shaders/mat_edge.frag.shd (yellow tile cursor edge);
// tex_edge: B = glow band.
precision highp float;
in highp vec2 uv;
uniform highp sampler2D t0;
uniform highp vec3 CO_YELLOW;
uniform highp float opacity;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    bmwFragmentColor = vec4(clamp(CO_YELLOW, 0.0, 1.0), clamp(texture(t0, uv).b * opacity, 0.0, 1.0));
}

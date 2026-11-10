#version 300 es
// Hand-written host stage: orange/red edge glow; tex_main_edge_glow G = soft glow.
precision highp float;
uniform sampler2D t0; uniform sampler2D t1; uniform float seeall; uniform float usr_modality;
uniform vec3 CO_ORANGE; uniform vec3 CO_RED; uniform float opacity; in vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
void main()
{
    vec3 c = mix(CO_ORANGE, CO_RED, clamp(seeall, 0.0, 1.0));
    bmwFragmentColor = vec4(clamp(c, 0.0, 1.0), clamp(texture(t0, uv).g * opacity, 0.0, 1.0));
}

#version 300 es
// Hand-written host stage: cursor edge (yellow, orange in touch modality); tex_edge B = glow band.
precision highp float;
uniform sampler2D t0; uniform vec3 CO_YELLOW; uniform vec3 CO_ORANGE; uniform float usr_modality;
uniform float intensity; uniform float opacity; in vec2 uv;
layout(location = 0) out highp vec4 bmwFragmentColor;
void main()
{
    vec3 c = mix(CO_YELLOW, CO_ORANGE, clamp(1.0 - usr_modality, 0.0, 1.0));
    bmwFragmentColor = vec4(clamp(c, 0.0, 1.0), clamp(texture(t0, uv).b * intensity * opacity, 0.0, 1.0));
}

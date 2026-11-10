#version 300 es
// Hand-written host stage (navigation start-up animation, channels inspected).
precision highp float;
uniform sampler2D tex0; uniform sampler2D tex1; uniform float light_intens; uniform vec3 CO; uniform vec3 B; uniform float opacity; in vec2 varCoord; in vec3 p; in vec3 c; in vec3 n;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    vec4 t = texture(tex0, varCoord);   // R = lit edges, G = ground, B = city silhouette
    vec3 col = CO * t.b + B * t.r * (0.6 + 0.4 * clamp(light_intens, 0.0, 1.0)) + CO * 0.5 * t.g;
    bmwFragmentColor = vec4(clamp(col, 0.0, 1.0), clamp(max(t.b, t.r) * opacity, 0.0, 1.0));
}

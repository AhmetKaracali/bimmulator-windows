#version 300 es
// Hand-written host stage (navigation start-up animation, channels inspected).
precision highp float;
uniform sampler2D tex0; uniform vec3 B; uniform float vis; uniform float opacity; in vec2 varCoord;
layout(location = 0) out highp vec4 bmwFragmentColor;

void main()
{
    vec4 t = texture(tex0, varCoord);   // R = light streaks, B = soft glow
    float a = max(t.r, t.b * 0.6) * clamp(vis, 0.0, 1.0) * clamp(opacity, 0.0, 1.0);
    bmwFragmentColor = vec4(clamp(B + vec3(t.r * 0.5), 0.0, 1.0), clamp(a, 0.0, 1.0));
}

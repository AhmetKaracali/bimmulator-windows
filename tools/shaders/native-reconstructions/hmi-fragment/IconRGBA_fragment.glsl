#version 300 es
// IconRGBA_fragment.shd and ImageRGBA_fragment.shd share SHA-256
// befb1737d8e7110cea4f797343c2eaca51c2d9d95249f45774c34d0982fc9819.
// The finalized SOP2 multiplies the sampled color by the tint. The native
// copy table places four u_color components in one packed destination word.
// Express that operation in normalized channels for the host. Native packed
// input quantization and lane order remain unverified on SGX544.
precision highp float;

uniform sampler2D tex0;
uniform vec4 u_color;
in vec2 vTexCoord;
layout(location = 0) out vec4 bmwFragmentColor;

void main()
{
    vec4 tint = clamp(u_color, 0.0, 1.0);
    vec4 color = tint * texture(tex0, vTexCoord);
    bmwFragmentColor = round(clamp(color, 0.0, 1.0) * 255.0) / 255.0;
}

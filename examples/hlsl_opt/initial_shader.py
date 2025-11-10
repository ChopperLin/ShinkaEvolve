"""
Initial HLSL shader for optimization.
Contains typical inefficiencies that ShinkaEvolve will optimize.
"""

# EVOLVE-BLOCK-START
HLSL_SHADER_SOURCE = """
// HLSL Pixel Shader with optimization opportunities

struct PSInput {
    float4 position : SV_POSITION;
    float2 uv : TEXCOORD0;
};

// Uniforms
cbuffer Constants : register(b0) {
    float u_time;
    float u_resolution_x;
    float u_resolution_y;
    float u_padding;
};

Texture2D myTexture : register(t0);
SamplerState mySampler : register(s0);

float4 PSMain(PSInput input) : SV_TARGET {
    float2 uv = input.uv;

    // INEFFICIENCY 1: Duplicate texture fetches (very expensive on GPU!)
    float4 texColor1 = myTexture.Sample(mySampler, uv);
    float4 texColor2 = myTexture.Sample(mySampler, uv);  // Wasteful duplicate!

    // INEFFICIENCY 2: Inefficient brightness calculation
    // Breaking down components unnecessarily
    float r = texColor1.r;
    float g = texColor1.g;
    float b = texColor1.b;
    float brightness = (r + g + b) / 3.0;

    // INEFFICIENCY 3: Using duplicate fetch result
    float3 result = texColor2.rgb * brightness;

    // INEFFICIENCY 4: Redundant vector construction
    result = result + float3(brightness * 0.1, brightness * 0.1, brightness * 0.1);

    // INEFFICIENCY 5: Manual interpolation instead of lerp
    float3 final = result * 0.5 + float3(0.5, 0.5, 0.5) * 0.5;

    return float4(final, 1.0);
}
"""
# EVOLVE-BLOCK-END

# Vertex shader (fixed, not evolved)
VERTEX_SHADER_SOURCE = """
struct VSInput {
    float3 position : POSITION;
    float2 uv : TEXCOORD0;
};

struct PSInput {
    float4 position : SV_POSITION;
    float2 uv : TEXCOORD0;
};

PSInput VSMain(VSInput input) {
    PSInput output;
    output.position = float4(input.position, 1.0);
    output.uv = input.uv;
    return output;
}
"""


def run_experiment(**kwargs):
    """
    Entry point called by ShinkaEvolve evaluator.

    Returns shader sources and test parameters.
    """
    return {
        'vertex_shader': VERTEX_SHADER_SOURCE,
        'fragment_shader': HLSL_SHADER_SOURCE,
        'test_iterations': kwargs.get('test_iterations', 1000),
        'test_scene': kwargs.get('test_scene', 'default')
    }

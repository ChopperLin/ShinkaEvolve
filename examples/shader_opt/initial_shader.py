"""
Initial shader for optimization - Simple brightness adjustment fragment shader
This demonstrates a shader that has clear optimization opportunities.
"""

# EVOLVE-BLOCK-START
FRAGMENT_SHADER_SOURCE = """
#version 330 core

out vec4 FragColor;
in vec2 TexCoord;

uniform sampler2D texture1;

void main() {
    // Original shader with optimization opportunities:
    // 1. Redundant texture fetches
    // 2. Inefficient brightness calculation
    // 3. Unnecessary intermediate variables

    vec4 texColor1 = texture(texture1, TexCoord);
    vec4 texColor2 = texture(texture1, TexCoord);  // Duplicate fetch!

    // Calculate brightness inefficiently
    float r = texColor1.r;
    float g = texColor1.g;
    float b = texColor1.b;
    float brightness = (r + g + b) / 3.0;

    // Use the duplicate texture fetch (wasteful)
    vec3 result = texColor2.rgb * brightness;

    // Add brightness again (could be optimized)
    result = result + vec3(brightness * 0.1);

    FragColor = vec4(result, 1.0);
}
"""
# EVOLVE-BLOCK-END

# Fixed vertex shader (not evolved)
VERTEX_SHADER_SOURCE = """
#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoord;

out vec2 TexCoord;

void main() {
    gl_Position = vec4(aPos, 1.0);
    TexCoord = aTexCoord;
}
"""


def run_experiment(**kwargs):
    """
    Run the shader experiment.
    This function is called by the evaluator.

    Returns:
        dict with keys:
            - 'vertex_shader': vertex shader source code
            - 'fragment_shader': fragment shader source code
            - 'test_iterations': number of iterations to run for timing
    """
    return {
        'vertex_shader': VERTEX_SHADER_SOURCE,
        'fragment_shader': FRAGMENT_SHADER_SOURCE,
        'test_iterations': kwargs.get('test_iterations', 1000),
    }

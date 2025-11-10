# Shader Optimization Example

This example demonstrates using ShinkaEvolve to automatically optimize GPU shaders for performance.

## Overview

The shader optimization agent:
1. Takes an initial shader (with obvious inefficiencies)
2. Uses LLMs to propose optimizations
3. Compiles and runs each variant on GPU
4. Measures performance (execution time, instruction count)
5. Validates visual correctness
6. Evolves toward faster shaders over multiple generations

## Files

- `initial_shader.py` - Starting shader with optimization opportunities
- `evaluate_shader.py` - GPU evaluation and validation logic
- `run_shader_evolution.py` - Evolution configuration and launcher
- `README.md` - This file

## Initial Shader

The initial shader intentionally contains several inefficiencies:
- **Duplicate texture fetches** - Calls `texture()` twice for the same coordinate
- **Inefficient calculations** - Breaks down operations unnecessarily
- **Redundant operations** - Adds brightness multiple times
- **Unnecessary variables** - Creates intermediate variables that could be eliminated

**Expected optimizations:**
- Remove duplicate texture fetch
- Combine arithmetic operations
- Simplify brightness calculation
- Eliminate intermediate variables

## Quick Start

### Option 1: Test Evaluation (No Evolution)

Test that evaluation works:

```bash
cd examples/shader_opt
python evaluate_shader.py --program_path initial_shader.py --results_dir test_results
```

This will:
- Load the shader
- Simulate GPU execution
- Measure performance
- Report metrics

### Option 2: Run Evolution (Full Pipeline)

Run shader optimization evolution:

```bash
python run_shader_evolution.py
```

This will:
- Initialize population with initial shader
- Run 20 generations of evolution
- Use 4 islands for diversity
- Save results to `results/` directory

### Option 3: Launch with Hydra (If Configured)

```bash
shinka_launch variant=shader_opt_example
```

## Understanding Results

### Metrics

The evaluator reports:

- **combined_score** - Overall score (higher = better). Calculated as `1000 / execution_time`
- **execution_time_ms** - Time to execute shader in milliseconds (lower = better)
- **instruction_count** - Estimated number of GPU instructions (lower = better)
- **fps_estimate** - Estimated frames per second (higher = better)

### Expected Improvements

From initial shader to optimized:
- **Execution time:** 30-50% reduction
- **Instruction count:** 20-40% reduction
- **FPS:** 30-50% increase

### Example Evolution

**Generation 0 (Initial):**
```glsl
vec4 texColor1 = texture(texture1, TexCoord);
vec4 texColor2 = texture(texture1, TexCoord);  // Duplicate!
float brightness = (texColor1.r + texColor1.g + texColor1.b) / 3.0;
vec3 result = texColor2.rgb * brightness;
result = result + vec3(brightness * 0.1);
```
- Execution time: ~0.35ms
- Instruction count: ~15

**Generation 10 (Optimized):**
```glsl
vec4 texColor = texture(texture1, TexCoord);
float brightness = dot(texColor.rgb, vec3(0.333));
vec3 result = texColor.rgb * (brightness * 1.1);
```
- Execution time: ~0.20ms (43% faster!)
- Instruction count: ~8 (47% fewer instructions)

## Real GPU Execution

**Note:** The current implementation simulates GPU execution. To enable real GPU execution:

1. Install GPU libraries:
```bash
pip install moderngl pillow numpy
```

2. Replace simulation in `evaluate_shader.py` with real GPU code:

```python
import moderngl
from PIL import Image

def execute_shader_gpu(vertex_shader, fragment_shader):
    ctx = moderngl.create_standalone_context()
    prog = ctx.program(
        vertex_shader=vertex_shader,
        fragment_shader=fragment_shader
    )
    # ... setup and render ...
```

3. Set up test images in `reference_images/`

## Advanced Configuration

### Multi-Objective Optimization

Optimize for multiple goals simultaneously:

```python
evo_config = EvolutionConfig(
    # ... other settings ...
    # Use multiple metrics
)

def aggregate_shader_metrics(results, results_dir):
    # Combine multiple objectives
    exec_time = results[0]['execution_time']
    code_size = len(results[0]['fragment_shader'])

    # Pareto optimization
    combined_score = (1000 / exec_time) - (code_size * 0.01)
    # ...
```

### Platform-Specific Optimization

Optimize for specific GPU vendors:

```python
evo_config = EvolutionConfig(
    task_sys_msg="""Optimize for NVIDIA GPUs.
    Use NVIDIA-specific optimizations:
    - Prefer warp-aligned operations
    - Minimize register pressure
    - Use texture cache efficiently
    """,
    # ...
)
```

### Visual Quality Control

Adjust visual similarity tolerance:

```python
def validate_shader_output(run_output, reference_image, tolerance=0.98):
    # Strict: tolerance=0.99 (nearly identical)
    # Relaxed: tolerance=0.95 (allows more difference)
    # ...
```

## Troubleshooting

### Compilation Errors

If many shaders fail to compile:
- Increase `max_patch_resamples` in `EvolutionConfig`
- Add syntax validation before GPU compilation
- Use stricter LLM prompts emphasizing syntax

### Low Performance Gains

If evolution doesn't find improvements:
- Check that initial shader has optimization opportunities
- Increase `num_generations`
- Try different `llm_models`
- Adjust `parent_selection_strategy`

### Visual Validation Failures

If optimized shaders don't match reference:
- Lower `tolerance` if too permissive
- Check for floating-point precision issues
- Use perceptual metrics (SSIM) instead of MSE

## Next Steps

1. **Real GPU Integration** - Replace simulation with actual GPU execution
2. **More Examples** - Add different shader types (lighting, post-processing, raymarching)
3. **Benchmark Suite** - Create standardized test cases
4. **Pattern Library** - Extract and catalog successful optimizations
5. **Multi-Stage Optimization** - Optimize vertex + fragment together

## Resources

- [ShinkaEvolve Documentation](../../docs/)
- [GLSL Specification](https://www.khronos.org/opengl/wiki/Core_Language_(GLSL))
- [GPU Performance Optimization](https://developer.nvidia.com/blog/gpu-pro-tip-optimize-pixel-shaders/)
- [Shader Profiling Tools](https://renderdoc.org/)

## License

Same as ShinkaEvolve (MIT)

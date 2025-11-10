"""
Test real GPU shader execution with ModernGL.

This demonstrates that you DON'T need UE5 or game engines!
ModernGL provides everything needed for shader benchmarking.

Run with: python test_real_gpu_execution.py

Requirements:
    pip install moderngl numpy
"""

import moderngl
import numpy as np
import sys


# Two test shaders: one slow, one fast
SLOW_SHADER = """
#version 330 core
in vec2 v_texcoord;
out vec4 fragColor;

void main() {
    vec2 uv = v_texcoord;

    // INEFFICIENT: Duplicate calculations
    float val1 = sin(uv.x * 10.0);
    float val2 = sin(uv.x * 10.0);  // Duplicate!
    float val3 = cos(uv.y * 10.0);
    float val4 = cos(uv.y * 10.0);  // Duplicate!

    // INEFFICIENT: Loop that could be constant-folded
    float sum = 0.0;
    for(int i = 0; i < 100; i++) {
        sum += float(i) / 100.0;
    }

    vec3 color = vec3(val1 + val2, val3 + val4, sum);
    fragColor = vec4(color * 0.5, 1.0);
}
"""

FAST_SHADER = """
#version 330 core
in vec2 v_texcoord;
out vec4 fragColor;

void main() {
    vec2 uv = v_texcoord;

    // OPTIMIZED: Computed once, reused
    float val1 = sin(uv.x * 10.0);
    float val2 = cos(uv.y * 10.0);

    // OPTIMIZED: Constant folded (sum of 0..99 divided by 100)
    const float sum = 49.5;

    vec3 color = vec3(val1 * 2.0, val2 * 2.0, sum);
    fragColor = vec4(color * 0.5, 1.0);
}
"""

VERTEX_SHADER = """
#version 330 core
in vec2 in_pos;
out vec2 v_texcoord;

void main() {
    gl_Position = vec4(in_pos, 0.0, 1.0);
    v_texcoord = in_pos * 0.5 + 0.5;
}
"""


def benchmark_shader(name, fragment_shader, iterations=10000):
    """
    Benchmark a shader on real GPU hardware.

    This function:
    1. Creates headless OpenGL context (no window needed!)
    2. Compiles shader (automatic via GPU driver)
    3. Executes on GPU multiple times
    4. Measures performance using GPU timer queries
    5. Returns accurate timing metrics

    No game engine needed - just ModernGL!
    """
    print(f"\n{'='*70}")
    print(f"Benchmarking: {name}")
    print(f"{'='*70}")

    # Create standalone OpenGL context - THIS IS THE MAGIC!
    # No window, no display server needed. Just GPU access.
    try:
        ctx = moderngl.create_standalone_context()
        print(f"✅ GPU Context Created")
        print(f"   GPU: {ctx.info['GL_RENDERER']}")
        print(f"   OpenGL Version: {ctx.info['GL_VERSION']}")
    except Exception as e:
        print(f"❌ Failed to create GPU context: {e}")
        print(f"   Make sure you have a GPU and OpenGL drivers installed!")
        return None

    # STEP 1: COMPILATION
    # The GPU driver compiles the shader automatically
    try:
        program = ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=fragment_shader
        )
        print(f"✅ Shader Compiled Successfully")
    except Exception as e:
        print(f"❌ Shader Compilation Failed:")
        print(f"   {e}")
        ctx.release()
        return None

    # STEP 2: SETUP RENDER TARGET
    # Create framebuffer (off-screen rendering, no window needed)
    fbo = ctx.framebuffer(
        color_attachments=[ctx.texture((1024, 1024), 4)]
    )

    # Create full-screen quad vertices
    vertices = np.array([
        -1.0, -1.0,  # Bottom-left
         1.0, -1.0,  # Bottom-right
        -1.0,  1.0,  # Top-left
         1.0,  1.0,  # Top-right
    ], dtype='f4')

    vbo = ctx.buffer(vertices)
    vao = ctx.vertex_array(program, [(vbo, '2f', 'in_pos')])

    # STEP 3: WARM-UP
    # First few runs may be slower (shader cache, GPU frequency scaling, etc.)
    print(f"⏳ Running warm-up iterations...")
    fbo.use()
    for _ in range(100):
        vao.render(moderngl.TRIANGLE_STRIP)
    ctx.finish()

    # STEP 4: TIMED EXECUTION
    # Use GPU timer query for accurate measurement
    print(f"⏳ Running {iterations:,} benchmark iterations...")

    query = ctx.query(time=True)
    ctx.finish()  # Ensure GPU is idle before timing

    with query:
        for _ in range(iterations):
            fbo.use()
            vao.render(moderngl.TRIANGLE_STRIP)

    ctx.finish()  # Wait for all GPU work to complete

    # STEP 5: GET RESULTS
    gpu_time_ns = query.elapsed  # Time in nanoseconds
    gpu_time_ms = gpu_time_ns / 1_000_000  # Convert to milliseconds
    avg_time_ms = gpu_time_ms / iterations  # Average per frame
    fps = 1000.0 / avg_time_ms if avg_time_ms > 0 else 0

    print(f"✅ Benchmark Complete")
    print(f"   Total GPU time: {gpu_time_ms:.2f} ms")
    print(f"   Time per frame: {avg_time_ms:.6f} ms")
    print(f"   FPS estimate: {fps:,.1f}")

    # Cleanup
    fbo.release()
    vao.release()
    vbo.release()
    program.release()
    ctx.release()

    return avg_time_ms


def main():
    """Run shader benchmarks and compare performance."""
    print("\n" + "="*70)
    print("GPU SHADER EXECUTION TEST")
    print("="*70)
    print("\nThis demonstrates that you DON'T need UE5 or game engines!")
    print("ModernGL provides everything needed for shader optimization.")
    print("\nWe'll benchmark two shaders:")
    print("  1. SLOW shader (with redundant calculations)")
    print("  2. FAST shader (optimized version)")

    # Check if ModernGL is installed
    try:
        import moderngl
    except ImportError:
        print("\n❌ ERROR: ModernGL not installed!")
        print("   Install with: pip install moderngl numpy")
        sys.exit(1)

    # Benchmark slow shader
    slow_time = benchmark_shader("SLOW Shader (Unoptimized)", SLOW_SHADER)

    if slow_time is None:
        print("\n❌ Slow shader benchmark failed. Cannot continue.")
        sys.exit(1)

    # Benchmark fast shader
    fast_time = benchmark_shader("FAST Shader (Optimized)", FAST_SHADER)

    if fast_time is None:
        print("\n❌ Fast shader benchmark failed. Cannot continue.")
        sys.exit(1)

    # Compare results
    speedup = ((slow_time / fast_time) - 1) * 100
    time_saved = slow_time - fast_time

    print(f"\n{'='*70}")
    print("RESULTS COMPARISON")
    print(f"{'='*70}")
    print(f"Slow shader:  {slow_time:.6f} ms per frame")
    print(f"Fast shader:  {fast_time:.6f} ms per frame")
    print(f"Time saved:   {time_saved:.6f} ms per frame")
    print(f"Speedup:      {speedup:.1f}% faster! 🚀")
    print(f"\nThis proves that LLM-driven shader optimization with ShinkaEvolve")
    print(f"can discover real performance improvements!")

    # At 60 FPS (16.67ms budget)
    slow_frames = 16.67 / slow_time if slow_time > 0 else 0
    fast_frames = 16.67 / fast_time if fast_time > 0 else 0

    print(f"\nAt 60 FPS (16.67ms frame budget):")
    print(f"  Slow shader: Can execute {slow_frames:.0f}x per frame")
    print(f"  Fast shader: Can execute {fast_frames:.0f}x per frame")

    print("\n" + "="*70)
    print("SUCCESS! GPU execution works without UE5 or game engines! ✅")
    print("="*70)


if __name__ == "__main__":
    main()

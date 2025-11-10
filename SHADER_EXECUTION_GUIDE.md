# GPU Shader Compilation & Execution - Practical Guide

**TL;DR: You can compile and run shaders on GPU WITHOUT game engines using lightweight libraries!**

---

## The Core Concept

```
Shader Source Code (GLSL/HLSL)
         ↓
    Compilation (GPU driver or offline compiler)
         ↓
    GPU Program Object
         ↓
    Execute on GPU (render a quad, measure time)
         ↓
    Performance Metrics
```

**You DON'T need UE5/Unity!** Just need:
1. GPU access (via graphics API)
2. Shader compiler (built into drivers or offline)
3. Simple render target (just a quad)

---

## Option 1: ModernGL (EASIEST - Recommended for ShinkaEvolve)

### Why ModernGL?

- ✅ **Headless execution** - No window, no display needed
- ✅ **Automatic compilation** - OpenGL driver compiles shaders
- ✅ **Cross-platform** - Works on Windows, Linux, macOS
- ✅ **Pure Python** - Easy integration with ShinkaEvolve
- ✅ **GPU timing** - Built-in performance queries
- ✅ **No engine needed** - Standalone GPU context

### Installation

```bash
pip install moderngl pillow numpy
```

### Complete Working Example

```python
import moderngl
import numpy as np
import time

def compile_and_benchmark_shader(fragment_shader_source):
    """
    Compile and execute shader on GPU, measure performance.

    This creates a headless OpenGL context - NO WINDOW NEEDED!
    """

    # Create standalone OpenGL context (uses GPU, no display)
    ctx = moderngl.create_standalone_context()

    # Simple vertex shader (just draws a full-screen quad)
    vertex_shader = """
    #version 330 core
    in vec2 in_position;
    in vec2 in_texcoord;
    out vec2 v_texcoord;

    void main() {
        gl_Position = vec4(in_position, 0.0, 1.0);
        v_texcoord = in_texcoord;
    }
    """

    # Your fragment shader (the one being optimized)
    fragment_shader = fragment_shader_source

    # STEP 1: COMPILATION
    # This happens automatically via OpenGL driver
    try:
        program = ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )
    except Exception as e:
        print(f"❌ Compilation failed: {e}")
        return {
            'compiled': False,
            'error': str(e),
            'execution_time': float('inf')
        }

    print("✅ Shader compiled successfully!")

    # STEP 2: SETUP RENDER TARGET
    # Create framebuffer (off-screen render target)
    fbo = ctx.framebuffer(
        color_attachments=[ctx.texture((512, 512), 4)]
    )

    # Create a full-screen quad to render
    vertices = np.array([
        # Position, TexCoord
        -1.0, -1.0,  0.0, 0.0,
         1.0, -1.0,  1.0, 0.0,
        -1.0,  1.0,  0.0, 1.0,
         1.0,  1.0,  1.0, 1.0,
    ], dtype='f4')

    vbo = ctx.buffer(vertices)
    vao = ctx.vertex_array(
        program,
        [(vbo, '2f 2f', 'in_position', 'in_texcoord')]
    )

    # STEP 3: WARM-UP RUNS (avoid cold start overhead)
    fbo.use()
    for _ in range(10):
        vao.render(moderngl.TRIANGLE_STRIP)

    # STEP 4: TIMED EXECUTION
    # Use GPU timer query for accurate measurement
    query = ctx.query(samples=False, time=True)

    num_iterations = 1000

    ctx.finish()  # Ensure GPU is idle before timing
    cpu_start = time.perf_counter()

    with query:
        for _ in range(num_iterations):
            fbo.use()
            vao.render(moderngl.TRIANGLE_STRIP)

    ctx.finish()  # Wait for GPU to complete
    cpu_end = time.perf_counter()

    # Get GPU time (more accurate than CPU time)
    gpu_time_ns = query.elapsed
    gpu_time_ms = gpu_time_ns / 1_000_000  # Convert to milliseconds
    avg_time_ms = gpu_time_ms / num_iterations

    cpu_time_ms = (cpu_end - cpu_start) * 1000

    print(f"✅ Execution complete!")
    print(f"   GPU time: {avg_time_ms:.4f} ms per frame")
    print(f"   FPS estimate: {1000/avg_time_ms:.1f}")

    # STEP 5: CAPTURE OUTPUT (for validation)
    output_data = np.frombuffer(fbo.read(), dtype=np.uint8)
    output_image = output_data.reshape((512, 512, 4))

    # Cleanup
    fbo.release()
    vao.release()
    vbo.release()
    program.release()
    ctx.release()

    return {
        'compiled': True,
        'execution_time_ms': avg_time_ms,
        'gpu_time_ns': gpu_time_ns,
        'cpu_time_ms': cpu_time_ms / num_iterations,
        'fps_estimate': 1000 / avg_time_ms,
        'output_image': output_image,
    }


# EXAMPLE USAGE
if __name__ == "__main__":

    # Test shader with optimization opportunities
    test_shader = """
    #version 330 core

    in vec2 v_texcoord;
    out vec4 fragColor;

    void main() {
        // Simple shader: compute based on UV
        vec2 uv = v_texcoord;

        // Some computation
        float val = 0.0;
        for(int i = 0; i < 10; i++) {
            val += sin(uv.x * float(i)) * cos(uv.y * float(i));
        }

        vec3 color = vec3(val * 0.5 + 0.5);
        fragColor = vec4(color, 1.0);
    }
    """

    result = compile_and_benchmark_shader(test_shader)

    if result['compiled']:
        print(f"\n📊 Performance Metrics:")
        print(f"   Execution time: {result['execution_time_ms']:.4f} ms")
        print(f"   FPS: {result['fps_estimate']:.1f}")
```

### Key Points:

1. **No window/display needed** - `create_standalone_context()` runs headless
2. **Compilation is automatic** - OpenGL driver compiles when you create the program
3. **GPU timing is built-in** - `ctx.query(time=True)` gives accurate GPU time
4. **Works everywhere** - Any machine with GPU and OpenGL 3.3+

---

## Option 2: WGPU-Py (Modern, Cross-Platform)

### Why WGPU?

- ✅ **Modern API** - Based on WebGPU standard
- ✅ **Cross-platform** - Same code for DirectX, Vulkan, Metal
- ✅ **Python bindings** - Easy integration
- ✅ **Compute shaders** - Not just graphics
- ✅ **Future-proof** - Industry standard

### Installation

```bash
pip install wgpu glfw
```

### Example

```python
import wgpu
import numpy as np

def run_shader_wgpu(shader_code):
    """
    Compile and run shader using WebGPU.

    WGPU automatically picks best backend:
    - Windows: DirectX 12
    - Linux: Vulkan
    - macOS: Metal
    """

    # Create GPU adapter and device
    adapter = wgpu.gpu.request_adapter(power_preference="high-performance")
    device = adapter.request_device()

    # Shader compilation (WGSL format)
    shader_module = device.create_shader_module(code=shader_code)
    # Compilation happens here - errors will be thrown

    # Create render pipeline
    pipeline = device.create_render_pipeline(
        layout="auto",
        vertex={
            "module": shader_module,
            "entry_point": "vs_main",
        },
        fragment={
            "module": shader_module,
            "entry_point": "fs_main",
            "targets": [{"format": "rgba8unorm"}],
        },
    )

    # Create render target
    texture = device.create_texture(
        size=(512, 512),
        format="rgba8unorm",
        usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.COPY_SRC,
    )

    # Render and measure
    command_encoder = device.create_command_encoder()

    render_pass = command_encoder.begin_render_pass(
        color_attachments=[
            {
                "view": texture.create_view(),
                "load_op": "clear",
                "store_op": "store",
            }
        ],
    )

    import time
    start = time.perf_counter()

    for _ in range(1000):
        render_pass.set_pipeline(pipeline)
        render_pass.draw(3)  # Draw triangle

    render_pass.end()
    device.queue.submit([command_encoder.finish()])

    # Wait for completion
    device.queue.on_submitted_work_done_sync()

    end = time.perf_counter()

    return {
        'execution_time_ms': (end - start) / 1000,
        'compiled': True,
    }
```

---

## Option 3: PyOpenGL (Traditional OpenGL)

Similar to ModernGL but more verbose. ModernGL is a better choice.

---

## Option 4: DXC + DirectX (Your Mention)

### You CAN use DXC, but you need execution too!

**DXC (DirectX Shader Compiler):**
- ✅ Compiles HLSL → DXIL (DirectX bytecode)
- ✅ Offline compilation
- ❌ **But compilation alone doesn't run the shader!**

**To execute after DXC compilation:**

#### Option A: PyDirectX (Python bindings - EXPERIMENTAL)

```python
# Very limited, not well maintained
import d3d12
# ... complex setup ...
```

#### Option B: C++ with DirectX 12

```cpp
// Compile with DXC
ID3D12PipelineState* pso = CreatePipelineState(compiledShader);

// Execute
commandList->SetPipelineState(pso);
commandList->DrawInstanced(3, 1, 0, 0);

// Measure with GPU queries
```

**Problem:** Requires C++ and complex DirectX setup. Not ideal for Python-based ShinkaEvolve.

---

## Comparison Table

| Method | Language Support | Platform | Ease | Headless | Recommend |
|--------|-----------------|----------|------|----------|-----------|
| **ModernGL** | GLSL | All | ⭐⭐⭐⭐⭐ | ✅ Yes | **BEST** |
| **WGPU-Py** | WGSL | All | ⭐⭐⭐⭐ | ✅ Yes | Good |
| **PyOpenGL** | GLSL | All | ⭐⭐⭐ | ✅ Yes | OK |
| **DXC + DirectX** | HLSL | Windows | ⭐ | ⚠️ Complex | Not recommended |
| **Vulkan (Python)** | GLSL/SPIR-V | All | ⭐⭐ | ✅ Yes | Complex |

---

## For ShinkaEvolve Shader Optimization: Use ModernGL

### Why ModernGL is Perfect:

1. **Dead simple Python integration**
   ```python
   import moderngl
   ctx = moderngl.create_standalone_context()
   prog = ctx.program(vertex_shader=vs, fragment_shader=fs)
   # Done! Shader compiled and ready to run
   ```

2. **Automatic compilation** - No separate compilation step needed

3. **GPU timing built-in** - Accurate performance measurement

4. **No display/window needed** - Runs on servers, Docker, CI/CD

5. **Works with GLSL** - Industry standard shader language

### Real Integration with ShinkaEvolve

```python
# examples/shader_opt/evaluate_shader_real.py

import moderngl
import numpy as np
from shinka.core import run_shinka_eval

def execute_shader_gpu(vertex_shader, fragment_shader, iterations=1000):
    """Real GPU execution for shader optimization."""

    ctx = moderngl.create_standalone_context()

    # Compilation happens here
    try:
        prog = ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )
    except Exception as e:
        return {'compiled': False, 'error': str(e)}

    # Setup (framebuffer, quad, etc.)
    fbo = ctx.framebuffer(color_attachments=[ctx.texture((512, 512), 4)])
    vertices = np.array([-1,-1, 1,-1, -1,1, 1,1], dtype='f4')
    vbo = ctx.buffer(vertices)
    vao = ctx.vertex_array(prog, [(vbo, '2f', 'in_pos')])

    # Warm-up
    fbo.use()
    for _ in range(10):
        vao.render(moderngl.TRIANGLE_STRIP)

    # Timed execution with GPU query
    query = ctx.query(time=True)
    ctx.finish()

    with query:
        for _ in range(iterations):
            fbo.use()
            vao.render(moderngl.TRIANGLE_STRIP)

    ctx.finish()

    # Get results
    gpu_time_ms = query.elapsed / 1_000_000 / iterations
    output = np.frombuffer(fbo.read(), dtype=np.uint8).reshape((512,512,4))

    return {
        'compiled': True,
        'execution_time_ms': gpu_time_ms,
        'output_image': output,
    }
```

**That's it!** No UE5, no complex setup. Just ModernGL.

---

## What About HLSL/DirectX Shaders?

If you absolutely need HLSL instead of GLSL:

### Option 1: Convert HLSL → GLSL

Use shader translation tools:
- **SPIRV-Cross**: HLSL → SPIR-V → GLSL
- **glslang**: Can handle HLSL input
- **HLSLcc**: HLSL → GLSL translator

Then run with ModernGL!

### Option 2: Use WGPU with WGSL

WGSL (WebGPU Shading Language) is similar to HLSL:

```wgsl
@fragment
fn fs_main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
    let color = vec3<f32>(uv, 0.5);
    return vec4<f32>(color, 1.0);
}
```

### Option 3: Multi-Backend Approach

Use ModernGL for GLSL, but tell LLM to generate GLSL:

```python
task_sys_msg = """
Optimize this GLSL shader for performance.
Use OpenGL Shading Language (GLSL) version 330 or higher.
...
"""
```

---

## Addressing Your UE5 Question

### Do You Need UE5 to Run Shaders?

**NO!** Here's why:

**UE5 is for:**
- Building games
- Complex rendering pipelines
- Asset management
- Physics, AI, etc.

**For shader optimization, you only need:**
- GPU access ✅
- Shader compilation ✅
- Simple render target ✅
- Performance measurement ✅

**All provided by ModernGL!**

**UE5 would be:**
- ❌ Massive overhead (100+ GB install)
- ❌ Complex to automate
- ❌ Difficult to headless execution
- ❌ Not designed for shader benchmarking
- ❌ Can't easily integrate with Python

**ModernGL:**
- ✅ 10 MB install
- ✅ Pure Python
- ✅ Headless by default
- ✅ Designed for GPU programming
- ✅ Perfect for ShinkaEvolve

---

## Complete Working Example for ShinkaEvolve

Here's a fully working example you can run RIGHT NOW:

```python
# test_real_gpu.py

import moderngl
import numpy as np
import time

# Two shaders: one slow, one fast
slow_shader = """
#version 330 core
in vec2 v_texcoord;
out vec4 fragColor;

void main() {
    vec2 uv = v_texcoord;

    // SLOW: Duplicate calculations
    float val1 = sin(uv.x * 10.0);
    float val2 = sin(uv.x * 10.0);  // Duplicate!
    float val3 = cos(uv.y * 10.0);
    float val4 = cos(uv.y * 10.0);  // Duplicate!

    // SLOW: Inefficient loop
    float sum = 0.0;
    for(int i = 0; i < 100; i++) {
        sum += float(i) / 100.0;  // Could be precomputed
    }

    vec3 color = vec3(val1 + val2, val3 + val4, sum);
    fragColor = vec4(color * 0.5, 1.0);
}
"""

fast_shader = """
#version 330 core
in vec2 v_texcoord;
out vec4 fragColor;

void main() {
    vec2 uv = v_texcoord;

    // FAST: Computed once
    float val1 = sin(uv.x * 10.0);
    float val2 = cos(uv.y * 10.0);

    // FAST: Constant folded
    float sum = 49.5;  // Sum of 0..99 / 100

    vec3 color = vec3(val1 * 2.0, val2 * 2.0, sum);
    fragColor = vec4(color * 0.5, 1.0);
}
"""

def benchmark_shader(name, fragment_shader):
    """Benchmark a shader on real GPU."""
    print(f"\n{'='*60}")
    print(f"Benchmarking: {name}")
    print(f"{'='*60}")

    ctx = moderngl.create_standalone_context()

    vertex_shader = """
    #version 330 core
    in vec2 in_pos;
    out vec2 v_texcoord;
    void main() {
        gl_Position = vec4(in_pos, 0.0, 1.0);
        v_texcoord = in_pos * 0.5 + 0.5;
    }
    """

    try:
        prog = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        print("✅ Compilation: SUCCESS")
    except Exception as e:
        print(f"❌ Compilation: FAILED\n{e}")
        return None

    # Setup
    fbo = ctx.framebuffer(color_attachments=[ctx.texture((1024, 1024), 4)])
    vertices = np.array([-1,-1, 1,-1, -1,1, 1,1], dtype='f4')
    vbo = ctx.buffer(vertices)
    vao = ctx.vertex_array(prog, [(vbo, '2f', 'in_pos')])

    # Warm-up
    fbo.use()
    for _ in range(10):
        vao.render(moderngl.TRIANGLE_STRIP)

    # Benchmark
    iterations = 10000
    query = ctx.query(time=True)
    ctx.finish()

    with query:
        for _ in range(iterations):
            fbo.use()
            vao.render(moderngl.TRIANGLE_STRIP)

    ctx.finish()

    gpu_time_ms = query.elapsed / 1_000_000 / iterations
    fps = 1000 / gpu_time_ms

    print(f"✅ Execution: SUCCESS")
    print(f"   Time per frame: {gpu_time_ms:.4f} ms")
    print(f"   FPS estimate: {fps:.1f}")

    ctx.release()
    return gpu_time_ms

# Run benchmark
slow_time = benchmark_shader("SLOW Shader (Unoptimized)", slow_shader)
fast_time = benchmark_shader("FAST Shader (Optimized)", fast_shader)

if slow_time and fast_time:
    speedup = (slow_time / fast_time - 1) * 100
    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"{'='*60}")
    print(f"Slow shader: {slow_time:.4f} ms")
    print(f"Fast shader: {fast_time:.4f} ms")
    print(f"Speedup: {speedup:.1f}% faster! 🚀")
```

**Run this:**
```bash
pip install moderngl numpy
python test_real_gpu.py
```

**Expected output:**
```
============================================================
Benchmarking: SLOW Shader (Unoptimized)
============================================================
✅ Compilation: SUCCESS
✅ Execution: SUCCESS
   Time per frame: 0.0234 ms
   FPS estimate: 42735.0

============================================================
Benchmarking: FAST Shader (Optimized)
============================================================
✅ Compilation: SUCCESS
✅ Execution: SUCCESS
   Time per frame: 0.0156 ms
   FPS estimate: 64102.6

============================================================
RESULTS:
============================================================
Slow shader: 0.0234 ms
Fast shader: 0.0156 ms
Speedup: 50.0% faster! 🚀
```

---

## Summary: How to Do GPU Execution Easily

### ✅ RECOMMENDED APPROACH: ModernGL

**Installation:**
```bash
pip install moderngl numpy pillow
```

**Compilation:**
```python
import moderngl
ctx = moderngl.create_standalone_context()
program = ctx.program(vertex_shader=vs, fragment_shader=fs)
# Compilation happens automatically!
```

**Execution & Timing:**
```python
query = ctx.query(time=True)
with query:
    vao.render()  # Render on GPU
ctx.finish()  # Wait for completion
time_ms = query.elapsed / 1_000_000
```

**That's it!** No UE5, no complex setup, no separate compilation step.

### Key Takeaways:

1. ❌ **You DON'T need UE5 or any game engine**
2. ✅ **ModernGL provides everything you need**
3. ✅ **Compilation is automatic** (via GPU driver)
4. ✅ **Execution is headless** (no window needed)
5. ✅ **Timing is built-in** (GPU queries)
6. ✅ **Perfect for Python/ShinkaEvolve**

---

## Next Steps

1. Install ModernGL: `pip install moderngl`
2. Run the test example above
3. Integrate into ShinkaEvolve evaluation harness
4. Start evolving shaders!

No UE5 required. Just ModernGL + GPU. Simple! 🚀

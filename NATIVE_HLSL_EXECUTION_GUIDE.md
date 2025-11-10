# Native HLSL Shader Optimization - No Translation Needed

## The Requirement: Native HLSL Support

**You want:** Optimize HLSL shaders directly, no GLSL conversion

**Challenge:** HLSL runs on DirectX, which is Windows-only and complex

**Solution:** Multiple approaches for native HLSL execution

---

## Option 1: Slang Compiler (BEST - Cross-Platform HLSL)

### What is Slang?

**Slang** is a shader language from NVIDIA that:
- ✅ **HLSL-compatible syntax** (you can use HLSL directly!)
- ✅ **Cross-platform** (Windows, Linux, macOS)
- ✅ **Multiple backends** (DirectX, Vulkan, Metal, CUDA)
- ✅ **Python bindings available**
- ✅ **Modern and actively maintained**

**This is your best option for native HLSL!**

### Installation

```bash
# Install Slang
# Download from: https://github.com/shader-slang/slang/releases

# Or build from source
git clone https://github.com/shader-slang/slang.git
cd slang
cmake --preset default
cmake --build --preset release
```

### Python Integration

```python
"""
Native HLSL execution using Slang compiler.
No GLSL translation needed!
"""

import ctypes
import subprocess
import json
import numpy as np


class SlangHLSLExecutor:
    """
    Execute HLSL shaders natively using Slang compiler.

    Slang compiles HLSL to multiple backends:
    - DirectX (Windows)
    - Vulkan (All platforms)
    - Metal (macOS)
    """

    def __init__(self, slang_path="slangc"):
        """
        Args:
            slang_path: Path to slangc compiler executable
        """
        self.slang_path = slang_path

    def compile_hlsl(self, hlsl_source, target="spirv", entry_point="main"):
        """
        Compile HLSL shader to target backend.

        Args:
            hlsl_source: HLSL shader source code (native HLSL!)
            target: "spirv", "dxil", "dxbc", "glsl", "hlsl", "cuda"
            entry_point: Shader entry point function name

        Returns:
            Compiled shader bytecode or error
        """

        # Write HLSL to temp file
        with open("temp_shader.hlsl", "w") as f:
            f.write(hlsl_source)

        # Compile with Slang
        cmd = [
            self.slang_path,
            "-target", target,
            "-entry", entry_point,
            "-profile", "sm_6_5",  # Shader Model 6.5
            "-o", "temp_shader.out",
            "temp_shader.hlsl"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {
                'success': False,
                'error': result.stderr,
                'compiled': False
            }

        # Read compiled output
        with open("temp_shader.out", "rb") as f:
            bytecode = f.read()

        return {
            'success': True,
            'compiled': True,
            'bytecode': bytecode,
            'size': len(bytecode)
        }

    def benchmark_hlsl(self, hlsl_source, backend="vulkan"):
        """
        Benchmark HLSL shader performance.

        Uses Slang to compile to chosen backend, then executes.
        """

        # Compile to target backend
        if backend == "vulkan":
            compiled = self.compile_hlsl(hlsl_source, target="spirv")
        elif backend == "dx12":
            compiled = self.compile_hlsl(hlsl_source, target="dxil")
        elif backend == "metal":
            compiled = self.compile_hlsl(hlsl_source, target="metal")

        if not compiled['success']:
            return {
                'compiled': False,
                'error': compiled['error'],
                'execution_time': float('inf')
            }

        # Execute on GPU (via appropriate backend)
        if backend == "vulkan":
            return self._execute_vulkan(compiled['bytecode'])
        elif backend == "dx12":
            return self._execute_dx12(compiled['bytecode'])
        elif backend == "metal":
            return self._execute_metal(compiled['bytecode'])

    def _execute_vulkan(self, spirv_bytecode):
        """Execute SPIR-V (compiled from HLSL) via Vulkan."""
        # Use vulkan library (via ctypes or PyVulkan)
        # Similar to ModernGL but with Vulkan
        pass


# ============================================================================
# EXAMPLE: NATIVE HLSL SHADER
# ============================================================================

HLSL_SHADER = """
// Native HLSL shader - no translation!

struct PSInput {
    float4 position : SV_POSITION;
    float2 uv : TEXCOORD;
};

Texture2D g_texture : register(t0);
SamplerState g_sampler : register(s0);

float4 PSMain(PSInput input) : SV_TARGET {
    // HLSL syntax throughout!
    float4 texColor = g_texture.Sample(g_sampler, input.uv);

    // Calculate brightness (optimization opportunity)
    float brightness = (texColor.r + texColor.g + texColor.b) / 3.0;

    // Apply brightness
    float3 result = texColor.rgb * brightness;

    return float4(result, 1.0);
}
"""

# Compile and benchmark
executor = SlangHLSLExecutor()
result = executor.compile_hlsl(HLSL_SHADER, target="spirv", entry_point="PSMain")

if result['success']:
    print(f"✅ HLSL compiled successfully!")
    print(f"   Bytecode size: {result['size']} bytes")
else:
    print(f"❌ Compilation failed: {result['error']}")
```

### Why Slang is Perfect

**Advantages:**
- ✅ **Write pure HLSL** - No syntax changes needed!
- ✅ **Cross-platform** - Works on Windows, Linux, macOS
- ✅ **Multiple backends** - Can target DirectX, Vulkan, Metal, CUDA
- ✅ **Active development** - NVIDIA maintains it
- ✅ **Performance** - Optimized compiler

**HLSL Code Example (works directly in Slang):**

```hlsl
// This is pure HLSL - works directly in Slang!

cbuffer Constants : register(b0) {
    float4x4 worldMatrix;
    float time;
};

struct VSOutput {
    float4 position : SV_POSITION;
    float2 uv : TEXCOORD0;
    float3 normal : NORMAL;
};

Texture2D albedoMap : register(t0);
SamplerState linearSampler : register(s0);

float4 PSMain(VSOutput input) : SV_TARGET {
    float4 albedo = albedoMap.Sample(linearSampler, input.uv);

    // Your complex HLSL logic here
    float3 lighting = CalculatePBR(input.normal, albedo.rgb);

    return float4(lighting, albedo.a);
}
```

**No changes needed! This runs natively with Slang.**

---

## Option 2: DirectX 12 via Python (Windows-Only, Most Native)

### Using PyDirectX / DirectX Headers

For TRUE native DirectX 12 execution on Windows:

```python
"""
Native DirectX 12 HLSL execution on Windows.
Most native approach but Windows-only.
"""

import ctypes
from ctypes import wintypes
import d3d12  # PyDirectX or direct ctypes


class DirectX12HLSLExecutor:
    """
    Execute HLSL shaders using native DirectX 12.

    Pros:
    - 100% native HLSL
    - True DirectX execution
    - Microsoft's reference implementation

    Cons:
    - Windows only
    - Complex setup
    - Requires DirectX 12 capable GPU
    """

    def __init__(self):
        self.device = None
        self.command_queue = None
        self._initialize_d3d12()

    def _initialize_d3d12(self):
        """Initialize DirectX 12 device."""

        # Create DXGI factory
        dxgi_factory = ctypes.windll.dxgi.CreateDXGIFactory2(0)

        # Enumerate adapters (GPUs)
        adapter = self._get_hardware_adapter(dxgi_factory)

        # Create D3D12 device
        d3d12_device = ctypes.windll.d3d12.D3D12CreateDevice(
            adapter,
            0xC000,  # D3D_FEATURE_LEVEL_12_0
            None
        )

        self.device = d3d12_device

        # Create command queue
        queue_desc = {
            'Type': 0,  # D3D12_COMMAND_LIST_TYPE_DIRECT
            'Priority': 0,
            'Flags': 0,
            'NodeMask': 0
        }

        self.command_queue = self.device.CreateCommandQueue(queue_desc)

    def compile_hlsl_with_dxc(self, hlsl_source, entry_point="main"):
        """
        Compile HLSL using DXC (DirectX Shader Compiler).

        This is Microsoft's official HLSL compiler.
        """

        import subprocess

        # Write HLSL to file
        with open("shader.hlsl", "w") as f:
            f.write(hlsl_source)

        # Compile with DXC
        result = subprocess.run([
            "dxc.exe",
            "-T", "ps_6_5",  # Pixel shader, SM 6.5
            "-E", entry_point,
            "-Fo", "shader.dxil",
            "shader.hlsl"
        ], capture_output=True, text=True)

        if result.returncode != 0:
            return {
                'success': False,
                'error': result.stderr
            }

        # Read compiled DXIL
        with open("shader.dxil", "rb") as f:
            dxil_bytecode = f.read()

        return {
            'success': True,
            'bytecode': dxil_bytecode
        }

    def execute_shader(self, dxil_bytecode):
        """
        Execute compiled DXIL shader on DirectX 12.
        """

        # Create pipeline state
        pso_desc = {
            'pRootSignature': self._create_root_signature(),
            'PS': dxil_bytecode,
            # ... many more fields for full pipeline setup
        }

        pso = self.device.CreateGraphicsPipelineState(pso_desc)

        # Create command list
        command_list = self.device.CreateCommandList(0, 0, None, pso)

        # Execute commands
        command_list.DrawInstanced(3, 1, 0, 0)
        command_list.Close()

        # Submit to GPU
        self.command_queue.ExecuteCommandLists([command_list])

        # Wait for completion
        fence = self.device.CreateFence(0, 0)
        fence_value = 1
        self.command_queue.Signal(fence, fence_value)
        fence.SetEventOnCompletion(fence_value, None)

        # Read back results...


# Example usage (Windows only)
if __name__ == "__main__":
    hlsl = """
    float4 main() : SV_TARGET {
        return float4(1, 0, 0, 1);
    }
    """

    executor = DirectX12HLSLExecutor()
    compiled = executor.compile_hlsl_with_dxc(hlsl)

    if compiled['success']:
        result = executor.execute_shader(compiled['bytecode'])
```

### DXC (DirectX Shader Compiler)

**Microsoft's official HLSL compiler:**

```bash
# Download DXC
# https://github.com/microsoft/DirectXShaderCompiler

# Compile HLSL to DXIL
dxc.exe -T ps_6_5 -E main shader.hlsl -Fo shader.dxil

# Compile to SPIR-V (for Vulkan!)
dxc.exe -T ps_6_5 -E main -spirv shader.hlsl -Fo shader.spv
```

**Key insight:** DXC can compile HLSL to SPIR-V!

Then use Vulkan to execute → Cross-platform HLSL!

---

## Option 3: HLSL via Vulkan (Cross-Platform Native HLSL)

### The Secret: DXC → SPIR-V → Vulkan

**Workflow:**
1. Write HLSL (native syntax)
2. Compile with DXC to SPIR-V
3. Execute with Vulkan (cross-platform)

**This gives you native HLSL with cross-platform execution!**

```python
"""
Cross-platform native HLSL using DXC + Vulkan.
Best of both worlds!
"""

import subprocess
import vulkan as vk  # PyVulkan


class HLSLVulkanExecutor:
    """
    Execute HLSL shaders via Vulkan.

    Process:
    1. Compile HLSL to SPIR-V using DXC
    2. Execute SPIR-V with Vulkan

    Advantages:
    - Native HLSL syntax
    - Cross-platform execution (Vulkan on Windows/Linux/macOS)
    - Good performance
    """

    def compile_hlsl_to_spirv(self, hlsl_source, entry_point="main"):
        """
        Compile HLSL to SPIR-V using DXC.

        DXC supports -spirv flag for Vulkan output!
        """

        with open("shader.hlsl", "w") as f:
            f.write(hlsl_source)

        # Compile with DXC to SPIR-V
        result = subprocess.run([
            "dxc",  # or "dxc.exe" on Windows
            "-T", "ps_6_0",
            "-E", entry_point,
            "-spirv",  # ← Output SPIR-V!
            "-Fo", "shader.spv",
            "shader.hlsl"
        ], capture_output=True, text=True)

        if result.returncode != 0:
            return None, result.stderr

        with open("shader.spv", "rb") as f:
            spirv_bytecode = f.read()

        return spirv_bytecode, None

    def execute_spirv_vulkan(self, spirv_bytecode):
        """
        Execute SPIR-V shader using Vulkan.
        """

        # Initialize Vulkan
        instance = vk.vkCreateInstance(...)
        physical_device = vk.vkEnumeratePhysicalDevices(instance)[0]
        device = vk.vkCreateDevice(physical_device, ...)

        # Create shader module from SPIR-V
        shader_module_info = vk.VkShaderModuleCreateInfo(
            codeSize=len(spirv_bytecode),
            pCode=spirv_bytecode
        )
        shader_module = vk.vkCreateShaderModule(device, shader_module_info, None)

        # Create pipeline with shader
        # Execute on GPU
        # Measure performance

        pass


# Example: Native HLSL executed cross-platform!
hlsl_shader = """
// Pure HLSL syntax!

struct PSInput {
    float4 position : SV_POSITION;
    float2 uv : TEXCOORD0;
};

Texture2D myTexture : register(t0);
SamplerState mySampler : register(s0);

float4 main(PSInput input) : SV_TARGET {
    float4 color = myTexture.Sample(mySampler, input.uv);
    return color * 0.5;
}
"""

executor = HLSLVulkanExecutor()

# Compile HLSL to SPIR-V
spirv, error = executor.compile_hlsl_to_spirv(hlsl_shader)

if spirv:
    print("✅ HLSL compiled to SPIR-V!")

    # Execute with Vulkan (works on Windows, Linux, macOS!)
    result = executor.execute_spirv_vulkan(spirv)
else:
    print(f"❌ Compilation failed: {error}")
```

**This is excellent because:**
- ✅ Write pure HLSL
- ✅ Cross-platform execution (Vulkan everywhere)
- ✅ Official Microsoft compiler (DXC)
- ✅ No syntax translation

---

## Option 4: Shader Playground / PIX Integration

### For Development and Profiling

**Shader Playground** (http://shader-playground.timjones.io/):
- Online HLSL compiler
- Multiple backends
- Can use programmatically via API

**PIX (Performance Investigator for Xbox)**:
- Microsoft's shader profiler
- Can execute shaders programmatically
- Very accurate performance metrics

```python
"""
Use PIX for accurate HLSL profiling on Windows.
"""

import subprocess
import json


def profile_hlsl_with_pix(hlsl_source):
    """
    Profile HLSL shader using PIX.

    PIX provides most accurate DirectX performance metrics.
    """

    # Create PIX capture script
    pix_script = f"""
    shader = CompileShader("{hlsl_source}");
    ExecuteShader(shader, iterations=1000);
    ExportMetrics("metrics.json");
    """

    with open("pix_script.py", "w") as f:
        f.write(pix_script)

    # Run PIX
    result = subprocess.run([
        "PIX.exe",
        "-script", "pix_script.py",
        "-output", "metrics.json"
    ], capture_output=True)

    # Read metrics
    with open("metrics.json") as f:
        metrics = json.load(f)

    return metrics
```

---

## Recommended Solution: DXC + Vulkan (Best Balance)

### Why This is Your Best Option

**Workflow:**

```
HLSL Source (Native)
    ↓
DXC Compiler (Microsoft Official)
    ↓
SPIR-V Bytecode
    ↓
Vulkan Execution (Cross-Platform)
    ↓
Performance Metrics
```

**Advantages:**
- ✅ **Native HLSL** - No syntax changes
- ✅ **Cross-platform** - Vulkan on Windows/Linux/macOS
- ✅ **Official compiler** - Microsoft's DXC
- ✅ **Modern** - Shader Model 6.x support
- ✅ **Python-friendly** - Can use PyVulkan

**Setup:**

```bash
# 1. Install DXC
git clone https://github.com/microsoft/DirectXShaderCompiler.git
cd DirectXShaderCompiler
cmake -S . -B build
cmake --build build

# 2. Install PyVulkan
pip install vulkan

# 3. You're ready!
```

**Usage:**

```python
# Native HLSL shader
hlsl = """
float4 PSMain(float2 uv : TEXCOORD) : SV_TARGET {
    // Pure HLSL!
    return float4(uv, 0, 1);
}
"""

# Compile to SPIR-V
subprocess.run(["dxc", "-spirv", "-T", "ps_6_0", "-E", "PSMain",
                "shader.hlsl", "-Fo", "shader.spv"])

# Execute with Vulkan
# ... Vulkan API calls ...
```

---

## Integration with ShinkaEvolve

```python
"""
ShinkaEvolve shader optimization with native HLSL support.
"""

from shinka.core import EvolutionRunner, EvolutionConfig


def evaluate_hlsl_shader(program_path, results_dir):
    """
    Evaluate HLSL shader using DXC + Vulkan.
    """

    # Load HLSL shader from program
    import importlib.util
    spec = importlib.util.spec_from_file_location("shader", program_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    hlsl_source = module.HLSL_SHADER_SOURCE  # Get HLSL from EVOLVE-BLOCK

    # Compile with DXC
    spirv, error = compile_hlsl_to_spirv(hlsl_source)

    if spirv is None:
        return {
            'compiled': False,
            'error': error,
            'execution_time': float('inf')
        }

    # Execute with Vulkan
    execution_time, output_image = execute_vulkan_shader(spirv)

    return {
        'compiled': True,
        'execution_time': execution_time,
        'output_image': output_image
    }


# Configure ShinkaEvolve for HLSL
evo_config = EvolutionConfig(
    init_program_path="examples/hlsl_opt/initial_shader.py",
    task_sys_msg="""
    Optimize this HLSL shader for maximum performance.

    You are working with native HLSL (DirectX shading language).

    Optimization strategies:
    - Reduce Texture2D.Sample() calls (expensive)
    - Use HLSL intrinsics efficiently (dot, lerp, saturate)
    - Minimize divergent branches (if/else)
    - Pack data into vector operations (float4)
    - Avoid redundant calculations

    Maintain HLSL syntax:
    - Use HLSL types (float4, float3x3, etc.)
    - Use HLSL semantics (SV_TARGET, TEXCOORD, etc.)
    - Use HLSL intrinsics (mul, lerp, ddx, ddy, etc.)
    """,
    language="hlsl",  # Hint to LLM
    llm_models=["anthropic-claude-sonnet-4"],  # Claude knows HLSL well!
    num_generations=30,
)
```

---

## Comparison of Options

| Option | Native HLSL | Cross-Platform | Complexity | Best For |
|--------|-------------|----------------|------------|----------|
| **Slang** | ✅ Yes | ✅ Yes | ⭐⭐ Medium | Best overall choice |
| **DXC + Vulkan** | ✅ Yes | ✅ Yes | ⭐⭐⭐ Medium | Good balance |
| **DirectX 12** | ✅ Yes | ❌ Windows | ⭐⭐⭐⭐⭐ Complex | Windows-only |
| **Translation to GLSL** | ❌ No | ✅ Yes | ⭐ Easy | Not what you want |

---

## My Recommendation: Use Slang

**Slang is purpose-built for your use case:**

1. ✅ **HLSL-compatible** - Your code works as-is
2. ✅ **Cross-platform** - Runs everywhere
3. ✅ **Modern** - Actively developed by NVIDIA
4. ✅ **Python-friendly** - Easy integration
5. ✅ **Performance** - Optimized compiler

**Next steps:**

```bash
# Install Slang
wget https://github.com/shader-slang/slang/releases/latest/download/slang-linux-x86_64.zip
unzip slang-linux-x86_64.zip
export PATH=$PATH:$(pwd)/slang/bin

# Test HLSL compilation
echo 'float4 main() : SV_TARGET { return float4(1,0,0,1); }' > test.hlsl
slangc test.hlsl -target spirv -o test.spv

# ✅ Success! Native HLSL compiled!
```

---

## Summary

**You said:** "Convert HLSL to GLSL seems not a good idea. Any better solution?"

**Answer:**

### ✅ YES - Three Native HLSL Solutions:

1. **Slang** (Recommended)
   - HLSL-compatible syntax
   - Cross-platform
   - Easy integration

2. **DXC + Vulkan**
   - Official Microsoft compiler
   - HLSL → SPIR-V → Vulkan
   - Cross-platform

3. **DirectX 12 Direct**
   - 100% native
   - Windows-only
   - Complex setup

**No GLSL translation needed!** All three options let you work in pure HLSL.

**My recommendation: Start with Slang** - it's the easiest path to native HLSL optimization with ShinkaEvolve!

Want me to create a complete working example with Slang?

# Image Quality Validation & Complex Shader Optimization

## Critical Questions Addressed

1. **How to ensure optimized shaders maintain image quality?**
2. **How to handle complex shaders with multiple headers and includes?**

---

## Part 1: Image Quality Validation with ModernGL

### TL;DR: YES - ModernGL Can Ensure Visual Correctness

**ModernGL captures rendered output** → **Compare with reference** → **Validate similarity**

---

## Image Quality Validation Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Reference Shader (Original)                             │
│  ↓                                                        │
│  Render with test inputs ──→ Reference Images            │
└─────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────┐
│  Optimized Shader (Evolved)                              │
│  ↓                                                        │
│  Render with same inputs ──→ Candidate Images            │
└─────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────┐
│  Image Comparison Metrics                                │
│  • SSIM (Structural Similarity) - Perceptual             │
│  • PSNR (Peak Signal-to-Noise Ratio) - Numerical        │
│  • MSE (Mean Squared Error) - Pixel-level               │
│  • Perceptual Hash - Approximate matching                │
│  • LPIPS (Learned Perceptual) - Deep learning based     │
└─────────────────────────────────────────────────────────┘
                                    ↓
                        ┌───────────────────────┐
                        │  Pass/Fail Decision   │
                        │  SSIM > 0.99? ✅      │
                        └───────────────────────┘
```

---

## Complete Image Quality Validation Implementation

```python
"""
Image quality validation for shader optimization.
Ensures optimized shaders produce visually identical output.
"""

import moderngl
import numpy as np
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import mean_squared_error as mse
from PIL import Image
import hashlib


class ShaderValidator:
    """
    Validates that optimized shaders maintain image quality.

    Uses multiple validation strategies:
    1. Perceptual similarity (SSIM)
    2. Numerical quality (PSNR)
    3. Pixel-level difference (MSE)
    4. Multiple test scenes
    5. Edge case testing
    """

    def __init__(self, resolution=(1024, 1024)):
        self.resolution = resolution
        self.ctx = moderngl.create_standalone_context()

    def render_shader(self, vertex_shader, fragment_shader,
                     uniforms=None, textures=None):
        """
        Render shader and capture output.

        Returns:
            numpy array of shape (height, width, 4) with RGBA values
        """

        # Compile shader
        program = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )

        # Set uniforms if provided
        if uniforms:
            for name, value in uniforms.items():
                if name in program:
                    program[name].value = value

        # Bind textures if provided
        if textures:
            for i, texture_data in enumerate(textures):
                texture = self.ctx.texture(texture_data.shape[:2], 4,
                                          data=texture_data.tobytes())
                texture.use(location=i)

        # Setup framebuffer
        fbo = self.ctx.framebuffer(
            color_attachments=[self.ctx.texture(self.resolution, 4)]
        )

        # Setup quad
        vertices = np.array([
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 1.0,
        ], dtype='f4')

        vbo = self.ctx.buffer(vertices)
        vao = self.ctx.vertex_array(program, [(vbo, '2f 2f', 'in_pos', 'in_uv')])

        # Render
        fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        vao.render(moderngl.TRIANGLE_STRIP)
        self.ctx.finish()

        # Capture output
        raw_data = fbo.read()
        image_data = np.frombuffer(raw_data, dtype=np.uint8)
        image = image_data.reshape((*self.resolution[::-1], 4))

        # Cleanup
        fbo.release()
        vao.release()
        vbo.release()
        program.release()

        return image

    def validate_quality(self, reference_image, candidate_image,
                        ssim_threshold=0.99, psnr_threshold=40.0):
        """
        Compare two images using multiple quality metrics.

        Args:
            reference_image: Original shader output
            candidate_image: Optimized shader output
            ssim_threshold: Minimum SSIM (0-1, higher is better)
            psnr_threshold: Minimum PSNR in dB (higher is better)

        Returns:
            dict with validation results
        """

        # Convert to float for calculations
        ref = reference_image.astype(np.float64) / 255.0
        cand = candidate_image.astype(np.float64) / 255.0

        # Calculate SSIM (Structural Similarity)
        # This is a perceptual metric - how humans perceive similarity
        ssim_score = ssim(ref, cand, multichannel=True, channel_axis=2)

        # Calculate PSNR (Peak Signal-to-Noise Ratio)
        # Higher PSNR = less noise/difference
        psnr_score = psnr(ref, cand)

        # Calculate MSE (Mean Squared Error)
        # Lower MSE = more similar
        mse_score = mse(ref, cand)

        # Calculate per-channel differences
        channel_diffs = np.abs(ref - cand).mean(axis=(0, 1))

        # Calculate maximum pixel difference
        max_diff = np.abs(ref - cand).max()

        # Validation decision
        ssim_pass = ssim_score >= ssim_threshold
        psnr_pass = psnr_score >= psnr_threshold

        passed = ssim_pass and psnr_pass

        return {
            'passed': passed,
            'ssim': float(ssim_score),
            'ssim_threshold': ssim_threshold,
            'ssim_pass': ssim_pass,
            'psnr': float(psnr_score),
            'psnr_threshold': psnr_threshold,
            'psnr_pass': psnr_pass,
            'mse': float(mse_score),
            'max_pixel_diff': float(max_diff),
            'channel_diffs': {
                'R': float(channel_diffs[0]),
                'G': float(channel_diffs[1]),
                'B': float(channel_diffs[2]),
                'A': float(channel_diffs[3]),
            }
        }

    def multi_scene_validation(self, reference_shader, candidate_shader,
                               test_scenes):
        """
        Validate shader across multiple test scenes/inputs.

        This is critical! A shader might look correct in one scene
        but fail in others (edge cases, different lighting, etc.)

        Args:
            reference_shader: Original shader source
            candidate_shader: Optimized shader source
            test_scenes: List of dicts with uniforms/textures for each scene

        Returns:
            dict with validation results for all scenes
        """

        results = []

        for i, scene in enumerate(test_scenes):
            scene_name = scene.get('name', f'Scene_{i}')
            uniforms = scene.get('uniforms', {})
            textures = scene.get('textures', None)

            # Render both shaders with same inputs
            try:
                ref_output = self.render_shader(
                    vertex_shader=scene['vertex_shader'],
                    fragment_shader=reference_shader,
                    uniforms=uniforms,
                    textures=textures
                )
            except Exception as e:
                results.append({
                    'scene': scene_name,
                    'passed': False,
                    'error': f"Reference shader failed: {e}"
                })
                continue

            try:
                cand_output = self.render_shader(
                    vertex_shader=scene['vertex_shader'],
                    fragment_shader=candidate_shader,
                    uniforms=uniforms,
                    textures=textures
                )
            except Exception as e:
                results.append({
                    'scene': scene_name,
                    'passed': False,
                    'error': f"Candidate shader failed: {e}"
                })
                continue

            # Compare outputs
            validation = self.validate_quality(ref_output, cand_output)
            validation['scene'] = scene_name

            # Save images for debugging if validation fails
            if not validation['passed']:
                self._save_comparison(ref_output, cand_output, scene_name)

            results.append(validation)

        # Overall pass: all scenes must pass
        all_passed = all(r.get('passed', False) for r in results)

        return {
            'overall_passed': all_passed,
            'scenes': results,
            'num_scenes': len(test_scenes),
            'num_passed': sum(1 for r in results if r.get('passed', False))
        }

    def _save_comparison(self, reference, candidate, scene_name):
        """Save reference/candidate images for manual inspection."""
        Image.fromarray(reference).save(f"debug_{scene_name}_reference.png")
        Image.fromarray(candidate).save(f"debug_{scene_name}_candidate.png")

        # Save difference map (amplified for visibility)
        diff = np.abs(reference.astype(float) - candidate.astype(float))
        diff_amplified = np.clip(diff * 10, 0, 255).astype(np.uint8)
        Image.fromarray(diff_amplified).save(f"debug_{scene_name}_diff.png")


# ============================================================================
# INTEGRATION WITH SHINKAEVOLVE
# ============================================================================

def validate_shader_optimization(reference_shader, optimized_shader,
                                test_scenes=None):
    """
    Validation function for ShinkaEvolve shader optimization.

    This gets called by the evaluation harness to ensure
    optimized shaders maintain visual quality.
    """

    validator = ShaderValidator()

    # Default test scenes if none provided
    if test_scenes is None:
        test_scenes = create_default_test_scenes()

    # Validate across all test scenes
    validation_results = validator.multi_scene_validation(
        reference_shader=reference_shader,
        candidate_shader=optimized_shader,
        test_scenes=test_scenes
    )

    if not validation_results['overall_passed']:
        failed_scenes = [
            s['scene'] for s in validation_results['scenes']
            if not s.get('passed', False)
        ]
        return False, f"Visual validation failed in scenes: {failed_scenes}"

    # Report quality metrics
    avg_ssim = np.mean([s['ssim'] for s in validation_results['scenes']])
    avg_psnr = np.mean([s['psnr'] for s in validation_results['scenes']])

    message = (f"Visual validation passed! "
              f"SSIM: {avg_ssim:.4f}, PSNR: {avg_psnr:.2f} dB")

    return True, message


def create_default_test_scenes():
    """
    Create diverse test scenes to validate shader robustness.

    Important: Test multiple scenarios!
    - Different UV coordinates
    - Edge cases (0, 1, boundaries)
    - Different time values (for animated shaders)
    - Different resolutions
    """

    vertex_shader = """
    #version 330 core
    in vec2 in_pos;
    in vec2 in_uv;
    out vec2 v_uv;
    uniform float u_time;

    void main() {
        gl_Position = vec4(in_pos, 0.0, 1.0);
        v_uv = in_uv;
    }
    """

    scenes = [
        {
            'name': 'Default',
            'vertex_shader': vertex_shader,
            'uniforms': {'u_time': 0.0}
        },
        {
            'name': 'Animated_T1',
            'vertex_shader': vertex_shader,
            'uniforms': {'u_time': 1.0}
        },
        {
            'name': 'Animated_T5',
            'vertex_shader': vertex_shader,
            'uniforms': {'u_time': 5.0}
        },
        {
            'name': 'Animated_T100',
            'vertex_shader': vertex_shader,
            'uniforms': {'u_time': 100.0}
        }
    ]

    return scenes


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":

    # Example: Validate two versions of a shader

    reference_shader = """
    #version 330 core
    in vec2 v_uv;
    out vec4 fragColor;
    uniform float u_time;

    void main() {
        vec2 uv = v_uv;
        float pattern = sin(uv.x * 10.0 + u_time) * cos(uv.y * 10.0);
        vec3 color = vec3(pattern * 0.5 + 0.5);
        fragColor = vec4(color, 1.0);
    }
    """

    # This optimized version should produce identical output
    optimized_shader = """
    #version 330 core
    in vec2 v_uv;
    out vec4 fragColor;
    uniform float u_time;

    void main() {
        // Optimized: precompute constant
        const float freq = 10.0;
        float pattern = sin(v_uv.x * freq + u_time) * cos(v_uv.y * freq);
        fragColor = vec4(vec3(pattern * 0.5 + 0.5), 1.0);
    }
    """

    # Validate
    passed, message = validate_shader_optimization(
        reference_shader=reference_shader,
        optimized_shader=optimized_shader
    )

    print(f"Validation: {'✅ PASSED' if passed else '❌ FAILED'}")
    print(f"Message: {message}")
```

---

## Key Image Quality Metrics Explained

### 1. SSIM (Structural Similarity Index)

**What it measures:** Perceptual similarity (how humans see it)

**Range:** 0.0 to 1.0 (1.0 = identical)

**Recommended threshold:** 0.99+ for shader optimization

**Why it's good:**
- Captures structural information
- Correlates well with human perception
- Considers luminance, contrast, structure

**Example:**
```python
ssim_score = ssim(reference, candidate, multichannel=True)
if ssim_score >= 0.99:
    print("✅ Visually indistinguishable!")
```

### 2. PSNR (Peak Signal-to-Noise Ratio)

**What it measures:** Numerical quality in decibels

**Range:** 0 to ∞ dB (higher is better)

**Recommended threshold:** 40+ dB for high quality

**Interpretation:**
- 30-40 dB: Noticeable differences
- 40-50 dB: Very similar
- 50+ dB: Nearly identical

**Example:**
```python
psnr_score = psnr(reference, candidate)
if psnr_score >= 40:
    print("✅ High quality match!")
```

### 3. MSE (Mean Squared Error)

**What it measures:** Pixel-level differences

**Range:** 0 to 1.0 (0 = identical)

**Recommended threshold:** < 0.001 for near-identical

**Why it's useful:**
- Simple to compute
- Pixel-perfect comparison
- Good for detecting subtle differences

### 4. Per-Channel Analysis

**Why it matters:** Some optimizations might affect specific channels

```python
channel_diffs = np.abs(reference - candidate).mean(axis=(0,1))
print(f"R diff: {channel_diffs[0]}")
print(f"G diff: {channel_diffs[1]}")
print(f"B diff: {channel_diffs[2]}")
print(f"A diff: {channel_diffs[3]}")
```

---

## Multiple Test Scenes - Critical!

### Why One Test Scene Isn't Enough

A shader might produce correct output in one scenario but fail in others:

**Edge cases:**
- UV coordinates at boundaries (0, 1)
- Extreme time values (very large/small)
- Different resolutions
- Different texture inputs
- Null/zero inputs

**Example: Bug Only Shows at Certain Times**

```glsl
// Original
float val = sin(time * 0.1);

// "Optimized" (WRONG!)
float val = sin(time);  // Oops! Different frequency
```

At `time=0`, both produce `0.0` ✅
At `time=1.57`, they differ significantly ❌

**Solution:** Test multiple time values!

### Recommended Test Scenes

```python
test_scenes = [
    # Basic test
    {'name': 'Default', 'uniforms': {'u_time': 0.0}},

    # Time-based animation
    {'name': 'T=1', 'uniforms': {'u_time': 1.0}},
    {'name': 'T=10', 'uniforms': {'u_time': 10.0}},
    {'name': 'T=100', 'uniforms': {'u_time': 100.0}},

    # Edge cases
    {'name': 'Edge_Zero', 'uniforms': {'u_value': 0.0}},
    {'name': 'Edge_One', 'uniforms': {'u_value': 1.0}},
    {'name': 'Edge_Large', 'uniforms': {'u_value': 1000.0}},

    # Different inputs
    {'name': 'Input_A', 'textures': [load_texture('test_a.png')]},
    {'name': 'Input_B', 'textures': [load_texture('test_b.png')]},
]
```

---

## Validation Strategies

### Strategy 1: Strict Validation (Lossless Optimization)

```python
validator.validate_quality(
    reference, candidate,
    ssim_threshold=0.999,  # Very strict
    psnr_threshold=50.0    # Nearly identical
)
```

**Use when:**
- Precision is critical
- No visual differences acceptable
- Medical, scientific applications

### Strategy 2: Perceptual Validation (Lossy Optimization)

```python
validator.validate_quality(
    reference, candidate,
    ssim_threshold=0.98,   # Perceptually identical
    psnr_threshold=40.0    # High quality
)
```

**Use when:**
- Human perception matters
- Tiny differences acceptable
- Games, real-time graphics

### Strategy 3: Adaptive Thresholds

```python
# Adjust based on shader complexity
if is_simple_shader:
    ssim_threshold = 0.999  # Strict
elif is_procedural_noise:
    ssim_threshold = 0.95   # Relaxed (stochastic)
else:
    ssim_threshold = 0.98   # Default
```

---

## Debugging Failed Validations

### Automatic Debug Output

When validation fails, save images for inspection:

```python
if not validation['passed']:
    # Save reference
    Image.fromarray(reference).save("debug_reference.png")

    # Save candidate
    Image.fromarray(candidate).save("debug_candidate.png")

    # Save amplified difference
    diff = np.abs(reference - candidate) * 10  # Amplify for visibility
    Image.fromarray(diff.astype(np.uint8)).save("debug_diff.png")
```

### Visual Diff Tools

Use image comparison tools:

```bash
# ImageMagick comparison
compare reference.png candidate.png -compose src diff.png

# Side-by-side comparison
montage reference.png candidate.png -geometry +5+5 comparison.png
```

---

## Integration with ShinkaEvolve

```python
# examples/shader_opt/evaluate_shader_with_validation.py

from shinka.core import run_shinka_eval

def shader_validation_function(run_output):
    """
    Called by ShinkaEvolve to validate each shader variant.
    """

    # Get reference shader output (cached)
    reference_image = load_reference_image()

    # Get candidate shader output
    candidate_image = run_output['output_image']

    # Validate quality
    validator = ShaderValidator()
    validation = validator.validate_quality(
        reference_image,
        candidate_image,
        ssim_threshold=0.99,
        psnr_threshold=40.0
    )

    if not validation['passed']:
        return False, f"Visual quality check failed: SSIM={validation['ssim']:.4f}"

    return True, f"Visual quality OK: SSIM={validation['ssim']:.4f}"
```

---

## Summary: Image Quality with ModernGL

### ✅ ModernGL Absolutely Ensures Quality

**How:**
1. **Captures rendered output** - `fbo.read()` gets pixel data
2. **Compares with reference** - Multiple metrics (SSIM, PSNR, MSE)
3. **Tests multiple scenes** - Catches edge cases
4. **Validates per-channel** - Detects subtle issues
5. **Saves debug images** - Manual inspection if needed

**Validation Pipeline:**
```
Reference Shader → Render → Reference Images
                              ↓
Optimized Shader → Render → Candidate Images
                              ↓
                         Compare (SSIM, PSNR)
                              ↓
                    Pass/Fail Decision (0.99+ threshold)
```

**This is MORE rigorous than manual testing!**

### Comparison to UE5

| Aspect | UE5 | ModernGL + Validation |
|--------|-----|----------------------|
| Image capture | ✅ Yes | ✅ Yes |
| Automated comparison | ⚠️ Manual | ✅ Automatic |
| Multiple metrics | ❌ Limited | ✅ SSIM, PSNR, MSE |
| Headless testing | ⚠️ Difficult | ✅ Easy |
| CI/CD integration | ❌ Hard | ✅ Simple |

**ModernGL is actually BETTER for quality validation than UE5!**

---

## Next: Complex Shaders with Headers

Now let me address the second critical question about complex shaders with includes...

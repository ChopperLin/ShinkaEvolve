"""
Test HLSL optimization setup.

This script verifies that:
1. DXC compiler is available
2. WGPU can access GPU
3. Basic shader compilation works
4. The pipeline is ready for ShinkaEvolve
"""

import sys
import subprocess
import os


def test_dxc():
    """Test if DXC compiler is available."""
    print("\n" + "="*70)
    print("TEST 1: DXC Compiler")
    print("="*70)

    try:
        result = subprocess.run(['dxc', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ DXC compiler found")
            print(f"   Version: {result.stdout.split()[0] if result.stdout else 'unknown'}")
            return True
        else:
            print("❌ DXC exists but returned error")
            return False
    except FileNotFoundError:
        print("❌ DXC compiler not found in PATH")
        print("   Download from: https://github.com/microsoft/DirectXShaderCompiler/releases")
        return False
    except Exception as e:
        print(f"❌ Error testing DXC: {e}")
        return False


def test_wgpu():
    """Test if WGPU can access GPU."""
    print("\n" + "="*70)
    print("TEST 2: WGPU GPU Access")
    print("="*70)

    try:
        import wgpu
        print("✅ WGPU module imported")

        adapter = wgpu.gpu.request_adapter(power_preference="high-performance")
        info = adapter.request_adapter_info()

        print("✅ GPU adapter found")
        print(f"   Name: {info.get('description', 'unknown')}")
        print(f"   Vendor: {info.get('vendor', 'unknown')}")
        print(f"   Backend: {info.get('backend', 'unknown')}")

        device = adapter.request_device()
        print("✅ GPU device created")

        return True

    except ImportError:
        print("❌ WGPU not installed")
        print("   Install with: pip install wgpu glfw")
        return False
    except Exception as e:
        print(f"❌ Failed to access GPU: {e}")
        print("   Ensure DirectX 12 capable GPU and updated drivers")
        return False


def test_compilation():
    """Test basic HLSL compilation with DXC."""
    print("\n" + "="*70)
    print("TEST 3: HLSL Compilation")
    print("="*70)

    test_shader = """
float4 PSMain(float2 uv : TEXCOORD) : SV_TARGET {
    return float4(uv, 0.0, 1.0);
}
"""

    try:
        # Write test shader
        with open('test_shader.hlsl', 'w') as f:
            f.write(test_shader)

        # Compile with DXC
        result = subprocess.run([
            'dxc',
            '-T', 'ps_6_0',
            '-E', 'PSMain',
            '-spirv',
            '-Fo', 'test_shader.spv',
            'test_shader.hlsl'
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0 and os.path.exists('test_shader.spv'):
            print("✅ HLSL shader compiled successfully")
            print(f"   Output: test_shader.spv ({os.path.getsize('test_shader.spv')} bytes)")

            # Cleanup
            os.remove('test_shader.hlsl')
            os.remove('test_shader.spv')
            return True
        else:
            print("❌ Compilation failed")
            print(f"   Error: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Compilation test failed: {e}")
        return False


def test_dependencies():
    """Test that all Python dependencies are installed."""
    print("\n" + "="*70)
    print("TEST 4: Python Dependencies")
    print("="*70)

    dependencies = {
        'wgpu': 'wgpu',
        'numpy': 'numpy',
        'PIL': 'pillow',
        'skimage': 'scikit-image',
    }

    all_ok = True
    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Install with: pip install {package}")
            all_ok = False

    return all_ok


def test_initial_shader():
    """Test that initial_shader.py is valid."""
    print("\n" + "="*70)
    print("TEST 5: Initial Shader Module")
    print("="*70)

    try:
        from initial_shader import HLSL_SHADER_SOURCE, VERTEX_SHADER_SOURCE, run_experiment

        print("✅ initial_shader.py imports successfully")

        # Check shader sources are non-empty
        if len(HLSL_SHADER_SOURCE) > 50:
            print(f"✅ Fragment shader defined ({len(HLSL_SHADER_SOURCE)} chars)")
        else:
            print("❌ Fragment shader too short")
            return False

        if len(VERTEX_SHADER_SOURCE) > 50:
            print(f"✅ Vertex shader defined ({len(VERTEX_SHADER_SOURCE)} chars)")
        else:
            print("❌ Vertex shader too short")
            return False

        # Test run_experiment
        result = run_experiment(test_iterations=100)
        if 'vertex_shader' in result and 'fragment_shader' in result:
            print("✅ run_experiment() works correctly")
        else:
            print("❌ run_experiment() missing required keys")
            return False

        return True

    except ImportError as e:
        print(f"❌ Cannot import initial_shader.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing initial_shader.py: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("HLSL SHADER OPTIMIZATION SETUP TEST")
    print("="*70)
    print("This verifies that your system is ready for HLSL optimization.")

    tests = [
        ("DXC Compiler", test_dxc),
        ("WGPU GPU Access", test_wgpu),
        ("HLSL Compilation", test_compilation),
        ("Python Dependencies", test_dependencies),
        ("Initial Shader", test_initial_shader),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ Unexpected error in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False

    print("="*70)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your system is ready for HLSL shader optimization with ShinkaEvolve!")
        print("\nNext steps:")
        print("  1. Create evaluate_hlsl.py from HLSL_PRODUCTION_SOLUTION.md")
        print("  2. Create run_hlsl_evolution.py from HLSL_PRODUCTION_SOLUTION.md")
        print("  3. Run: python run_hlsl_evolution.py")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Please fix the issues above before running optimization.")
        print("\nCommon fixes:")
        print("  - Install DXC: https://github.com/microsoft/DirectXShaderCompiler/releases")
        print("  - Install WGPU: pip install wgpu glfw")
        print("  - Install other deps: pip install numpy pillow scikit-image")
        print("  - Update GPU drivers")
        return 1


if __name__ == "__main__":
    sys.exit(main())

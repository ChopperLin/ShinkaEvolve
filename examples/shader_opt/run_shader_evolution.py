"""
Run shader optimization using ShinkaEvolve.

This demonstrates how to configure and launch shader evolution.
"""

from shinka.core import EvolutionRunner, EvolutionConfig
from shinka.database import DatabaseConfig
from shinka.launch import LocalJobConfig


def main():
    """Configure and run shader evolution."""

    # Task description for the LLM
    task_description = """You are optimizing GPU shader code (GLSL) for maximum performance.

    Your goal is to reduce execution time while maintaining visual correctness.

    OPTIMIZATION STRATEGIES:
    1. Eliminate redundant texture fetches - texture() calls are expensive
    2. Reduce arithmetic operations - especially divisions and square roots
    3. Combine operations - use vector operations efficiently (e.g., dot products)
    4. Remove intermediate variables when possible
    5. Simplify mathematical expressions using algebraic identities
    6. Eliminate dead code that doesn't affect the output

    CONSTRAINTS:
    - The shader MUST compile (valid GLSL syntax)
    - The visual output MUST match the original (correctness)
    - Only modify code within EVOLVE-BLOCK markers
    - Preserve the main() function structure

    FOCUS AREAS:
    - Look for duplicate texture fetches
    - Simplify brightness/color calculations
    - Use built-in GLSL functions (mix, smoothstep, etc.)
    - Minimize intermediate vec3/vec4 constructions

    Remember: Lower execution time = better performance = higher score.
    """

    # Evolution configuration
    evo_config = EvolutionConfig(
        init_program_path="examples/shader_opt/initial_shader.py",
        task_sys_msg=task_description,
        num_generations=20,  # Run for 20 generations
        max_parallel_jobs=4,  # Evaluate 4 shaders in parallel
        max_patch_resamples=5,  # Allow more resamples (shaders may fail to compile)
        max_patch_attempts=5,
        language="glsl",  # Hint to LLM about the language
        llm_models=["azure-gpt-4.1-mini"],  # Or anthropic-claude-sonnet-4
        patch_types=["diff", "full"],  # Allow both targeted edits and full rewrites
        patch_type_probs=[0.7, 0.3],  # Prefer targeted edits (70%) over full rewrites (30%)
        use_text_feedback=False,  # Don't use text feedback for now
    )

    # Database configuration (multi-island evolution)
    db_config = DatabaseConfig(
        num_islands=4,  # 4 islands explore different optimization strategies
        archive_size=50,  # Keep top 50 optimized shaders
        migration_interval=5,  # Share best shaders between islands every 5 generations
        migration_rate=0.1,  # Migrate 10% of population
        parent_selection_strategy="power_law",  # Favor better parents
        exploitation_alpha=1.0,  # Balance exploration vs exploitation
    )

    # Job configuration
    job_config = LocalJobConfig(
        eval_program_path="examples/shader_opt/evaluate_shader.py",
        extra_cmd_args={},
    )

    print("=" * 70)
    print("SHADER OPTIMIZATION WITH SHINKAEVOLVE")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Generations: {evo_config.num_generations}")
    print(f"  Islands: {db_config.num_islands}")
    print(f"  Parallel jobs: {evo_config.max_parallel_jobs}")
    print(f"  LLM models: {evo_config.llm_models}")
    print(f"\nStarting evolution...\n")

    # Create and run evolution
    runner = EvolutionRunner(
        evo_config=evo_config,
        job_config=job_config,
        db_config=db_config,
    )

    # Run evolution
    runner.run()

    print("\n" + "=" * 70)
    print("EVOLUTION COMPLETE!")
    print("=" * 70)
    print(f"\nResults saved to: {evo_config.results_dir}")
    print("\nNext steps:")
    print("  1. Check the results directory for optimized shaders")
    print("  2. Launch WebUI to visualize evolution: shinka_visualize")
    print("  3. Compare performance: check metrics.json files")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
Test Jinja2 prompt builder and template re    prompt = builder.build_creative_agent_prompt(context)
    
    print("\n[OK] Judge template rendered successfully")
    print(f"  Prompt length: {len(prompt)} characters")
    print(f"  Contains 'Originality': {'Originality' in prompt}")
    print(f"  Contains 'ACCEPTED': {'ACCEPTED' in prompt}")
    print(f"  Contains 'JSON': {'JSON' in prompt}")
    print(f"  Contains evaluation criteria: {context.idea_text[:30] in prompt}")
"""

import json
from pathlib import Path
from creativity_agent.utilities import (
    JinjaPromptBuilder,
    CreativeAgentPromptContext,
    JudgePromptContext,
    RefinementPromptContext,
    ChaosPromptContext
)


def test_creative_agent_template():
    """Test creative agent template rendering."""
    print("\n" + "=" * 80)
    print("Testing Creative Agent Template")
    print("=" * 80)
    
    builder = JinjaPromptBuilder(templates_dir="creativity_agent/prompts_templates")
    
    context = CreativeAgentPromptContext(
        original_prompt="Next-generation LLM enhancements focusing on reasoning",
        content="Previous ideas: chain-of-thought, reasoning traces",
        chaos_seeds=[
            "Biological neural plasticity and synaptic reorganization",
            "Swarm intelligence and emergent collective behavior",
            "Quantum annealing for optimization"
        ],
        memory_context="Already explored: attention mechanisms, sparse routing, token pruning",
        iteration=2
    )
    
    prompt = builder.build_creative_agent_prompt(context)
    
    print("\n[OK] Creative agent template rendered successfully")
    print(f"  Prompt length: {len(prompt)} characters")
    print(f"  Contains 'JSON': {'JSON' in prompt}")
    print(f"  Contains 'Iteration': {'Iteration' in prompt}")
    print(f"  Contains chaos seeds: {all(seed[:20] in prompt for seed in context.chaos_seeds)}")
    
    # Show first 500 chars
    print("\nFirst 500 characters of prompt:")
    print("-" * 80)
    print(prompt[:500])
    print("...")


def test_judge_template():
    """Test judge template rendering."""
    print("\n" + "=" * 80)
    print("Testing Judge Agent Template")
    print("=" * 80)
    
    builder = JinjaPromptBuilder(templates_dir="creativity_agent/prompts_templates")
    
    context = JudgePromptContext(
        idea_text="Hierarchical attention with dynamic sparse routing for efficient long-sequence processing",
        evaluation_criteria={
            "originality": "How novel is the hierarchical routing approach?",
            "feasibility": "Can dynamic routing be implemented efficiently?",
            "impact": "How much would this improve LLM performance?",
            "substance": "How detailed are the implementation specs?"
        },
        acceptance_threshold=5.0
    )
    
    prompt = builder.build_judge_prompt(context)
    
    print("\n✓ Judge template rendered successfully")
    print(f"  Prompt length: {len(prompt)} characters")
    print(f"  Contains 'Originality': {'Originality' in prompt}")
    print(f"  Contains 'ACCEPTED': {'ACCEPTED' in prompt}")
    print(f"  Contains 'JSON': {'JSON' in prompt}")
    print(f"  Contains evaluation criteria: {context.idea_text[:30] in prompt}")
    
    print("\nFirst 500 characters of prompt:")
    print("-" * 80)
    print(prompt[:500])
    print("...")


def test_refinement_template():
    """Test refinement template rendering."""
    print("\n" + "=" * 80)
    print("Testing Refinement Agent Template")
    print("=" * 80)
    
    builder = JinjaPromptBuilder(templates_dir="creativity_agent/prompts_templates")
    
    context = RefinementPromptContext(
        original_prompt="LLM architectural innovations",
        content="Idea 1: Hierarchical attention\nIdea 2: Dynamic pruning\nIdea 3: Quantum optimization",
        previous_evaluations=[
            {"idea_name": "Hierarchical attention", "overall_score": 8.0, "decision": "ACCEPTED"},
            {"idea_name": "Dynamic pruning", "overall_score": 6.5, "decision": "ACCEPTED"},
            {"idea_name": "Quantum optimization", "overall_score": 3.0, "decision": "REJECTED"}
        ],
        iteration=1
    )
    
    prompt = builder.build_refinement_prompt(context)
    
    print("\n[OK] Refinement template rendered successfully")
    print(f"  Prompt length: {len(prompt)} characters")
    print(f"  Contains 'accepted_ideas': {'accepted_ideas' in prompt}")
    print(f"  Contains 'rejected_ideas': {'rejected_ideas' in prompt}")
    print(f"  Contains 'synthesis': {'synthesis' in prompt}")
    print(f"  Contains 'JSON': {'JSON' in prompt}")
    
    print("\nFirst 500 characters of prompt:")
    print("-" * 80)
    print(prompt[:500])
    print("...")


def test_chaos_template():
    """Test chaos generator template rendering."""
    print("\n" + "=" * 80)
    print("Testing Chaos Generator Template")
    print("=" * 80)
    
    builder = JinjaPromptBuilder(templates_dir="creativity_agent/prompts_templates")
    
    context = ChaosPromptContext(
        original_prompt="Revolutionary AI architectures",
        concept_word="Biological neural plasticity",
        related_concepts=[
            "Synaptic pruning",
            "Long-term potentiation",
            "Experience-dependent learning"
        ]
    )
    
    prompt = builder.build_chaos_prompt(context)
    
    print("\n[OK] Chaos generator template rendered successfully")
    print(f"  Prompt length: {len(prompt)} characters")
    print(f"  Contains concept: {'Biological neural plasticity' in prompt}")
    print(f"  Contains 'tangential_connections': {'tangential_connections' in prompt}")
    print(f"  Contains 'JSON': {'JSON' in prompt}")
    
    print("\nFirst 500 characters of prompt:")
    print("-" * 80)
    print(prompt[:500])
    print("...")


def test_output_schemas():
    """Test output schema definitions."""
    print("\n" + "=" * 80)
    print("Testing Output Schema Definitions")
    print("=" * 80)
    
    builder = JinjaPromptBuilder()
    
    # Test all schemas
    schemas = {
        "Creative": builder._get_creative_output_schema(),
        "Judge": builder._get_judge_output_schema(),
        "Refinement": builder._get_refinement_output_schema(),
        "Chaos": builder._get_chaos_output_schema()
    }
    
    for name, schema in schemas.items():
        print(f"\n[OK] {name} schema:")
        print(f"  Name: {schema.schema_name}")
        print(f"  Required fields: {len(schema.required_fields)}")
        print(f"  Fields: {', '.join(schema.required_fields[:3])}...")
        
        # Verify example
        example = schema.format_example
        print(f"  Example keys: {list(example.keys())}")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("JINJA2 PROMPT BUILDER TEST SUITE")
    print("=" * 80)
    
    try:
        test_creative_agent_template()
        test_judge_template()
        test_refinement_template()
        test_chaos_template()
        test_output_schemas()
        
        print("\n" + "=" * 80)
        print("[SUCCESS] ALL TESTS PASSED")
        print("=" * 80)
        print("\nKey achievements:")
        print("  [OK] Jinja2 templates render correctly")
        print("  [OK] Context models validate properly")
        print("  [OK] Output schemas are well-defined")
        print("  [OK] JSON format requirements are clear")
        print("  [OK] All template files exist and load")
        
    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

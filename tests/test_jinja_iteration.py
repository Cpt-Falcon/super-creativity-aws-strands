#!/usr/bin/env python3
"""
Test runner for Jinja2 prompt system - Single iteration with verbose logging.

Tests each node sequentially and inspects outputs at each stage.
"""

import json
import logging
from pathlib import Path
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_jinja_iteration.log')
    ]
)
logger = logging.getLogger(__name__)


def verify_json_output(file_path: Path, node_name: str) -> dict | None:
    """Read and verify JSON output from node."""
    try:
        content = file_path.read_text(encoding='utf-8')
        logger.info(f"\n{'='*70}")
        logger.info(f"RAW OUTPUT FROM {node_name}:")
        logger.info(f"{'='*70}")
        logger.info(f"File size: {len(content)} bytes")
        logger.info(f"First 500 chars:\n{content[:500]}")
        
        # Try to extract JSON
        if '{' in content and '}' in content:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            json_str = content[json_start:json_end]
            
            try:
                data = json.loads(json_str)
                logger.info(f"\n[OK] JSON PARSING SUCCESSFUL")
                logger.info(f"JSON structure:\n{json.dumps(data, indent=2)[:1000]}")
                return data
            except json.JSONDecodeError as e:
                logger.error(f"[FAIL] JSON parsing failed: {e}")
                logger.error(f"JSON string (first 500 chars):\n{json_str[:500]}")
                return None
        else:
            logger.warning(f"[WARN] No JSON markers found in output")
            return None
    except Exception as e:
        logger.error(f"[FAIL] Error reading file {file_path}: {e}")
        return None


def test_single_iteration():
    """Run single iteration with verbose output inspection."""
    logger.info("="*70)
    logger.info("JINJA2 PROMPT SYSTEM - SINGLE ITERATION TEST")
    logger.info("="*70)
    
    try:
        # Import after logging setup
        from creativity_agent.agent_flow_graph import CreativityAgentFlowGraph
        from creativity_agent.config import FlowConfig
        
        # Load config from flow_config.json
        logger.info("\n1. Loading configuration...")
        config_path = Path(__file__).parent / "creativity_agent" / "flow_config.json"
        config = FlowConfig.from_json(config_path)
        
        # Override iterations to 1 for testing
        config.iterations = 1
        logger.info(f"   Config loaded: {config_path}")
        logger.info(f"   Config: iterations={config.iterations}, models={list(config.models.keys())}")
        
        # Create graph with Jinja2 builder
        logger.info("\n2. Initializing CreativityAgentFlowGraph...")
        logger.info("   This will initialize JinjaPromptBuilder...")
        
        try:
            graph = CreativityAgentFlowGraph(
                config=config,
                enable_memory=True,
                enable_chaos=True,
                enable_judge=True,
                enable_observability=False,
                chaos_seeds_per_iteration=2,
                mock_mode=False  # Use real prompts!
            )
            logger.info(f"   [OK] Graph initialized successfully")
            logger.info(f"   - Jinja builder: {type(graph.jinja_builder).__name__}")
            logger.info(f"   - Run directory: {graph.run_dir}")
        except Exception as e:
            logger.error(f"   [FAIL] Failed to initialize graph: {e}", exc_info=True)
            return False
        
        # Run single iteration
        logger.info("\n3. Running single iteration...")
        user_prompt = "Create innovative AI-powered tools for creative collaboration"
        
        try:
            result = graph.run(user_prompt)
            logger.info(f"   [OK] Iteration completed")
        except Exception as e:
            logger.error(f"   [FAIL] Iteration failed: {e}", exc_info=True)
            return False
        
        # Inspect outputs
        logger.info("\n4. Inspecting node outputs...")
        run_dir = graph.run_dir
        
        # Check chaos output
        chaos_file = run_dir / "chaos_input_iteration_0.txt"
        if chaos_file.exists():
            logger.info(f"\n[OK] Found chaos output: {chaos_file}")
            verify_json_output(chaos_file, "CHAOS_GENERATOR_NODE")
        else:
            logger.warning(f"[WARN] Chaos output not found: {chaos_file}")
        
        # Check creative output
        creative_file = run_dir / "claude_creative_iteration_0.txt"
        if creative_file.exists():
            logger.info(f"\n[OK] Found creative output: {creative_file}")
            creative_json = verify_json_output(creative_file, "CREATIVE_AGENT_NODE")
            if creative_json:
                logger.info(f"\nCreative JSON structure:")
                logger.info(f"  - ideas count: {len(creative_json.get('ideas', []))}")
                logger.info(f"  - has web_research_summary: {'web_research_summary' in creative_json}")
                logger.info(f"  - has key_innovations: {'key_innovations' in creative_json}")
        else:
            logger.warning(f"[WARN] Creative output not found: {creative_file}")
        
        # Check refinement output
        refinement_file = run_dir / "claude_refinement_iteration_0.txt"
        if refinement_file.exists():
            logger.info(f"\n[OK] Found refinement output: {refinement_file}")
            refinement_json = verify_json_output(refinement_file, "REFINEMENT_AGENT_NODE")
            if refinement_json:
                logger.info(f"\nRefinement JSON structure:")
                logger.info(f"  - accepted_ideas count: {len(refinement_json.get('accepted_ideas', []))}")
                logger.info(f"  - rejected_ideas count: {len(refinement_json.get('rejected_ideas', []))}")
                logger.info(f"  - has synthesis: {'synthesis' in refinement_json}")
        else:
            logger.warning(f"[WARN] Refinement output not found: {refinement_file}")
        
        # Check judge output
        judge_file = run_dir / "judge_evaluations_iteration_0.txt"
        if judge_file.exists():
            logger.info(f"\n[OK] Found judge output: {judge_file}")
            content = judge_file.read_text(encoding='utf-8')
            logger.info(f"Judge evaluation summary (first 500 chars):\n{content[:500]}")
        else:
            logger.warning(f"[WARN] Judge output not found: {judge_file}")
        
        # Check memory
        memory_file = run_dir / "memory" / "idea_memory.json"
        if memory_file.exists():
            logger.info(f"\n[OK] Found memory file: {memory_file}")
            memory_data = json.loads(memory_file.read_text(encoding='utf-8'))
            logger.info(f"Memory statistics:")
            logger.info(f"  - explored_ideas count: {len(memory_data.get('explored_ideas', []))}")
            logger.info(f"  - rejected_ideas count: {len(memory_data.get('rejected_ideas', []))}")
        else:
            logger.warning(f"[WARN] Memory file not found: {memory_file}")
        
        # Check final output
        final_file = run_dir / "final_output.txt"
        if final_file.exists():
            logger.info(f"\n[OK] Found final output: {final_file}")
            content = final_file.read_text(encoding='utf-8')
            logger.info(f"Final output (first 500 chars):\n{content[:500]}")
        else:
            logger.warning(f"[WARN] Final output not found: {final_file}")
        
        logger.info("\n" + "="*70)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        
        # Summary
        logger.info(f"\nRun directory: {run_dir}")
        logger.info(f"Check outputs at: {run_dir}")
        logger.info("\nFiles to inspect:")
        for f in sorted(run_dir.glob("**/*.txt")):
            logger.info(f"  - {f.relative_to(run_dir)}")
        if (run_dir / "memory").exists():
            for f in (run_dir / "memory").glob("*.json"):
                logger.info(f"  - {f.relative_to(run_dir)}")
        
        return True
        
    except Exception as e:
        logger.error(f"[FAIL] Test failed with exception: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_single_iteration()
    exit(0 if success else 1)

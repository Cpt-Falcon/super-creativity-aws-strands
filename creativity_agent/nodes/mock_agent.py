from creativity_agent.nodes.base_node import BaseNode
from creativity_agent.models import ExecutionState, SharedState
from strands.multiagent import MultiAgentResult
from typing import Optional, Union
from strands.types.content import ContentBlock
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MockAgent(BaseNode):
    """
    Mock agent that returns fake results for fast graph debugging.
    Uses typed ExecutionState like real agents.
    """
    
    def __init__(
        self,
        shared_state: SharedState,
        name: str,
        agent_type: str = "generic",
        outputs_dir: Optional[Path] = None
    ):
        """
        Initialize mock agent.
        
        Args:
            shared_state: SharedState instance for node coordination
            name: Agent identifier
            agent_type: Type of agent ("creative", "refinement", "final")
            outputs_dir: Directory to save outputs (optional)
        """
        super().__init__(
            node_name=name,
            shared_state=shared_state,
            outputs_dir=outputs_dir
        )
        self.agent_type = agent_type
        
    async def invoke_async(
        self,
        task: Union[str, list[ContentBlock]],
        invocation_state: Optional[dict] = None,
        **kwargs
    ) -> MultiAgentResult:
        """
        Return mock result without LLM call.
        Uses typed ExecutionState for proper state management.
        """
        try:
            # Parse typed input
            node_input = self._get_typed_input(task, invocation_state)
            state = node_input.state
            iteration = state.iteration
            
            # Generate mock response based on agent type
            if self.agent_type == "creative":
                message = f"""[MOCK {self.name} - CREATIVE MODE]
Iteration: {iteration}

Generated 5 creative ideas:
1. Idea Alpha - A novel approach using quantum mechanics
2. Idea Beta - Innovative combination of AI and blockchain
3. Idea Gamma - Revolutionary user interface paradigm
4. Idea Delta - Sustainable solution using bio-inspired algorithms
5. Idea Epsilon - Cross-domain synthesis of disparate technologies

(This is a mock response for graph structure debugging)
"""
                # Update state with mock creative output
                updated_state = state.with_updates(
                    creative_output=message,
                    creative_model=self.name,
                    success=True
                )
            elif self.agent_type == "refinement":
                message = f"""[MOCK {self.name} - REFINEMENT MODE]
Iteration: {iteration}

REFINED IDEAS (Top 3):

**Idea Alpha** (Score: 8.5/10)
- Originality: High
- Feasibility: Medium-High
- Impact: Significant
- Implementation: 6-12 months

**Idea Beta** (Score: 7.8/10)
- Originality: Medium-High
- Feasibility: High
- Impact: Moderate
- Implementation: 3-6 months

**Idea Gamma** (Score: 8.2/10)
- Originality: Very High
- Feasibility: Medium
- Impact: High
- Implementation: 12-18 months

(This is a mock response for graph structure debugging)
"""
                # Update state with mock refinement output
                updated_state = state.with_updates(
                    refinement_output=message,
                    refinement_model=self.name,
                    success=True
                )
            elif self.agent_type == "final":
                message = f"""[MOCK {self.name} - DEEP RESEARCH MODE]

# COMPREHENSIVE INNOVATION ANALYSIS

## EXECUTIVE SUMMARY
After {iteration} iterations of creative exploration, we identified 3 breakthrough concepts with high potential for impact and feasibility.

## TOP IDEAS IDENTIFIED
1. Idea Alpha - Quantum-inspired computational approach
2. Idea Beta - AI-blockchain hybrid system
3. Idea Gamma - Revolutionary interface paradigm

## DETAILED ANALYSIS
[Mock deep research analysis would appear here with citations and implementation roadmap]

## STRATEGIC RECOMMENDATIONS
- Priority 1: Begin with Idea Beta (highest feasibility)
- Resource Requirements: 2-3 person team, 6 months
- Risk Mitigation: Phased rollout with MVP validation

(This is a mock response for graph structure debugging)
"""
                # Update state with mock final research output
                updated_state = state.with_updates(
                    final_research_output=message,
                    is_finished=True,
                    success=True
                )
            else:
                message = f"""[MOCK {self.name}]
Iteration: {iteration}
Processed task successfully.

(This is a mock response for graph structure debugging)
"""
                updated_state = state.with_updates(success=True)
            
            logger.info(f"🎭 Mock agent '{self.name}' executed (type: {self.agent_type}, iteration: {iteration})")
            
            # Save output file if outputs_dir is provided
            if self.outputs_dir:
                output_file = self.outputs_dir / f"{self.name}_iteration_{iteration}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(message)
                logger.info(f"🎭 Mock agent saved output to {output_file}")
            
            return self.create_result(
                message=message,
                state=updated_state,
                execution_time=1
            )
            
        except Exception as e:
            # Create error state preserving original_prompt
            error_state = ExecutionState(
                original_prompt=invocation_state.get('original_prompt', '') if invocation_state else '',
                iteration=invocation_state.get('iteration', 0) if invocation_state else 0,
                run_id=invocation_state.get('run_id', 'unknown') if invocation_state else 'unknown',
                run_dir=invocation_state.get('run_dir', '.') if invocation_state else '.'
            )
            return self.handle_error(e, error_state)



class MockChaosNode(BaseNode):
    """Mock chaos generator for fast debugging with typed state."""
    
    def __init__(self, shared_state: SharedState, chaos_seeds_per_iteration: int, outputs_dir: Path):
        super().__init__(
            node_name="chaos_generator",
            shared_state=shared_state,
            outputs_dir=outputs_dir
        )
        self.chaos_seeds_per_iteration = chaos_seeds_per_iteration
        
    async def invoke_async(
        self,
        task: Union[str, list[ContentBlock]],
        invocation_state: Optional[dict] = None,
        **kwargs
    ) -> MultiAgentResult:
        """Generate mock chaos seeds with typed state, including real web searches."""
        try:
            # Parse typed input
            node_input = self._get_typed_input(task, invocation_state)
            state = node_input.state
            iteration = state.iteration
            
            # Generate fake chaos seeds
            fake_seeds = ["quantum", "fractal", "emergence", "paradox", "synthesis"][:self.chaos_seeds_per_iteration]
            
            # Import here to avoid circular imports
            from creativity_agent.tools import search_web, get_url_content
            import re
            
            # Call real web search for each seed to test caching
            search_results = {}
            for seed in fake_seeds:
                try:
                    logger.info(f"Mock chaos: searching web for '{seed}' to test caching...")
                    results_text = search_web(f"what is {seed}", max_results=2, output_format="list")
                    search_results[seed] = results_text
                    
                    # Extract URLs from the formatted results using regex
                    # Format is: "   URL: https://..."
                    url_pattern = r'URL:\s*(https?://[^\s\n]+)'
                    urls = re.findall(url_pattern, results_text)
                    
                    # Fetch content from first URL to test cache
                    if urls and len(urls) > 0:
                        first_url = urls[0]
                        logger.info(f"Mock chaos: fetching content from {first_url[:60]}... to test cache")
                        content = get_url_content(first_url)
                        if content:
                            logger.info(f"Mock chaos: fetched {len(content)} bytes from {first_url[:60]}...")
                except Exception as e:
                    logger.warning(f"Mock chaos: web search for '{seed}' failed: {e}")
                    search_results[seed] = ""
            
            chaos_context = f"""[MOCK CHAOS GENERATOR]
Iteration: {iteration}

DIVERGENT EXPLORATION SEEDS:
{chr(10).join(f'• {seed} - Tangential concept for creative exploration' for seed in fake_seeds)}

WEB SEARCH RESULTS (for cache testing):
{chr(10).join(f'  {seed}: Found results' for seed in fake_seeds)}

(This is mock chaos data for graph structure debugging - includes real web searches for cache testing)
"""
            
            # Save to file
            if self.outputs_dir:
                chaos_file = self.outputs_dir / f"chaos_input_iteration_{iteration}.txt"
                with open(chaos_file, 'w', encoding='utf-8') as f:
                    f.write(chaos_context)
                logger.info(f"🎭 Mock chaos generator created {chaos_file}")
            
            # Convert chaos_seeds to proper format: List[Dict[str, str]]
            chaos_seeds_dicts = [
                {
                    'concept': seed,
                    'context': f'Context for {seed}',
                    'relevance': 'Medium tangential relevance'
                }
                for seed in fake_seeds
            ]
            
            # Update state with chaos output
            updated_state = state.with_updates(
                chaos_context=chaos_context,
                chaos_seeds=chaos_seeds_dicts,
                chaos_seeds_count=len(fake_seeds),
                success=True
            )
            
            return self.create_result(
                message=f"Generated {len(fake_seeds)} mock chaos seeds",
                state=updated_state,
                execution_time=1
            )
            
        except Exception as e:
            # Create error state
            error_state = ExecutionState(
                original_prompt=invocation_state.get('original_prompt', '') if invocation_state else '',
                iteration=invocation_state.get('iteration', 0) if invocation_state else 0,
                run_id=invocation_state.get('run_id', 'unknown') if invocation_state else 'unknown',
                run_dir=invocation_state.get('run_dir', '.') if invocation_state else '.'
            )
            return self.handle_error(e, error_state)



class MockJudgeNode(BaseNode):
    """Mock judge for fast debugging with typed state."""
    
    def __init__(self, shared_state: SharedState, outputs_dir: Path):
        super().__init__(
            node_name="judge",
            shared_state=shared_state,
            outputs_dir=outputs_dir
        )
        
    async def invoke_async(
        self,
        task: Union[str, list[ContentBlock]],
        invocation_state: Optional[dict] = None,
        **kwargs
    ) -> MultiAgentResult:
        """Generate mock judge evaluations with typed state."""
        try:
            # Parse typed input
            node_input = self._get_typed_input(task, invocation_state)
            state = node_input.state
            iteration = state.iteration
            
            evaluation_text = f"""[MOCK JUDGE EVALUATION]
Iteration: {iteration}

Total Ideas Evaluated: 3
Accepted: 2
Rejected: 1

IDEA 1: Quantum Approach
- Originality: 8/10
- Feasibility: 7/10
- Impact: 9/10
- Decision: ACCEPTED

IDEA 2: Hybrid System
- Originality: 7/10
- Feasibility: 8/10
- Impact: 7/10
- Decision: ACCEPTED

IDEA 3: Interface Paradigm
- Originality: 6/10
- Feasibility: 5/10
- Impact: 6/10
- Decision: REJECTED

(This is mock judge data for graph structure debugging)
"""
            
            # Save to file
            if self.outputs_dir:
                judge_file = self.outputs_dir / f"judge_evaluations_iteration_{iteration}.txt"
                with open(judge_file, 'w', encoding='utf-8') as f:
                    f.write(evaluation_text)
                logger.info(f"🎭 Mock judge created {judge_file}")
            
            # Update state with judge output
            updated_state = state.with_updates(
                judge_evaluations=[
                    {
                        "idea": "Quantum Approach",
                        "originality": 8,
                        "feasibility": 7,
                        "impact": 9,
                        "decision": "ACCEPTED"
                    },
                    {
                        "idea": "Hybrid System",
                        "originality": 7,
                        "feasibility": 8,
                        "impact": 7,
                        "decision": "ACCEPTED"
                    },
                    {
                        "idea": "Interface Paradigm",
                        "originality": 6,
                        "feasibility": 5,
                        "impact": 6,
                        "decision": "REJECTED"
                    }
                ],
                accepted_ideas_count=2,
                success=True
            )
            
            return self.create_result(
                message="Evaluated 3 mock ideas",
                state=updated_state,
                execution_time=1
            )
            
        except Exception as e:
            # Create error state
            error_state = ExecutionState(
                original_prompt=invocation_state.get('original_prompt', '') if invocation_state else '',
                iteration=invocation_state.get('iteration', 0) if invocation_state else 0,
                run_id=invocation_state.get('run_id', 'unknown') if invocation_state else 'unknown',
                run_dir=invocation_state.get('run_dir', '.') if invocation_state else '.'
            )
            return self.handle_error(e, error_state)


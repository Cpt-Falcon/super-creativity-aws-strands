"""
Chaos Generator Node - Generates divergent thinking seeds using Jinja2 templates.

Uses typed ExecutionState for proper state management throughout the graph.
"""

from creativity_agent.nodes.base_node import BaseNode
from creativity_agent.models import ExecutionState, SharedState
from strands.multiagent import MultiAgentResult
from creativity_agent.utilities import ChaosGenerator, JinjaPromptBuilder, ChaosPromptContext
from pathlib import Path
from typing import Optional, Union
from strands.types.content import ContentBlock
import logging
import time

logger = logging.getLogger(__name__)


class ChaosGeneratorNode(BaseNode):
    """Node that generates chaos seeds for divergent thinking using Jinja2 templates."""
    
    def __init__(
        self,
        shared_state: SharedState,
        chaos_generator: ChaosGenerator,
        chaos_seeds_per_iteration: int,
        outputs_dir: Path,
        prompts_dir: Optional[Path] = None,
        jinja_builder: Optional[JinjaPromptBuilder] = None
    ):
        super().__init__(
            node_name="chaos_generator",
            shared_state=shared_state,
            prompts_dir=prompts_dir,
            outputs_dir=outputs_dir
        )
        self.chaos_generator = chaos_generator
        self.chaos_seeds_per_iteration = chaos_seeds_per_iteration
        self.jinja_builder = jinja_builder or JinjaPromptBuilder()
        
    async def invoke_async(
        self,
        task: Union[str, list[ContentBlock]],
        invocation_state: Optional[dict] = None,
        **kwargs
    ) -> MultiAgentResult:
        """Generate chaos seeds for the current iteration using Jinja2 templates."""
        try:
            # Parse typed input
            node_input = self._get_typed_input(task, invocation_state)
            state = node_input.state
            
            # Get current iteration from shared state
            iteration = self.shared_state.get_current_iteration()
            
            logger.info(f"Generating chaos seeds for iteration {iteration}")
            
            start_time = time.time()
            
            # Generate chaos seeds from original prompt
            chaos_input = self.chaos_generator.generate_chaos_input(
                state.original_prompt,
                num_seeds=self.chaos_seeds_per_iteration
            )
            
            # Extract seeds for state and Jinja2 template
            chaos_seeds = [
                {
                    'concept': concept.term,
                    'context': concept.context,
                    'relevance': concept.relevance_note
                }
                for concept in chaos_input.tangential_concepts
            ]
            
            # Build chaos summary using Jinja2
            related_concepts_list = [s['concept'] for s in chaos_seeds]
            context = ChaosPromptContext(
                original_prompt=state.original_prompt,
                concept_word=', '.join(related_concepts_list),
                related_concepts=related_concepts_list
            )
            chaos_summary = self.jinja_builder.build_chaos_prompt(context)
            
            logger.debug(f"Built chaos prompt ({len(chaos_summary)} chars) with {len(chaos_seeds)} seeds")
            
            # Save chaos input
            filename = f"chaos_input_iteration_{iteration}.txt"
            self.save_output(filename, chaos_summary)
            
            # Update state with chaos output
            updated_state = state.with_updates(
                iteration=iteration,
                chaos_context=chaos_summary,
                chaos_seeds=chaos_seeds,
                chaos_seeds_count=self.chaos_seeds_per_iteration,
                success=True
            )
            
            execution_time = int(time.time() - start_time)
            
            return self.create_result(
                message=chaos_summary,
                state=updated_state,
                execution_time=execution_time
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

"""
Iteration Controller Node - Manages iteration loops and completion.

This node acts like the condition checker in a for loop.
It receives iteration count and determines whether to continue or finish.

Iteration tracking uses SharedState which is passed to all nodes during initialization.
"""

from creativity_agent.nodes.base_node import BaseNode
from creativity_agent.models import ExecutionState, SharedState
from strands.multiagent import MultiAgentResult
from pathlib import Path
from typing import Optional, Union
from strands.types.content import ContentBlock
import logging

logger = logging.getLogger(__name__)


class IterationControllerNode(BaseNode):
    """Node that controls iteration loop and decides when to proceed to final step."""
    
    def __init__(
        self,
        shared_state: SharedState,
        prompts_dir: Optional[Path] = None,
        outputs_dir: Optional[Path] = None
    ):
        super().__init__(
            node_name="iteration_controller",
            shared_state=shared_state,
            prompts_dir=prompts_dir,
            outputs_dir=outputs_dir
        )
        
    async def invoke_async(
        self,
        task: Union[str, list[ContentBlock]],
        invocation_state: Optional[dict] = None,
        **kwargs
    ) -> MultiAgentResult:
        """Check if we should continue iterating or proceed to final step."""
        try:
            # Parse typed input (note: invocation_state is read-only)
            node_input = self._get_typed_input(task, invocation_state)
            state = node_input.state
            
            # Get current iteration from shared state
            current_iteration = self.shared_state.get_current_iteration()
            max_iterations = self.shared_state.max_iterations
            
            # Check if we should continue
            should_continue = current_iteration < max_iterations
            
            if should_continue:
                msg = f"Iteration {current_iteration} complete. Starting iteration {current_iteration + 1}..."
                next_iteration = self.shared_state.increment_iteration()
            else:
                msg = f"All {max_iterations} iterations complete. Proceeding to deep research..."
                next_iteration = current_iteration
            
            logger.info(msg)
            
            # Update state to reflect current iteration (for logging/output only)
            # The actual iteration tracking is in the shared_state instance
            updated_state = state.with_updates(
                iteration=current_iteration,
                should_continue=should_continue,
                is_finished=not should_continue,
                max_iterations=max_iterations,
                success=True
            )
            
            return self.create_result(
                message=msg,
                state=updated_state,
                execution_time=1
            )
            
        except Exception as e:
            # Create error state
            error_state = ExecutionState(
                original_prompt=invocation_state.get('original_prompt', '') if invocation_state else '',
                iteration=self.shared_state.get_current_iteration(),
                run_id=invocation_state.get('run_id', 'unknown') if invocation_state else 'unknown',
                run_dir=invocation_state.get('run_dir', '.') if invocation_state else '.'
            )
            return self.handle_error(e, error_state)

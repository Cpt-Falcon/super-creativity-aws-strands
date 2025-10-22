"""
Creative agent node with Jinja2-based prompt building and output management.
"""

from strands import Agent
from strands.multiagent import MultiAgentResult
from strands.types.content import ContentBlock
from typing import Optional, Union
from pathlib import Path
import logging
import time

from creativity_agent.nodes.base_node import BaseNode
from creativity_agent.utilities import JinjaPromptBuilder, CreativeAgentPromptContext
from creativity_agent.models import ExecutionState, SharedState

logger = logging.getLogger(__name__)


class CreativeAgentNode(BaseNode):
    """
    High-temperature creative agent node.
    Uses Jinja2 templates for sophisticated prompt building with chaos and memory context.
    
    Extends BaseNode for typed state management and proper error handling.
    """
    
    def __init__(
        self,
        shared_state: SharedState,
        agent: Agent,
        node_name: str,
        outputs_dir: Path,
        memory_manager: Optional[object] = None,
        jinja_builder: Optional[JinjaPromptBuilder] = None
    ):
        """
        Initialize creative agent node.
        
        Args:
            shared_state: SharedState instance for node coordination
            agent: Strands Agent instance
            node_name: Node identifier
            outputs_dir: Directory for saving outputs
            memory_manager: Optional memory manager for concept extraction
            jinja_builder: Optional Jinja2 prompt builder (will be created if not provided)
        """
        super().__init__(node_name=node_name, shared_state=shared_state, outputs_dir=outputs_dir)
        self.agent = agent
        self.memory_manager = memory_manager
        self.jinja_builder = jinja_builder or JinjaPromptBuilder()
        
    async def invoke_async(
        self,
        task: Union[str, list[ContentBlock]],
        invocation_state: Optional[dict] = None,
        **kwargs
    ) -> MultiAgentResult:
        """
        Execute creative agent with Jinja2 prompt building and typed state.
        
        Args:
            task: Input task/prompt
            invocation_state: Current execution state (converted to ExecutionState)
            **kwargs: Additional arguments
            
        Returns:
            MultiAgentResult with agent output and typed state updates
        """
        logger.info("task: %s", task)
        logger.info("invocation_state: %s", invocation_state)

        start_time = time.time()
        
        try:
            # Parse typed input
            node_input = self._get_typed_input(task, invocation_state)
            state = node_input.state  # Type: ExecutionState
            
            result = task if isinstance(task, str) else str(task)

            # Extract context from typed state
            original_prompt = state.original_prompt
            iteration = state.iteration
            
            # Get current content (from previous step or task)
            if isinstance(task, list):
                current_content = '\n'.join([block['text'] for block in task if isinstance(block, dict) and 'text' in block])
            else:
                current_content = str(task)
            
            logger.info(f"Creative agent '{self.name}' executing (iteration: {iteration})")
            
            # Build sophisticated prompt using Jinja2
            context = CreativeAgentPromptContext(
                original_prompt=original_prompt,
                content=current_content,
                chaos_seeds=result,
                memory_context='',  # Can be enhanced later
                iteration=iteration
            )
            enhanced_prompt = self.jinja_builder.build_creative_agent_prompt(context)
            
            logger.debug(f"Built creative agent prompt ({len(enhanced_prompt)} chars)")
            
            # Invoke the actual agent (streaming is controlled by BedrockModel config)
            # The agent will use tools (web search, etc.) and synthesize a final response
            agent_result = await self.agent.invoke_async(enhanced_prompt)
            
            # Extract the final message content from the agent result
            str_result = self.extract_message_content(agent_result)
            
            # Save raw output to file
            if self.outputs_dir:
                output_file = self.outputs_dir / f"{self.name}_iteration_{iteration}.txt"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(str_result)
                logger.info(f"Saved creative output to {output_file}")
            
            execution_time = int(time.time() - start_time)
            
            # Create updated state with creative output
            updated_state = state.with_updates(
                creative_output=str_result,
                creative_model=self.name,
                success=True
            )
            
            # Return typed result
            return self.create_result(
                message=str_result,
                state=updated_state,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"Error in creative agent '{self.name}': {e}", exc_info=True)
            
            # Create error state preserving context
            error_state = ExecutionState(
                original_prompt=f"Critical error occured: {e}",
                iteration=invocation_state.get('iteration', 0) if invocation_state else 0,
                run_id=invocation_state.get('run_id', 'unknown') if invocation_state else 'unknown',
                run_dir=invocation_state.get('run_dir', '.') if invocation_state else '.'
            )
            
            execution_time = int(time.time() - start_time)
            return self.handle_error(e, error_state)

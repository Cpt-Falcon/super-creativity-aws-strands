"""
Base node class for graph-based creativity flow.

All nodes inherit from this base class which provides:
- Typed execution state with Pydantic
- Prompt management
- State handling
- Logging
- Common utilities
"""

from abc import ABC, abstractmethod
from strands.multiagent import MultiAgentBase, MultiAgentResult
from strands.multiagent.base import NodeResult, Status
from strands.agent.agent_result import AgentResult
from strands.types.content import ContentBlock, Message
from pathlib import Path
from typing import Dict, Any, Optional, Union
from creativity_agent.models import ExecutionState, NodeInput, SharedState
import logging

logger = logging.getLogger(__name__)


class BaseNode(MultiAgentBase, ABC):
    """
    Base class for all creativity flow nodes.
    
    Provides common functionality:
    - Typed execution state with Pydantic (replaces duck typing)
    - Prompt loading and management
    - State extraction and updates
    - Result wrapping
    - Error handling
    
    All nodes work with ExecutionState for type safety.
    """
    
    def __init__(
        self,
        node_name: str,
        shared_state: SharedState,
        prompts_dir: Optional[Path] = None,
        outputs_dir: Optional[Path] = None
    ):
        """
        Initialize base node.
        
        Args:
            node_name: Unique identifier for this node
            shared_state: SharedState instance for node coordination
            prompts_dir: Directory containing prompt templates
            outputs_dir: Directory for saving node outputs
        """
        super().__init__()
        self.name = node_name
        self.shared_state = shared_state
        self.prompts_dir = prompts_dir or Path(__file__).parent.parent / "prompts"
        self.outputs_dir = outputs_dir
    
    def _get_typed_input(
        self,
        task: Union[str, list[ContentBlock]],
        invocation_state: Optional[Dict[str, Any]] = None
    ) -> NodeInput:
        """
        Convert raw Strands input to typed NodeInput with ExecutionState.
        
        Args:
            task: Raw task from Strands
            invocation_state: Raw invocation state dict from Strands
            
        Returns:
            NodeInput with typed ExecutionState
            
        Raises:
            ValueError: If state is invalid
        """
        try:
            return NodeInput.from_strands(task, invocation_state)
        except Exception as e:
            logger.error(f"Failed to parse input for {self.name}: {e}")
            raise
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a prompt template from the prompts directory.
        
        Args:
            prompt_name: Name of the prompt file (without .txt extension)
            
        Returns:
            Prompt template content
        """
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        
        if prompt_file.exists():
            return prompt_file.read_text(encoding='utf-8')
        else:
            logger.warning(f"Prompt file not found: {prompt_file}")
            return ""
    
    def save_output(self, filename: str, content: str) -> Optional[Path]:
        """
        Save node output to file.
        
        Args:
            filename: Output filename
            content: Content to save
            
        Returns:
            Path to saved file or None if no outputs_dir
        """
        if not self.outputs_dir:
            logger.warning(f"No outputs_dir configured for {self.name}")
            return None
        
        output_file = self.outputs_dir / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved {self.name} output to {output_file}")
        return output_file
    
    def create_result(
        self,
        message: str,
        state: ExecutionState,
        execution_time: int = 1,
        status: Status = Status.COMPLETED
    ) -> MultiAgentResult:
        """
        Create a standard MultiAgentResult with typed state.
        
        Args:
            message: Result message
            state: Updated ExecutionState
            execution_time: Node execution time in seconds
            status: Execution status
            
        Returns:
            MultiAgentResult object
        """
        agent_result = AgentResult(
            stop_reason="end_turn",
            message=Message(role="assistant", content=[ContentBlock(text=message)]),
            state=state.to_dict(),
            metrics=None # type: ignore
        )

        return MultiAgentResult(
            status=status,
            results={self.name: NodeResult(result=agent_result, execution_time=execution_time, status=status)},
            execution_count=1,
            execution_time=execution_time
        )
    
    def handle_error(
        self,
        error: Exception,
        state: ExecutionState
    ) -> MultiAgentResult:
        """
        Handle node execution errors with typed state.
        
        Args:
            error: Exception that occurred
            state: Current execution state
            
        Returns:
            Error result
        """
        error_msg = f"Error in {self.name}: {str(error)}"
        logger.error(error_msg, exc_info=True)
        
        # Update state to indicate failure
        error_state = state.with_updates(
            error_message=str(error),
            success=False
        )
        
        return self.create_result(
            message=error_msg,
            state=error_state,
            status=Status.FAILED
        )
    
    def extract_message_content(self, agent_result: Any) -> str:
        """
        Extract final message content from an agent result.
        
        Handles AgentResult objects from Strands agents by extracting
        the final synthesized message (after tool use) rather than raw
        string conversion which captures tool calls.
        
        Filters out tool use blocks and only extracts text content.
        
        Args:
            agent_result: Result object from agent.invoke_async()
            
        Returns:
            String content of the final message, or stringified result as fallback
        """
        str_result = ""
        
        try:
            # Try to access message content via structured attributes
            if hasattr(agent_result, 'message') and agent_result.message:
                message = agent_result.message
                
                # Try dict-style access first (TypedDict)
                try:
                    if 'content' in message:
                        content_list = message['content']
                        for content_block in content_list:
                            # Skip tool use blocks, only collect text
                            if isinstance(content_block, dict):
                                # Filter out tool_use and tool_result blocks
                                if 'text' in content_block and content_block.get('type') != 'tool_use':
                                    str_result += content_block['text']
                                elif 'text' in content_block and 'type' not in content_block:
                                    # Plain text dict
                                    str_result += content_block['text']
                            elif not isinstance(content_block, dict) and hasattr(content_block, 'text'):
                                # Object with text attribute - check if it's not a tool block
                                if not hasattr(content_block, 'type') or content_block.type != 'tool_use':
                                    str_result += str(content_block.text)
                except (TypeError, KeyError):
                    # If dict access fails, try attribute access
                    if hasattr(message, 'content'):
                        content_list = message.content
                        for content_block in content_list:
                            # Skip tool use blocks, only collect text
                            if isinstance(content_block, dict):
                                if 'text' in content_block and content_block.get('type') != 'tool_use':
                                    str_result += content_block['text']
                                elif 'text' in content_block and 'type' not in content_block:
                                    str_result += content_block['text']
                            elif not isinstance(content_block, dict) and hasattr(content_block, 'text'):
                                if not hasattr(content_block, 'type') or content_block.type != 'tool_use':
                                    str_result += str(content_block.text)
        except Exception as e:
            logger.debug(f"Failed to extract structured message content: {e}")
        
        # Fallback: if no structured result, convert to string
        if not str_result:
            str_result = str(agent_result)
            logger.debug(f"Using fallback string conversion for agent result")
        
        return str_result
    
    @abstractmethod
    async def invoke_async(
        self,
        task: Union[str, list[ContentBlock]],
        invocation_state: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> MultiAgentResult:
        """
        Execute the node's main logic.

        Must be implemented by subclasses.
        
        Subclasses should:
        1. Call self._get_typed_input() to get typed NodeInput
        2. Extract state from node_input.state
        3. Perform work
        4. Return updated state via self.create_result()
        
        Args:
            task: Input task/prompt
            invocation_state: Current execution state dict
            **kwargs: Additional arguments
            
        Returns:
            MultiAgentResult with typed ExecutionState
        """
        pass

"""
Agent wrapper that provides fallback from streaming to non-streaming invoke.

Some Bedrock models don't support tool use in streaming mode, so this wrapper
attempts streaming first and falls back to non-streaming if needed.
"""

from strands import Agent
from strands.agent.agent_result import AgentResult
from typing import Optional, Literal
import logging
import asyncio

logger = logging.getLogger(__name__)


class RobustAgent:
    """
    Wrapper around Strands Agent that provides fallback mechanisms.
    
    Attempts:
    1. Streaming invoke (default)
    2. Non-streaming invoke if streaming fails with tool-use error
    """
    
    def __init__(self, agent: Agent):
        """Initialize wrapper with a Strands Agent."""
        self.agent = agent
        self._non_streaming_tried = False
    
    async def invoke_async(self, prompt: str) -> AgentResult:
        """
        Invoke agent with fallback support.
        
        Args:
            prompt: Input prompt for the agent
            
        Returns:
            AgentResult from the agent
            
        Raises:
            Exception: If both streaming and non-streaming fail
        """
        try:
            # Try streaming first (default)
            logger.debug("Attempting streaming invoke...")
            result = await self.agent.invoke_async(prompt)
            logger.debug("Streaming invoke succeeded")
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if this is a tool-use streaming error
            if "tool use in streaming mode" in error_str or "doesn't support" in error_str:
                logger.warning(f"Streaming failed with tool-use error, attempting non-streaming: {e}")
                return await self._invoke_non_streaming(prompt)
            else:
                # Other errors should be re-raised
                logger.error(f"Streaming invoke failed with non-recoverable error: {e}")
                raise
    
    async def _invoke_non_streaming(self, prompt: str) -> AgentResult:
        """
        Invoke agent without streaming.
        
        Uses the underlying Bedrock model's non-streaming converse method.
        
        Args:
            prompt: Input prompt for the agent
            
        Returns:
            AgentResult from the agent
        """
        try:
            logger.info("Using non-streaming invoke as fallback")
            
            # Get the Bedrock model from the agent
            model = self.agent.model
            system_prompt = self.agent.system_prompt
            
            # Build messages
            messages = self.agent.messages.copy()
            messages.append({"role": "user", "content": prompt})  # type: ignore
            
            # Get tool specs if available
            tool_specs = []
            if hasattr(self.agent, 'tools') and self.agent.tools:  # type: ignore
                for tool in self.agent.tools:  # type: ignore
                    if hasattr(tool, 'to_bedrock_tool'):
                        tool_specs.append(tool.to_bedrock_tool())
            
            # Use non-streaming converse if available
            if hasattr(model, 'converse'):
                logger.debug("Using model.converse() non-streaming method")
                response = model.converse(  # type: ignore
                    system=system_prompt,
                    messages=messages,
                    tool_specs=tool_specs if tool_specs else None
                )
                
                # Parse the response into AgentResult format
                agent_result = self._parse_bedrock_response(response)
                return agent_result
            else:
                logger.error("Model does not support non-streaming converse method")
                raise RuntimeError("Model does not support non-streaming fallback")
                
        except Exception as e:
            logger.error(f"Non-streaming fallback failed: {e}", exc_info=True)
            raise RuntimeError(f"Both streaming and non-streaming invoke methods failed: {e}")
    
    def _parse_bedrock_response(self, response: dict) -> AgentResult:
        """
        Parse Bedrock converse response into AgentResult.
        
        Args:
            response: Response from Bedrock converse API
            
        Returns:
            AgentResult with properly formatted content
        """
        try:
            # Extract content and stop reason
            content_blocks = response.get('output', {}).get('message', {}).get('content', [])
            stop_reason_raw = response.get('stopReason', 'end_turn')
            # Ensure stop_reason is one of the valid Bedrock values
            valid_stop_reasons: tuple[str, ...] = (
                'content_filtered', 'end_turn', 'guardrail_intervened', 
                'interrupt', 'max_tokens', 'stop_sequence', 'tool_use'
            )
            stop_reason: Literal['content_filtered', 'end_turn', 'guardrail_intervened', 'interrupt', 'max_tokens', 'stop_sequence', 'tool_use'] = (
                stop_reason_raw if stop_reason_raw in valid_stop_reasons else 'end_turn'  # type: ignore
            )
            
            # Format as Message dict
            message = {
                'role': 'assistant',
                'content': content_blocks
            }
            
            # Create AgentResult
            agent_result = AgentResult(
                stop_reason=stop_reason,
                message=message,  # type: ignore
                state={},
                metrics=response.get('usage', {})  # type: ignore
            )
            
            return agent_result
            
        except Exception as e:
            logger.error(f"Failed to parse Bedrock response: {e}")
            # Return a safe default with valid stop_reason
            return AgentResult(
                stop_reason='end_turn',  # type: ignore
                message={'role': 'assistant', 'content': [{'text': f'Error parsing response: {e}'}]},  # type: ignore
                state={'error': str(e)},
                metrics={}  # type: ignore
            )   
    
    def __getattr__(self, name):
        """Delegate other attributes to the underlying agent."""
        return getattr(self.agent, name)


async def wrap_agent_invoke(agent: Agent, prompt: str) -> AgentResult:
    """
    Utility function to invoke agent with fallback support.
    
    Args:
        agent: Strands Agent to invoke
        prompt: Input prompt
        
    Returns:
        AgentResult from the agent
    """
    wrapper = RobustAgent(agent)
    return await wrapper.invoke_async(prompt)

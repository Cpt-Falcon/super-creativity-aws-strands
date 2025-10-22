"""
Test message extraction utility from agent results.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from creativity_agent.nodes.base_node import BaseNode
from creativity_agent.models import SharedState, ExecutionState
from strands.multiagent import MultiAgentResult
from unittest.mock import Mock, MagicMock, AsyncMock


class ConcreteTestNode(BaseNode):
    """Concrete implementation of BaseNode for testing."""
    
    async def invoke_async(self, task, invocation_state=None, **kwargs):
        """Dummy implementation for testing."""
        state = ExecutionState(
            original_prompt="",
            iteration=0,
            run_id="test",
            run_dir="."
        )
        return self.create_result(message="test", state=state)


def test_extract_message_content_with_dict_content():
    """Test extracting content from agent result with dict-style message."""
    
    # Create a mock BaseNode instance
    shared_state = Mock(spec=SharedState)
    node = ConcreteTestNode(node_name="test", shared_state=shared_state, outputs_dir=Path("."))
    
    # Create mock agent result with dict-style content
    agent_result = Mock()
    agent_result.message = {
        'content': [
            {'text': 'This is the first part. '},
            {'text': 'This is the second part.'}
        ]
    }
    
    result = node.extract_message_content(agent_result)
    assert result == 'This is the first part. This is the second part.'
    print("✓ Dict-style content extraction works")


def test_extract_message_content_with_object_content():
    """Test extracting content from agent result with object-style message."""
    
    shared_state = Mock(spec=SharedState)
    node = ConcreteTestNode(node_name="test", shared_state=shared_state, outputs_dir=Path("."))
    
    # Create mock content block with .text attribute
    content_block = Mock()
    content_block.text = 'This is from an object. '
    
    agent_result = Mock()
    agent_result.message = Mock()
    agent_result.message.content = [content_block, {'text': 'And this from dict.'}]
    
    result = node.extract_message_content(agent_result)
    assert 'This is from an object.' in result
    assert 'And this from dict.' in result
    print("✓ Object-style content extraction works")


def test_extract_message_content_with_fallback():
    """Test fallback to string conversion when no structured content."""
    
    shared_state = Mock(spec=SharedState)
    node = ConcreteTestNode(node_name="test", shared_state=shared_state, outputs_dir=Path("."))
    
    # Create agent result without proper message structure
    agent_result = "Just a string result"
    
    result = node.extract_message_content(agent_result)
    assert result == "Just a string result"
    print("✓ Fallback string conversion works")


def test_extract_message_content_with_empty_message():
    """Test extraction when message is empty or None."""
    
    shared_state = Mock(spec=SharedState)
    node = ConcreteTestNode(node_name="test", shared_state=shared_state, outputs_dir=Path("."))
    
    # Create agent result with empty message
    agent_result = Mock()
    agent_result.message = None
    
    result = node.extract_message_content(agent_result)
    # Should fall back to str(agent_result)
    assert isinstance(result, str)
    print("✓ Empty message handling works")


if __name__ == "__main__":
    try:
        test_extract_message_content_with_dict_content()
        test_extract_message_content_with_object_content()
        test_extract_message_content_with_fallback()
        test_extract_message_content_with_empty_message()
        print("\n✓ All message extraction tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

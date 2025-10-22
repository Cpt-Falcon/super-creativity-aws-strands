"""
Comprehensive tests for all node types in the creativity flow.

Tests include:
- BaseNode functionality
- ChaosGeneratorNode
- CreativeAgentNode
- RefinementAgentNode
- JudgeNode
- IterationControllerNode
"""

import pytest
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from creativity_agent.nodes.base_node import BaseNode
from creativity_agent.nodes.chaos_generator_node import ChaosGeneratorNode
from creativity_agent.nodes.creative_agent_node import CreativeAgentNode
from creativity_agent.nodes.refinement_agent_node import RefinementAgentNode
from creativity_agent.nodes.judge_node import JudgeNode
from creativity_agent.nodes.iteration_controller_node import IterationControllerNode
from strands.multiagent.base import Status


class TestBaseNode:
    """Tests for BaseNode functionality."""
    
    def test_base_node_initialization(self):
        """Test BaseNode can be instantiated with proper configuration."""
        with TemporaryDirectory() as tmpdir:
            prompts_dir = Path(tmpdir) / "prompts"
            prompts_dir.mkdir()
            outputs_dir = Path(tmpdir) / "outputs"
            outputs_dir.mkdir()
            
            # Create a concrete implementation for testing
            class TestNode(BaseNode):
                def get_required_state_keys(self):
                    return ['test_key']
                
                async def invoke_async(self, task, invocation_state=None, **kwargs):
                    pass
            
            node = TestNode(
                node_name="test_node",
                prompts_dir=prompts_dir,
                outputs_dir=outputs_dir
            )
            
            assert node.name == "test_node"
            assert node.prompts_dir == prompts_dir
            assert node.outputs_dir == outputs_dir
    
    def test_load_prompt(self):
        """Test prompt loading from file."""
        with TemporaryDirectory() as tmpdir:
            prompts_dir = Path(tmpdir) / "prompts"
            prompts_dir.mkdir()
            
            # Create a test prompt file
            prompt_content = "Test prompt content"
            prompt_file = prompts_dir / "test_prompt.txt"
            prompt_file.write_text(prompt_content, encoding='utf-8')
            
            class TestNode(BaseNode):
                def get_required_state_keys(self):
                    return []
                async def invoke_async(self, task, invocation_state=None, **kwargs):
                    pass
            
            node = TestNode(node_name="test", prompts_dir=prompts_dir)
            loaded = node.load_prompt("test_prompt")
            
            assert loaded == prompt_content
    
    def test_load_prompt_missing_file(self):
        """Test prompt loading returns empty string for missing file."""
        with TemporaryDirectory() as tmpdir:
            prompts_dir = Path(tmpdir) / "prompts"
            prompts_dir.mkdir()
            
            class TestNode(BaseNode):
                def get_required_state_keys(self):
                    return []
                async def invoke_async(self, task, invocation_state=None, **kwargs):
                    pass
            
            node = TestNode(node_name="test", prompts_dir=prompts_dir)
            loaded = node.load_prompt("nonexistent")
            
            assert loaded == ""
    
    def test_state_extraction(self):
        """Test safe state value extraction."""
        class TestNode(BaseNode):
            def get_required_state_keys(self):
                return []
            async def invoke_async(self, task, invocation_state=None, **kwargs):
                pass
        
        node = TestNode(node_name="test")
        state = {"key1": "value1", "key2": 42}
        
        assert node.get_state_value(state, "key1") == "value1"
        assert node.get_state_value(state, "key2") == 42
        assert node.get_state_value(state, "missing", "default") == "default"
    
    def test_state_update(self):
        """Test state update functionality."""
        class TestNode(BaseNode):
            def get_required_state_keys(self):
                return []
            async def invoke_async(self, task, invocation_state=None, **kwargs):
                pass
        
        node = TestNode(node_name="test")
        state = {"key1": "value1"}
        updates = {"key2": "value2", "key1": "updated"}
        
        updated_state = node.update_state(state, updates)
        
        assert updated_state["key1"] == "updated"
        assert updated_state["key2"] == "value2"
    
    def test_validate_state_success(self):
        """Test state validation with all required keys present."""
        class TestNode(BaseNode):
            def get_required_state_keys(self):
                return ['key1', 'key2']
            async def invoke_async(self, task, invocation_state=None, **kwargs):
                pass
        
        node = TestNode(node_name="test")
        state = {"key1": "value1", "key2": "value2", "key3": "extra"}
        
        is_valid, error = node.validate_state(state)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_state_failure(self):
        """Test state validation fails with missing required keys."""
        class TestNode(BaseNode):
            def get_required_state_keys(self):
                return ['key1', 'key2']
            async def invoke_async(self, task, invocation_state=None, **kwargs):
                pass
        
        node = TestNode(node_name="test")
        state = {"key1": "value1"}  # Missing key2
        
        is_valid, error = node.validate_state(state)
        
        assert is_valid is False
        assert "key2" in error


class TestChaosGeneratorNode:
    """Tests for ChaosGeneratorNode."""
    
    @pytest.mark.asyncio
    async def test_chaos_generator_initialization(self):
        """Test ChaosGeneratorNode initialization."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            
            mock_chaos_gen = Mock()
            
            node = ChaosGeneratorNode(
                chaos_generator=mock_chaos_gen,
                chaos_seeds_per_iteration=5,
                outputs_dir=outputs_dir
            )
            
            assert node.name == "chaos_generator"
            assert node.chaos_seeds_per_iteration == 5
    
    @pytest.mark.asyncio
    async def test_chaos_generator_required_state_keys(self):
        """Test required state keys."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            mock_chaos_gen = Mock()
            
            node = ChaosGeneratorNode(
                chaos_generator=mock_chaos_gen,
                chaos_seeds_per_iteration=5,
                outputs_dir=outputs_dir
            )
            
            required = node.get_required_state_keys()
            assert 'iteration' in required
            assert 'original_prompt' in required
    
    @pytest.mark.asyncio
    async def test_chaos_generator_invoke_success(self):
        """Test successful chaos generation."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            
            mock_chaos_input = Mock()
            mock_chaos_input.get_chaos_summary.return_value = "Chaos summary"
            
            mock_chaos_gen = Mock()
            mock_chaos_gen.generate_chaos_input.return_value = mock_chaos_input
            
            node = ChaosGeneratorNode(
                chaos_generator=mock_chaos_gen,
                chaos_seeds_per_iteration=5,
                outputs_dir=outputs_dir
            )
            
            state = {
                'iteration': 0,
                'original_prompt': 'Test prompt'
            }
            
            result = await node.invoke_async(
                task='Test task',
                invocation_state=state
            )
            
            assert result.status == Status.COMPLETED
            assert result.execution_count == 1
            # Verify output file was created
            output_files = list(outputs_dir.glob("chaos_input_iteration_*.txt"))
            assert len(output_files) == 1
    
    @pytest.mark.asyncio
    async def test_chaos_generator_missing_state(self):
        """Test error handling for missing state."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            mock_chaos_gen = Mock()
            
            node = ChaosGeneratorNode(
                chaos_generator=mock_chaos_gen,
                chaos_seeds_per_iteration=5,
                outputs_dir=outputs_dir
            )
            
            state = {}  # Missing required keys
            
            result = await node.invoke_async(
                task='Test task',
                invocation_state=state
            )
            
            assert result.status == Status.FAILED


class TestIterationControllerNode:
    """Tests for IterationControllerNode."""
    
    @pytest.mark.asyncio
    async def test_iteration_controller_initialization(self):
        """Test IterationControllerNode initialization."""
        with TemporaryDirectory() as tmpdir:
            node = IterationControllerNode(
                max_iterations=5,
                outputs_dir=Path(tmpdir)
            )
            
            assert node.name == "iteration_controller"
            assert node.max_iterations == 5
    
    @pytest.mark.asyncio
    async def test_iteration_controller_continue(self):
        """Test iteration controller continues when below max."""
        with TemporaryDirectory() as tmpdir:
            node = IterationControllerNode(
                max_iterations=5,
                outputs_dir=Path(tmpdir)
            )
            
            state = {'iteration': 0}
            
            result = await node.invoke_async(
                task='Test',
                invocation_state=state
            )
            
            assert result.status == Status.COMPLETED
            assert result.execution_count == 1
    
    @pytest.mark.asyncio
    async def test_iteration_controller_stop(self):
        """Test iteration controller stops at max iterations."""
        with TemporaryDirectory() as tmpdir:
            node = IterationControllerNode(
                max_iterations=3,
                outputs_dir=Path(tmpdir)
            )
            
            state = {'iteration': 2}  # Already at iteration 2, will be 3 after increment
            
            result = await node.invoke_async(
                task='Test',
                invocation_state=state
            )
            
            assert result.status == Status.COMPLETED
            assert result.execution_count == 1
    
    @pytest.mark.asyncio
    async def test_iteration_controller_required_state(self):
        """Test required state keys."""
        with TemporaryDirectory() as tmpdir:
            node = IterationControllerNode(max_iterations=5, outputs_dir=Path(tmpdir))
            
            required = node.get_required_state_keys()
            assert 'iteration' in required


class TestCreativeAgentNode:
    """Tests for CreativeAgentNode."""
    
    @pytest.mark.asyncio
    async def test_creative_agent_initialization(self):
        """Test CreativeAgentNode initialization."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            mock_agent = Mock()
            
            node = CreativeAgentNode(
                agent=mock_agent,
                node_name="creative_test",
                outputs_dir=outputs_dir
            )
            
            assert node.name == "creative_test"
            assert node.agent == mock_agent
    
    @pytest.mark.asyncio
    async def test_creative_agent_invoke_success(self):
        """Test successful creative agent invocation."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            
            # Mock the agent result
            mock_content_block = {"text": "Creative idea output"}
            mock_message = {"content": [mock_content_block]}
            mock_agent_result = Mock()
            mock_agent_result.message = mock_message
            
            mock_agent = Mock()
            mock_agent.invoke_async = AsyncMock(return_value=mock_agent_result)
            
            node = CreativeAgentNode(
                agent=mock_agent,
                node_name="creative_test",
                outputs_dir=outputs_dir
            )
            
            state = {
                'iteration': 0,
                'original_prompt': 'Test prompt',
                'chaos_context': 'Some chaos',
                'memory_context': 'Some memory'
            }
            
            result = await node.invoke_async(
                task='Test task',
                invocation_state=state
            )
            
            assert result.status == Status.COMPLETED
            assert result.execution_count == 1
            # Verify output file was created
            output_files = list(outputs_dir.glob("creative_test_iteration_*.txt"))
            assert len(output_files) == 1
    
    @pytest.mark.asyncio
    async def test_creative_agent_with_memory_manager(self):
        """Test creative agent extracts concepts to memory."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            
            mock_content_block = {"text": "## Idea 1\nThis is a great idea"}
            mock_message = {"content": [mock_content_block]}
            mock_agent_result = Mock()
            mock_agent_result.message = mock_message
            
            mock_agent = Mock()
            mock_agent.invoke_async = AsyncMock(return_value=mock_agent_result)
            
            mock_memory = Mock()
            mock_memory.extract_concepts_from_text = Mock()
            mock_memory.save_memory = Mock()
            
            node = CreativeAgentNode(
                agent=mock_agent,
                node_name="creative_test",
                outputs_dir=outputs_dir,
                memory_manager=mock_memory
            )
            
            state = {
                'iteration': 0,
                'original_prompt': 'Test prompt',
                'chaos_context': '',
                'memory_context': ''
            }
            
            result = await node.invoke_async(
                task='Test',
                invocation_state=state
            )
            
            assert result.status == Status.COMPLETED
            mock_memory.extract_concepts_from_text.assert_called_once()
            mock_memory.save_memory.assert_called_once()


class TestRefinementAgentNode:
    """Tests for RefinementAgentNode."""
    
    @pytest.mark.asyncio
    async def test_refinement_agent_initialization(self):
        """Test RefinementAgentNode initialization."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            mock_agent = Mock()
            
            node = RefinementAgentNode(
                agent=mock_agent,
                node_name="refinement_test",
                outputs_dir=outputs_dir
            )
            
            assert node.name == "refinement_test"
            assert node.agent == mock_agent
    
    @pytest.mark.asyncio
    async def test_refinement_agent_invoke_success(self):
        """Test successful refinement agent invocation."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            
            # Mock the agent result
            mock_content_block = {"text": "Refined ideas"}
            mock_message = {"content": [mock_content_block]}
            mock_agent_result = Mock()
            mock_agent_result.message = mock_message
            
            mock_agent = Mock()
            mock_agent.invoke_async = AsyncMock(return_value=mock_agent_result)
            
            node = RefinementAgentNode(
                agent=mock_agent,
                node_name="refinement_test",
                outputs_dir=outputs_dir
            )
            
            state = {
                'iteration': 0,
                'original_prompt': 'Test prompt',
                'memory_context': 'Some memory'
            }
            
            result = await node.invoke_async(
                task='Creative output',
                invocation_state=state
            )
            
            assert result.status == Status.COMPLETED
            assert result.execution_count == 1
            # Verify output file was created
            output_files = list(outputs_dir.glob("refinement_test_iteration_*.txt"))
            assert len(output_files) == 1
    
    @pytest.mark.asyncio
    async def test_refinement_agent_updates_state(self):
        """Test refinement agent updates state with output."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            
            mock_content_block = {"text": "Refined content"}
            mock_message = {"content": [mock_content_block]}
            mock_agent_result = Mock()
            mock_agent_result.message = mock_message
            
            mock_agent = Mock()
            mock_agent.invoke_async = AsyncMock(return_value=mock_agent_result)
            
            node = RefinementAgentNode(
                agent=mock_agent,
                node_name="refinement_test",
                outputs_dir=outputs_dir
            )
            
            state = {
                'iteration': 0,
                'original_prompt': 'Test prompt',
                'memory_context': ''
            }
            
            result = await node.invoke_async(
                task='Input',
                invocation_state=state
            )
            
            assert result.status == Status.COMPLETED
            assert result.execution_count == 1


class TestJudgeNode:
    """Tests for JudgeNode."""
    
    @pytest.mark.asyncio
    async def test_judge_node_initialization(self):
        """Test JudgeNode initialization."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            mock_judge = Mock()
            
            node = JudgeNode(
                judge=mock_judge,
                observability=None,
                outputs_dir=outputs_dir
            )
            
            assert node.name == "judge"
            assert node.judge == mock_judge
    
    @pytest.mark.asyncio
    async def test_judge_node_required_state(self):
        """Test required state keys."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            mock_judge = Mock()
            
            node = JudgeNode(
                judge=mock_judge,
                observability=None,
                outputs_dir=outputs_dir
            )
            
            required = node.get_required_state_keys()
            assert 'iteration' in required
    
    @pytest.mark.asyncio
    async def test_judge_node_extract_ideas(self):
        """Test idea extraction from content."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            mock_judge = Mock()
            
            node = JudgeNode(
                judge=mock_judge,
                observability=None,
                outputs_dir=outputs_dir
            )
            
            # Test numbered ideas
            content = "1. First idea\n2. Second idea\n3. Third idea"
            ideas = node._extract_ideas_from_content(content)
            
            assert len(ideas) == 3
            assert "First idea" in ideas[0]
    
    @pytest.mark.asyncio
    async def test_judge_node_invoke_success(self):
        """Test successful judge invocation."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            
            # Mock judge evaluations
            from creativity_agent.models.observability_models import JudgeEvaluation
            
            mock_eval = JudgeEvaluation(
                idea_id="test_1",
                idea_name="Test Idea",
                originality_score=8.0,
                feasibility_score=7.0,
                impact_score=9.0,
                substance_score=8.0,
                overall_quality_score=8.0,
                accepted=True,
                rejection_reasons=[],
                key_points=["Good", "Novel"],
                model_id="test-model",
                temperature=0.7,
                iteration=0,
                evaluation_timestamp=__import__('datetime').datetime.now(),
                judge_model="judge-model"
            )
            
            mock_judge = Mock()
            mock_judge.batch_evaluate.return_value = [mock_eval]
            
            node = JudgeNode(
                judge=mock_judge,
                observability=None,
                outputs_dir=outputs_dir
            )
            
            state = {
                'iteration': 0,
                'refinement_output': '1. Test idea\n2. Another idea',
                'step_model_id': 'test-model',
                'step_temp': 0.7
            }
            
            result = await node.invoke_async(
                task='Test',
                invocation_state=state
            )
            
            assert result.status == Status.COMPLETED
            # Verify judge output file was created
            output_files = list(outputs_dir.glob("judge_evaluations_iteration_*.txt"))
            assert len(output_files) == 1
    
    @pytest.mark.asyncio
    async def test_judge_node_missing_state(self):
        """Test error handling for missing required state."""
        with TemporaryDirectory() as tmpdir:
            outputs_dir = Path(tmpdir)
            mock_judge = Mock()
            
            node = JudgeNode(
                judge=mock_judge,
                observability=None,
                outputs_dir=outputs_dir
            )
            
            state = {}  # Missing 'iteration'
            
            result = await node.invoke_async(
                task='Test',
                invocation_state=state
            )
            
            assert result.status == Status.FAILED


# Test execution helpers
def run_async_test(coro):
    """Helper to run async tests."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

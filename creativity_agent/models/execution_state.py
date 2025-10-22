"""
Execution State Model - Typed state for all graph nodes.

Provides a Pydantic-based state object that:
1. Ensures type safety and IDE autocompletion
2. Validates required fields at each step
3. Maintains immutability where needed
4. Passes original prompt and metadata through the graph
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime


class ExecutionState(BaseModel):
    """
    Typed execution state passed through all graph nodes.
    
    This replaces duck typing with proper type checking and IDE support.
    All nodes receive and return this state with updated fields.
    """
    
    # Core execution context (set once, passed through all nodes)
    original_prompt: str = Field(
        description="The original user prompt, preserved throughout execution"
    )
    iteration: int = Field(
        default=0,
        description="Current iteration number (0-indexed)"
    )
    run_id: str = Field(
        description="Unique run identifier for this graph execution"
    )
    run_dir: str = Field(
        description="Output directory for this run"
    )
    start_time: Optional[str] = Field(
        default=None,
        description="ISO format timestamp when execution started"
    )
    
    # Iteration controller state
    should_continue: bool = Field(
        default=True,
        description="Whether to continue iterating"
    )
    is_finished: bool = Field(
        default=False,
        description="Whether all iterations are complete"
    )
    max_iterations: int = Field(
        default=1,
        description="Total number of iterations to run"
    )
    
    # Chaos generator state
    chaos_context: Optional[str] = Field(
        default=None,
        description="Chaos context/prompt built from tangential concepts"
    )
    chaos_seeds: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="List of chaos seeds with concept, context, relevance"
    )
    chaos_seeds_count: int = Field(
        default=0,
        description="Number of chaos seeds generated"
    )
    
    # Creative agent state
    creative_output: Optional[str] = Field(
        default=None,
        description="Output from the creative (high-temperature) agent"
    )
    creative_model: Optional[str] = Field(
        default=None,
        description="Model key used for creative generation"
    )
    
    # Refinement agent state
    refinement_output: Optional[str] = Field(
        default=None,
        description="Output from the refinement (low-temperature) agent"
    )
    refinement_model: Optional[str] = Field(
        default=None,
        description="Model key used for refinement"
    )
    
    # Judge state
    judge_evaluations: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Judge evaluations for ideas"
    )
    idea_statistics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Statistics about evaluated ideas"
    )
    accepted_ideas_count: int = Field(
        default=0,
        description="Number of ideas accepted by judge"
    )
    
    # Deep research state
    final_research_output: Optional[str] = Field(
        default=None,
        description="Final output from deep research agent"
    )
    
    # Error tracking
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if any node failed"
    )
    success: bool = Field(
        default=True,
        description="Whether current step succeeded"
    )
    
    class Config:
        """Pydantic config for execution state."""
        arbitrary_types_allowed = True
        validate_assignment = True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for AWS Strands invocation_state.
        
        Returns:
            Dictionary representation of state
        """
        return self.model_dump(exclude_none=False)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ExecutionState':
        """
        Create ExecutionState from dictionary (AWS Strands invocation_state).
        
        Args:
            data: Dictionary with state values
            
        Returns:
            ExecutionState instance
            
        Raises:
            ValueError: If required fields are missing
        """
        try:
            return ExecutionState(**data)
        except Exception as e:
            raise ValueError(f"Failed to create ExecutionState from dict: {e}")
    
    def with_updates(self, **updates) -> 'ExecutionState':
        """
        Create a new ExecutionState with specified updates.
        
        Args:
            **updates: Fields to update
            
        Returns:
            New ExecutionState with updates applied
        """
        return self.model_copy(update=updates)


class NodeInput(BaseModel):
    """
    Type-safe input for node execution.
    
    Wraps the task input and execution state.
    """
    
    task: str = Field(
        description="Input task/prompt for this node"
    )
    state: ExecutionState = Field(
        description="Current execution state"
    )
    
    @staticmethod
    def from_strands(
        task: Any,
        invocation_state: Optional[Dict[str, Any]] = None
    ) -> 'NodeInput':
        """
        Convert AWS Strands input to NodeInput.
        
        Args:
            task: Task from Strands graph
            invocation_state: Invocation state dict from Strands
            
        Returns:
            NodeInput instance
        """
        task_str = task if isinstance(task, str) else str(task)
        state_dict = invocation_state or {}
        
        # Ensure required fields for ExecutionState
        if 'original_prompt' not in state_dict:
            state_dict['original_prompt'] = task_str
        if 'run_id' not in state_dict:
            state_dict['run_id'] = 'unknown'
        if 'run_dir' not in state_dict:
            state_dict['run_dir'] = '.'
        
        state = ExecutionState.from_dict(state_dict)
        return NodeInput(task=task_str, state=state)

"""
SharedState - Pydantic-based shared state container for graph execution.

Since AWS Strands' invocation_state is read-only and not propagated between
node executions, we use a SharedState object that is instantiated once and
passed to all nodes during initialization. This allows nodes to coordinate
and share mutable state across the graph execution.

All fields are type-safe with Pydantic validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class SharedState(BaseModel):
    """
    Shared mutable state accessible by all nodes during graph execution.
    
    This is instantiated once per graph run and passed to all nodes,
    allowing them to coordinate and track state that cannot be threaded
    through invocation_state.
    """
    
    current_iteration: int = Field(
        default=0,
        description="Current iteration number (0-indexed)"
    )
    max_iterations: int = Field(
        default=1,
        description="Maximum number of iterations"
    )
    run_id: str = Field(
        default="unknown",
        description="Unique run identifier"
    )
    run_dir: str = Field(
        default=".",
        description="Run output directory"
    )
    
    # Execution tracking
    nodes_executed: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of how many times each node has executed"
    )
    
    # Custom shared data
    custom_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom key-value store for node communication"
    )
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
        validate_assignment = True
    
    def increment_iteration(self) -> int:
        """Increment iteration and return new value."""
        if self.current_iteration < self.max_iterations:
            self.current_iteration += 1
        return self.current_iteration
    
    def get_current_iteration(self) -> int:
        """Get current iteration."""
        return self.current_iteration
    
    def set_iteration(self, iteration: int):
        """Set iteration to specific value."""
        self.current_iteration = iteration
    
    def record_node_execution(self, node_name: str):
        """Record that a node has executed."""
        if node_name not in self.nodes_executed:
            self.nodes_executed[node_name] = 0
        self.nodes_executed[node_name] += 1
    
    def get_node_execution_count(self, node_name: str) -> int:
        """Get how many times a node has executed."""
        return self.nodes_executed.get(node_name, 0)

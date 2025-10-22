"""
Strict Pydantic models for all data structures in the creativity agent system.

Eliminates duck typing and ensures type safety throughout the codebase.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from datetime import datetime
from enum import Enum


class NodeType(str, Enum):
    """Types of nodes in the graph."""
    CHAOS_GENERATOR = "chaos_generator"
    CREATIVE_AGENT = "creative_agent"
    REFINEMENT_AGENT = "refinement_agent"
    JUDGE = "judge"
    ITERATION_CONTROLLER = "iteration_controller"


class TemperatureType(str, Enum):
    """Temperature settings for agent execution."""
    HIGH = "high"  # Divergent thinking
    LOW = "low"    # Refinement/convergence


class InvocationState(BaseModel):
    """Strict type definition for graph invocation state."""
    
    iteration: int = Field(
        description="Current iteration number",
        ge=0
    )
    original_prompt: str = Field(
        description="Original user prompt/request"
    )
    
    # Chaos context for divergent thinking
    chaos_context: Optional[str] = Field(
        default="",
        description="Chaos seeds and tangential concepts"
    )
    chaos_seeds_count: int = Field(
        default=0,
        description="Number of chaos seeds generated"
    )
    
    # Memory context for tracking explored ideas
    memory_context: Optional[str] = Field(
        default="",
        description="Summary of previously explored ideas"
    )
    
    # Refinement output for judge evaluation
    refinement_output: Optional[str] = Field(
        default="",
        description="Output from refinement agent"
    )
    
    # Judge evaluation results
    idea_statistics: Optional[Dict[str, Union[int, float]]] = Field(
        default=None,
        description="Statistics from idea evaluation"
    )
    evaluations: List[Dict] = Field(
        default_factory=list,
        description="Judge evaluation results"
    )
    accepted_ideas_count: int = Field(
        default=0,
        description="Number of accepted ideas"
    )
    
    # Iteration control
    should_continue: bool = Field(
        default=True,
        description="Whether to continue iterating"
    )
    is_finished: bool = Field(
        default=False,
        description="Whether all iterations are complete"
    )
    
    # Run metadata
    run_dir: Optional[str] = Field(
        default=None,
        description="Directory for run outputs"
    )
    
    # Tracking and metadata
    step_model_id: Optional[str] = Field(
        default=None,
        description="Model ID used in current step"
    )
    step_temp: float = Field(
        default=0.7,
        description="Temperature used in current step"
    )
    
    # Status tracking
    success: bool = Field(
        default=True,
        description="Whether current step succeeded"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if step failed"
    )


class NodeOutput(BaseModel):
    """Strict output structure from node execution."""
    
    node_name: str = Field(description="Name of the node")
    node_type: NodeType = Field(description="Type of node")
    
    status: str = Field(description="Execution status (COMPLETED, FAILED, etc)")
    message: str = Field(description="Result message")
    
    execution_time: int = Field(
        description="Execution time in seconds",
        ge=0
    )
    
    state_updates: InvocationState = Field(
        description="Updated invocation state"
    )
    
    output_content: Optional[str] = Field(
        default=None,
        description="Generated content output"
    )
    
    error_details: Optional[str] = Field(
        default=None,
        description="Error details if execution failed"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this node executed"
    )


class ChaosInput(BaseModel):
    """Structured chaos generation input."""
    
    original_prompt: str = Field(description="Original user prompt")
    tangential_concepts: List[str] = Field(
        description="Tangential concepts for divergent thinking"
    )
    iteration: int = Field(description="Iteration number", ge=0)
    
    def get_chaos_summary(self) -> str:
        """Get a formatted summary of chaos input."""
        lines = [
            f"Original Request: {self.original_prompt}",
            f"Iteration: {self.iteration}",
            "\nTangential Concepts for Exploration:",
        ]
        for i, concept in enumerate(self.tangential_concepts, 1):
            lines.append(f"  {i}. {concept}")
        return "\n".join(lines)


class IdeaEvaluation(BaseModel):
    """Structured idea evaluation from judge."""
    
    idea_id: str = Field(description="Unique idea identifier")
    idea_name: str = Field(description="Name/title of idea")
    
    originality_score: float = Field(
        description="Originality score (0-10)",
        ge=0,
        le=10
    )
    feasibility_score: float = Field(
        description="Feasibility score (0-10)",
        ge=0,
        le=10
    )
    impact_score: float = Field(
        description="Impact score (0-10)",
        ge=0,
        le=10
    )
    substance_score: float = Field(
        description="Substance/detail score (0-10)",
        ge=0,
        le=10
    )
    
    overall_quality_score: float = Field(
        description="Overall quality score (0-10)",
        ge=0,
        le=10
    )
    
    accepted: bool = Field(description="Whether idea was accepted")
    rejection_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons for rejection if applicable"
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="Key points supporting the idea"
    )
    
    model_id: str = Field(description="Model that generated the idea")
    temperature: float = Field(description="Temperature used")
    iteration: int = Field(description="Iteration number", ge=0)
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Evaluation timestamp"
    )


class ExploredIdea(BaseModel):
    """Structured record of an explored idea in memory."""
    
    concept: str = Field(description="The concept or idea")
    key_points: List[str] = Field(
        default_factory=list,
        description="Key points about the idea"
    )
    iteration: int = Field(description="Iteration discovered", ge=0)
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When idea was explored"
    )
    quality_score: float = Field(
        description="Quality score if evaluated",
        ge=0,
        le=10,
        default=5.0
    )


class RejectedIdea(BaseModel):
    """Structured record of a rejected idea."""
    
    concept: str = Field(description="The rejected concept")
    reason: str = Field(description="Why it was rejected")
    iteration: int = Field(description="Iteration rejected", ge=0)
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When idea was rejected"
    )


class IterationMetrics(BaseModel):
    """Metrics for a single iteration."""
    
    iteration: int = Field(description="Iteration number", ge=0)
    
    ideas_generated: int = Field(
        default=0,
        description="Number of ideas generated",
        ge=0
    )
    ideas_evaluated: int = Field(
        default=0,
        description="Number of ideas evaluated",
        ge=0
    )
    ideas_accepted: int = Field(
        default=0,
        description="Number of ideas accepted",
        ge=0
    )
    ideas_rejected: int = Field(
        default=0,
        description="Number of ideas rejected",
        ge=0
    )
    
    execution_time_seconds: int = Field(
        default=0,
        description="Total execution time",
        ge=0
    )
    
    chaos_seeds_generated: int = Field(
        default=0,
        description="Number of chaos seeds",
        ge=0
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When iteration executed"
    )


class RunSummary(BaseModel):
    """Summary of a complete run."""
    
    run_id: str = Field(description="Unique run identifier")
    original_prompt: str = Field(description="Original user prompt")
    
    total_iterations: int = Field(description="Total iterations completed", ge=0)
    total_ideas_explored: int = Field(default=0, ge=0)
    total_ideas_evaluated: int = Field(default=0, ge=0)
    total_accepted: int = Field(default=0, ge=0)
    total_rejected: int = Field(default=0, ge=0)
    
    iteration_metrics: List[IterationMetrics] = Field(
        default_factory=list,
        description="Per-iteration metrics"
    )
    
    success: bool = Field(description="Whether run succeeded")
    error_message: Optional[str] = Field(default=None)
    
    start_time: datetime = Field(description="Run start time")
    end_time: Optional[datetime] = Field(default=None)
    total_duration_seconds: int = Field(default=0, ge=0)
    
    output_file_path: Optional[str] = Field(default=None)


class NodeConfiguration(BaseModel):
    """Configuration for a specific node."""
    
    node_name: str = Field(description="Node identifier")
    node_type: NodeType = Field(description="Type of node")
    
    enabled: bool = Field(default=True)
    
    # Optional parameters by type
    temperature: Optional[float] = Field(
        default=None,
        ge=0,
        le=2,
        description="Temperature for agent execution"
    )
    model_id: Optional[str] = Field(default=None)
    max_iterations: Optional[int] = Field(default=None, ge=1)
    timeout_seconds: Optional[int] = Field(default=None, ge=1)
    
    # Custom parameters
    custom_params: Dict[str, Union[str, int, float, bool]] = Field(
        default_factory=dict,
        description="Additional node-specific parameters"
    )


__all__ = [
    'NodeType',
    'TemperatureType',
    'InvocationState',
    'NodeOutput',
    'ChaosInput',
    'IdeaEvaluation',
    'ExploredIdea',
    'RejectedIdea',
    'IterationMetrics',
    'RunSummary',
    'NodeConfiguration',
]

"""
Observability and metrics tracking models for comprehensive monitoring.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ModelType(str, Enum):
    """Supported model types for tracking."""
    CLAUDE_SONNET_4 = "claude-sonnet-4"
    NOVA_PRO = "nova-pro"
    UNKNOWN = "unknown"


class TemperatureType(str, Enum):
    """Temperature settings for model invocations."""
    HIGH = "high"
    LOW = "low"


class StepType(str, Enum):
    """Agent step types in the flow."""
    CREATIVE = "creative"
    REFINEMENT = "refinement"
    JUDGE = "judge"


class IdeaStatistics(BaseModel):
    """Statistics about generated ideas."""
    total_ideas: int = Field(description="Total number of ideas generated")
    unique_ideas: int = Field(description="Number of unique ideas (after deduplication)")
    duplicate_ideas: int = Field(description="Number of duplicate ideas detected")
    accepted_ideas: int = Field(description="Number of ideas accepted by judge")
    rejected_ideas: int = Field(description="Number of ideas rejected by judge")
    ideas_above_8: int = Field(default=0, description="Ideas with quality score >= 8.0")
    ideas_above_5: int = Field(default=0, description="Ideas with quality score >= 5.0")
    median_quality_score: Optional[float] = Field(default=None, description="Median quality score across all ideas")
    mean_quality_score: Optional[float] = Field(default=None, description="Mean quality score across all ideas")


class TokenUtilization(BaseModel):
    """Token usage tracking for model invocations."""
    input_tokens: int = Field(description="Number of input tokens consumed")
    output_tokens: int = Field(description="Number of output tokens generated")
    total_tokens: int = Field(description="Total tokens (input + output)")
    estimated_cost_usd: Optional[float] = Field(default=None, description="Estimated cost in USD")


class StepMetrics(BaseModel):
    """Metrics for a single agent step execution."""
    step_id: str = Field(description="Step identifier (e.g., 'ah', 'al', 'bh', 'bl')")
    model_id: str = Field(description="AWS Bedrock model ID used")
    model_type: ModelType = Field(description="Model type for aggregation")
    temperature: float = Field(description="Temperature setting used")
    temperature_type: TemperatureType = Field(description="Temperature type (high/low)")
    step_type: StepType = Field(description="Type of step (creative/refinement/judge)")
    prompt_file: str = Field(description="Prompt file used for this step")
    
    duration_seconds: float = Field(description="Execution duration in seconds")
    token_usage: TokenUtilization = Field(description="Token utilization for this step")
    
    ideas_generated: int = Field(default=0, description="Number of ideas generated in this step")
    web_searches: int = Field(default=0, description="Number of web searches performed")
    cache_hits: int = Field(default=0, description="Number of web cache hits")
    cache_misses: int = Field(default=0, description="Number of web cache misses")
    
    error: Optional[str] = Field(default=None, description="Error message if step failed")
    success: bool = Field(default=True, description="Whether step completed successfully")


class IterationMetrics(BaseModel):
    """Metrics for a complete iteration through the agent flow."""
    iteration_number: int = Field(description="Iteration number (0-indexed)")
    steps: List[StepMetrics] = Field(description="Metrics for each step in iteration")
    
    total_duration_seconds: float = Field(description="Total duration for iteration")
    total_ideas_generated: int = Field(description="Total ideas generated in iteration")
    chaos_seeds_used: int = Field(description="Number of chaos seeds used")
    
    idea_statistics: IdeaStatistics = Field(description="Aggregated idea statistics")
    total_token_usage: TokenUtilization = Field(description="Total token usage for iteration")


class RunMetrics(BaseModel):
    """Complete metrics for an entire run (all iterations)."""
    run_id: str = Field(description="Unique run identifier (timestamp-based)")
    run_timestamp: datetime = Field(description="Start time of the run")
    
    original_prompt: str = Field(description="Original user prompt")
    config_iterations: int = Field(description="Number of iterations configured")
    chaos_seeds_per_iteration: int = Field(description="Chaos seeds per iteration")
    semantic_backend: str = Field(description="Semantic backend used (auto/gensim/sentence-transformers/simple)")
    
    iterations: List[IterationMetrics] = Field(description="Metrics for each iteration")
    
    total_duration_seconds: float = Field(description="Total run duration")
    total_ideas_generated: int = Field(description="Total ideas generated across all iterations")
    final_idea_statistics: IdeaStatistics = Field(description="Final aggregated idea statistics")
    total_token_usage: TokenUtilization = Field(description="Total token usage across all iterations")
    
    # Model-specific aggregations
    model_breakdown: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Breakdown by model type (duration, tokens, ideas)"
    )
    temperature_breakdown: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Breakdown by temperature (high/low)"
    )
    
    success: bool = Field(default=True, description="Whether run completed successfully")
    error: Optional[str] = Field(default=None, description="Error message if run failed")
    
    # ElasticSearch metadata
    index_name: str = Field(default="super-creativity", description="ElasticSearch index name")
    indexed_at: Optional[datetime] = Field(default=None, description="When this was indexed to ES")


class JudgeEvaluation(BaseModel):
    """Evaluation from the independent judge."""
    idea_id: str = Field(description="Unique identifier for the idea")
    idea_name: str = Field(description="Name/title of the idea")
    
    originality_score: float = Field(description="Originality score (0-10)")
    feasibility_score: float = Field(description="Technical feasibility score (0-10)")
    impact_score: float = Field(description="Impact potential score (0-10)")
    substance_score: float = Field(description="Substance/detail score (0-10)")
    
    overall_quality_score: float = Field(description="Average of all criteria scores")
    
    accepted: bool = Field(description="Whether idea was accepted (>= 5.0)")
    rejection_reasons: List[str] = Field(default_factory=list, description="Reasons for rejection if applicable")
    key_points: List[str] = Field(default_factory=list, description="Key points extracted from idea")
    
    model_id: str = Field(description="Model that generated this idea")
    temperature: float = Field(description="Temperature used when generating idea")
    iteration: int = Field(description="Iteration in which idea was generated")
    
    evaluation_timestamp: datetime = Field(description="When this evaluation was performed")
    judge_model: str = Field(description="Judge model used for evaluation")

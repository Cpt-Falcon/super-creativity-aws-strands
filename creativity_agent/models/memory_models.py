"""
Pydantic models for tracking idea memory and exploration history.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ExploredIdea(BaseModel):
    """Represents an idea that has been explored and refined."""
    
    concept: str = Field(description="Core concept or theme of the idea")
    key_points: List[str] = Field(
        description="Key points or aspects that were explored",
        default_factory=list
    )
    iteration: int = Field(description="Iteration number when this was explored")
    timestamp: datetime = Field(
        description="When this idea was explored",
        default_factory=datetime.now
    )
    quality_score: Optional[float] = Field(
        description="Quality/feasibility score if assessed (0-1)",
        default=None
    )


class RejectedIdea(BaseModel):
    """Represents an idea that was rejected and should not be regenerated."""
    
    concept: str = Field(description="Core concept that was rejected")
    reason: str = Field(description="Why this idea was rejected")
    iteration: int = Field(description="Iteration number when this was rejected")
    timestamp: datetime = Field(
        description="When this idea was rejected",
        default_factory=datetime.now
    )


class IdeaMemory(BaseModel):
    """
    Memory system for tracking explored and rejected ideas across iterations.
    """
    
    explored_ideas: List[ExploredIdea] = Field(
        description="List of ideas that have been explored",
        default_factory=list
    )
    rejected_ideas: List[RejectedIdea] = Field(
        description="List of ideas that have been rejected",
        default_factory=list
    )
    
    def add_explored_idea(
        self, 
        concept: str, 
        key_points: List[str], 
        iteration: int,
        quality_score: Optional[float] = None
    ) -> None:
        """Add a new explored idea to memory."""
        idea = ExploredIdea(
            concept=concept,
            key_points=key_points,
            iteration=iteration,
            quality_score=quality_score
        )
        self.explored_ideas.append(idea)
    
    def add_rejected_idea(
        self,
        concept: str,
        reason: str,
        iteration: int
    ) -> None:
        """Add a new rejected idea to memory."""
        idea = RejectedIdea(
            concept=concept,
            reason=reason,
            iteration=iteration
        )
        self.rejected_ideas.append(idea)
    
    def get_memory_summary(self) -> str:
        """
        Generate a formatted summary of memory for prompt injection.
        Returns a string that can be prepended to agent prompts.
        """
        lines = []
        
        if self.explored_ideas:
            lines.append("PREVIOUSLY EXPLORED IDEAS (do not regenerate these exact concepts):")
            for idea in self.explored_ideas:
                lines.append(f"- {idea.concept}")
                if idea.key_points:
                    for point in idea.key_points[:3]:  # Limit to top 3 points
                        lines.append(f"  • {point}")
            lines.append("")
        
        if self.rejected_ideas:
            lines.append("REJECTED IDEAS (avoid these directions entirely):")
            for idea in self.rejected_ideas:
                lines.append(f"- {idea.concept}: {idea.reason}")
            lines.append("")
        
        return "\n".join(lines) if lines else ""
    
    def get_recent_concepts(self, limit: int = 10) -> List[str]:
        """Get the most recent explored concepts."""
        sorted_ideas = sorted(
            self.explored_ideas,
            key=lambda x: x.timestamp,
            reverse=True
        )
        return [idea.concept for idea in sorted_ideas[:limit]]

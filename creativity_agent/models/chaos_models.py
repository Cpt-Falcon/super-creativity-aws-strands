"""
Pydantic models for the chaos generator system.
"""

from pydantic import BaseModel, Field
from typing import List


class TangentialConcept(BaseModel):
    """Represents a tangential concept discovered through chaos exploration."""
    
    term: str = Field(description="The tangential term or concept")
    context: str = Field(description="Brief context from web search")
    relevance_note: str = Field(
        description="How this tangent might relate to the original prompt"
    )


class ChaosInput(BaseModel):
    """
    Structured chaos input for divergent exploration.
    Contains tangential concepts that can inspire creative divergence.
    """
    
    original_prompt: str = Field(description="The original user prompt")
    random_seeds: List[str] = Field(
        description="Random tangential words generated for exploration",
        default_factory=list
    )
    tangential_concepts: List[TangentialConcept] = Field(
        description="Researched tangential concepts from web searches",
        default_factory=list
    )
    
    def get_chaos_summary(self) -> str:
        """
        Generate a formatted summary of chaos input for prompt injection.
        Returns a string that can be prepended to creative agent prompts.
        """
        if not self.tangential_concepts:
            # Still provide seeds even if research failed
            if self.random_seeds:
                return (
                    "DIVERGENT EXPLORATION SEEDS (tangential words for inspiration):\n"
                    f"• {', '.join(self.random_seeds)}\n\n"
                    "Consider how these tangential concepts might inspire unexpected creative directions.\n"
                )
            return ""
        
        lines = [
            "DIVERGENT EXPLORATION SEEDS (use these to inspire unexpected creative directions):",
            ""
        ]
        
        for concept in self.tangential_concepts:
            lines.append(f"• {concept.term}")
            lines.append(f"  Context: {concept.context}")
            lines.append(f"  Potential connection: {concept.relevance_note}")
            lines.append("")
        
        return "\n".join(lines)

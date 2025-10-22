"""
Utility for building enhanced prompts with memory and chaos context.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Builds enhanced prompts by injecting memory and chaos context.
    Handles formatting and organization of context for optimal agent performance.
    """
    
    @staticmethod
    def build_creative_prompt(
        base_prompt: str,
        original_prompt: str,
        content: str,
        memory_context: Optional[str] = None,
        chaos_context: Optional[str] = None
    ) -> str:
        """
        Build enhanced creative agent prompt with memory and chaos context.
        
        Args:
            base_prompt: The base prompt template
            original_prompt: User's original request
            content: Previous iteration content
            memory_context: Formatted memory summary
            chaos_context: Formatted chaos input
            
        Returns:
            Complete formatted prompt with all context
        """
        sections = []
        
        # Add chaos context first (for inspiration)
        if chaos_context:
            sections.append("=" * 80)
            sections.append(chaos_context)
            sections.append("=" * 80)
            sections.append("")
        
        # Add memory context (for constraints)
        if memory_context:
            sections.append("=" * 80)
            sections.append(memory_context)
            sections.append("=" * 80)
            sections.append("")
        
        # Add base prompt with filled template
        base_filled = base_prompt.format(
            original_prompt=original_prompt,
            content=content
        )
        sections.append(base_filled)
        
        return "\n".join(sections)
    
    @staticmethod
    def build_refinement_prompt(
        base_prompt: str,
        original_prompt: str,
        content: str,
        memory_context: Optional[str] = None
    ) -> str:
        """
        Build enhanced refinement agent prompt with memory context.
        
        Args:
            base_prompt: The base prompt template
            original_prompt: User's original request
            content: Creative content to refine
            memory_context: Formatted memory summary
            
        Returns:
            Complete formatted prompt with all context
        """
        sections = []
        
        # Add memory context for refinement agents too
        if memory_context:
            sections.append("=" * 80)
            sections.append(memory_context)
            sections.append("=" * 80)
            sections.append("")
        
        # Add base prompt
        base_filled = base_prompt.format(
            original_prompt=original_prompt,
            content=content
        )
        sections.append(base_filled)
        
        return "\n".join(sections)

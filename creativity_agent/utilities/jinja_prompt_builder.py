"""
Advanced prompt building system using Jinja2 templates with structured output requirements.

Replaces simple string formatting with sophisticated template-based prompts that enforce
structured JSON output, clear evaluation criteria, and validated results.
"""

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from pydantic import BaseModel, Field


class PromptConfig(BaseModel):
    """Configuration for prompt templates."""
    
    templates_dir: str = Field(description="Directory containing Jinja2 templates")
    strict_json_output: bool = Field(
        default=True,
        description="Enforce structured JSON output from LLM"
    )
    enable_validation: bool = Field(
        default=True,
        description="Enable output validation against schema"
    )


class CreativeAgentPromptContext(BaseModel):
    """Context variables for creative agent template."""
    
    original_prompt: str = Field(description="Original user request")
    content: str = Field(
        default="",
        description="Previous iteration content to build upon"
    )
    chaos_seeds: str = Field(
        default="",
        description="Chaos seeds for divergent thinking"
    )
    memory_context: str = Field(
        default="",
        description="Previously explored ideas"
    )
    iteration: int = Field(default=0, description="Current iteration number")


class JudgePromptContext(BaseModel):
    """Context variables for judge agent template."""
    
    refinement_output: Optional[str] = Field(default=None, description="Refinement output to parse and evaluate (for batch evaluation)")
    evaluation_criteria: Dict[str, str] = Field(
        description="Scoring criteria descriptions"
    )
    acceptance_threshold: float = Field(
        default=5.0,
        description="Minimum score for acceptance"
    )


class RefinementPromptContext(BaseModel):
    """Context variables for refinement agent template."""
    
    original_prompt: str = Field(description="Original user request")
    content: str = Field(description="Ideas to refine")
    previous_evaluations: List[Dict] = Field(
        default_factory=list,
        description="Previous judge evaluations"
    )
    iteration: int = Field(default=0, description="Current iteration number")


class ChaosPromptContext(BaseModel):
    """Context variables for chaos generator template."""
    
    original_prompt: str = Field(description="Original user request")
    concept_word: str = Field(description="Tangential concept to explore")
    related_concepts: List[str] = Field(
        default_factory=list,
        description="Related concepts for context"
    )


class PromptOutputSchema(BaseModel):
    """Schema definition for structured prompt output."""
    
    schema_name: str = Field(description="Name of output schema")
    required_fields: List[str] = Field(description="Required fields in JSON output")
    field_descriptions: Dict[str, str] = Field(
        description="Descriptions of each field"
    )
    format_example: Dict[str, Any] = Field(
        description="Example of correctly formatted output"
    )


class JinjaPromptBuilder:
    """Advanced prompt builder using Jinja2 templates with structured output."""
    
    def __init__(self, templates_dir: str = "prompts_templates"):
        """
        Initialize prompt builder.
        
        Args:
            templates_dir: Directory containing Jinja2 template files
        """
        self.templates_dir = Path(templates_dir)
        self.system_prompts_dir = Path(templates_dir).parent / "system_prompts"
        
        # Initialize Jinja2 environment for templates
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Initialize Jinja2 environment for system prompts
        self.system_env = Environment(
            loader=FileSystemLoader(str(self.system_prompts_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self.env.filters['json_stringify'] = self._json_stringify
        self.env.filters['format_list'] = self._format_list
        self.system_env.filters['json_stringify'] = self._json_stringify
        self.system_env.filters['format_list'] = self._format_list
        
        # Cache system prompts
        self._system_prompts_cache: Dict[str, str] = {}
    
    def get_creative_agent_system_prompt(self) -> str:
        """Get the system prompt for creative agent."""
        if 'creative' not in self._system_prompts_cache:
            try:
                template = self.system_env.get_template('creative_agent_system.j2')
                self._system_prompts_cache['creative'] = template.render()
            except Exception as e:
                import logging
                logging.warning(f"Could not load creative agent system prompt: {e}")
                self._system_prompts_cache['creative'] = ""
        return self._system_prompts_cache['creative']
    
    def get_refinement_agent_system_prompt(self) -> str:
        """Get the system prompt for refinement agent."""
        if 'refinement' not in self._system_prompts_cache:
            try:
                template = self.system_env.get_template('refinement_agent_system.j2')
                self._system_prompts_cache['refinement'] = template.render()
            except Exception as e:
                import logging
                logging.warning(f"Could not load refinement agent system prompt: {e}")
                self._system_prompts_cache['refinement'] = ""
        return self._system_prompts_cache['refinement']
    
    def get_chaos_generator_system_prompt(self) -> str:
        """Get the system prompt for chaos generator."""
        if 'chaos' not in self._system_prompts_cache:
            try:
                template = self.system_env.get_template('chaos_generator_system.j2')
                self._system_prompts_cache['chaos'] = template.render()
            except Exception as e:
                import logging
                logging.warning(f"Could not load chaos generator system prompt: {e}")
                self._system_prompts_cache['chaos'] = ""
        return self._system_prompts_cache['chaos']
    
    def get_judge_system_prompt(self) -> str:
        """Get the system prompt for judge agent."""
        if 'judge' not in self._system_prompts_cache:
            try:
                template = self.system_env.get_template('judge_system.j2')
                self._system_prompts_cache['judge'] = template.render()
            except Exception as e:
                import logging
                logging.warning(f"Could not load judge system prompt: {e}")
                self._system_prompts_cache['judge'] = ""
        return self._system_prompts_cache['judge']
    
    @staticmethod
    def _json_stringify(data: Any) -> str:
        """Filter to convert data to JSON string."""
        return json.dumps(data, indent=2)
    
    @staticmethod
    def _format_list(items: List[str], separator: str = "\n- ") -> str:
        """Filter to format list as bullet points."""
        if not items:
            return ""
        return separator + separator.join(items)
    
    def build_creative_agent_prompt(
        self,
        context: CreativeAgentPromptContext
    ) -> str:
        """
        Build creative agent prompt with structured output requirements.
        
        Args:
            context: Context variables for template rendering
            
        Returns:
            Rendered prompt string with JSON output schema
        """
        template = self.env.get_template('creative_agent.j2')
        
        context_dict = {
            **context.model_dump(),
            'output_schema': self._get_creative_output_schema(),
            'json_format_example': self._get_creative_output_example()
        }
        
        return template.render(**context_dict)
    
    def build_judge_prompt(
        self,
        context: JudgePromptContext
    ) -> str:
        """
        Build judge evaluation prompt with scoring schema.
        
        Args:
            context: Context variables for template rendering
            
        Returns:
            Rendered prompt with evaluation criteria and JSON schema
        """
        template = self.env.get_template('judge_agent.j2')
        
        context_dict = {
            **context.model_dump(),
            'output_schema': self._get_judge_output_schema(),
            'json_format_example': self._get_judge_output_example(),
            'scoring_guidelines': self._get_scoring_guidelines()
        }
        
        return template.render(**context_dict)
    
    def build_refinement_prompt(
        self,
        context: RefinementPromptContext
    ) -> str:
        """
        Build refinement agent prompt with quality assessment.
        
        Args:
            context: Context variables for template rendering
            
        Returns:
            Rendered prompt with refinement and evaluation requirements
        """
        template = self.env.get_template('refinement_agent.j2')
        
        context_dict = {
            **context.model_dump(),
            'output_schema': self._get_refinement_output_schema(),
            'json_format_example': self._get_refinement_output_example()
        }
        
        return template.render(**context_dict)
    
    def build_chaos_prompt(
        self,
        context: ChaosPromptContext
    ) -> str:
        """
        Build chaos generator prompt.
        
        Args:
            context: Context variables for template rendering
            
        Returns:
            Rendered prompt for tangential concept generation
        """
        template = self.env.get_template('chaos_generator.j2')
        
        context_dict = {
            **context.model_dump(),
            'output_schema': self._get_chaos_output_schema(),
            'json_format_example': self._get_chaos_output_example()
        }
        
        return template.render(**context_dict)
    
    @staticmethod
    def _get_creative_output_schema() -> PromptOutputSchema:
        """Get output schema for creative agent."""
        return PromptOutputSchema(
            schema_name="CreativeIdeasOutput",
            required_fields=[
                "ideas",
                "web_research_summary",
                "key_innovations",
                "implementation_considerations"
            ],
            field_descriptions={
                "ideas": "List of creative ideas with detailed explanations",
                "web_research_summary": "Summary of web research findings that inspired ideas",
                "key_innovations": "Most innovative aspects across all ideas",
                "implementation_considerations": "Technical and practical considerations"
            },
            format_example={
                "ideas": [
                    {
                        "title": "Idea name",
                        "description": "Detailed explanation",
                        "innovation_level": "High/Medium/Low",
                        "web_research_backing": "What research supports this"
                    }
                ],
                "web_research_summary": "Summary of research performed",
                "key_innovations": ["Innovation 1", "Innovation 2"],
                "implementation_considerations": ["Consideration 1", "Consideration 2"]
            }
        )
    
    @staticmethod
    def _get_creative_output_example() -> Dict[str, Any]:
        """Get example output for creative agent."""
        return {
            "ideas": [
                {
                    "title": "Hierarchical Attention with Dynamic Routing",
                    "description": "Multi-level attention mechanism that routes queries through sparse hierarchical pathways",
                    "innovation_level": "High",
                    "web_research_backing": "Based on sparse attention research and mixture of experts patterns"
                }
            ],
            "web_research_summary": "Research shows that efficient attention mechanisms are critical for scaling LLMs",
            "key_innovations": [
                "Sparse hierarchical routing",
                "Dynamic mixture selection",
                "Query-specific pathway optimization"
            ],
            "implementation_considerations": [
                "Requires new CUDA kernels for efficient routing",
                "Training stability with sparse gradients",
                "Inference optimization for production deployment"
            ]
        }
    
    @staticmethod
    def _get_judge_output_schema() -> PromptOutputSchema:
        """Get output schema for judge agent."""
        return PromptOutputSchema(
            schema_name="IdeaEvaluation",
            required_fields=[
                "idea_name",
                "originality_score",
                "feasibility_score",
                "impact_score",
                "substance_score",
                "overall_score",
                "decision",
                "key_strengths",
                "concerns",
                "verdict"
            ],
            field_descriptions={
                "idea_name": "Name of the idea being evaluated",
                "originality_score": "Score 0-10 for novelty and uniqueness",
                "feasibility_score": "Score 0-10 for technical feasibility",
                "impact_score": "Score 0-10 for potential impact",
                "substance_score": "Score 0-10 for idea substance and detail",
                "overall_score": "Average of the four scores",
                "decision": "ACCEPTED or REJECTED based on overall_score >= 5.0",
                "key_strengths": "List of key strengths",
                "concerns": "List of concerns or limitations",
                "verdict": "1-2 sentence summary of evaluation"
            },
            format_example={
                "idea_name": "Idea Title",
                "originality_score": 8,
                "feasibility_score": 7,
                "impact_score": 9,
                "substance_score": 7,
                "overall_score": 7.75,
                "decision": "ACCEPTED",
                "key_strengths": ["Strength 1", "Strength 2"],
                "concerns": ["Concern 1"],
                "verdict": "Highly innovative with clear implementation path."
            }
        )
    
    @staticmethod
    def _get_judge_output_example() -> Dict[str, Any]:
        """Get example output for judge."""
        return {
            "idea_name": "Hierarchical Attention",
            "originality_score": 8,
            "feasibility_score": 7,
            "impact_score": 9,
            "substance_score": 8,
            "overall_score": 8.0,
            "decision": "ACCEPTED",
            "key_strengths": [
                "Novel hierarchical routing mechanism",
                "Clear path to implementation",
                "Potentially 10x speedup for long sequences"
            ],
            "concerns": [
                "Requires new optimization techniques",
                "May affect model interpretability"
            ],
            "verdict": "Excellent idea with strong innovation and feasibility. Recommended for development."
        }
    
    @staticmethod
    def _get_scoring_guidelines() -> Dict[str, Dict[int, str]]:
        """Get detailed scoring guidelines for judge."""
        return {
            "originality": {
                9: "Groundbreaking, no clear precedent, revolutionary approach",
                7: "Highly innovative with unique elements, significant novelty",
                5: "Moderate novelty, combines existing ideas in new ways",
                3: "Mostly derivative with minor twists",
                1: "Common, trivial, or already well-established idea"
            },
            "feasibility": {
                9: "Proven technology exists, clear implementation path",
                7: "Feasible with current or emerging technology",
                5: "Requires some breakthroughs but plausible",
                3: "Major technical hurdles, requires breakthroughs",
                1: "Technically implausible, violates constraints"
            },
            "impact": {
                9: "Transformative, paradigm-shifting impact (>10x improvement)",
                7: "Major improvements to current state (5-10x improvement)",
                5: "Moderate improvements (2-5x improvement)",
                3: "Minor incremental gains (<2x improvement)",
                1: "Negligible impact"
            },
            "substance": {
                9: "Comprehensive with clear architecture and implementation details",
                7: "Well-developed with key components identified",
                5: "Decent outline with some technical details",
                3: "Vague concept with limited specifics",
                1: "Too abstract or underdeveloped"
            }
        }
    
    @staticmethod
    def _get_refinement_output_schema() -> PromptOutputSchema:
        """Get output schema for refinement agent."""
        return PromptOutputSchema(
            schema_name="RefinedIdeas",
            required_fields=[
                "accepted_ideas",
                "rejected_ideas",
                "synthesis",
                "top_recommendations"
            ],
            field_descriptions={
                "accepted_ideas": "Ideas scoring >= 5.0 with full evaluation",
                "rejected_ideas": "Ideas scoring < 5.0 with rejection reasons",
                "synthesis": "Analysis of how ideas work together",
                "top_recommendations": "Ranked recommendations for pursuit"
            },
            format_example={
                "accepted_ideas": [
                    {
                        "idea_name": "Name",
                        "quality_score": 7.5,
                        "originality": 8,
                        "feasibility": 7,
                        "impact": 8,
                        "substance": 7,
                        "description": "Refined description",
                        "key_points": ["Point 1", "Point 2"],
                        "next_steps": ["Step 1", "Step 2"]
                    }
                ],
                "rejected_ideas": [
                    {
                        "idea_name": "Name",
                        "quality_score": 3.5,
                        "rejection_reasons": ["Reason 1", "Reason 2"]
                    }
                ],
                "synthesis": "How ideas synergize",
                "top_recommendations": [
                    {"rank": 1, "idea": "Name", "value_prop": "Why pursue first"}
                ]
            }
        )
    
    @staticmethod
    def _get_refinement_output_example() -> Dict[str, Any]:
        """Get example output for refinement."""
        return {
            "accepted_ideas": [
                {
                    "idea_name": "Hierarchical Attention",
                    "quality_score": 8.0,
                    "originality": 8,
                    "feasibility": 7,
                    "impact": 9,
                    "substance": 8,
                    "description": "Refined description of hierarchical attention mechanism",
                    "key_points": ["Sparse routing", "Dynamic pathways", "Efficient implementation"],
                    "next_steps": ["Prototype CUDA kernel", "Benchmark on long sequences"]
                }
            ],
            "rejected_ideas": [
                {
                    "idea_name": "Vague Idea",
                    "quality_score": 3.0,
                    "rejection_reasons": ["Insufficient substance", "Unclear feasibility"]
                }
            ],
            "synthesis": "Hierarchical attention with dynamic routing provides the foundation",
            "top_recommendations": [
                {
                    "rank": 1,
                    "idea": "Hierarchical Attention",
                    "value_prop": "Highest impact and feasibility"
                }
            ]
        }
    
    @staticmethod
    def _get_chaos_output_schema() -> PromptOutputSchema:
        """Get output schema for chaos generator."""
        return PromptOutputSchema(
            schema_name="ChaosExploration",
            required_fields=[
                "concept",
                "context",
                "relevance",
                "tangential_connections"
            ],
            field_descriptions={
                "concept": "The tangential concept explored",
                "context": "Definition and background of the concept",
                "relevance": "How it relates to the original request",
                "tangential_connections": "Other concepts it could connect to"
            },
            format_example={
                "concept": "Swarm Intelligence",
                "context": "Distributed problem-solving inspired by swarms in nature",
                "relevance": "Could inspire novel LLM ensemble architectures",
                "tangential_connections": [
                    "Particle swarm optimization",
                    "Collective behavior algorithms",
                    "Emergent consensus mechanisms"
                ]
            }
        )
    
    @staticmethod
    def _get_chaos_output_example() -> Dict[str, Any]:
        """Get example output for chaos generator."""
        return {
            "concept": "Biological Neural Plasticity",
            "context": "The brain's ability to reorganize neural networks through learning",
            "relevance": "Could inspire dynamic model reorganization for domain adaptation",
            "tangential_connections": [
                "Synaptic pruning mechanisms",
                "Neural pathway strengthening",
                "Experience-based optimization"
            ]
        }


__all__ = [
    'JinjaPromptBuilder',
    'PromptConfig',
    'CreativeAgentPromptContext',
    'JudgePromptContext',
    'RefinementPromptContext',
    'ChaosPromptContext',
    'PromptOutputSchema',
    'PromptOutputSchema',
]

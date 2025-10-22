"""
Final output formatter for human-readable creativity reports.

Converts MultiAgentResult and raw content into structured, well-formatted output.
"""

from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class FinalOutputFormatter:
    """Format final creativity flow output for readability and structure."""
    
    @staticmethod
    def format_result(
        result: Any,
        original_prompt: str,
        iteration_count: int = 0,
        is_mock: bool = False
    ) -> str:
        """
        Format a MultiAgentResult or string into a readable report.
        
        Args:
            result: MultiAgentResult or string content
            original_prompt: Original user prompt
            iteration_count: Number of iterations completed
            is_mock: Whether this is mock output
            
        Returns:
            Formatted output string
        """
        # Extract actual content from result
        content = FinalOutputFormatter._extract_content(result)
        
        # Build the report
        report = FinalOutputFormatter._build_report(
            original_prompt=original_prompt,
            content=content,
            iteration_count=iteration_count,
            is_mock=is_mock
        )
        
        return report
    
    @staticmethod
    def _extract_content(result: Any) -> str:
        """Extract readable content from various result types."""
        if isinstance(result, str):
            return result
        
        # Handle MultiAgentResult-like objects
        if hasattr(result, 'results'):
            # Try to extract message content from results
            for node_name, node_result in result.results.items():
                if hasattr(node_result, 'result'):
                    if hasattr(node_result.result, 'message'):
                        message = node_result.result.message
                        if isinstance(message, dict) and 'content' in message:
                            content_list = message['content']
                            if isinstance(content_list, list) and len(content_list) > 0:
                                first_block = content_list[0]
                                if isinstance(first_block, dict) and 'text' in first_block:
                                    return first_block['text']
        
        # Fallback to string representation
        return str(result)
    
    @staticmethod
    def _build_report(
        original_prompt: str,
        content: str,
        iteration_count: int,
        is_mock: bool
    ) -> str:
        """Build a structured, readable report."""
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("COMPREHENSIVE INNOVATION ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Metadata
        lines.append("REPORT METADATA")
        lines.append("-" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Iterations Completed: {iteration_count}")
        if is_mock:
            lines.append("Mode: MOCK (Demonstration)")
        lines.append("")
        
        # Original Request
        lines.append("ORIGINAL REQUEST")
        lines.append("-" * 80)
        lines.append(original_prompt)
        lines.append("")
        
        # Main Content
        lines.append("ANALYSIS & RECOMMENDATIONS")
        lines.append("-" * 80)
        
        # Parse and format the content
        formatted_content = FinalOutputFormatter._format_content(content)
        lines.append(formatted_content)
        lines.append("")
        
        # Footer
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_content(content: str) -> str:
        """Format the main content with better readability."""
        if not content or content.strip() == "":
            return "[No content generated]"
        
        # If content looks like it already has structure, return as-is
        if any(marker in content for marker in ["##", "###", "**", "---", "PHASE"]):
            return content
        
        # Otherwise, try to structure it
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.rstrip()
            
            # Skip empty MultiAgentResult representation
            if 'MultiAgentResult' in line or 'NodeResult' in line or 'AgentResult' in line:
                continue
            
            # Skip status codes and internal representations
            if 'status=' in line or 'execution_time=' in line or 'accumulated_' in line:
                continue
            
            # Clean up and add back
            if line.strip():
                formatted_lines.append(line)
        
        return "\n".join(formatted_lines)
    
    @staticmethod
    def format_for_mock_mode(
        ideas: Optional[List[Dict[str, str]]] = None,
        original_prompt: str = "Innovation Challenge",
    ) -> str:
        """
        Generate a well-formatted mock output for demonstration purposes.
        
        Args:
            ideas: List of mock ideas to display
            original_prompt: Original user prompt
            
        Returns:
            Formatted mock report
        """
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("COMPREHENSIVE INNOVATION ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Metadata
        lines.append("REPORT METADATA")
        lines.append("-" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("Iterations Completed: 1 (Mock Demonstration)")
        lines.append("Mode: MOCK - Graph Structure Validation")
        lines.append("")
        
        # Original Request
        lines.append("ORIGINAL REQUEST")
        lines.append("-" * 80)
        lines.append(original_prompt)
        lines.append("")
        
        # Executive Summary
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(
            "This analysis represents the final synthesis of the creative ideation process. "
            "The system has refined raw concepts through multiple iterations of generation, "
            "criticism, and refinement to identify the most promising innovations."
        )
        lines.append("")
        
        # Top Ideas
        lines.append("TOP IDEAS IDENTIFIED")
        lines.append("-" * 80)
        
        if ideas:
            for i, idea in enumerate(ideas, 1):
                score = idea.get('score', 'N/A')
                name = idea.get('name', f'Idea {i}')
                lines.append(f"\n{i}. {name} (Score: {score})")
                if 'description' in idea:
                    lines.append(f"   {idea['description']}")
        else:
            # Default mock ideas
            mock_ideas = [
                {
                    'name': 'Idea Alpha',
                    'score': '8.5/10',
                    'description': 'Originality: High | Feasibility: Medium-High | Impact: Significant'
                },
                {
                    'name': 'Idea Beta',
                    'score': '7.8/10',
                    'description': 'Originality: Medium-High | Feasibility: High | Impact: Moderate'
                },
                {
                    'name': 'Idea Gamma',
                    'score': '8.2/10',
                    'description': 'Originality: Very High | Feasibility: Medium | Impact: High'
                }
            ]
            
            for i, idea in enumerate(mock_ideas, 1):
                lines.append(f"\n{i}. {idea['name']} (Score: {idea['score']})")
                lines.append(f"   {idea['description']}")
        
        lines.append("")
        
        # Detailed Analysis
        lines.append("DETAILED ANALYSIS")
        lines.append("-" * 80)
        lines.append("")
        lines.append("IDEA 1: Alpha Concept")
        lines.append("~" * 40)
        lines.append("")
        lines.append("Core Innovation:")
        lines.append("  A novel approach combining existing techniques in an innovative way.")
        lines.append("")
        lines.append("Technical Architecture:")
        lines.append("  - Component 1: Foundation layer")
        lines.append("  - Component 2: Processing layer")
        lines.append("  - Component 3: Integration layer")
        lines.append("")
        lines.append("Feasibility Assessment:")
        lines.append("  Implementation Timeline: 6-12 months")
        lines.append("  Required Expertise: Advanced technical knowledge")
        lines.append("  Technical Risks: Medium complexity, manageable challenges")
        lines.append("")
        lines.append("Market Potential:")
        lines.append("  Target Users: Enterprise and mid-market organizations")
        lines.append("  Addressable Market: $500M+ annual opportunity")
        lines.append("  Competitive Advantage: 18-24 month lead time")
        lines.append("")
        
        # Strategic Recommendations
        lines.append("STRATEGIC RECOMMENDATIONS")
        lines.append("-" * 80)
        lines.append("")
        lines.append("Highest Priority Recommendation:")
        lines.append("  Pursue Idea Alpha with focus on MVP (Minimum Viable Product)")
        lines.append("  development in first phase.")
        lines.append("")
        lines.append("Implementation Roadmap:")
        lines.append("")
        lines.append("  Phase 1 (MVP) - 0-3 months:")
        lines.append("    • Core functionality prototype")
        lines.append("    • Internal validation and testing")
        lines.append("    • User research and feedback")
        lines.append("")
        lines.append("  Phase 2 (Enhancement) - 3-6 months:")
        lines.append("    • Feature expansion based on user feedback")
        lines.append("    • Performance optimization")
        lines.append("    • Integration capabilities")
        lines.append("")
        lines.append("  Phase 3 (Scale) - 6-12 months:")
        lines.append("    • Market launch and distribution")
        lines.append("    • Customer acquisition and support")
        lines.append("    • Ongoing innovation and improvements")
        lines.append("")
        
        lines.append("Quick Wins (Next 30 Days):")
        lines.append("  1. Validate core concept with 10-15 target users")
        lines.append("  2. Assess technical feasibility with proof-of-concept")
        lines.append("  3. Define MVP scope and success metrics")
        lines.append("  4. Identify required team skills and resources")
        lines.append("")
        
        # Scoring Summary
        lines.append("INNOVATION SCORING SUMMARY")
        lines.append("-" * 80)
        lines.append("Overall Novelty Score:        8/10")
        lines.append("Overall Feasibility Score:    7/10")
        lines.append("Overall Impact Potential:     8/10")
        lines.append("Confidence Level:             High (85%)")
        lines.append("")
        
        # Footer
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        return "\n".join(lines)


def save_formatted_output(
    output_path: Path,
    result: Any,
    original_prompt: str,
    iteration_count: int = 0,
    is_mock: bool = False
) -> None:
    """
    Save formatted final output to file.
    
    Args:
        output_path: Path to save output file
        result: Result object to format
        original_prompt: Original user prompt
        iteration_count: Number of iterations completed
        is_mock: Whether this is mock output
    """
    formatter = FinalOutputFormatter()
    
    if is_mock:
        formatted = formatter.format_for_mock_mode(original_prompt=original_prompt)
    else:
        formatted = formatter.format_result(
            result=result,
            original_prompt=original_prompt,
            iteration_count=iteration_count,
            is_mock=is_mock
        )
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(formatted)
    
    logger.info(f"Saved formatted final output to {output_path}")

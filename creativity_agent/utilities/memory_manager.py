"""
Memory management utilities for tracking explored and rejected ideas.
"""

from pathlib import Path
from typing import Optional, List
import json
import logging
from creativity_agent.models import IdeaMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages persistent storage and retrieval of idea memory.
    Handles saving/loading memory state across sessions.
    """
    
    def __init__(self, memory_dir: Path):
        """
        Initialize memory manager.
        
        Args:
            memory_dir: Directory where memory files will be stored
        """
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(exist_ok=True)
        self.memory = IdeaMemory()
        self.memory_file = self.memory_dir / "idea_memory.json"
    
    def load_memory(self) -> IdeaMemory:
        """Load memory from disk if it exists."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.memory = IdeaMemory(**data)
                logger.info(f"Loaded memory: {len(self.memory.explored_ideas)} explored, "
                          f"{len(self.memory.rejected_ideas)} rejected")
            except Exception as e:
                logger.error(f"Error loading memory: {e}")
                self.memory = IdeaMemory()
        return self.memory
    
    def save_memory(self) -> None:
        """Save current memory state to disk."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.memory.model_dump(mode='json'),
                    f,
                    indent=2,
                    default=str
                )
            logger.info("Memory saved successfully")
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def extract_concepts_from_text(
        self,
        text: str,
        iteration: int,
        max_concepts: int = 20,
        is_high_temp: bool = True
    ) -> None:
        """
        Extract evaluated concepts from agent output.
        Handles both JSON format and Python code with embedded JSON.
        
        Args:
            text: The agent output text (JSON or Python code with JSON)
            iteration: Current iteration number
            max_concepts: Maximum concepts to extract
            is_high_temp: Whether this is from high-temp (divergent) or low-temp (refined) agent
        """
        import json
        import re
        
        # Try to extract and parse JSON from the output
        try:
            # Look for JSON object in the text (between { and })
            json_match = None
            if '{' in text and '}' in text:
                # Try to find valid JSON
                start_idx = text.find('{')
                depth = 0
                end_idx = start_idx
                for i in range(start_idx, len(text)):
                    if text[i] == '{':
                        depth += 1
                    elif text[i] == '}':
                        depth -= 1
                        if depth == 0:
                            end_idx = i + 1
                            break
                
                json_str = text[start_idx:end_idx]
                try:
                    data = json.loads(json_str)
                    json_match = data
                except json.JSONDecodeError:
                    pass
            
            if json_match:
                self._extract_from_json(json_match, iteration, max_concepts, is_high_temp)
                return
        except Exception as e:
            logger.debug(f"Could not extract JSON: {e}")
        
        # Fallback to text-based extraction
        if is_high_temp:
            self._extract_simple_concepts(text, iteration, max_concepts)
        else:
            # For refinement (low-temp), try to parse structured format
            accepted_ideas = self._parse_accepted_ideas(text)
            for idea in accepted_ideas[:max_concepts]:
                self.memory.add_explored_idea(
                    concept=idea['concept'],
                    key_points=idea['key_points'],
                    iteration=iteration,
                    quality_score=idea['quality_score']
                )
            
            rejected_ideas = self._parse_rejected_ideas(text)
            for idea in rejected_ideas:
                self.memory.add_rejected_idea(
                    concept=idea['concept'],
                    reason=idea['reason'],
                    iteration=iteration
                )
    
    def _extract_from_json(
        self,
        data: dict,
        iteration: int,
        max_concepts: int,
        is_high_temp: bool
    ) -> None:
        """
        Extract concepts from parsed JSON data.
        
        Args:
            data: Parsed JSON dictionary
            iteration: Current iteration number
            max_concepts: Maximum concepts to extract
            is_high_temp: Whether this is from creative (high-temp) or refinement (low-temp) agent
        """
        import json
        
        # For creative agent output (high-temp): extract from "ideas" array
        if is_high_temp and 'ideas' in data:
            ideas = data['ideas']
            if isinstance(ideas, list):
                for i, idea in enumerate(ideas[:max_concepts]):
                    if isinstance(idea, dict):
                        # Extract title/concept
                        title = idea.get('title', idea.get('concept', f'Idea_{i+1}'))
                        # Extract key components or key_points
                        key_points = idea.get('key_components', idea.get('key_points', []))
                        if isinstance(key_points, str):
                            key_points = [key_points]
                        
                        self.memory.add_explored_idea(
                            concept=title,
                            key_points=key_points,
                            iteration=iteration,
                            quality_score=None  # Creative output doesn't have scores yet
                        )
                        logger.debug(f"Extracted idea from creative: {title}")
        
        # For refinement agent output (low-temp): extract from "accepted_ideas" and "rejected_ideas"
        elif not is_high_temp:
            # Process accepted ideas
            if 'accepted_ideas' in data:
                accepted = data['accepted_ideas']
                if isinstance(accepted, list):
                    for i, idea in enumerate(accepted[:max_concepts]):
                        if isinstance(idea, dict):
                            title = idea.get('idea_name', idea.get('title', f'Idea_{i+1}'))
                            key_points = idea.get('key_points', [])
                            if isinstance(key_points, str):
                                key_points = [key_points]
                            quality = idea.get('quality_score', None)
                            
                            self.memory.add_explored_idea(
                                concept=title,
                                key_points=key_points,
                                iteration=iteration,
                                quality_score=quality
                            )
                            logger.debug(f"Extracted accepted idea: {title}")
            
            # Process rejected ideas
            if 'rejected_ideas' in data:
                rejected = data['rejected_ideas']
                if isinstance(rejected, list):
                    for idea in rejected:
                        if isinstance(idea, dict):
                            title = idea.get('idea_name', idea.get('title', 'Unknown'))
                            reasons = idea.get('rejection_reasons', [])
                            reason_text = ', '.join(reasons) if isinstance(reasons, list) else str(reasons)
                            
                            self.memory.add_rejected_idea(
                                concept=title,
                                reason=reason_text,
                                iteration=iteration
                            )
                            logger.debug(f"Extracted rejected idea: {title}")
    
    def _extract_simple_concepts(
        self,
        text: str,
        iteration: int,
        max_concepts: int
    ) -> None:
        """
        Smart extraction for divergent (high-temp) output.
        Captures actual ideas and avoids generic section headers.
        """
        import re
        
        concepts = []
        lines = text.split('\n')
        
        # Metadata/structure patterns to skip
        skip_patterns = [
            'executive summary', 'introduction', 'conclusion', 'background',
            'overview', 'summary', 'final thoughts', 'key takeaways',
            'tier', 'breakthrough', 'category', 'theme', 'section',
            'synthesis', 'refinement', 'improvement', 'enhancement'
        ]
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines and very short lines
            if len(line) < 10 or not line:
                continue
            
            # Extract from markdown headers (##, ###)
            if line.startswith('##'):
                concept = line.lstrip('#').strip()
                concept = concept.rstrip(':').strip()  # Remove trailing colon
                
                # Skip if it's just metadata
                if any(marker in concept.lower() for marker in skip_patterns):
                    continue
                
                # Must be a real idea (typically 4+ words)
                if len(concept.split()) >= 4 and len(concept) > 15:
                    concepts.append(concept)
            
            # Extract from numbered lists (1. 2. etc)
            elif re.match(r'^\d+\.\s+', line):
                concept = re.sub(r'^\d+\.\s*', '', line).strip()
                
                # Filter out meta patterns
                if any(marker in concept.lower() for marker in skip_patterns):
                    continue
                
                if len(concept.split()) >= 4 and len(concept) > 15:
                    concepts.append(concept)
            
            # Extract from bullet points (-, *, +) if they look like ideas
            elif re.match(r'^[-*+]\s+', line):
                concept = re.sub(r'^[-*+]\s+', '', line).strip()
                
                # Skip very short bullets or meta content
                if len(concept) > 20 and not any(marker in concept.lower() for marker in skip_patterns):
                    concepts.append(concept)
        
        # Remove duplicates and clean up
        unique_concepts = []
        seen = set()
        for concept in concepts:
            # Normalize for deduplication
            normalized = concept.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_concepts.append(concept)
        
        # Limit to max requested
        unique_concepts = unique_concepts[:max_concepts]
        
        # Add to memory
        for concept in unique_concepts:
            self.memory.add_explored_idea(
                concept=concept,
                key_points=[],
                iteration=iteration,
                quality_score=6.0  # Default moderate score for divergent ideas
            )
        
        logger.info(f"Extracted {len(unique_concepts)} real concepts from divergent output")
    
    def _parse_accepted_ideas(self, text: str) -> List[dict]:
        """
        Parse ACCEPTED IDEAS section from refinement agent output.
        
        Expected format:
        ### IDEA: [name]
        **Quality Score**: [X.X/10]
        **Description**: [text]
        **Key Points**:
        - [point 1]
        - [point 2]
        """
        import re
        
        accepted_ideas = []
        
        # Find the ACCEPTED IDEAS section
        accepted_section_match = re.search(
            r'###\s*ACCEPTED IDEAS(.*?)(?:###\s*REJECTED IDEAS|###\s*SYNTHESIS|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not accepted_section_match:
            logger.warning("No ACCEPTED IDEAS section found in refinement output")
            return []
        
        accepted_section = accepted_section_match.group(1)
        
        # Split into individual ideas (separated by "### IDEA:")
        idea_pattern = r'###\s*IDEA:\s*(.+?)(?=###\s*IDEA:|###\s*REJECTED|$)'
        idea_matches = re.finditer(idea_pattern, accepted_section, re.DOTALL | re.IGNORECASE)
        
        for match in idea_matches:
            idea_text = match.group(0)
            idea_name_match = re.search(r'###\s*IDEA:\s*(.+?)(?:\n|$)', idea_text)
            
            if not idea_name_match:
                continue
            
            idea_name = idea_name_match.group(1).strip()
            
            # Extract quality score
            score_match = re.search(
                r'\*\*Quality Score\*\*:\s*(\d+\.?\d*)',
                idea_text,
                re.IGNORECASE
            )
            quality_score = float(score_match.group(1)) if score_match else 7.0
            
            # Extract key points
            key_points = []
            key_points_section = re.search(
                r'\*\*Key Points\*\*:\s*((?:[-•*]\s*.+\n?)+)',
                idea_text,
                re.IGNORECASE | re.MULTILINE
            )
            
            if key_points_section:
                points_text = key_points_section.group(1)
                point_matches = re.findall(r'[-•*]\s*(.+)', points_text)
                key_points = [p.strip() for p in point_matches if len(p.strip()) > 10]
            
            accepted_ideas.append({
                'concept': idea_name,
                'quality_score': quality_score,
                'key_points': key_points[:5]  # Limit to 5
            })
        
        logger.info(f"Parsed {len(accepted_ideas)} accepted ideas from LLM judge")
        return accepted_ideas
    
    def _parse_rejected_ideas(self, text: str) -> List[dict]:
        """
        Parse REJECTED IDEAS section from refinement agent output.
        
        Expected format:
        ### REJECTED: [name]
        **Quality Score**: [X.X/10] (REJECTED)
        **Rejection Reasons**:
        - [reason 1]
        - [reason 2]
        """
        import re
        
        rejected_ideas = []
        
        # Find the REJECTED IDEAS section
        rejected_section_match = re.search(
            r'###\s*REJECTED IDEAS(.*?)(?:###\s*SYNTHESIS|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not rejected_section_match:
            # No rejections is okay
            return []
        
        rejected_section = rejected_section_match.group(1)
        
        # Split into individual rejections
        rejection_pattern = r'###\s*REJECTED:\s*(.+?)(?=###\s*REJECTED:|###\s*SYNTHESIS:|$)'
        rejection_matches = re.finditer(rejection_pattern, rejected_section, re.DOTALL | re.IGNORECASE)
        
        for match in rejection_matches:
            rejection_text = match.group(0)
            idea_name_match = re.search(r'###\s*REJECTED:\s*(.+?)(?:\n|$)', rejection_text)
            
            if not idea_name_match:
                continue
            
            idea_name = idea_name_match.group(1).strip()
            
            # Extract rejection reasons
            reasons = []
            reasons_section = re.search(
                r'\*\*Rejection Reasons?\*\*:\s*((?:[-•*]\s*.+\n?)+)',
                rejection_text,
                re.IGNORECASE | re.MULTILINE
            )
            
            if reasons_section:
                reasons_text = reasons_section.group(1)
                reason_matches = re.findall(r'[-•*]\s*(.+)', reasons_text)
                reasons = [r.strip() for r in reason_matches]
            
            reason_text = '; '.join(reasons) if reasons else "Did not meet quality threshold"
            
            rejected_ideas.append({
                'concept': idea_name,
                'reason': reason_text
            })
        
        logger.info(f"Parsed {len(rejected_ideas)} rejected ideas from LLM judge")
        return rejected_ideas
    
    
    def mark_as_rejected(
        self,
        concept: str,
        reason: str,
        iteration: int
    ) -> None:
        """
        Mark a concept as rejected.
        
        Args:
            concept: The concept to reject
            reason: Why it was rejected
            iteration: Current iteration number
        """
        self.memory.add_rejected_idea(concept, reason, iteration)
        logger.info(f"Marked as rejected: {concept}")
    
    def get_memory_context(self) -> str:
        """Get formatted memory context for prompt injection."""
        return self.memory.get_memory_summary()
    
    def clear_memory(self) -> None:
        """Clear all memory (useful for starting fresh)."""
        self.memory = IdeaMemory()
        if self.memory_file.exists():
            self.memory_file.unlink()
        logger.info("Memory cleared")

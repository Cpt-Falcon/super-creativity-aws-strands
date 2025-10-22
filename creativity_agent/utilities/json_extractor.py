"""
JSON Extraction Utility - Centralized JSON parsing for agent outputs.

Handles extraction of structured data from both creative and refinement agent outputs,
with fallback to text patterns for robustness.
"""

import json
import re
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class JsonExtractor:
    """Utility for extracting ideas from structured and unstructured content."""
    
    @staticmethod
    def extract_json_object(content: str) -> Optional[Dict[str, Any]]:
        """
        Extract first valid JSON object from content.
        
        Args:
            content: Raw string content that may contain JSON
            
        Returns:
            Parsed JSON dict if found, None otherwise
        """
        if '{' not in content or '}' not in content:
            return None
        
        try:
            # Find first opening brace
            start_idx = content.find('{')
            depth = 0
            end_idx = start_idx
            
            # Track braces to find matching closing brace
            for i in range(start_idx, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end_idx = i + 1
                        break
            
            json_str = content[start_idx:end_idx]
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Failed to parse JSON: {e}")
            return None
    
    @staticmethod
    def extract_ideas_from_creative_output(data: Dict[str, Any]) -> List[str]:
        """
        Extract ideas from creative agent output JSON.
        
        Creative output format:
        {
          "ideas": [
            {"title": "...", "description": "...", "key_components": [...]}
          ],
          ...
        }
        
        Args:
            data: Parsed JSON from creative agent
            
        Returns:
            List of formatted idea strings
        """
        ideas = []
        
        if not isinstance(data, dict) or 'ideas' not in data:
            return ideas
        
        ideas_array = data['ideas']
        if not isinstance(ideas_array, list):
            return ideas
        
        for i, idea in enumerate(ideas_array):
            if not isinstance(idea, dict):
                continue
            
            # Extract core fields
            title = idea.get('title', idea.get('concept', f'Idea_{i+1}'))
            description = idea.get('description', '')
            
            # Format as text
            text = f"{title}\n{description}" if description else title
            if text.strip():
                ideas.append(text)
        
        logger.debug(f"Extracted {len(ideas)} ideas from creative output")
        return ideas
    
    @staticmethod
    def extract_ideas_from_refinement_output(data: Dict[str, Any]) -> List[str]:
        """
        Extract ideas from refinement agent output JSON.
        
        Refinement output format:
        {
          "accepted_ideas": [
            {
              "idea_name": "...",
              "quality_score": 8,
              "key_points": [...],
              "implementation_path": "...",
              "required_resources": [...],
              "success_metrics": [...],
              "next_steps": [...]
            }
          ],
          ...
        }
        
        Args:
            data: Parsed JSON from refinement agent
            
        Returns:
            List of formatted idea strings (accepted ideas only)
        """
        ideas = []
        
        if not isinstance(data, dict):
            return ideas
        
        # Extract from accepted_ideas array
        if 'accepted_ideas' in data:
            accepted = data['accepted_ideas']
            if isinstance(accepted, list):
                for i, idea in enumerate(accepted):
                    if not isinstance(idea, dict):
                        continue
                    
                    title = idea.get('idea_name', idea.get('title', f'Idea_{i+1}'))
                    
                    # Build comprehensive description from all available fields
                    description_parts = []
                    
                    if idea.get('key_points'):
                        description_parts.append(f"Key Points: {', '.join(idea['key_points'])}")
                    
                    if idea.get('implementation_path'):
                        description_parts.append(f"Implementation: {idea['implementation_path']}")
                    
                    if idea.get('required_resources'):
                        resources = idea['required_resources']
                        if isinstance(resources, list):
                            description_parts.append(f"Resources: {', '.join(resources)}")
                        else:
                            description_parts.append(f"Resources: {resources}")
                    
                    if idea.get('success_metrics'):
                        metrics = idea['success_metrics']
                        if isinstance(metrics, list):
                            description_parts.append(f"Success Metrics: {', '.join(metrics)}")
                        else:
                            description_parts.append(f"Success Metrics: {metrics}")
                    
                    if idea.get('next_steps'):
                        steps = idea['next_steps']
                        if isinstance(steps, list):
                            description_parts.append(f"Next Steps: {', '.join(steps)}")
                        else:
                            description_parts.append(f"Next Steps: {steps}")
                    
                    # Add scores if available
                    scores = []
                    for score_field in ['quality_score', 'feasibility_score', 'impact_score', 'originality_score']:
                        if score_field in idea:
                            scores.append(f"{score_field.replace('_score', '').title()}: {idea[score_field]}")
                    
                    if scores:
                        description_parts.insert(0, f"Scores: {', '.join(scores)}")
                    
                    description = '\n'.join(description_parts) if description_parts else ''
                    
                    text = f"{title}\n{description}" if description else title
                    if text.strip():
                        ideas.append(text)
        
        logger.debug(f"Extracted {len(ideas)} ideas from refinement output")
        return ideas
    
    @staticmethod
    def extract_ideas_from_any_format(content: str) -> List[str]:
        """
        Extract ideas from content in any format (JSON or text).
        
        Tries JSON extraction first, then falls back to text patterns.
        
        Args:
            content: Raw content that may be JSON or text
            
        Returns:
            List of extracted idea strings
        """
        ideas = []
        
        # Try JSON extraction first
        json_data = JsonExtractor.extract_json_object(content)
        if json_data:
            # Try creative format first
            ideas = JsonExtractor.extract_ideas_from_creative_output(json_data)
            
            # If no ideas found, try refinement format
            if not ideas:
                ideas = JsonExtractor.extract_ideas_from_refinement_output(json_data)
            
            if ideas:
                logger.debug(f"Successfully extracted {len(ideas)} ideas from JSON")
                return ideas[:20]  # Limit to 20 ideas max
        
        # Fallback to text pattern matching
        logger.debug("JSON extraction failed, falling back to text patterns")
        
        # Try numbered ideas (1., 2., etc.)
        numbered_pattern = r'^\d+\.\s+(.+?)(?=^\d+\.|$)'
        numbered_matches = re.findall(
            numbered_pattern,
            content,
            re.MULTILINE | re.DOTALL
        )
        if numbered_matches:
            ideas.extend([m.strip() for m in numbered_matches if m.strip()])
            logger.debug(f"Extracted {len(ideas)} ideas from numbered pattern")
            return ideas[:20]
        
        # Try bullet points
        bullet_pattern = r'^[-*]\s+(.+?)(?=^[-*]|$)'
        bullet_matches = re.findall(
            bullet_pattern,
            content,
            re.MULTILINE | re.DOTALL
        )
        if bullet_matches:
            ideas.extend([m.strip() for m in bullet_matches if m.strip()])
            logger.debug(f"Extracted {len(ideas)} ideas from bullet pattern")
            return ideas[:20]
        
        # Split by double newlines as last resort
        sections = content.split('\n\n')
        ideas = [s.strip() for s in sections if s.strip() and len(s.strip()) > 50]
        logger.debug(f"Extracted {len(ideas)} ideas from paragraph pattern")
        
        return ideas[:20]

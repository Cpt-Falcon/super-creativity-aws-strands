"""
Independent judge system using Claude 4.5 Sonnet for standardized idea evaluation.
Uses Jinja2 templates for prompt rendering.
"""
from strands import Agent
from strands.models import BedrockModel
from typing import List, Dict, Optional, TYPE_CHECKING
from creativity_agent.models.observability_models import JudgeEvaluation
from datetime import datetime
import logging
import re
import json

if TYPE_CHECKING:
    from creativity_agent.utilities.jinja_prompt_builder import JinjaPromptBuilder

logger = logging.getLogger(__name__)


class IndependentJudge:
    """
    Independent judge using Claude 4.5 Sonnet for consistent idea evaluation.
    Separate from the generation models to avoid self-judging bias.
    """
    
    def __init__(
        self,
        jinja_builder: "JinjaPromptBuilder",
        judge_model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0",
        judge_temperature: float = 0.1,
        streaming: bool = True,
        region_name: str = "us-east-1"
    ):
        """
        Initialize the independent judge.
        
        Args:
            jinja_builder: JinjaPromptBuilder instance for prompt rendering
            judge_model_id: Model ID for the judge (from flow_config)
            judge_temperature: Temperature for judge evaluation
            streaming: Whether to use streaming mode (disable for models that don't support it)
            region_name: AWS region for Bedrock
        """
        self.jinja_builder = jinja_builder
        self.judge_model_id = judge_model_id
        model = BedrockModel(
            model_id=self.judge_model_id,
            temperature=judge_temperature,
            streaming=streaming,
            region_name=region_name
        )
        
        # Create agent wrapper for the judge model
        self.agent = Agent(model=model, tools=[])
        
        logger.info(f"Independent judge initialized with {self.judge_model_id}")
    
    def evaluate_idea(
        self, 
        idea_text: str, 
        idea_name: str,
        source_model: str,
        temperature: float,
        iteration: int
    ) -> JudgeEvaluation:
        """
        Evaluate a single idea using the independent judge.
        
        Args:
            idea_text: The full text of the idea to evaluate
            idea_name: Name/title of the idea
            source_model: Model that generated this idea
            temperature: Temperature used when generating
            iteration: Iteration number in which idea was generated
            
        Returns:
            JudgeEvaluation with detailed scores and decision
        """
        logger.info(f"Evaluating idea: {idea_name[:50]}...")
        
        try:
            # Build the judge prompt using Jinja2 builder
            from creativity_agent.utilities.jinja_prompt_builder import JudgePromptContext
            
            judge_context = JudgePromptContext(
                idea_text=idea_text,
                evaluation_criteria={
                    "originality": "How novel and creative is this idea?",
                    "feasibility": "How practical and implementable is this?",
                    "impact": "What is the potential impact or value?",
                    "substance": "How well-developed and substantial is the idea?"
                },
                acceptance_threshold=5.0
            )
            
            prompt = self.jinja_builder.build_judge_prompt(judge_context)
            
            # Get evaluation from judge
            agent_result = self.agent(prompt)
            response_content = agent_result.message['content']
            response_text = response_content[0].get('text', '') if response_content else ''
            
            # Parse the evaluation response
            evaluation = self._parse_evaluation(
                response_text,
                idea_name,
                source_model,
                temperature,
                iteration
            )
            
            logger.info(f"Evaluation complete: {idea_name} - Score: {evaluation.overall_quality_score:.1f}, Decision: {'ACCEPTED' if evaluation.accepted else 'REJECTED'}")
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating idea '{idea_name}': {e}")
            # Return a default rejection evaluation
            return JudgeEvaluation(
                idea_id=f"error_{datetime.now().timestamp()}",
                idea_name=idea_name,
                originality_score=0.0,
                feasibility_score=0.0,
                impact_score=0.0,
                substance_score=0.0,
                overall_quality_score=0.0,
                accepted=False,
                rejection_reasons=[f"Evaluation error: {str(e)}"],
                key_points=[],
                model_id=source_model,
                temperature=temperature,
                iteration=iteration,
                evaluation_timestamp=datetime.now(),
                judge_model=self.judge_model_id
            )
    
    def _parse_evaluation(
        self,
        response_text: str,
        idea_name: str,
        source_model: str,
        temperature: float,
        iteration: int
    ) -> JudgeEvaluation:
        """
        Parse the judge's JSON response into a structured evaluation.
        
        Args:
            response_text: Raw JSON response from judge model
            idea_name: Name of the idea
            source_model: Model that generated the idea
            temperature: Temperature used
            iteration: Iteration number
            
        Returns:
            Parsed JudgeEvaluation
        """
        logger.debug(f"Parsing evaluation response:\n{response_text[:500]}")
        
        try:
            # Try to parse as JSON first
            response_data = json.loads(response_text.strip())
            
            # Extract the first evaluation from the evaluations array
            if "evaluations" in response_data and response_data["evaluations"]:
                eval_data = response_data["evaluations"][0]
                
                originality = float(eval_data.get("originality_score", 5.0))
                feasibility = float(eval_data.get("feasibility_score", 5.0))
                impact = float(eval_data.get("impact_score", 5.0))
                substance = float(eval_data.get("substance_score", 5.0))
                overall = float(eval_data.get("average_score", (originality + feasibility + impact + substance) / 4.0))
                
                decision = eval_data.get("decision", "REJECT").upper()
                accepted = decision == "ACCEPT"
                
                # Map JSON fields to our model
                rejection_reasons = eval_data.get("weaknesses", []) if not accepted else []
                key_points = eval_data.get("strengths", [])
                
            else:
                # Fallback to old parsing if JSON structure is different
                logger.warning("Unexpected JSON structure, falling back to text parsing")
                return self._parse_evaluation_fallback(response_text, idea_name, source_model, temperature, iteration)
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"JSON parsing failed: {e}, falling back to text parsing")
            return self._parse_evaluation_fallback(response_text, idea_name, source_model, temperature, iteration)
        
        idea_id = f"{source_model}_{iteration}_{idea_name[:20].replace(' ', '_')}"
        
        return JudgeEvaluation(
            idea_id=idea_id,
            idea_name=idea_name,
            originality_score=originality,
            feasibility_score=feasibility,
            impact_score=impact,
            substance_score=substance,
            overall_quality_score=overall,
            accepted=accepted,
            rejection_reasons=rejection_reasons,
            key_points=key_points,
            model_id=source_model,
            temperature=temperature,
            iteration=iteration,
            evaluation_timestamp=datetime.now(),
            judge_model=self.judge_model_id
        )
    
    def _parse_evaluation_fallback(
        self,
        response_text: str,
        idea_name: str,
        source_model: str,
        temperature: float,
        iteration: int
    ) -> JudgeEvaluation:
        """
        Fallback text parsing for judge responses that aren't JSON.
        """
        # Extract scores using new format
        originality = self._extract_score_new(response_text, "ORIGINALITY_SCORE")
        feasibility = self._extract_score_new(response_text, "FEASIBILITY_SCORE")
        impact = self._extract_score_new(response_text, "IMPACT_SCORE")
        substance = self._extract_score_new(response_text, "SUBSTANCE_SCORE")
        
        # Extract overall score
        overall_match = re.search(r"OVERALL_SCORE:\s*([\d.]+)", response_text)
        if overall_match:
            overall = float(overall_match.group(1))
        else:
            # Calculate from individual scores if not found
            overall = (originality + feasibility + impact + substance) / 4.0
        
        # Determine acceptance
        decision_match = re.search(r"DECISION:\s*(ACCEPTED|REJECTED)", response_text)
        accepted = decision_match.group(1).upper() == "ACCEPTED" if decision_match else (overall >= 5.0)
        
        # Extract strengths and concerns
        strengths = self._extract_csv_list(response_text, "STRENGTHS")
        concerns = self._extract_csv_list(response_text, "CONCERNS")
        
        idea_id = f"{source_model}_{iteration}_{idea_name[:20].replace(' ', '_')}"
        
        return JudgeEvaluation(
            idea_id=idea_id,
            idea_name=idea_name,
            originality_score=originality,
            feasibility_score=feasibility,
            impact_score=impact,
            substance_score=substance,
            overall_quality_score=overall,
            accepted=accepted,
            rejection_reasons=concerns if not accepted else [],
            key_points=strengths,
            model_id=source_model,
            temperature=temperature,
            iteration=iteration,
            evaluation_timestamp=datetime.now(),
            judge_model=self.judge_model_id
        )
    
    def _extract_score_new(self, text: str, label: str) -> float:
        """Extract a score using the new label format (e.g., ORIGINALITY_SCORE: 7)."""
        pattern = rf"{label}:\s*([\d.]+)"
        match = re.search(pattern, text)
        if match:
            try:
                score = float(match.group(1))
                # Clamp between 0 and 10
                return max(0.0, min(10.0, score))
            except ValueError:
                logger.warning(f"Could not parse score from {label}")
                return 5.0
        logger.warning(f"Could not find {label} in response")
        return 5.0  # Default to middle score
    
    def _extract_csv_list(self, text: str, label: str) -> List[str]:
        """Extract a comma-separated list from a labeled line."""
        pattern = rf"{label}:\s*(.+?)(?=\n|$)"
        match = re.search(pattern, text)
        
        if not match:
            return []
        
        line = match.group(1).strip()
        
        # Split by comma and clean up
        items = [item.strip() for item in line.split(",")]
        return [item for item in items if item and item.lower() != "none"]
    
    def batch_evaluate(
        self,
        ideas: List[Dict[str, str]],
        source_model: str,
        temperature: float,
        iteration: int
    ) -> List[JudgeEvaluation]:
        """
        Evaluate multiple ideas in batch.
        
        Args:
            ideas: List of dicts with 'name' and 'text' keys
            source_model: Model that generated these ideas
            temperature: Temperature used
            iteration: Iteration number
            
        Returns:
            List of JudgeEvaluations
        """
        evaluations = []
        
        for idea in ideas:
            evaluation = self.evaluate_idea(
                idea_text=idea['text'],
                idea_name=idea['name'],
                source_model=source_model,
                temperature=temperature,
                iteration=iteration
            )
            evaluations.append(evaluation)
        
        logger.info(f"Batch evaluation complete: {len(evaluations)} ideas evaluated")
        
        return evaluations

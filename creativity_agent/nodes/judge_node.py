"""
Judge Node - Evaluates ideas using independent Claude judge.

Uses typed ExecutionState for proper state management throughout the graph.
"""

from creativity_agent.nodes.base_node import BaseNode
from creativity_agent.models import IdeaStatistics, JudgeEvaluation, ExecutionState, SharedState
from strands.multiagent import MultiAgentResult
from creativity_agent.utilities import IndependentJudge, ObservabilityTracker, JsonExtractor
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from strands.types.content import ContentBlock
import logging
import time
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class JudgeNode(BaseNode):
    """Node that evaluates ideas using independent judge."""
    
    def __init__(
        self,
        shared_state: SharedState,
        judge: IndependentJudge,
        observability: Optional[ObservabilityTracker],
        outputs_dir: Path,
        prompts_dir: Optional[Path] = None
    ):
        super().__init__(
            node_name="judge",
            shared_state=shared_state,
            prompts_dir=prompts_dir,
            outputs_dir=outputs_dir
        )
        self.judge = judge
        self.observability = observability
        
    async def invoke_async(
        self,
        task: Union[str, list[ContentBlock]],
        invocation_state: Optional[dict] = None,
        **kwargs
    ) -> MultiAgentResult:
        """Evaluate ideas from refinement output."""
        try:
            # Parse typed input
            result = task if isinstance(task, str) else str(task)
            start_time = time.time()
            
            logger.info("\njudge_input\n")
            logger.info(result)
            logger.info("\n------------\n")

            node_input = self._get_typed_input(task, invocation_state)
            state = node_input.state

            # Pass the entire refinement output to the judge for parsing and evaluation
            evaluations_data = self._evaluate_refinement_output(result, state)
            
            # Extract accepted/rejected ideas from the judge's response
            accepted_ideas = evaluations_data.get('accepted_ideas', [])
            rejected_ideas = evaluations_data.get('rejected_ideas', [])
            
            # Convert to JudgeEvaluation objects for compatibility
            judge_evaluations = []
            for idea in accepted_ideas + rejected_ideas:
                # Create a JudgeEvaluation for each idea
                eval_obj = JudgeEvaluation(
                    idea_id=f"{state.run_id}_{state.iteration}_{idea.get('idea_name', 'unknown').replace(' ', '_')}",
                    idea_name=idea.get('idea_name', 'Unknown Idea'),
                    originality_score=idea.get('originality_score', idea.get('quality_score', 5.0)),
                    feasibility_score=idea.get('feasibility_score', 5.0),
                    impact_score=idea.get('impact_score', 5.0),
                    substance_score=idea.get('substance_score', idea.get('quality_score', 5.0)),
                    overall_quality_score=idea.get('quality_score', 5.0),
                    accepted=idea in accepted_ideas,
                    rejection_reasons=[idea.get('rejection_reason', '')] if idea in rejected_ideas else [],
                    key_points=idea.get('key_points', []),
                    model_id=state.refinement_model or 'unknown',
                    temperature=0.1,  # Judge temperature
                    iteration=state.iteration,
                    evaluation_timestamp=datetime.now(),
                    judge_model=self.judge.judge_model_id
                )
                judge_evaluations.append(eval_obj)
            
            # Save judge evaluations
            self._save_evaluations(state.iteration, judge_evaluations)
            
            # Record to observability
            if self.observability:
                for eval_result in judge_evaluations:
                    self.observability.record_judge_evaluation(eval_result)
            
            # Save accepted ideas to memory and update shared_state
            memory_data = self._save_accepted_ideas_to_memory(accepted_ideas, state.iteration)
            self._update_shared_state_with_judge_results(state, accepted_ideas, rejected_ideas, memory_data)
            
            # Calculate statistics
            idea_stats = self._calculate_idea_statistics_from_judge_data(accepted_ideas, rejected_ideas) if judge_evaluations else None
            
            accepted_count = len(accepted_ideas)
            result_msg = f"Evaluated {len(judge_evaluations)} ideas. Accepted: {accepted_count}"
            
            # Update state with judge output
            updated_state = state.with_updates(
                judge_evaluations=[e.model_dump() for e in judge_evaluations],
                idea_statistics=idea_stats.model_dump() if idea_stats else None,
                accepted_ideas_count=accepted_count,
                success=True
            )
            
            execution_time = int(time.time() - start_time)
            
            return self.create_result(
                message=result_msg,
                state=updated_state,
                execution_time=execution_time
            )
            
        except Exception as e:
            # Create error state preserving original_prompt
            error_state = ExecutionState(
                original_prompt=invocation_state.get('original_prompt', '') if invocation_state else '',
                iteration=invocation_state.get('iteration', 0) if invocation_state else 0,
                run_id=invocation_state.get('run_id', 'unknown') if invocation_state else 'unknown',
                run_dir=invocation_state.get('run_dir', '.') if invocation_state else '.'
            )
            return self.handle_error(e, error_state)
    
    def _extract_ideas_from_content(self, content: str) -> List[str]:
        """Extract individual ideas from agent output (JSON or text format)."""
        return JsonExtractor.extract_ideas_from_any_format(content)
    
    def _calculate_idea_statistics(
        self,
        ideas: List[Dict],
        evaluations: List[JudgeEvaluation]
    ) -> Optional[IdeaStatistics]:
        """Calculate statistics from evaluations."""
        total_ideas = len(ideas)
        unique_ideas = len(set(str(i) for i in ideas))
        duplicate_ideas = total_ideas - unique_ideas
        accepted_ideas = sum(1 for e in evaluations if e.accepted)
        rejected_ideas = sum(1 for e in evaluations if not e.accepted)
        ideas_above_8 = sum(1 for e in evaluations if e.overall_quality_score >= 8.0)
        ideas_above_5 = sum(1 for e in evaluations if e.overall_quality_score >= 5.0)
        
        scores = [e.overall_quality_score for e in evaluations]
        median_score = sorted(scores)[len(scores) // 2] if scores else 0.0
        mean_score = sum(scores) / len(scores) if scores else 0.0
        
        return IdeaStatistics(
            total_ideas=total_ideas,
            unique_ideas=unique_ideas,
            duplicate_ideas=duplicate_ideas,
            accepted_ideas=accepted_ideas,
            rejected_ideas=rejected_ideas,
            ideas_above_8=ideas_above_8,
            ideas_above_5=ideas_above_5,
            median_quality_score=median_score,
            mean_quality_score=mean_score
        )
    
    def _save_evaluations(self, iteration: int, evaluations: List[JudgeEvaluation]) -> None:
        """Save judge evaluations to file."""
        content_lines = []
        content_lines.append(f"INDEPENDENT JUDGE EVALUATION - Iteration {iteration}\n")
        content_lines.append(f"Total Ideas Evaluated: {len(evaluations)}\n")
        content_lines.append(f"Accepted: {sum(1 for e in evaluations if e.accepted)}\n")
        content_lines.append(f"Rejected: {sum(1 for e in evaluations if not e.accepted)}\n\n")
        
        for eval_result in evaluations:
            content_lines.append(f"{'='*80}\n")
            content_lines.append(f"Idea: {eval_result.idea_name}\n")
            content_lines.append(f"Originality: {eval_result.originality_score}/10\n")
            content_lines.append(f"Feasibility: {eval_result.feasibility_score}/10\n")
            content_lines.append(f"Impact: {eval_result.impact_score}/10\n")
            content_lines.append(f"Substance: {eval_result.substance_score}/10\n")
            content_lines.append(f"Overall Quality: {eval_result.overall_quality_score}/10\n")
            content_lines.append(f"Decision: {'ACCEPTED' if eval_result.accepted else 'REJECTED'}\n")
            
            if eval_result.key_points:
                content_lines.append(f"Key Points: {', '.join(eval_result.key_points)}\n")
            if eval_result.rejection_reasons:
                content_lines.append(f"Rejection Reasons: {', '.join(eval_result.rejection_reasons)}\n")
            content_lines.append("\n")
        
        content = ''.join(content_lines)
        filename = f"judge_evaluations_iteration_{iteration}.txt"
        self.save_output(filename, content)
    
    def _evaluate_refinement_output(self, refinement_result: str, state: ExecutionState) -> Dict[str, Any]:
        """Send the refinement output to the judge for parsing and evaluation."""
        try:
            # Build the judge prompt using Jinja2 builder
            from creativity_agent.utilities.jinja_prompt_builder import JudgePromptContext
            
            judge_context = JudgePromptContext(
                refinement_output=refinement_result,
                evaluation_criteria={
                    "originality": "How novel and creative?",
                    "feasibility": "How practical and implementable?",
                    "impact": "What value/benefit would it create?",
                    "substance": "How well-developed and substantial?"
                },
                acceptance_threshold=6.0
            )
            
            prompt = self.judge.jinja_builder.build_judge_prompt(judge_context)
            
            # Get evaluation from judge
            agent_result = self.judge.agent(prompt)
            response_content = agent_result.message['content']
            response_text = response_content[0].get('text', '') if response_content else ''
            
            # Parse the JSON response - extract and validate JSON
            try:
                response_text = response_text.strip()
                logger.debug(f"Raw judge response (first 200 chars): {response_text[:200]}")
                
                # Method 1: Try direct JSON parse first
                try:
                    evaluations_data = json.loads(response_text)
                    logger.info(f"Judge returned {len(evaluations_data.get('accepted_ideas', []))} accepted and {len(evaluations_data.get('rejected_ideas', []))} rejected ideas")
                    return evaluations_data
                except json.JSONDecodeError:
                    # Method 2: Try to strip markdown code blocks
                    cleaned = response_text
                    
                    # Remove various markdown patterns
                    if cleaned.startswith('```json'):
                        cleaned = cleaned[7:].lstrip()
                    elif cleaned.startswith('```'):
                        cleaned = cleaned[3:].lstrip()
                    
                    if cleaned.endswith('```'):
                        cleaned = cleaned[:-3].rstrip()
                    
                    # Try parsing cleaned response
                    evaluations_data = json.loads(cleaned)
                    logger.info(f"Judge returned {len(evaluations_data.get('accepted_ideas', []))} accepted and {len(evaluations_data.get('rejected_ideas', []))} rejected ideas (after markdown stripping)")
                    return evaluations_data
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse judge JSON response: {e}")
                logger.error(f"Raw response first 500 chars: {response_text[:500]}")
                logger.error(f"Raw response last 200 chars: {response_text[-200:]}")
                # Return empty structure as fallback
                return {
                    "accepted_ideas": [],
                    "rejected_ideas": [{"idea_name": "Parse Error", "rejection_reason": f"Failed to parse judge response: {str(e)}"}],
                    "synthesis": "Error in judge evaluation",
                    "top_recommendations": [],
                    "strategic_insights": [],
                    "unresolved_questions": []
                }
            
        except Exception as e:
            logger.error(f"Error in judge evaluation: {e}")
            return {
                "accepted_ideas": [],
                "rejected_ideas": [{"idea_name": "Evaluation Error", "rejection_reason": f"Judge evaluation failed: {str(e)}"}],
                "synthesis": "Error in judge evaluation",
                "top_recommendations": [],
                "strategic_insights": [],
                "unresolved_questions": []
            }
    
    def _calculate_idea_statistics_from_judge_data(
        self,
        accepted_ideas: List[Dict],
        rejected_ideas: List[Dict]
    ) -> Optional[IdeaStatistics]:
        """Calculate statistics from judge's accepted/rejected data."""
        total_ideas = len(accepted_ideas) + len(rejected_ideas)
        
        if total_ideas == 0:
            return None
            
        # Extract scores from accepted ideas
        scores = []
        for idea in accepted_ideas:
            score = idea.get('quality_score', idea.get('overall_quality_score', 5.0))
            scores.append(score)
        
        # For rejected ideas, assume lower scores
        for idea in rejected_ideas:
            score = idea.get('quality_score', 3.0)  # Default lower score for rejected
            scores.append(score)
        
        unique_ideas = total_ideas  # Assume all are unique for now
        duplicate_ideas = 0
        accepted_count = len(accepted_ideas)
        rejected_count = len(rejected_ideas)
        ideas_above_8 = sum(1 for s in scores if s >= 8.0)
        ideas_above_5 = sum(1 for s in scores if s >= 5.0)
        
        
        median_score = sorted(scores)[len(scores) // 2] if scores else 0.0
        mean_score = sum(scores) / len(scores) if scores else 0.0
        
        return IdeaStatistics(
            total_ideas=total_ideas,
            unique_ideas=unique_ideas,
            duplicate_ideas=duplicate_ideas,
            accepted_ideas=accepted_count,
            rejected_ideas=rejected_count,
            ideas_above_8=ideas_above_8,
            ideas_above_5=ideas_above_5,
            median_quality_score=median_score,
            mean_quality_score=mean_score
        )
    
    def _save_accepted_ideas_to_memory(
        self,
        accepted_ideas: List[Dict],
        iteration: int
    ) -> Dict[str, Any]:
        """
        Save accepted ideas to a memory file (ideas.json) for future iterations.
        Returns the saved data for updating shared_state.
        
        Args:
            accepted_ideas: List of accepted idea dictionaries from judge
            iteration: Current iteration number
            
        Returns:
            Dictionary with accepted ideas data to be stored in shared_state
        """
        try:
            # Use run_dir from shared_state if outputs_dir is not available
            output_base = self.outputs_dir or Path(self.shared_state.run_dir)
            memory_file = output_base / "memory" / "ideas.json"
            memory_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing ideas if file exists
            existing_ideas = []
            if memory_file.exists():
                try:
                    with open(memory_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        existing_ideas = data.get('accepted_ideas', [])
                except Exception as e:
                    logger.warning(f"Could not load existing ideas.json: {e}")
            
            # Add new accepted ideas with metadata
            for idea in accepted_ideas:
                idea_record = {
                    **idea,
                    'discovered_in_iteration': iteration,
                    'timestamp': datetime.now().isoformat()
                }
                existing_ideas.append(idea_record)
            
            # Save updated ideas to file
            memory_data = {
                'accepted_ideas': existing_ideas,
                'last_updated': datetime.now().isoformat(),
                'total_accepted': len(existing_ideas),
                'iterations_run': iteration + 1
            }
            
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, default=str)
            
            logger.info(f"Saved {len(accepted_ideas)} accepted ideas to {memory_file}")
            
            return memory_data
            
        except Exception as e:
            logger.error(f"Error saving accepted ideas to memory: {e}")
            return {
                'accepted_ideas': [],
                'error': str(e)
            }
    
    def _update_shared_state_with_judge_results(
        self,
        state: ExecutionState,
        accepted_ideas: List[Dict],
        rejected_ideas: List[Dict],
        memory_data: Dict[str, Any]
    ) -> ExecutionState:
        """
        Update shared state with judge results for access in future iterations.
        
        Args:
            state: Current execution state
            accepted_ideas: List of accepted ideas
            rejected_ideas: List of rejected ideas
            memory_data: Data saved to memory file
            
        Returns:
            Updated execution state with judge results in custom_data
        """
        try:
            # Store judge results in shared_state custom_data for next iteration
            self.shared_state.custom_data['judge_results_iteration_' + str(state.iteration)] = {
                'accepted_count': len(accepted_ideas),
                'rejected_count': len(rejected_ideas),
                'accepted_ideas_names': [idea.get('idea_name', 'unknown') for idea in accepted_ideas],
                'timestamp': datetime.now().isoformat()
            }
            
            # Store reference to memory file
            output_base = self.outputs_dir or Path(self.shared_state.run_dir)
            self.shared_state.custom_data['ideas_memory_file'] = str(output_base / "memory" / "ideas.json")
            self.shared_state.custom_data['total_accepted_ideas'] = memory_data.get('total_accepted', 0)
            
            logger.info(f"Updated shared_state with judge results. Total accepted ideas in memory: {memory_data.get('total_accepted', 0)}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error updating shared_state with judge results: {e}")
            return state


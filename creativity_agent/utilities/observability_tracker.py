"""
Observability and metrics tracking with ElasticSearch integration.
"""
from elasticsearch import Elasticsearch
from typing import Dict, List, Optional, Any
from datetime import datetime
from creativity_agent.models.observability_models import (
    RunMetrics, IterationMetrics, StepMetrics, IdeaStatistics,
    TokenUtilization, ModelType, TemperatureType, StepType, JudgeEvaluation
)
import logging
import time
from statistics import median, mean

logger = logging.getLogger(__name__)


class ObservabilityTracker:
    """
    Tracks comprehensive metrics for creativity agent runs and sends to ElasticSearch.
    """
    
    def __init__(
        self,
        es_uri: str,
        es_api_key: str,
        index_name: str = "super-creativity"
    ):
        """
        Initialize observability tracker with ElasticSearch connection.
        
        Args:
            es_uri: ElasticSearch URI
            es_api_key: ElasticSearch API key
            index_name: Index name for storing metrics
        """
        self.es_client = Elasticsearch(
            [es_uri],
            api_key=es_api_key,
            verify_certs=True
        )
        
        self.index_name = index_name
        
        # Test connection
        try:
            if self.es_client.ping():
                logger.info(f"Successfully connected to ElasticSearch at {es_uri}")
            else:
                logger.error("Failed to ping ElasticSearch")
        except Exception as e:
            logger.error(f"ElasticSearch connection error: {e}")
        
        # Create index if it doesn't exist
        self._ensure_index_exists()
        
        # Current run tracking
        self.current_run: Optional[RunMetrics] = None
        self.current_iteration: Optional[IterationMetrics] = None
        self.current_step_start: Optional[float] = None
    
    def _ensure_index_exists(self):
        """Create the index with proper mappings if it doesn't exist."""
        if not self.es_client.indices.exists(index=self.index_name):
            mappings = {
                "properties": {
                    "run_id": {"type": "keyword"},
                    "run_timestamp": {"type": "date"},
                    "original_prompt": {"type": "text"},
                    "config_iterations": {"type": "integer"},
                    "total_duration_seconds": {"type": "float"},
                    "total_ideas_generated": {"type": "integer"},
                    "final_idea_statistics": {
                        "properties": {
                            "total_ideas": {"type": "integer"},
                            "unique_ideas": {"type": "integer"},
                            "duplicate_ideas": {"type": "integer"},
                            "accepted_ideas": {"type": "integer"},
                            "rejected_ideas": {"type": "integer"},
                            "ideas_above_8": {"type": "integer"},
                            "ideas_above_5": {"type": "integer"},
                            "median_quality_score": {"type": "float"},
                            "mean_quality_score": {"type": "float"}
                        }
                    },
                    "total_token_usage": {
                        "properties": {
                            "input_tokens": {"type": "integer"},
                            "output_tokens": {"type": "integer"},
                            "total_tokens": {"type": "integer"},
                            "estimated_cost_usd": {"type": "float"}
                        }
                    },
                    "model_breakdown": {"type": "object"},
                    "temperature_breakdown": {"type": "object"},
                    "success": {"type": "boolean"},
                    "indexed_at": {"type": "date"}
                }
            }
            
            self.es_client.indices.create(
                index=self.index_name,
                body={"mappings": mappings}
            )
            logger.info(f"Created ElasticSearch index: {self.index_name}")
    
    def start_run(
        self,
        run_id: str,
        original_prompt: str,
        config_iterations: int,
        chaos_seeds_per_iteration: int,
        semantic_backend: str
    ):
        """Start tracking a new run."""
        self.current_run = RunMetrics(
            run_id=run_id,
            run_timestamp=datetime.now(),
            original_prompt=original_prompt,
            config_iterations=config_iterations,
            chaos_seeds_per_iteration=chaos_seeds_per_iteration,
            semantic_backend=semantic_backend,
            iterations=[],
            total_duration_seconds=0.0,
            total_ideas_generated=0,
            final_idea_statistics=IdeaStatistics(
                total_ideas=0,
                unique_ideas=0,
                duplicate_ideas=0,
                accepted_ideas=0,
                rejected_ideas=0
            ),
            total_token_usage=TokenUtilization(
                input_tokens=0,
                output_tokens=0,
                total_tokens=0
            )
        )
        
        logger.info(f"Started tracking run: {run_id}")
    
    def start_iteration(self, iteration_number: int):
        """Start tracking a new iteration."""
        self.current_iteration = IterationMetrics(
            iteration_number=iteration_number,
            steps=[],
            total_duration_seconds=0.0,
            total_ideas_generated=0,
            chaos_seeds_used=0,
            idea_statistics=IdeaStatistics(
                total_ideas=0,
                unique_ideas=0,
                duplicate_ideas=0,
                accepted_ideas=0,
                rejected_ideas=0
            ),
            total_token_usage=TokenUtilization(
                input_tokens=0,
                output_tokens=0,
                total_tokens=0
            )
        )
        
        logger.info(f"Started tracking iteration: {iteration_number}")
    
    def start_step(self):
        """Mark the start of a step for timing."""
        self.current_step_start = time.time()
    
    def end_step(
        self,
        step_id: str,
        model_id: str,
        temperature: float,
        prompt_file: str,
        input_tokens: int,
        output_tokens: int,
        ideas_generated: int = 0,
        web_searches: int = 0,
        cache_hits: int = 0,
        cache_misses: int = 0,
        error: Optional[str] = None
    ):
        """Record a completed step."""
        if self.current_step_start is None:
            duration = 0.0
        else:
            duration = time.time() - self.current_step_start
        
        # Determine model type
        if "claude" in model_id.lower():
            model_type = ModelType.CLAUDE_SONNET_4
        elif "nova" in model_id.lower():
            model_type = ModelType.NOVA_PRO
        else:
            model_type = ModelType.UNKNOWN
        
        # Determine temperature type and step type
        temp_type = TemperatureType.HIGH if temperature >= 0.8 else TemperatureType.LOW
        
        if "creative" in prompt_file or "high" in step_id:
            step_type = StepType.CREATIVE
        elif "refinement" in prompt_file or "low" in step_id:
            step_type = StepType.REFINEMENT
        else:
            step_type = StepType.JUDGE
        
        # Calculate cost estimate (approximate AWS Bedrock pricing)
        cost_per_1k_input = 0.003  # Example: $3 per 1M input tokens = $0.003 per 1k
        cost_per_1k_output = 0.015  # Example: $15 per 1M output tokens = $0.015 per 1k
        estimated_cost = (input_tokens / 1000 * cost_per_1k_input) + (output_tokens / 1000 * cost_per_1k_output)
        
        step_metrics = StepMetrics(
            step_id=step_id,
            model_id=model_id,
            model_type=model_type,
            temperature=temperature,
            temperature_type=temp_type,
            step_type=step_type,
            prompt_file=prompt_file,
            duration_seconds=duration,
            token_usage=TokenUtilization(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                estimated_cost_usd=estimated_cost
            ),
            ideas_generated=ideas_generated,
            web_searches=web_searches,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            error=error,
            success=error is None
        )
        
        if self.current_iteration:
            self.current_iteration.steps.append(step_metrics)
        
        logger.info(f"Recorded step: {step_id} - Duration: {duration:.2f}s, Tokens: {input_tokens + output_tokens}, Ideas: {ideas_generated}")
    
    def end_iteration(
        self,
        chaos_seeds_used: int,
        idea_statistics: IdeaStatistics
    ):
        """Finalize the current iteration."""
        if not self.current_iteration:
            logger.warning("No active iteration to finalize")
            return
        
        # Calculate totals
        self.current_iteration.total_duration_seconds = sum(s.duration_seconds for s in self.current_iteration.steps)
        self.current_iteration.total_ideas_generated = sum(s.ideas_generated for s in self.current_iteration.steps)
        self.current_iteration.chaos_seeds_used = chaos_seeds_used
        self.current_iteration.idea_statistics = idea_statistics
        
        # Total tokens
        total_input = sum(s.token_usage.input_tokens for s in self.current_iteration.steps)
        total_output = sum(s.token_usage.output_tokens for s in self.current_iteration.steps)
        total_cost = sum(s.token_usage.estimated_cost_usd or 0 for s in self.current_iteration.steps)
        
        self.current_iteration.total_token_usage = TokenUtilization(
            input_tokens=total_input,
            output_tokens=total_output,
            total_tokens=total_input + total_output,
            estimated_cost_usd=total_cost
        )
        
        if self.current_run:
            self.current_run.iterations.append(self.current_iteration)
        
        logger.info(f"Finalized iteration {self.current_iteration.iteration_number}")
        self.current_iteration = None
    
    def end_run(
        self,
        final_idea_statistics: IdeaStatistics,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Finalize and send the run metrics to ElasticSearch."""
        if not self.current_run:
            logger.warning("No active run to finalize")
            return
        
        # Calculate run totals
        self.current_run.total_duration_seconds = sum(i.total_duration_seconds for i in self.current_run.iterations)
        self.current_run.total_ideas_generated = sum(i.total_ideas_generated for i in self.current_run.iterations)
        self.current_run.final_idea_statistics = final_idea_statistics
        
        # Total tokens
        total_input = sum(i.total_token_usage.input_tokens for i in self.current_run.iterations)
        total_output = sum(i.total_token_usage.output_tokens for i in self.current_run.iterations)
        total_cost = sum(i.total_token_usage.estimated_cost_usd or 0 for i in self.current_run.iterations)
        
        self.current_run.total_token_usage = TokenUtilization(
            input_tokens=total_input,
            output_tokens=total_output,
            total_tokens=total_input + total_output,
            estimated_cost_usd=total_cost
        )
        
        # Model breakdown
        model_stats: Dict[str, Dict[str, Any]] = {}
        for iteration in self.current_run.iterations:
            for step in iteration.steps:
                model_key = step.model_type.value
                if model_key not in model_stats:
                    model_stats[model_key] = {
                        "total_duration_seconds": 0.0,
                        "total_tokens": 0,
                        "total_ideas": 0,
                        "step_count": 0
                    }
                
                model_stats[model_key]["total_duration_seconds"] += step.duration_seconds
                model_stats[model_key]["total_tokens"] += step.token_usage.total_tokens
                model_stats[model_key]["total_ideas"] += step.ideas_generated
                model_stats[model_key]["step_count"] += 1
        
        self.current_run.model_breakdown = model_stats
        
        # Temperature breakdown
        temp_stats: Dict[str, Dict[str, Any]] = {}
        for iteration in self.current_run.iterations:
            for step in iteration.steps:
                temp_key = step.temperature_type.value
                if temp_key not in temp_stats:
                    temp_stats[temp_key] = {
                        "total_duration_seconds": 0.0,
                        "total_tokens": 0,
                        "total_ideas": 0,
                        "step_count": 0
                    }
                
                temp_stats[temp_key]["total_duration_seconds"] += step.duration_seconds
                temp_stats[temp_key]["total_tokens"] += step.token_usage.total_tokens
                temp_stats[temp_key]["total_ideas"] += step.ideas_generated
                temp_stats[temp_key]["step_count"] += 1
        
        self.current_run.temperature_breakdown = temp_stats
        
        self.current_run.success = success
        self.current_run.error = error
        self.current_run.indexed_at = datetime.now()
        
        # Send to ElasticSearch
        self._send_to_elasticsearch()
        
        logger.info(f"Finalized run: {self.current_run.run_id}")
        self.current_run = None
    
    def _send_to_elasticsearch(self):
        """Send the current run metrics to ElasticSearch."""
        if not self.current_run:
            logger.warning("No run to send to ElasticSearch")
            return
        
        try:
            # Convert to dict for indexing
            doc = self.current_run.model_dump(mode='json')
            
            # Index to ElasticSearch
            response = self.es_client.index(
                index=self.index_name,
                id=self.current_run.run_id,
                body=doc
            )
            
            logger.info(f"Successfully indexed run {self.current_run.run_id} to ElasticSearch: {response['result']}")
            
        except Exception as e:
            logger.error(f"Failed to index run to ElasticSearch: {e}")
    
    def record_judge_evaluation(self, evaluation: JudgeEvaluation):
        """Record a judge evaluation (can be used for separate judge tracking)."""
        try:
            # Index judge evaluation separately for detailed analysis
            judge_index = f"{self.index_name}-judge-evaluations"
            
            doc = evaluation.model_dump(mode='json')
            
            self.es_client.index(
                index=judge_index,
                id=evaluation.idea_id,
                body=doc
            )
            
            logger.info(f"Recorded judge evaluation for: {evaluation.idea_name}")
            
        except Exception as e:
            logger.error(f"Failed to record judge evaluation: {e}")

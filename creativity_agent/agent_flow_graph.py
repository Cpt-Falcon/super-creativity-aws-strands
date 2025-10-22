#!/usr/bin/env python3
"""
Graph-based Creativity Agent Flow

A multi-agent graph with feedback loops for creative ideation using:
1. Chaos Generator (divergent thinking)
2. High-temperature creative agent
3. Low-temperature refinement agent
4. Independent judge evaluation
5. Iteration control
6. Deep research expansion

This replaces the manual flow control with a clean graph architecture.
"""

from strands import Agent
from strands.multiagent import GraphBuilder
from strands.models import BedrockModel
from typing import Optional
import os
import logging
from pathlib import Path
from datetime import datetime
from creativity_agent.config import FlowConfig
from creativity_agent.tools import search_web, get_url_content, bulk_search_web, set_web_cache
from creativity_agent.utilities import (
    MemoryManager, ChaosGenerator,
    GlobalWebCache, IndependentJudge, ObservabilityTracker,
    JinjaPromptBuilder
)
from creativity_agent.models import IdeaStatistics, ExecutionState, SharedState
from creativity_agent.nodes import (
    ChaosGeneratorNode, IterationControllerNode, JudgeNode,
    MockAgent, MockChaosNode, MockJudgeNode,
    CreativeAgentNode, RefinementAgentNode
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CreativityAgentFlowGraph:
    """Graph-based creativity flow with automatic loop control."""
    
    def __init__(
        self,
        config: FlowConfig,
        enable_memory: bool = True,
        enable_observability: bool = True,
        chaos_seeds_per_iteration: int = 3,
        semantic_backend: str = "auto",
        es_uri: Optional[str] = None,
        es_api_key: Optional[str] = None,
        global_cache_dir: Optional[Path] = None,
        mock_mode: bool = False
    ):
        self.config = config
        self.mock_mode = mock_mode
        self.base_outputs_dir = Path(__file__).parent / "outputs"
        self.base_outputs_dir.mkdir(exist_ok=True)
        
        # Create timestamped run directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"run_{timestamp}"
        self.run_dir = self.base_outputs_dir / self.run_id
        self.run_dir.mkdir(exist_ok=True)
        
        logger.info(f"Created run directory: {self.run_dir}")
        
        self.enable_memory = enable_memory
        self.enable_observability = enable_observability
        self.chaos_seeds_per_iteration = chaos_seeds_per_iteration
        
        # Initialize Jinja2 prompt builder (always required)
        self.jinja_builder = JinjaPromptBuilder()
        logger.info("Jinja2 prompt builder initialized")
        
        # Initialize global web cache
        if global_cache_dir is None:
            global_cache_dir = self.base_outputs_dir / "global_cache"
        self.global_web_cache = GlobalWebCache(global_cache_dir)
        logger.info(f"Global web cache initialized at {global_cache_dir}")
        
        # Set the global web cache for the tools module
        set_web_cache(self.global_web_cache)

        
        # Initialize memory manager
        if self.enable_memory:
            memory_dir = self.run_dir / "memory"
            self.memory_manager = MemoryManager(memory_dir)
            self.memory_manager.load_memory()
            logger.info(f"Memory system enabled")
        else:
            self.memory_manager = None
        
        # Initialize independent judge
        self.judge = IndependentJudge(
            jinja_builder=self.jinja_builder,
            judge_model_id=config.judge.model_id,
            judge_temperature=config.judge.temperature,
            streaming=config.judge.streaming,
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
        logger.info(f"Independent judge enabled ({config.judge.model_id})")
        
        # Initialize observability
        if self.enable_observability and es_uri and es_api_key:
            self.observability = ObservabilityTracker(
                es_uri=es_uri,
                es_api_key=es_api_key,
                index_name="super-creativity"
            )
            logger.info("Observability tracking enabled (ElasticSearch)")
        else:
            self.observability = None

        # Initialize chaos generator
        self.chaos_generator = ChaosGenerator(
            model_id=config.chaos_generator.model_id,
            temperature=config.chaos_generator.temperature,
            streaming=config.chaos_generator.streaming,
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
            semantic_backend=semantic_backend,
            tangent_range=(0.3, 0.7)
        )
        logger.info("Chaos generator enabled")
        
        # Create model instances
        self.models = {}
        for model_key, model_config in config.models.items():
            self.models[f"{model_key}_high"] = BedrockModel(
                model_id=model_config.model_id,
                temperature=model_config.high_temp,
                streaming=model_config.streaming,
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
            )
            self.models[f"{model_key}_low"] = BedrockModel(
                model_id=model_config.model_id,
                temperature=model_config.low_temp,
                streaming=model_config.streaming,
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            )
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the multi-agent graph with feedback loops.
        
        Graph flow (like a for loop, SEQUENTIAL):
        iteration_controller (condition check) 
            -> if not done: chaos_generator 
                -> model_A_creative 
                -> model_A_refinement 
                -> model_A_judge
                -> model_B_creative 
                -> model_B_refinement
                -> model_B_judge
                -> back to iteration_controller
            -> if done: deep_research
        
        Note: Each iteration runs through all model chains SEQUENTIALLY.
        Each model chain: creative (high temp) -> refinement (low temp) -> judge
        Each model gets its own judge instance to avoid graph flow conflicts.
        
        The original prompt flows through invocation_state to all nodes.
        """
        # Create SharedState instance for coordinating all nodes
        shared_state = SharedState(
            current_iteration=0,
            max_iterations=self.config.iterations,
            run_id=self.run_id,
            run_dir=str(self.run_dir)
        )
        logger.info(f"Created SharedState for graph with max_iterations={self.config.iterations}")
        
        builder = GraphBuilder()
        
        # Create chaos generator node
        if self.mock_mode:
            chaos_node = MockChaosNode(
                shared_state=shared_state,
                chaos_seeds_per_iteration=self.chaos_seeds_per_iteration,
                outputs_dir=self.run_dir
            )
        elif self.chaos_generator:
            chaos_node = ChaosGeneratorNode(
                shared_state=shared_state,
                chaos_generator=self.chaos_generator,
                chaos_seeds_per_iteration=self.chaos_seeds_per_iteration,
                outputs_dir=self.run_dir,
                jinja_builder=self.jinja_builder
            )
        else:
            raise ValueError("Chaos generator must be provided or mock_mode enabled")
        
        builder.add_node(chaos_node, "chaos_generator")
        
        # Create creative, refinement, and judge agents for each model (in order)
        # These will be chained sequentially
        agent_chain = []  # List of (creative_name, refinement_name, judge_name) tuples
        
        for model_key in self.config.models.keys():
            creative_agent_name = f"{model_key}_creative"
            refinement_agent_name = f"{model_key}_refinement"
            judge_agent_name = f"{model_key}_judge"
            
            # Create creative agent (high temperature)
            if self.mock_mode:
                creative_agent = MockAgent(
                    shared_state=shared_state,
                    name=creative_agent_name,
                    agent_type="creative",
                    outputs_dir=self.run_dir
                )
            else:
                agent = Agent(
                    name=creative_agent_name,
                    model=self.models[f"{model_key}_high"],
                    tools=[search_web, get_url_content, bulk_search_web],
                    system_prompt=self.jinja_builder.get_creative_agent_system_prompt()
                )
                creative_agent = CreativeAgentNode(
                    shared_state=shared_state,
                    agent=agent,
                    node_name=creative_agent_name,
                    outputs_dir=self.run_dir,
                    memory_manager=self.memory_manager,
                    jinja_builder=self.jinja_builder
                )
            builder.add_node(creative_agent, creative_agent_name)
            
            # Create refinement agent (low temperature)
            if self.mock_mode:
                refinement_agent = MockAgent(
                    shared_state=shared_state,
                    name=refinement_agent_name,
                    agent_type="refinement",
                    outputs_dir=self.run_dir
                )
            else:
                agent = Agent(
                    name=refinement_agent_name,
                    model=self.models[f"{model_key}_low"],
                    tools=[search_web, get_url_content, bulk_search_web],
                    system_prompt=self.jinja_builder.get_refinement_agent_system_prompt()
                )
                refinement_agent = RefinementAgentNode(
                    shared_state=shared_state,
                    agent=agent,
                    node_name=refinement_agent_name,
                    outputs_dir=self.run_dir,
                    memory_manager=self.memory_manager,
                    jinja_builder=self.jinja_builder
                )
            builder.add_node(refinement_agent, refinement_agent_name)
            
            # Create judge node for this model
            if self.mock_mode:
                judge_node = MockJudgeNode(shared_state=shared_state, outputs_dir=self.run_dir)
            elif self.judge:
                judge_node = JudgeNode(
                    shared_state=shared_state,
                    judge=self.judge,
                    observability=self.observability,
                    outputs_dir=self.run_dir
                )
            else:
                judge_node = None
            
            if judge_node:
                builder.add_node(judge_node, judge_agent_name)
            
            # Store the triple for building the chain
            agent_chain.append((creative_agent_name, refinement_agent_name, judge_agent_name if judge_node else None))
        
        # Create iteration controller (acts like the for loop condition)
        iteration_controller = IterationControllerNode(shared_state=shared_state)
        builder.add_node(iteration_controller, "iteration_controller")
        
        # Create deep research agent (final step after iterations complete)
        final_model_key = list(self.config.models.keys())[0]
        if self.mock_mode:
            deep_research_agent = MockAgent(
                shared_state=shared_state,
                name="deep_research",
                agent_type="final",
                outputs_dir=self.run_dir
            )
        else:
            deep_research_agent = Agent(
                name="deep_research",
                model=self.models[f"{final_model_key}_low"],
                tools=[search_web, get_url_content, bulk_search_web]
            )
        builder.add_node(deep_research_agent, "deep_research")
        
        # Conditional functions following AWS Strands documentation pattern
        def should_continue_iterating(state):
            """Loop condition: if iterations remain, continue to chaos generator."""
            controller_result = state.results.get("iteration_controller")
            if not controller_result:
                return False
            
            try:
                # The result should be a MultiAgentResult with the state updates
                result_obj = controller_result.result
                if hasattr(result_obj, 'results') and 'iteration_controller' in result_obj.results:
                    node_result = result_obj.results['iteration_controller']
                    if hasattr(node_result, 'state'):
                        return node_result.state.get("should_continue", False)
                
                # Fallback: check the result message
                result_text = str(result_obj)
                return "Starting iteration" in result_text or "complete. Starting" in result_text
            except (AttributeError, KeyError):
                return False
        
        def is_done_iterating(state):
            """Exit condition: if all iterations complete, proceed to deep research."""
            controller_result = state.results.get("iteration_controller")
            if not controller_result:
                return False
            
            try:
                # The result should be a MultiAgentResult with the state updates
                result_obj = controller_result.result
                if hasattr(result_obj, 'results') and 'iteration_controller' in result_obj.results:
                    node_result = result_obj.results['iteration_controller']
                    if hasattr(node_result, 'state'):
                        return node_result.state.get("is_finished", False)
                
                # Fallback: check the result message
                result_text = str(result_obj)
                return "Proceeding to deep research" in result_text or "All" in result_text and "iterations complete" in result_text
            except (AttributeError, KeyError):
                return False
        
        # Build the graph edges - SEQUENTIAL chain of all models with per-model judges
        # Entry point is iteration controller (like the for loop condition check)
        builder.set_entry_point("iteration_controller")
        
        # From iteration controller: if iterations remain, go to chaos generator
        builder.add_edge("iteration_controller", "chaos_generator", condition=should_continue_iterating)
        
        # From iteration controller: if done, go to deep research
        builder.add_edge("iteration_controller", "deep_research", condition=is_done_iterating)
        
        # Build the sequential chain: chaos -> A_creative -> A_refinement -> A_judge -> B_creative -> B_refinement -> B_judge -> ... -> iteration_controller
        previous_node = "chaos_generator"
        for i, (creative_name, refinement_name, judge_name) in enumerate(agent_chain):
            builder.add_edge(previous_node, creative_name)
            builder.add_edge(creative_name, refinement_name)
            builder.add_edge(refinement_name, judge_name)
            previous_node = judge_name
        
        # Connect last judge/refinement back to iteration controller for the next condition check
        builder.add_edge(previous_node, "iteration_controller")
        
        # Graph execution settings for cyclic graphs
        # Each iteration: chaos + (3 nodes per model: creative + refinement + judge) + controller
        num_models = len(self.config.models)
        nodes_per_iteration = 1 + (num_models * 3) + 1  # chaos + models(creative+refinement+judge) + controller
        builder.set_max_node_executions(self.config.iterations * nodes_per_iteration + 10)
        builder.set_execution_timeout(600)  # 10 minutes max
        builder.reset_on_revisit(False)  # Keep state across iterations
        
        return builder.build()
    
    def run(self, user_prompt: str) -> str:
        """Run the creativity flow graph for multiple iterations.
        
        The graph operates like a for loop:
        - iteration_controller checks if iterations remain (entry point)
        - If yes: chaos_generator -> creative -> refinement -> judge -> back to controller
        - If no: proceed to deep_research
        
        The user_prompt flows through ExecutionState to all nodes with full type safety.
        """
        logger.info(f"Starting graph-based creativity flow for {self.config.iterations} iterations")
        logger.info(f"Original prompt: {user_prompt}\n")
        
        # Start observability
        if self.observability:
            self.observability.start_run(
                run_id=self.run_id,
                original_prompt=user_prompt,
                config_iterations=self.config.iterations,
                chaos_seeds_per_iteration=self.chaos_seeds_per_iteration,
                semantic_backend="auto"
            )
        
        # Create typed ExecutionState for graph execution
        initial_state = ExecutionState(
            original_prompt=user_prompt,
            iteration=0,
            run_id=self.run_id,
            run_dir=str(self.run_dir),
            max_iterations=self.config.iterations,
            start_time=datetime.now().isoformat()
        )
        
        # Run the entire graph once with typed state
        # The iteration_controller and conditional edges will handle the loop internally
        logger.info("Executing graph with iteration control and typed state...")
        result = self.graph(
            user_prompt,
            invocation_state=initial_state.to_dict()
        )
        
        # Print execution summary
        print("\n" + "="*80)
        print("GRAPH EXECUTION SUMMARY")
        print("="*80)
        print("\n--- Execution Order ---")
        for i, node in enumerate(result.execution_order, 1):
            print(f"{i}. {node.node_id}")
        
        print(f"\n--- Performance Metrics ---")
        print(f"Total nodes in graph: {result.total_nodes}")
        print(f"Completed nodes: {result.completed_nodes}")
        print(f"Failed nodes: {result.failed_nodes}")
        print(f"Execution time: {result.execution_time}ms")
        print(f"Token usage: {result.accumulated_usage}")
        print("="*80 + "\n")
        
        # Extract final output
        final_output = None
        
        # Prefer deep_research output (final step)
        if "deep_research" in result.results:
            final_output = str(result.results['deep_research'].result)
        else:
            # Fallback to last judge output if deep_research wasn't executed
            judge_results = [k for k in result.results.keys() if 'judge' in k]
            if judge_results:
                last_judge = judge_results[-1]
                judge_raw_output = str(result.results[last_judge].result)
                # Format judge JSON output as a readable summary
                final_output = self._format_judge_output_as_summary(judge_raw_output)
            else:
                # Last resort: check for any refinement output
                refinement_results = [k for k in result.results.keys() if 'refinement' in k]
                if refinement_results:
                    last_refinement = refinement_results[-1]
                    final_output = str(result.results[last_refinement].result)
        
        # End observability
        if self.observability:
            final_stats = IdeaStatistics(
                total_ideas=0,
                unique_ideas=0,
                duplicate_ideas=0,
                accepted_ideas=0,
                rejected_ideas=0
            )
            self.observability.end_run(
                final_idea_statistics=final_stats,
                success=result.status.value == "COMPLETED"
            )
        
        # Save final output with formatting
        if final_output is None:
            final_output = "No final output generated"
            logger.warning("No final output was generated by the graph")
        
        from creativity_agent.utilities import save_formatted_output
        output_file = self.run_dir / "final_output.txt"
        save_formatted_output(
            output_path=output_file,
            result=final_output,
            original_prompt=user_prompt,
            iteration_count=self.config.iterations,
            is_mock=self.mock_mode
        )
        logger.info(f"Saved final output to {output_file}")
        logger.info("Graph-based creativity flow completed successfully")
        
        return final_output
    
    def _format_judge_output_as_summary(self, judge_output: str) -> str:
        """
        Convert judge JSON output to a readable summary report.
        
        Args:
            judge_output: Judge output (either JSON or already formatted)
            
        Returns:
            Formatted summary text
        """
        import json
        
        try:
            # Try to parse as JSON
            judge_data = None
            
            # First try direct JSON parse
            try:
                judge_data = json.loads(judge_output)
            except json.JSONDecodeError:
                # Try to extract JSON from text if it contains markdown
                if '```json' in judge_output:
                    start = judge_output.find('{')
                    end = judge_output.rfind('}') + 1
                    if start >= 0 and end > start:
                        judge_data = json.loads(judge_output[start:end])
                elif '{' in judge_output:
                    start = judge_output.find('{')
                    end = judge_output.rfind('}') + 1
                    if start >= 0 and end > start:
                        judge_data = json.loads(judge_output[start:end])
            
            if judge_data is None:
                # Could not parse, return as-is
                return judge_output
            
            # Build formatted summary
            lines = []
            lines.append("=" * 80)
            lines.append("JUDGE EVALUATION SUMMARY")
            lines.append("=" * 80)
            
            # Accepted ideas
            accepted = judge_data.get('accepted_ideas', [])
            if accepted:
                lines.append(f"\nACCEPTED IDEAS ({len(accepted)} total):")
                lines.append("-" * 80)
                for i, idea in enumerate(accepted, 1):
                    lines.append(f"\n{i}. {idea.get('idea_name', 'Unknown')}")
                    lines.append(f"   Quality Score: {idea.get('quality_score', 'N/A')}/10")
                    lines.append(f"   Feasibility: {idea.get('feasibility_score', 'N/A')}/10")
                    lines.append(f"   Impact: {idea.get('impact_score', 'N/A')}/10")
                    lines.append(f"   Originality: {idea.get('originality_score', 'N/A')}/10")
                    
                    if idea.get('key_points'):
                        lines.append("   Key Points:")
                        for point in idea['key_points'][:3]:
                            lines.append(f"     - {point}")
                    
                    if idea.get('implementation_path'):
                        lines.append(f"   Implementation: {idea['implementation_path'][:100]}...")
            
            # Rejected ideas
            rejected = judge_data.get('rejected_ideas', [])
            if rejected:
                lines.append(f"\n\nREJECTED IDEAS ({len(rejected)} total):")
                lines.append("-" * 80)
                for i, idea in enumerate(rejected, 1):
                    lines.append(f"\n{i}. {idea.get('idea_name', 'Unknown')}")
                    lines.append(f"   Reason: {idea.get('rejection_reason', 'No details provided')}")
            
            # Synthesis
            synthesis = judge_data.get('synthesis')
            if synthesis:
                lines.append(f"\n\nSYNTHESIS:")
                lines.append("-" * 80)
                lines.append(synthesis)
            
            # Top recommendations
            recommendations = judge_data.get('top_recommendations', [])
            if recommendations:
                lines.append(f"\n\nTOP RECOMMENDATIONS:")
                lines.append("-" * 80)
                for i, rec in enumerate(recommendations, 1):
                    lines.append(f"{i}. {rec}")
            
            # Strategic insights
            insights = judge_data.get('strategic_insights', [])
            if insights:
                lines.append(f"\n\nSTRATEGIC INSIGHTS:")
                lines.append("-" * 80)
                for i, insight in enumerate(insights, 1):
                    lines.append(f"{i}. {insight}")
            
            # Unresolved questions
            questions = judge_data.get('unresolved_questions', [])
            if questions:
                lines.append(f"\n\nUNRESOLVED QUESTIONS:")
                lines.append("-" * 80)
                for i, question in enumerate(questions, 1):
                    lines.append(f"{i}. {question}")
            
            lines.append("\n" + "=" * 80)
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error formatting judge output: {e}")
            return judge_output


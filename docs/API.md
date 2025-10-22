# API Reference

## Main Entry Point

### CreativityAgentFlowGraph

**Location**: `creativity_agent/agent_flow_graph.py`

Main class for orchestrating the complete creativity flow.

```python
from creativity_agent.agent_flow_graph import CreativityAgentFlowGraph
from creativity_agent.config import FlowConfig
from pathlib import Path

# Load configuration
config = FlowConfig.from_json(Path("flow_config.json"))

# Create flow instance
flow = CreativityAgentFlowGraph(
    config=config,
    enable_memory=True,
    enable_chaos=True,
    enable_judge=True,
    enable_observability=True,
    chaos_seeds_per_iteration=3,
    semantic_backend="auto",
    es_uri="https://elastic.example.com",
    es_api_key="your-key",
    mock_mode=False
)

# Run the flow
result = flow.run("Your creative prompt here")
print(f"Results saved to: {flow.run_dir}")
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | FlowConfig | Required | Flow configuration |
| `enable_memory` | bool | True | Track explored/rejected ideas |
| `enable_chaos` | bool | True | Generate tangential concepts |
| `enable_judge` | bool | True | Independent evaluation |
| `enable_observability` | bool | True | ElasticSearch tracking |
| `chaos_seeds_per_iteration` | int | 3 | Number of chaos seeds |
| `semantic_backend` | str | "auto" | Word discovery backend: auto/sentence-transformers/gensim/wordnet/simple |
| `es_uri` | str | None | ElasticSearch URI |
| `es_api_key` | str | None | ElasticSearch API key |
| `global_cache_dir` | Path | outputs/global_cache | Web cache directory |
| `mock_mode` | bool | False | Use mock agents (no LLM calls) |

#### Methods

##### `run(user_prompt: str) -> str`

Execute the full creativity flow.

```python
result = flow.run("Design an innovative water filtration system")
# Returns: Final synthesized creative output (str)
# Side effects: Creates run directory with all outputs
```

**Returns**: Final synthesized creative solution

**Output Files Created**:
- `chaos_input_iteration_*.txt` - Chaos seeds per iteration
- `A_creative_iteration_*.txt` - Creative agent A outputs
- `A_refinement_iteration_*.txt` - Refinement agent A outputs
- `B_creative_iteration_*.txt` - Creative agent B outputs
- `B_refinement_iteration_*.txt` - Refinement agent B outputs
- `judge_evaluations_iteration_*.txt` - Judge evaluations
- `memory/idea_memory.json` - Memory state
- `final_output.txt` - Final synthesized result

#### Properties

```python
flow.run_dir: Path          # Output directory for this run
flow.run_id: str            # Unique run identifier (run_YYYYMMDD_HHMMSS)
flow.memory_manager: MemoryManager or None
flow.chaos_generator: ChaosGenerator or None
flow.judge: IndependentJudge or None
flow.observability: ObservabilityTracker or None
flow.graph: Graph            # The Strands graph object
```

---

## Utilities

### MemoryManager

**Location**: `creativity_agent/utilities/memory_manager.py`

Manage persistent memory of explored and rejected ideas.

```python
from creativity_agent.utilities.memory_manager import MemoryManager
from pathlib import Path

memory = MemoryManager(Path("outputs/memory"))
memory.load_memory()
```

#### Methods

##### `load_memory() -> IdeaMemory`

Load memory from disk.

```python
memory_state = memory.load_memory()
# memory_state.explored_ideas: List[ExploredIdea]
# memory_state.rejected_ideas: List[RejectedIdea]
```

##### `save_memory() -> None`

Persist memory to disk.

```python
memory.save_memory()
# Saves to: memory_dir/idea_memory.json
```

##### `extract_concepts_from_text(text: str, iteration: int, max_concepts: int = 20, is_high_temp: bool = True) -> None`

Extract concepts from agent output and add to memory.

```python
memory.extract_concepts_from_text(
    text=agent_output,
    iteration=0,
    max_concepts=10,
    is_high_temp=True  # From creative agent
)
# Updates: memory_state.explored_ideas
# Saves: idea_memory.json
```

##### `add_explored_idea(idea: str, iteration: int, source: str) -> None`

Manually add an explored idea.

```python
memory.add_explored_idea(
    idea="Blockchain-based voting system",
    iteration=0,
    source="creative_agent_A"
)
```

##### `reject_idea(idea: str, reason: str) -> None`

Mark an idea as rejected.

```python
memory.reject_idea(
    idea="Blockchain-based voting system",
    reason="Too speculative, lacks feasibility"
)
```

##### `get_memory_context() -> str`

Get formatted memory context for prompt injection.

```python
context = memory.get_memory_context()
# Returns formatted string like:
# """
# PREVIOUSLY EXPLORED IDEAS:
# - Blockchain voting system (iteration 0)
# - IoT sensor network (iteration 0)
# 
# REJECTED IDEAS:
# - Blockchain tokens: Too speculative
# """
```

---

### ChaosGenerator

**Location**: `creativity_agent/utilities/chaos_generator.py`

Generate divergent exploration seeds using semantic discovery.

```python
from creativity_agent.utilities.chaos_generator import ChaosGenerator

chaos = ChaosGenerator(
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    temperature=1.0,
    semantic_backend="sentence-transformers",
    tangent_range=(0.3, 0.7)
)
```

#### Methods

##### `generate_chaos_seeds(prompt: str, num_seeds: int = 3) -> List[str]`

Generate tangential seed words.

```python
seeds = chaos.generate_chaos_seeds(
    prompt="Design an urban farming solution",
    num_seeds=5
)
# Returns: ["mycelium", "tessellation", "stochastic", ...]
```

##### `generate_chaos_input(original_prompt: str, num_seeds: int = 3) -> ChaosInput`

Generate fully researched chaos input.

```python
chaos_input = chaos.generate_chaos_input(
    original_prompt="Design an urban farming solution",
    num_seeds=3
)

# chaos_input.original_prompt: str
# chaos_input.random_seeds: List[str]
# chaos_input.tangential_concepts: List[TangentialConcept]
#   - Each has: term, context, relevance_note
```

---

### IndependentJudge

**Location**: `creativity_agent/utilities/independent_judge.py`

Evaluate ideas with Claude 4.5 Sonnet.

```python
from creativity_agent.utilities.independent_judge import IndependentJudge

judge = IndependentJudge(region_name="us-east-1")
```

#### Methods

##### `evaluate_ideas(ideas: str, original_prompt: str) -> JudgeEvaluation`

Evaluate creative ideas with standardized rubric.

```python
evaluation = judge.evaluate_ideas(
    ideas="""
    Idea 1: Vertical LED-lit growing pods
    - Modular design with IoT sensors
    - Auto-irrigation and nutrient delivery
    
    Idea 2: Aeroponic towers with renewable energy
    - Grows crops in mist without soil
    - Solar panels for greenhouse power
    """,
    original_prompt="Design an innovative urban farming solution"
)

# evaluation.ideas: List[IdeaScore]
# evaluation.reasoning: str
# evaluation.accepted_count: int
# evaluation.rejected_count: int
# evaluation.average_score: float
```

##### `score_idea(idea: str, original_prompt: str) -> IdeaScore`

Score a single idea.

```python
score = judge.score_idea(
    idea="LED-lit vertical farming pods",
    original_prompt="Design an innovative urban farming solution"
)

# score.idea: str
# score.originality: float (0-10)
# score.technical_feasibility: float (0-10)
# score.impact_potential: float (0-10)
# score.substance: float (0-10)
# score.average_score: float
# score.accepted: bool (True if average >= 5.0)
# score.reasoning: str
```

---

### ObservabilityTracker

**Location**: `creativity_agent/utilities/observability_tracker.py`

Track metrics in ElasticSearch for monitoring and analysis.

```python
from creativity_agent.utilities.observability_tracker import ObservabilityTracker

tracker = ObservabilityTracker(
    es_uri="https://elastic.example.com",
    es_api_key="your-key",
    index_name="super-creativity"
)
```

#### Methods

##### `start_run(run_id: str, original_prompt: str, config_iterations: int, chaos_seeds_per_iteration: int, semantic_backend: str) -> None`

Record the start of a run.

```python
tracker.start_run(
    run_id="run_20251020_123456",
    original_prompt="Design an urban farming solution",
    config_iterations=2,
    chaos_seeds_per_iteration=3,
    semantic_backend="sentence-transformers"
)
```

##### `end_run(final_idea_statistics: IdeaStatistics, success: bool) -> None`

Record the end of a run.

```python
from creativity_agent.models.observability_models import IdeaStatistics

tracker.end_run(
    final_idea_statistics=IdeaStatistics(
        total_ideas=45,
        unique_ideas=42,
        duplicate_ideas=3,
        accepted_ideas=38,
        rejected_ideas=4
    ),
    success=True
)
```

##### `track_step(step_id: str, model_id: str, temperature: float, input_tokens: int, output_tokens: int, execution_time: float, ideas_count: int) -> None`

Track individual step metrics.

```python
tracker.track_step(
    step_id="A_creative_iteration_0",
    model_id="claude-sonnet-4",
    temperature=1.0,
    input_tokens=2048,
    output_tokens=1024,
    execution_time=45.5,
    ideas_count=8
)
```

---

## Models (Pydantic)

### IdeaMemory

**Location**: `creativity_agent/models/memory_models.py`

```python
from creativity_agent.models import IdeaMemory

class IdeaMemory(BaseModel):
    explored_ideas: List[ExploredIdea]
    rejected_ideas: List[RejectedIdea]
    created_at: datetime
    last_updated: datetime
    
class ExploredIdea(BaseModel):
    content: str
    iteration: int
    source: str  # e.g., "creative_agent_A"
    timestamp: datetime
    quality_score: Optional[float]
    
class RejectedIdea(BaseModel):
    content: str
    reason: str
    rejected_at: datetime
```

### ChaosInput

**Location**: `creativity_agent/models/chaos_models.py`

```python
from creativity_agent.models import ChaosInput, TangentialConcept

class ChaosInput(BaseModel):
    original_prompt: str
    random_seeds: List[str]
    tangential_concepts: List[TangentialConcept]
    generated_at: datetime
    
class TangentialConcept(BaseModel):
    term: str
    context: str  # What it is in reality
    relevance_note: str  # How it might inspire ideas
```

### JudgeEvaluation

**Location**: `creativity_agent/models/observability_models.py`

```python
from creativity_agent.models import JudgeEvaluation, IdeaScore

class JudgeEvaluation(BaseModel):
    ideas: List[IdeaScore]
    reasoning: str
    accepted_count: int
    rejected_count: int
    average_score: float
    evaluated_at: datetime
    
class IdeaScore(BaseModel):
    idea: str
    originality: float  # 0-10
    technical_feasibility: float  # 0-10
    impact_potential: float  # 0-10
    substance: float  # 0-10
    average_score: float
    accepted: bool  # True if average >= 5.0
    reasoning: str
```

---

## Configuration

### FlowConfig

**Location**: `creativity_agent/config.py`

```python
from creativity_agent.config import FlowConfig
from pathlib import Path

config = FlowConfig.from_json(Path("flow_config.json"))

# Properties:
config.iterations: int
config.models: Dict[str, ModelConfig]  # {"A": ModelConfig, "B": ModelConfig}
config.steps: List[StepConfig]
config.loop_back_to: Optional[str]
config.final_step: str
```

#### Methods

##### `from_json(json_path: Path) -> FlowConfig`

Load configuration from JSON file.

```python
config = FlowConfig.from_json(Path("creativity_agent/flow_config.json"))
```

Example `flow_config.json`:
```json
{
  "iterations": 2,
  "models": {
    "A": {
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
      "high_temp": 1.0,
      "low_temp": 0.1
    },
    "B": {
      "model_id": "us.amazon.nova-pro-1:0",
      "high_temp": 0.95,
      "low_temp": 0.2
    }
  },
  "steps": []
}
```

---

## Tools

### search_web

**Location**: `creativity_agent/tools.py`

Search the web using DuckDuckGo.

```python
from creativity_agent.tools import search_web

results = search_web(
    query="urban farming innovations 2024",
    max_results=5
)
# Returns: List of search result dicts with title, link, snippet
```

### get_url_content

**Location**: `creativity_agent/tools.py`

Fetch and parse web page content.

```python
from creativity_agent.tools import get_url_content

content = get_url_content(url="https://example.com/article")
# Returns: Cleaned text content from the page
```

### bulk_search_web

**Location**: `creativity_agent/tools.py`

Execute multiple web searches efficiently.

```python
from creativity_agent.tools import bulk_search_web

results = bulk_search_web(queries=[
    "vertical farming systems",
    "hydroponic urban gardens",
    "LED grow technology"
])
# Returns: Dict[query -> List[results]]
```

---

## CLI Usage

### main.py

**Location**: `creativity_agent/main.py`

Complete command-line interface with all options.

```bash
python main.py [OPTIONS]

Options:
  --prompt TEXT                  Creative request prompt
  --no-memory                    Disable memory tracking
  --no-chaos                     Disable chaos generation
  --no-judge                     Disable independent judge
  --no-observability             Disable ElasticSearch
  --chaos-seeds INT              Number of chaos seeds per iteration (default: 3)
  --semantic-backend TEXT        Word discovery backend (default: auto)
                                 Options: auto, sentence-transformers, gensim, wordnet, simple
  --mock                         Use mock agents for fast debugging
  --es-uri TEXT                  ElasticSearch URI
  --es-api-key TEXT              ElasticSearch API key
  --help                         Show help message
```

### Examples

```bash
# Full feature set
python main.py --prompt "Design an innovative water filtration system"

# High chaos mode
python main.py --chaos-seeds 6 --prompt "Create new entertainment form"

# Memory-only (no chaos)
python main.py --no-chaos --prompt "Improve customer onboarding"

# Mock mode (no LLM calls)
python main.py --mock --prompt "test"

# Minimal mode
python main.py --no-memory --no-chaos --prompt "Your request"
```

---

## Examples

### Using the API Programmatically

```python
from pathlib import Path
from creativity_agent.agent_flow_graph import CreativityAgentFlowGraph
from creativity_agent.config import FlowConfig

# Load config
config = FlowConfig.from_json(Path("creativity_agent/flow_config.json"))

# Create flow with all features
flow = CreativityAgentFlowGraph(
    config=config,
    enable_memory=True,
    enable_chaos=True,
    enable_judge=True,
    enable_observability=True,
    chaos_seeds_per_iteration=5,
    semantic_backend="sentence-transformers"
)

# Run
result = flow.run("Design an innovative transportation solution")

# Access outputs
print(f"Final result: {result}")
print(f"Outputs saved to: {flow.run_dir}")

# Access memory
if flow.memory_manager:
    memory = flow.memory_manager.memory
    print(f"Explored ideas: {len(memory.explored_ideas)}")
    print(f"Rejected ideas: {len(memory.rejected_ideas)}")
```

### Extending with Custom Logic

```python
from creativity_agent.nodes import BaseNode

class CustomNode(BaseNode):
    async def invoke_async(self, task, invocation_state=None, **kwargs):
        # Get data from state
        original_prompt = invocation_state.get('original_prompt')
        
        # Do custom work
        result = process_something(original_prompt)
        
        # Update state
        invocation_state['custom_result'] = result
        
        # Return
        return self.create_result(
            message=result,
            state_updates={'custom_result': result}
        )
    
    def get_required_state_keys(self):
        return ['original_prompt']
```

---

## Troubleshooting

### Common Issues

**Issue**: ImportError for creativity_agent modules

**Solution**:
```bash
pip install -e .
export PYTHONPATH=$(pwd):$PYTHONPATH
```

**Issue**: AWS Bedrock access errors

**Solution**:
```bash
# Verify credentials
aws sts get-caller-identity

# Check region supports Bedrock
export AWS_DEFAULT_REGION=us-east-1
```

**Issue**: ElasticSearch connection failed

**Solution**:
```bash
# Verify URI and API key in .env
# Test connection
curl -H "Authorization: ApiKey YOUR_KEY" https://your-elastic/
```

For more help, see [INSTALLATION.md](./INSTALLATION.md).

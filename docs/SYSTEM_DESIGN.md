# System Design & Architecture

## Overview

Super Creativity is a production-ready multi-agent AI system for creative ideation built on AWS Strands with sophisticated graph-based orchestration, persistent memory, chaos-driven divergent thinking, and independent evaluation.

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    SUPER CREATIVITY SYSTEM                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐         ┌──────────────────┐              │
│  │  AWS Bedrock     │         │   Graph Engine   │              │
│  │  (Claude, Nova)  │         │   (AWS Strands)  │              │
│  └────────┬─────────┘         └────────┬─────────┘              │
│           │                            │                        │
│           └────────────┬───────────────┘                        │
│                        ▼                                        │
│  ┌─────────────────────────────────────┐                       │
│  │    Multi-Agent Orchestration        │                       │
│  ├─────────────────────────────────────┤                       │
│  │  • Iteration Controller             │                       │
│  │  • Chaos Generator                  │                       │
│  │  • Creative Agents (High Temp)      │                       │
│  │  • Refinement Agents (Low Temp)     │                       │
│  │  • Judge Agents (Independent)       │                       │
│  │  • Deep Research Agent              │                       │
│  └─────────────────────────────────────┘                       │
│           │              │              │                      │
│           ▼              ▼              ▼                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │   Memory     │ │   Web Cache  │ │ Observability│           │
│  │   Manager    │ │   (SQLite)   │ │(ElasticSearch)           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Core Layers

### Layer 1: LLM & Infrastructure
- **AWS Bedrock**: Claude Sonnet, Nova Pro, other models
- **Streaming Support**: Per-model streaming configuration
- **Token Tracking**: Monitor usage and cost per model
- **Error Resilience**: Retry logic and fallback models

### Layer 2: Graph Engine (AWS Strands)
- **GraphBuilder**: Declarative graph construction
- **Node Orchestration**: Automatic state flow between nodes
- **Conditional Routing**: If-else based on state
- **Error Handling**: Caught and managed per node

### Layer 3: Multi-Agent Orchestration
**Six Key Agent Types**:

1. **Iteration Controller**: Loop condition checker
2. **Chaos Generator**: Divergent thinking seed creation
3. **Creative Agents**: High-temperature idea generation
4. **Refinement Agents**: Low-temperature idea validation
5. **Judge Agents**: Independent idea evaluation
6. **Deep Research**: Final comprehensive research

### Layer 4: Persistent Systems
- **Memory Manager**: Tracks explored ideas and rejections
- **Web Cache**: SQLite-based URL content caching
- **Observability**: ElasticSearch metrics and visualization

---

## Architecture Principles

### 1. Separation of Concerns
Each component has single responsibility:
- **Chaos Generator**: Only creates divergent seeds
- **Creative Agents**: Only generate ideas
- **Refinement Agents**: Only validate and organize
- **Judge Agents**: Only evaluate independently
- **Iteration Controller**: Only manages loop logic

### 2. Typed State Management
All communication via immutable `ExecutionState` Pydantic model:
```python
state: ExecutionState = ExecutionState(
    original_prompt="...",
    iteration=0,
    run_id="run_001",
    run_dir="/outputs"
)

# Nodes update state immutably
updated = state.with_updates(chaos_seeds=[...], success=True)
```

**Benefits**:
- IDE autocompletion for all state fields
- Type checking catches bugs early
- Validation at creation/update
- Immutability prevents accidental mutations

### 3. Modular Node Architecture
All nodes inherit from `BaseNode` which provides:
```python
class BaseNode(MultiAgentBase, ABC):
    """Base for all graph nodes."""
    
    def __init__(self, node_name: str, prompts_dir=None, outputs_dir=None):
        super().__init__()
        self.node_name = node_name
        self.prompts_dir = prompts_dir
        self.outputs_dir = outputs_dir
    
    @abstractmethod
    async def invoke_async(self, task, invocation_state, **kwargs):
        """Implement node logic here."""
        pass
    
    def _get_typed_input(self, task, invocation_state) -> NodeInput:
        """Parse raw Strands input to typed NodeInput."""
        return NodeInput.from_strands(task, invocation_state)
    
    def create_result(self, message, state, execution_time):
        """Return typed result to graph."""
        return MultiAgentResult(...)
    
    def handle_error(self, error, state):
        """Consistent error handling."""
        ...
```

### 4. Graph-Based Orchestration
Instead of manual loops:
```python
# OLD (imperative, hard to maintain)
for iteration in range(max_iterations):
    chaos = chaos_generator.invoke(...)
    for model in models:
        creative = creative_agent.invoke(...)
        refinement = refinement_agent.invoke(...)
        judge = judge_agent.invoke(...)
    if iteration < max_iterations - 1:
        continue

# NEW (declarative, clear structure)
builder = GraphBuilder()
builder.add_node("iteration_controller", iteration_controller)
builder.add_node("chaos", chaos_generator)
builder.add_node("creative_a", creative_a)
# ... add all nodes

builder.add_edge("iteration_controller", "chaos", 
                condition=lambda r: r.state.should_continue)
# ... add edges with conditions

graph = builder.build()
result = await graph.run(task, invocation_state)
```

### 5. Template-Based Prompts
Jinja2 templates for sophisticated prompts:
```python
# System prompt (fixed behavior)
system_prompts/
  ├─ creative_agent_system.j2
  ├─ judge_system.j2
  └─ refinement_agent_system.j2

# User prompts (with template variables)
prompts_templates/
  ├─ creative_agent.j2
  ├─ judge_agent.j2
  └─ refinement_agent.j2

# In node:
context = CreativeAgentPromptContext(
    original_prompt="...",
    chaos_seeds=[...],
    iteration=0
)
prompt = jinja_builder.build_creative_agent_prompt(context)
```

**Benefits**:
- Separate template maintenance from code
- Variable injection prevents string concatenation errors
- Easy to A/B test different prompts
- Human-readable template format

---

## Data Flow Architecture

### Execution State Lifecycle

```
Initial Creation
  ↓
ExecutionState(
  original_prompt="...",
  iteration=0,
  run_id="...",
  run_dir="..."
)
  ↓
Iteration Controller Node
  ├─ should_continue = true
  ├─ is_finished = false
  └─ state.to_dict() → graph
      ↓
Chaos Generator Node
  ├─ Reads: original_prompt, iteration
  ├─ Generates: chaos_seeds, chaos_context
  └─ Returns: state.with_updates(chaos_seeds=[...])
      ↓
Creative Agent Nodes (A, B, ...)
  ├─ Reads: original_prompt, chaos_seeds, iteration
  ├─ Generates: creative_output
  └─ Returns: state.with_updates(creative_output="...", creative_model="A")
      ↓
Refinement Agent Nodes
  ├─ Reads: creative_output, previous judge evaluations
  ├─ Generates: refinement_output
  └─ Returns: state.with_updates(refinement_output="...", refinement_model="A")
      ↓
Judge Agent Nodes
  ├─ Reads: refinement_output
  ├─ Generates: evaluations, statistics
  └─ Returns: state.with_updates(judge_evaluations=[...], accepted_ideas_count=N)
      ↓
Iteration Controller (Loop Check)
  ├─ Reads: iteration, max_iterations
  ├─ Increments: iteration += 1
  ├─ Updates: should_continue, is_finished
  └─ Conditional routing → Chaos (continue) or Deep Research (finish)
      ↓
Final Output
  └─ All state persisted to run_dir/{run_id}/
```

### State Immutability Pattern

```python
# State never mutated, always new copies
state = ExecutionState(original_prompt="test", iteration=0, ...)

# Node updates create new state
new_state = state.with_updates(
    chaos_seeds=[...],
    success=True
)

# Original unchanged
assert state.chaos_seeds is None  # Still None
assert new_state.chaos_seeds == [...]  # Has data
assert state.original_prompt == new_state.original_prompt  # Both same
```

**Benefits**:
- No accidental side effects
- Easy to debug (compare states)
- Safe for concurrent processing
- Functional programming approach

---

## Component Interactions

### 1. Chaos Generator & Creative Agent
```
Chaos Generator
  ├─ Input: original_prompt, iteration
  ├─ Process: 
  │   ├─ Select random tangential concepts
  │   ├─ Research each via web
  │   └─ Build context/relevance
  └─ Output: chaos_seeds=[{concept, context, relevance}]
              chaos_context="<formatted prompt>"
      ↓
Creative Agent
  ├─ Input: original_prompt, chaos_seeds, chaos_context
  ├─ Process:
  │   ├─ Combine original + chaos context
  │   ├─ Generate diverse ideas
  │   └─ Optional web research on ideas
  └─ Output: creative_output="<ideas>"
```

### 2. Creative → Refinement → Judge Chain
```
Creative Agent
  └─ creative_output: Raw, diverse ideas
      ↓
Refinement Agent
  ├─ Input: creative_output
  ├─ Process: Filter, organize, enhance ideas
  └─ Output: refinement_output: Organized ideas
      ↓
Judge Agent
  ├─ Input: refinement_output
  ├─ Criteria: Originality, Feasibility, Impact, Substance
  ├─ Scoring: 0-10 per criterion, average for total
  ├─ Threshold: ≥5.0 accepted, <5.0 rejected
  └─ Output: judge_evaluations, idea_statistics, accepted_count
```

### 3. Memory Manager Integration
```
Refinement Agent
  ├─ Extracts key concepts from ideas
  └─ Calls: memory_manager.add_concepts([...])
      ↓
Memory Manager
  ├─ File: outputs/{run_id}/idea_memory.json
  ├─ Tracks: {explored_ideas, rejected_ideas, key_concepts}
  └─ Returns: memory_context for next iteration
      ↓
Next Iteration's Creative Agent
  ├─ Reads: memory_context
  ├─ Knows: What's been explored, what was rejected
  └─ Generates: Novel ideas (avoids redundancy)
```

### 4. Web Cache & Creative/Refinement Agents
```
Creative/Refinement Agents
  ├─ Need: Information about concept X
  └─ Call: get_url_content(url)
      ↓
Global Web Cache
  ├─ Check: Is URL cached?
  ├─ If yes: Return cached content (fast)
  ├─ If no: Fetch via HTTP, cache for future
  └─ Return: Content
      ↓
Agent continues with information
```

---

## Configuration Architecture

### flow_config.json
```json
{
  "max_iterations": 3,
  "models": {
    "A": {
      "provider": "bedrock",
      "model_id": "claude-sonnet",
      "creative_temperature": 1.2,
      "refinement_temperature": 0.3
    },
    "B": {
      "provider": "bedrock",
      "model_id": "nova-pro",
      "creative_temperature": 1.0,
      "refinement_temperature": 0.5
    }
  },
  "chaos_generation": {
    "enabled": true,
    "num_seeds": 3,
    "backend": "transformers"
  },
  "memory_management": {
    "enabled": true,
    "persist_concepts": true
  },
  "web_cache": {
    "enabled": true,
    "cache_dir": "outputs/global_cache"
  },
  "observability": {
    "elasticsearch_host": "localhost:9200",
    "enable_metrics": true
  }
}
```

### Per-Node Configuration
Each node has dedicated configuration:
```python
# Stored as class attributes
class CreativeAgentNode(BaseNode):
    TEMPERATURE = 1.2
    MAX_TOKENS = 2000
    TOP_P = 0.95
    
    # Can be overridden per instance
    def __init__(self, agent, node_name, 
                 outputs_dir, 
                 temperature=None, 
                 max_tokens=None):
        super().__init__(node_name, outputs_dir=outputs_dir)
        self.agent = agent
        self.temperature = temperature or self.TEMPERATURE
        self.max_tokens = max_tokens or self.MAX_TOKENS
```

---

## Error Handling & Resilience

### Node-Level Error Handling
```python
async def invoke_async(self, task, invocation_state, **kwargs):
    try:
        # Parse typed input
        node_input = self._get_typed_input(task, invocation_state)
        state = node_input.state
        
        # Execute node logic
        result = perform_operation(state)
        
        # Return success
        updated_state = state.with_updates(success=True, result=result)
        return self.create_result("Success", state=updated_state)
        
    except SpecificError as e:
        # Specific error handling
        logger.error(f"Specific error: {e}")
        error_state = state.with_updates(
            success=False,
            error_message=f"Operation failed: {e}"
        )
        return self.handle_error(e, error_state)
        
    except Exception as e:
        # Generic error handling
        logger.exception(f"Unexpected error: {e}")
        # Create minimal state if needed
        error_state = ExecutionState(
            original_prompt=invocation_state.get('original_prompt', ''),
            run_id=invocation_state.get('run_id', ''),
            run_dir=invocation_state.get('run_dir', '.')
        )
        return self.handle_error(e, error_state)
```

### Error Recovery Strategies
1. **Retry Logic**: Automatic retry on transient errors
2. **Fallback Models**: Try alternative model if primary fails
3. **Graceful Degradation**: Continue with partial results
4. **Error State Logging**: All errors logged to state for analysis

---

## Performance Optimization

### 1. Parallel Processing (Where Applicable)
- Agents A and B could run in parallel (in future enhancement)
- Creative and refinement could be parallelized with different prompts
- Currently sequential for state management simplicity

### 2. Caching Layers
- **Web Cache**: URL content cached in SQLite (massive speedup on 2+ iterations)
- **Model Output Caching**: Optional caching of LLM responses
- **Memory Persistence**: Ideas and rejections cached across runs

### 3. Streaming & Incremental Output
- LLM responses streamed during generation
- Long-running operations show progress
- Partial results available before completion

### 4. Resource Management
- Configurable token limits per model
- Batch processing for bulk searches
- Connection pooling for web requests

---

## Security & Compliance

### 1. Prompt Injection Prevention
- Template-based prompts (no string concatenation)
- Input validation before LLM calls
- Output escaping when used in subsequent prompts

### 2. Data Privacy
- All data stays within user's AWS account
- Optional ElasticSearch (can be disabled)
- Run outputs stored locally or in S3

### 3. Cost Control
- Token counting and cost estimation
- Per-model and per-step cost tracking
- Configurable budget limits

---

## Integration Points

### AWS Services
- **Bedrock**: LLM inference
- **ElasticSearch**: Metrics and visualization
- **S3**: Optional run storage
- **CloudWatch**: Logging

### External APIs
- **Web Search**: DuckDuckGo, Bing, Wikipedia
- **Information Retrieval**: HTTP content fetching
- **Custom APIs**: Extensible tool framework

### Local Systems
- **SQLite**: Web cache and state storage
- **File System**: Run outputs and configurations
- **JSON**: Data serialization

---

## Extensibility Points

### 1. Custom Nodes
```python
class CustomNode(BaseNode):
    async def invoke_async(self, task, invocation_state, **kwargs):
        node_input = self._get_typed_input(task, invocation_state)
        state = node_input.state
        
        # Custom logic here
        result = custom_operation(state)
        
        updated_state = state.with_updates(custom_field=result)
        return self.create_result("Done", state=updated_state)
```

### 2. Custom Models in ExecutionState
```python
class ExtendedExecutionState(ExecutionState):
    custom_field: Optional[str] = Field(
        default=None,
        description="Custom field for extension"
    )
```

### 3. Tool Extensions
Add new tools to creative/refinement agents:
```python
# In agent_wrapper.py
def my_custom_tool():
    """Custom tool for agents."""
    ...

# Register with agent
agent.tools.append(my_custom_tool)
```

---

## Related Documentation

- **GRAPH_FLOWS.md**: Detailed graph topology and flow
- **TYPED_STATE_MIGRATION.md**: ExecutionState implementation
- **API_REFERENCE.md**: Programmatic APIs and examples
- **QUICKSTART.md**: Setup and first run
- **WEB_CACHE_REFACTORING.md**: Caching strategy

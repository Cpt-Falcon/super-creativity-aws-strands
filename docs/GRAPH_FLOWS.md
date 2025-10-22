# Graph Flow Architecture

## Overview

Super Creativity uses AWS Strands' `GraphBuilder` for declarative, graph-based multi-agent orchestration. The graph implements a sophisticated feedback loop pattern with conditional branching for iteration control and deep research.

## Graph Structure

### Core Topology

```
                    ┌─────────────────────┐
                    │   START: USER PROMPT │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │  Iteration Controller    │
                    │  (Loop Condition Check)  │
                    │  should_continue=true?   │
                    └──┬──────────────────┬───┘
                       │                  │
            iteration < max_iterations    all iterations done
                       │                  │
                       ▼                  ▼
            ┌─────────────────────┐  ┌──────────────────┐
            │ CHAOS GENERATION    │  │ DEEP RESEARCH    │
            │ (Divergent Seeds)   │  │ (Final Output)   │
            └────────────┬────────┘  └──────────────────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
    ┌─────────────┐           ┌──────────────┐
    │ MODEL A:    │           │ MODEL B:     │
    │ CREATIVE    │           │ CREATIVE     │
    │ (High Temp) │           │ (High Temp)  │
    └──────┬──────┘           └──────┬───────┘
           │                         │
           ▼                         ▼
    ┌─────────────┐           ┌──────────────┐
    │ MODEL A:    │           │ MODEL B:     │
    │ REFINEMENT  │           │ REFINEMENT   │
    │ (Low Temp)  │           │ (Low Temp)   │
    └──────┬──────┘           └──────┬───────┘
           │                         │
           ▼                         ▼
    ┌─────────────┐           ┌──────────────┐
    │ MODEL A:    │           │ MODEL B:     │
    │ JUDGE       │           │ JUDGE        │
    │ (Evaluate)  │           │ (Evaluate)   │
    └──────┬──────┘           └──────┬───────┘
           │                         │
           └─────────────┬───────────┘
                         │
                         ▼
            ┌──────────────────────────┐
            │  Iteration Controller    │
            │  (Check next iteration)  │
            │  iteration += 1          │
            └────────┬─────────────────┘
                     │
                     └────────────────────► (Loop back)
```

### State Flow Through Graph

```
ExecutionState carries through all nodes:

START
  │
  ├─ original_prompt ✓ (immutable throughout)
  ├─ run_id ✓
  ├─ run_dir ✓
  └─ iteration = 0
     │
     ▼
  ITERATION_CONTROLLER
  ├─ should_continue = (iteration < max_iterations)
  └─ is_finished = (iteration >= max_iterations)
     │
     ├─ if should_continue:
     │   ▼
     │  CHAOS_GENERATOR
     │  ├─ chaos_context (built prompt)
     │  ├─ chaos_seeds (List[Dict])
     │  └─ chaos_seeds_count
     │     │
     │     ├─ MODEL_A_CREATIVE
     │     │  ├─ creative_output
     │     │  ├─ creative_model = "A"
     │     │  │
     │     │  ▼
     │     │  MODEL_A_REFINEMENT
     │     │  ├─ refinement_output
     │     │  ├─ refinement_model = "A"
     │     │  │
     │     │  ▼
     │     │  MODEL_A_JUDGE
     │     │  ├─ judge_evaluations
     │     │  ├─ idea_statistics
     │     │  └─ accepted_ideas_count
     │     │
     │     ├─ MODEL_B_CREATIVE
     │     │  ├─ creative_output
     │     │  ├─ creative_model = "B"
     │     │  │
     │     │  ▼
     │     │  MODEL_B_REFINEMENT
     │     │  ├─ refinement_output
     │     │  ├─ refinement_model = "B"
     │     │  │
     │     │  ▼
     │     │  MODEL_B_JUDGE
     │     │  ├─ judge_evaluations
     │     │  ├─ idea_statistics
     │     │  └─ accepted_ideas_count
     │     │
     │     ▼
     │  ITERATION_CONTROLLER (loop check)
     │  ├─ iteration += 1
     │  └─ Loop condition re-evaluated
     │
     ├─ if is_finished:
     │   ▼
     │  DEEP_RESEARCH
     │  ├─ final_research_output
     │  └─ success = true/false
     │
     ▼
   END (return final state)
```

## Node Details

### 1. Iteration Controller
**Role**: Loop condition checker (acts as `for` loop controller)

**Responsibilities**:
- Check if `iteration < max_iterations`
- Set `should_continue` (bool)
- Set `is_finished` (bool)
- Increment iteration counter for next pass
- Determine conditional routing

**Type**: Custom node extending `BaseNode`

**Key Logic**:
```python
should_continue = state.iteration < state.max_iterations
is_finished = state.iteration >= state.max_iterations
# Next node determined by these flags
```

---

### 2. Chaos Generator
**Role**: Creates divergent thinking seeds

**Inputs**:
- `original_prompt` from state
- Current iteration number

**Process**:
1. Select 3-5 random tangential concepts
2. Research each concept with web search
3. Build context about each concept
4. Generate relevance connections

**Outputs**:
- `chaos_context`: Built prompt with all seeds
- `chaos_seeds`: List[Dict] with concept, context, relevance
- `chaos_seeds_count`: Integer count

**Data Structure**:
```python
chaos_seeds = [
    {
        "concept": "mycelium",
        "context": "Fungal network structure...",
        "relevance": "Information distribution without central control"
    },
    {
        "concept": "tessellation",
        "context": "Patterns that tile without gaps...",
        "relevance": "Efficient space utilization"
    },
    # ... more seeds
]
```

---

### 3. Creative Agent (High Temperature)
**Role**: Generate novel, diverse ideas

**Input Chain**:
- Original user prompt
- Chaos context (tangential seeds)
- Previous refinements (if iteration > 0)
- Memory of explored ideas (optional)

**Temperature**: 1.0-1.5 (high)

**Outputs**:
- `creative_output`: Generated ideas (text)
- `creative_model`: Model identifier (e.g., "claude-sonnet")

**Per-Model Execution**:
- Model A creative → Model A refinement → Model A judge
- Model B creative → Model B refinement → Model B judge
- (Sequential, not parallel)

---

### 4. Refinement Agent (Low Temperature)
**Role**: Validate and enhance creative ideas

**Input Chain**:
- Creative output from previous node
- Previous judge evaluations (if available)
- Memory context (optional)

**Temperature**: 0.3-0.5 (low)

**Outputs**:
- `refinement_output`: Refined ideas (text)
- `refinement_model`: Model identifier

**Process**:
1. Analyze creative ideas
2. Filter for feasibility
3. Organize by theme/category
4. Enhance with technical details
5. Extract key concepts for memory

---

### 5. Judge Node
**Role**: Independent evaluation of ideas

**Input**:
- `refinement_output` from previous node

**Evaluation Criteria** (0-10 scale each):
| Criterion | Weight | Description |
|-----------|--------|-------------|
| Originality | 1.0 | How novel and unique |
| Technical Feasibility | 1.0 | Can it be built |
| Impact Potential | 1.0 | Significance of impact |
| Substance | 1.0 | How well-developed |

**Quality Score**: Average of 4 criteria

**Acceptance Threshold**: ≥ 5.0

**Outputs**:
- `judge_evaluations`: List[Dict] with scores and reasoning
- `idea_statistics`: Summary statistics
- `accepted_ideas_count`: Integer

**Evaluation Structure**:
```python
judge_evaluations = [
    {
        "idea": "idea text",
        "scores": {
            "originality": 8,
            "feasibility": 6,
            "impact": 7,
            "substance": 7
        },
        "average_score": 7.0,
        "accepted": true,
        "reasoning": "Strong concept with clear potential..."
    },
    # ... more evaluations
]
```

---

### 6. Deep Research (Optional Final Step)
**Role**: Conduct deep research on accepted ideas

**Triggered**: When all iterations complete (`is_finished = true`)

**Process**:
1. Take all accepted ideas
2. Research each in depth
3. Find real-world examples
4. Identify next steps
5. Generate final recommendations

**Outputs**:
- `final_research_output`: Comprehensive research document

---

## Conditional Edges

The graph uses conditional edges for iteration control:

```python
# Edge from Iteration Controller to Chaos (if continue)
builder.add_edge(
    "iteration_controller",
    "chaos_generator",
    condition=lambda result: result.state.should_continue
)

# Edge from Iteration Controller to Deep Research (if finished)
builder.add_edge(
    "iteration_controller",
    "deep_research",
    condition=lambda result: result.state.is_finished
)
```

## Multi-Model Sequential Execution

The graph handles multiple models (A, B, ...) sequentially:

```python
# For each model in config
for model_key in ["A", "B"]:
    # Create creative node
    builder.add_node(
        f"creative_{model_key.lower()}",
        creative_agent_A  # or creative_agent_B
    )
    # Create refinement node
    builder.add_node(
        f"refinement_{model_key.lower()}",
        refinement_agent_A
    )
    # Create judge node
    builder.add_node(
        f"judge_{model_key.lower()}",
        judge_agent_A
    )
    
    # Chain them: creative → refinement → judge
    builder.add_edge(f"creative_{model_key.lower()}", f"refinement_{model_key.lower()}")
    builder.add_edge(f"refinement_{model_key.lower()}", f"judge_{model_key.lower()}")
    
    # Last judge → iteration controller
    builder.add_edge(f"judge_{model_key.lower()}", "iteration_controller")
```

## Execution Flow Example

### Iteration 0 (First Pass)

1. **Iteration Controller**: Check iteration=0 < max=3 → continue=true
2. **Chaos Generator**: Create divergent seeds
3. **Model A Creative**: Generate ideas from chaos + prompt
4. **Model A Refinement**: Select and refine Model A ideas
5. **Model A Judge**: Score Model A ideas
6. **Model B Creative**: Generate ideas from chaos + prompt
7. **Model B Refinement**: Select and refine Model B ideas
8. **Model B Judge**: Score Model B ideas
9. **Iteration Controller**: Check iteration=0 → increment to 1, continue=true → loop

### Iteration 1 (Second Pass)

1. **Iteration Controller**: Check iteration=1 < max=3 → continue=true
2. **Chaos Generator**: Create NEW divergent seeds (different from iteration 0)
3. **Model A Creative**: Generate NEW ideas (aware of iteration history)
4-9. Repeat evaluation chain
10. **Iteration Controller**: Check iteration=1 → increment to 2, continue=true → loop

### Iteration 2 (Final Pass)

1. **Iteration Controller**: Check iteration=2 < max=3 → continue=true
2. Repeat chain
3. **Iteration Controller**: Check iteration=2 → increment to 3, continue=false, is_finished=true

### After Iterations

1. **Deep Research**: Conduct comprehensive research on all accepted ideas
2. **Final Output**: Generate final recommendations

---

## State Management

### ExecutionState Fields

```python
# Core context (immutable, set once)
original_prompt: str          # User's creative request
run_id: str                   # Unique run identifier
run_dir: str                  # Output directory
start_time: str               # ISO timestamp

# Iteration control
iteration: int                # Current iteration (0-indexed)
max_iterations: int           # Total iterations to run
should_continue: bool         # Whether to continue iterating
is_finished: bool             # Whether all iterations done

# Chaos generator
chaos_context: str            # Built prompt with seeds
chaos_seeds: List[Dict]       # Tangential concepts and context
chaos_seeds_count: int        # Number of seeds

# Creative agent
creative_output: str          # Generated ideas
creative_model: str           # Model used

# Refinement agent
refinement_output: str        # Refined ideas
refinement_model: str         # Model used

# Judge agent
judge_evaluations: List[Dict] # Evaluation results
idea_statistics: Dict         # Stats about ideas
accepted_ideas_count: int     # Count of accepted ideas

# Deep research
final_research_output: str    # Final output

# Error tracking
error_message: str            # Error if any
success: bool                 # Overall success flag
```

---

## Integration with AWS Strands

The graph is built using AWS Strands patterns:

```python
from strands.multiagent import GraphBuilder, MultiAgentBase

# Create graph builder
builder = GraphBuilder()

# Add nodes (each extends MultiAgentBase)
builder.add_node("iteration_controller", iteration_controller_node)
builder.add_node("chaos_generator", chaos_generator_node)
# ... etc

# Add edges with optional conditions
builder.add_edge("iteration_controller", "chaos_generator",
                condition=lambda r: r.state.should_continue)

# Build and execute
graph = builder.build()
result = await graph.run(
    task="Generate ideas for...",
    invocation_state=ExecutionState(...).to_dict()
)
```

---

## Key Design Patterns

### 1. Feedback Loop with Conditional Branching
- Iteration controller as for-loop condition
- Two output paths: continue or finish
- Automatic increment of iteration counter

### 2. Sequential Multi-Model Execution
- Not parallel, sequential chains
- Each model runs full creative→refinement→judge cycle
- Results accumulate in state
- All models see same original_prompt but different creative outputs

### 3. Immutable State Pattern
- `original_prompt` never changes
- State updates via `.with_updates(field=value)`
- Each node returns new ExecutionState
- Previous values preserved in state object

### 4. Error Resilience
- Each node can fail independently
- Error state created preserving original_prompt
- Error message stored in state
- Graph can continue or halt based on error severity

---

## Debugging Graph Flows

### View Execution Order
```python
result = await graph.run(task="...", invocation_state=state.to_dict())
# Check result.results dictionary for execution order
# Each entry has: {node_name: NodeResult(result=..., status=..., time=...)}
```

### Check State at Each Node
```python
# ExecutionState available in each node's invoke_async
state = node_input.state
print(f"Iteration: {state.iteration}")
print(f"Continue: {state.should_continue}")
print(f"Chaos seeds: {state.chaos_seeds_count}")
```

### Trace Conditional Edges
```python
# In iteration_controller_node
if state.iteration < self.max_iterations:
    # This edge to chaos will be taken
else:
    # This edge to deep_research will be taken
```

---

## Performance Considerations

### Graph Execution Time

| Component | Typical Time | Notes |
|-----------|-------------|-------|
| Chaos Generation | 10-30s | Includes web search for each seed |
| Creative Agent | 30-60s | LLM call + web research |
| Refinement Agent | 20-45s | LLM call for filtering |
| Judge Agent | 15-30s | Independent LLM scoring |
| Per Model Chain | 75-165s | Creative + Refinement + Judge |
| Full Iteration (2 models) | 150-330s | Both model chains sequentially |
| 3 Iterations | 450-990s | 7.5-16.5 minutes |

### Optimization Tips

1. **Reduce chaos seeds**: Fewer seeds = faster generation
2. **Fewer iterations**: Test with 1-2 before running 3+
3. **Use mock mode**: For flow testing without LLM calls
4. **Enable caching**: Web cache drastically improves 2nd+ iterations
5. **Parallel models**: (If architecture supported) Run models A,B in parallel

---

## Related Documentation

- **SYSTEM_DESIGN.md**: Architecture and components
- **TYPED_STATE_MIGRATION.md**: ExecutionState model details
- **QUICKSTART.md**: First run and setup
- **API_REFERENCE.md**: Programmatic APIs

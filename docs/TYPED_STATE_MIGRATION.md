# Typed State Migration - ExecutionState Implementation

## Overview

This document describes the migration from duck typing to Pydantic-based typed state management in the graph-based creativity flow.

## What Changed

### 1. **New ExecutionState Model** (`models/execution_state.py`)

Created `ExecutionState` - a Pydantic BaseModel that replaces dictionary-based duck typing with strongly-typed, validated state.

#### Core Fields:
- **Execution Context** (immutable through iterations):
  - `original_prompt`: The user's prompt, preserved throughout execution
  - `run_id`: Unique identifier for this run
  - `run_dir`: Output directory for this run
  - `start_time`: ISO timestamp when execution started

- **Iteration Control**:
  - `iteration`: Current iteration number (0-indexed)
  - `max_iterations`: Total iterations to run
  - `should_continue`: Whether to loop again
  - `is_finished`: Whether all iterations complete

- **Stage-Specific State**:
  - `chaos_context`, `chaos_seeds`: Chaos generator output
  - `creative_output`, `creative_model`: Creative agent output + model used
  - `refinement_output`, `refinement_model`: Refinement agent output + model used
  - `judge_evaluations`, `idea_statistics`: Judge results
  - `final_research_output`: Deep research output

- **Error Tracking**:
  - `error_message`: Error details if node fails
  - `success`: Whether current step succeeded

#### Benefits:
✅ **Type Safety**: IDE autocompletion and type checking  
✅ **Validation**: Pydantic automatically validates field types  
✅ **Immutability**: `.with_updates()` creates new instances, prevents accidental mutations  
✅ **Serialization**: `.to_dict()` and `.from_dict()` for AWS Strands integration  

### 2. **NodeInput Wrapper** (`models/execution_state.py`)

Created `NodeInput` to wrap task + typed state for clean node invocation.

```python
node_input = NodeInput.from_strands(task, invocation_state)
state = node_input.state  # Type: ExecutionState with IDE hints
```

### 3. **Updated BaseNode** (`nodes/base_node.py`)

- **Removed**: Duck-typed `get_state_value()`, `update_state()`, `validate_state()` methods
- **Added**: `_get_typed_input()` method that parses raw Strands input to typed `NodeInput`
- **Updated**: `create_result()` and `handle_error()` now work with `ExecutionState` objects

```python
# OLD (duck typing):
iteration = self.get_state_value(invocation_state, 'iteration', 0)
state_updates = {'iteration': iteration, 'success': True}
return self.create_result(message, state_updates=state_updates)

# NEW (typed):
node_input = self._get_typed_input(task, invocation_state)
state = node_input.state  # Type: ExecutionState
updated_state = state.with_updates(success=True)
return self.create_result(message, state=updated_state)
```

### 4. **Updated Nodes**

All concrete nodes updated to use typed state:

- **IterationControllerNode**: Manages iteration count with typed state
- **ChaosGeneratorNode**: Generates chaos seeds, stores in typed state
- **JudgeNode**: Evaluates ideas, stores evaluations in typed state

Each node now:
1. Calls `self._get_typed_input(task, invocation_state)` to parse input
2. Extracts `ExecutionState` from `node_input.state`
3. Performs work
4. Returns updated state via `self.create_result(..., state=updated_state)`

### 5. **Graph Integration** (`agent_flow_graph.py`)

Updated `run()` method to use `ExecutionState`:

```python
# Create typed initial state
initial_state = ExecutionState(
    original_prompt=user_prompt,
    iteration=0,
    run_id=self.run_id,
    run_dir=str(self.run_dir),
    max_iterations=self.config.iterations,
    start_time=datetime.now().isoformat()
)

# Pass to graph
result = self.graph(
    user_prompt,
    invocation_state=initial_state.to_dict()
)
```

## Design Principles

### 1. **Type Safety Throughout**
- All nodes receive and return `ExecutionState`
- Pydantic validates field types and defaults
- IDE provides full autocompletion

### 2. **Immutability Pattern**
- State objects are never mutated in place
- Use `.with_updates(**fields)` to create new state
- Prevents accidental side effects

### 3. **Original Prompt Preservation**
- `original_prompt` is set once, never modified
- Available to all nodes through `state.original_prompt`
- Enables consistent reference throughout execution

### 4. **Error Handling**
- Nodes catch exceptions and create error states
- `error_message` and `success` fields indicate problems
- Graph can inspect state to make decisions

### 5. **Mock Compatibility**
- Mock agents (`MockAgent`, `MockChaosNode`, `MockJudgeNode`) unchanged
- They work independently without typed state
- Graph structure can be tested quickly without LLM calls

## Usage Examples

### In a Node

```python
async def invoke_async(self, task, invocation_state=None, **kwargs):
    try:
        # Parse typed input
        node_input = self._get_typed_input(task, invocation_state)
        state = node_input.state  # Type: ExecutionState
        
        # Access fields with IDE hints
        original_prompt = state.original_prompt  # IDE knows this is str
        iteration = state.iteration  # IDE knows this is int
        
        # Perform work
        result = do_something(original_prompt)
        
        # Create updated state
        updated_state = state.with_updates(
            creative_output=result,
            creative_model="A",
            success=True
        )
        
        return self.create_result("Done", state=updated_state)
        
    except Exception as e:
        error_state = ExecutionState(...)  # Preserve original_prompt
        return self.handle_error(e, error_state)
```

### Creating ExecutionState

```python
from creativity_agent.models import ExecutionState

# Create initial state
state = ExecutionState(
    original_prompt="Design a new product",
    iteration=0,
    run_id="run_001",
    run_dir="/outputs",
    max_iterations=3
)

# Update with results
state = state.with_updates(
    chaos_seeds=seeds,
    chaos_seeds_count=len(seeds)
)

# Convert for AWS Strands
invocation_state_dict = state.to_dict()
```

### Accessing State in Conditionals

```python
def should_continue_iterating(state):
    """Conditional edge function."""
    controller_result = state.results.get("iteration_controller")
    if not controller_result:
        return False
    
    # Extract from result
    result_obj = controller_result.result
    # ... existing logic ...
    
    # Now result contains typed ExecutionState in agent_result.state
```

## Migration Checklist

- [x] Created `ExecutionState` Pydantic model with all necessary fields
- [x] Created `NodeInput` wrapper for Strands integration
- [x] Updated `BaseNode` to use typed state instead of duck typing
- [x] Updated `IterationControllerNode` to use typed state
- [x] Updated `ChaosGeneratorNode` to use typed state
- [x] Updated `JudgeNode` to use typed state
- [x] Maintained mock agent compatibility
- [x] Updated `agent_flow_graph.py` to initialize and use `ExecutionState`
- [x] Exported new models from `models/__init__.py`

## Testing

### Quick Graph Test (Mock Mode)
```bash
python -c "
from creativity_agent.agent_flow_graph import CreativityAgentFlowGraph
from creativity_agent.config import FlowConfig

config = FlowConfig.from_file('flow_config.json')
graph = CreativityAgentFlowGraph(config, mock_mode=True)
result = graph.run('Test prompt')
print('Graph executed successfully!')
"
```

### Type Checking with Pylance
- All nodes should show zero Pylance errors
- IDE autocomplete works for all `ExecutionState` fields
- Type hints are enforced throughout

## Benefits Summary

1. **No More Duck Typing**
   - Explicit types throughout the codebase
   - Compiler/IDE catches more errors early

2. **Better IDE Support**
   - Autocompletion for all state fields
   - Jump-to-definition for state access
   - Type hints in function signatures

3. **Safer State Management**
   - Immutable updates with `.with_updates()`
   - Validation of field types
   - Clear state schema

4. **Original Prompt Preservation**
   - `original_prompt` always available
   - Flows through entire execution
   - Never modified

5. **Maintains Mocking**
   - Mock agents work unchanged
   - Fast graph structure testing
   - No dependency on typed state for mocks

## Next Steps

Optional future improvements:
- Add state history logging with timestamps
- Implement state snapshots for checkpointing
- Add state validation hooks for specific transitions
- Create visualization of state flow through iterations

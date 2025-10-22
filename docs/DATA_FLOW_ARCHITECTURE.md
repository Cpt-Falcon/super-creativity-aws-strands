# Data Flow Architecture

## Overview

This document describes the standardized data flow pattern across all nodes in the creativity agent workflow. The flow ensures consistent data handling, memory persistence, and state management across iterations.

## Data Format by Stage

### Stage 1: Chaos Generator Node
- **Output Format**: Plain text
- **Content**: Tangential concepts and ideas in natural language format
- **Purpose**: Generate diverse, unpredictable input for creative thinking
- **Flow**: Text output passed to creative agent nodes as prompts

### Stage 2: Creative Agent Nodes (A_creative, B_creative)
- **Output Format**: Plain text with structured ideas
- **Content**: Generated creative ideas, typically 10-20 ideas with explanations
- **Purpose**: Generate high-quality creative ideas based on chaos input
- **Flow**: Text passed to refinement nodes for quality assessment
- **Note**: Output may contain structured content but remains primarily text format

### Stage 3: Refinement Agent Nodes (A_refinement, B_refinement)
- **Output Format**: Plain text with detailed evaluations
- **Content**: Evaluated and refined ideas with scoring (0-10 scale)
- **Purpose**: Apply quality criteria and provide scored feedback
- **Flow**: Text passed to judge node for final evaluation
- **Scoring**: Ideas evaluated on originality, feasibility, impact, substance

### Stage 4: Judge Node ⭐ KEY TRANSFORMATION POINT
- **Input Format**: Plain text from refinement nodes
- **Output Format**: **Strict JSON (no markdown, no code blocks)**
- **JSON Schema**:
```json
{
  "accepted_ideas": [
    {
      "idea_name": "string",
      "quality_score": 0-10,
      "feasibility_score": 0-10,
      "impact_score": 0-10,
      "originality_score": 0-10,
      "key_points": ["string"],
      "implementation_path": "string",
      "required_resources": ["string"],
      "success_metrics": ["string"],
      "next_steps": ["string"]
    }
  ],
  "rejected_ideas": [
    {
      "idea_name": "string",
      "rejection_reason": "string",
      "quality_score": 0-10,
      "fatal_flaw": "string"
    }
  ],
  "synthesis": "string",
  "top_recommendations": ["string"],
  "strategic_insights": ["string"],
  "unresolved_questions": ["string"]
}
```

#### Judge Node Process Flow:
1. **Parse Input**: Extracts ideas from refinement output (text format)
2. **Evaluate**: Scores each idea against 4 criteria
3. **Format Output**: Produces clean JSON (crucial - no markdown wrappers)
4. **Parse Response**: Two-stage JSON parsing:
   - Stage 1: Direct JSON parse
   - Stage 2: Fallback with markdown stripping
5. **Persist to Memory**: Saves accepted ideas to `outputs/global_cache/ideas.json`
6. **Update Shared State**: Adds judge results to shared_state custom_data

#### Critical Requirements for Judge Output:
- ✅ Output MUST be pure JSON
- ✅ NO ```json code blocks
- ✅ NO backticks or markdown
- ✅ NO explanatory text before/after JSON
- ✅ Single valid JSON object
- ✅ All numeric scores (NOT strings)

### Stage 5: Memory Persistence
- **File Location**: `outputs/global_cache/ideas.json`
- **Format**: JSON with metadata
- **Content**:
  - All accepted ideas from all iterations
  - Timestamp when idea was accepted
  - Iteration number where discovered
  - Cumulative statistics
- **Purpose**: Maintain history of accepted ideas across iterations
- **Access**: Available in shared_state custom_data for subsequent iterations

### Stage 6: Shared State Update
- **Key**: `judge_results_iteration_N`
- **Data**: Accepted/rejected counts and idea names
- **Key**: `ideas_memory_file`
- **Data**: Path to ideas.json for reference
- **Key**: `total_accepted_ideas`
- **Data**: Total count of accepted ideas in memory
- **Purpose**: Make judge results available to all nodes in same and future iterations

### Stage 7: Final Output Formatting
- **Source**: Judge JSON output
- **Transformation**: Convert JSON to readable summary
- **Format**: Structured text report with sections:
  - Accepted ideas (with scores and details)
  - Rejected ideas (with reasons)
  - Synthesis and insights
  - Recommendations and strategic insights
- **Destination**: `final_output.txt`

## Data Flow Diagram

```
Chaos Generator (text)
    ↓
Creative Node A (text) ──→ Refinement Node A (text) ──┐
Creative Node B (text) ──→ Refinement Node B (text) ──┤
    ↓                                                   ↓
[Iteration Control] ←────────────── Judge Node (JSON) ←┘
                                         ↓
                            [Parse JSON & Extract Ideas]
                                         ↓
                          [Save to ideas.json] 
                                         ↓
                        [Update shared_state]
                                         ↓
                         [Format Summary]
                                         ↓
                        [final_output.txt]
```

## Iteration Flow

### Multi-Iteration Scenario:
1. **Iteration 0**:
   - Chaos → Creative → Refinement → Judge
   - Accepted ideas saved to ideas.json
   - Shared state updated with judge results
   
2. **Iteration 1**:
   - Judge results from iteration 0 accessible via shared_state
   - Can modify prompts to avoid regenerating accepted ideas
   - New judge results appended to ideas.json
   - History preserved for analysis

## Implementation Details

### Judge Node Methods:

#### `_evaluate_refinement_output()`
- Parses refinement text output
- Builds judge prompt with context
- Calls judge agent
- **Robust JSON parsing**:
  - Attempts direct JSON parse first
  - Falls back to markdown stripping if needed
  - Logs raw response on failure for debugging
  - Returns error structure if both fail

#### `_save_accepted_ideas_to_memory()`
- Loads existing ideas from ideas.json
- Appends new accepted ideas with metadata
- Saves back to ideas.json
- Returns memory_data for shared state update

#### `_update_shared_state_with_judge_results()`
- Stores judge results in shared_state.custom_data
- Adds reference to ideas.json file
- Updates total count of accepted ideas
- Makes data available to all nodes

### Format Functions:

#### `_format_judge_output_as_summary()` (in agent_flow_graph.py)
- Converts judge JSON to readable summary
- Handles JSON parsing failures gracefully
- Generates structured text report
- Includes all judge insights and recommendations

## Consistency Checks

### Data Format Validation:
- ✅ Chaos/Creative/Refinement: Plain text (no JSON requirements)
- ✅ Judge input: Accepts text format from refinement
- ✅ Judge output: Pure JSON without markdown
- ✅ Memory storage: JSON format with metadata
- ✅ Final output: Readable summary text

### Error Handling:
- Judge JSON parsing failures → Fallback to markdown stripping
- Memory file load failures → Creates new ideas.json
- Shared state updates → Logging on all errors
- Output formatting → Falls back to raw judge output if parsing fails

## Best Practices

1. **Always validate judge output** is pure JSON before processing
2. **Log raw responses** when parsing fails for debugging
3. **Persist immediately** after judge evaluation succeeds
4. **Update shared state** to make data available downstream
5. **Format final output** for human readability
6. **Preserve history** in ideas.json across all iterations
7. **Use consistent timestamps** for all metadata

## Future Extensions

- Multi-threaded idea persistence
- Database backend for ideas.json
- Real-time memory updates during judge processing
- Streaming judge output handling
- Batch evaluation of multiple refinement outputs

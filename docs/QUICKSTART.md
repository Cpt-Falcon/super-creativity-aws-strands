# Super Creativity - Quick Start Examples

## Installation First

Before running examples, ensure you've installed and configured the system:

```bash
# Clone and install
git clone https://github.com/yourusername/super-creativity-strands.git
cd super-creativity-strands
pip install -e ".[semantic]"

# Configure AWS (or use environment variables)
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key

# Change to creativity_agent directory
cd creativity_agent
```

All examples below use commands from this directory.

---

## Example 1: Full Feature Set (Recommended)

```bash
python main_graph.py --prompt "Design an innovative urban farming solution for densely populated cities"
```

**What Happens:**
1. **Chaos Generation**: 3 semantic tangential concepts researched in real-time
   - Example: Mycelium networks, tessellation patterns, biomimicry principles
2. **Creative Phase A**: High-temperature agent (T=0.7) generates diverse ideas
   - Tools: Web search, URL content retrieval for research
3. **Refinement Phase A**: Low-temperature agent (T=0.1) scores and organizes
4. **Judge Evaluation**: Independent Claude model evaluates with 4-criteria rubric
5. **Iteration**: Process repeats with new chaos seeds
6. **Final Synthesis**: Best ideas synthesized into comprehensive output

**Output Structure:**
```
outputs/run_YYYYMMDD_HHMMSS/
├── chaos_input_iteration_0.txt        # Seeds used
├── A_creative_iteration_0.txt         # Model A raw ideas
├── A_refinement_iteration_0.txt       # Model A refined + scored
├── B_creative_iteration_0.txt         # Model B raw ideas
├── B_refinement_iteration_0.txt       # Model B refined + scored
├── judge_evaluations_iteration_0.txt  # Judge scores (JSON)
├── final_output.txt                   # Final synthesis
└── memory/
    └── ideas.json                     # Accepted ideas tracking
```

**Execution Time:** ~10-15 minutes
**Cost:** ~$0.50-$1.00 (AWS Bedrock)

---

## Example 2: Maximum Divergence (Brainstorming Mode)

For intensive creative exploration:

```bash
python main_graph.py \
  --chaos-seeds 8 \
  --semantic-backend sentence-transformers \
  --prompt "Create revolutionary new forms of human-computer interaction"
```

**Why This Works:**
- 8 semantic seeds per iteration = more creative directions
- sentence-transformers backend = highest quality tangential concepts
- Perfect for brainstorming workshops
- Explores diverse solution spaces

**Best for:** Innovation sprints, ideation workshops, blue-sky thinking

**Execution Time:** ~20-25 minutes
**Cost:** ~$1.50-$2.00

---

## Example 3: Memory-Focused (Iterative Development)
````

For focused iteration without random tangents:

```bash
python main.py --no-chaos --prompt "Improve customer onboarding for SaaS products"
```

**Benefits:**
- Builds systematically on previous ideas
- No random tangents distracting from core topic
- Faster execution (no chaos research step)
- Good for refining existing concept

---

## Example 4: Fresh Start (No Memory)

For completely independent sessions:

```bash
python main.py --no-memory --prompt "Design a wellness tracking app"
```

**Benefits:**
- Ignores previous exploration history
- Allows regenerating previously explored ideas
- Useful for comparing different creative approaches
- Fresh perspective on familiar topics

---

## Example 5: Minimal Mode

For fastest execution:

```bash
python main.py --no-memory --no-chaos --prompt "Your creative request here"
```

**Benefits:**
- Pure alternating high/low temperature agents
- No additional processing overhead
- Original Super Creativity behavior
- Good for quick tests

---

## Example 6: Interactive Session

```bash
python main.py
# Then enter your prompt when asked
Enter your creative request: Design a carbon-neutral transportation network
```

---

## Understanding the Output

### Chaos Input Files
```
outputs/chaos_input_iteration_0.txt
```

Example content:
```
DIVERGENT EXPLORATION SEEDS:

• symbiosis
  Context: Mutually beneficial relationships between organisms, now studied
  in distributed systems and collaborative AI architectures...
  Potential connection: Could inspire transportation systems that create
  mutual benefits between users, infrastructure, and environment.
```

### Memory File
```
outputs/memory/idea_memory.json
```

Example content:
```json
{
  "explored_ideas": [
    {
      "concept": "Vertical hydroponic towers integrated into building facades",
      "key_points": [
        "Utilizes unused vertical space",
        "Reduces transportation costs",
        "Natural building insulation"
      ],
      "iteration": 0,
      "timestamp": "2025-01-15T10:30:00",
      "quality_score": null
    }
  ],
  "rejected_ideas": []
}
```

### Agent Output Files

**High-temperature creative output** (`ah_iteration_0.txt`):
- Raw creative ideas with chaos inspiration
- Diverse concepts and approaches
- Speculative and innovative thinking

**Low-temperature refinement output** (`al_iteration_0.txt`):
- Structured analysis of creative ideas
- Feasibility assessment
- Organized themes and categories
- Implementation considerations

**Final output** (`bl_final.txt`):
- Comprehensive synthesis
- Best ideas from all iterations
- Actionable recommendations
- Clear structure and priorities

---

## Monitoring Execution

### Console Output
```
================================================================================
SUPER CREATIVITY - Enhanced Multi-Agent Ideation
================================================================================
Iterations: 2
Memory Tracking: ENABLED
Chaos Generator: ENABLED
Chaos Seeds per Iteration: 3
================================================================================

Starting creativity flow...
Iteration 1, Step ah: Completed successfully
Iteration 1, Step al: Completed successfully
Iteration 1, Step bh: Completed successfully
Iteration 1, Step bl: Completed successfully
Iteration 2, Step ah: Completed successfully
Iteration 2, Step al: Completed successfully
Iteration 2, Step bh: Completed successfully
Final step bl: Completed successfully

================================================================================
Flow completed!
================================================================================
Final result saved to outputs/bl_final.txt
Check the outputs/ directory for all intermediate results.
Memory state saved to outputs/memory/idea_memory.json
Chaos inputs saved as outputs/chaos_input_iteration_*.txt
```

---

## Tips for Best Results

### 1. Start Broad, Then Focus
```bash
# First run: Generate diverse ideas
python main.py --chaos-seeds 5 --prompt "Innovation in education"

# Second run: Focus on specific area (with memory)
python main.py --chaos-seeds 2 --prompt "AI-powered personalized learning"
```

### 2. Build on Previous Sessions
Memory persists across runs, so you can:
```bash
# Day 1: Initial exploration
python main.py --prompt "Sustainable packaging solutions"

# Day 2: Continue building (memory prevents regeneration)
python main.py --prompt "Sustainable packaging solutions"
# System will avoid previously explored concepts
```

### 3. Compare Approaches
```bash
# Run A: With chaos
python main.py --prompt "Remote work collaboration tool"

# Rename outputs
mv outputs outputs_with_chaos

# Run B: Without chaos
python main.py --no-chaos --no-memory --prompt "Remote work collaboration tool"

# Compare approaches
diff outputs_with_chaos/bl_final.txt outputs/bl_final.txt
```

### 4. Manual Memory Management

If the system explores a poor direction, manually reject it:

```python
from pathlib import Path
from utilities import MemoryManager

memory_mgr = MemoryManager(Path("creativity_agent/outputs/memory"))
memory_mgr.load_memory()

memory_mgr.mark_as_rejected(
    concept="Blockchain-based timestamping for collaboration",
    reason="Too speculative, unclear value proposition",
    iteration=1
)

memory_mgr.save_memory()
```

Then run again:
```bash
python main.py --prompt "Remote work collaboration tool"
# System will now avoid blockchain directions
```

---

## Troubleshooting

### Issue: "No chaos seeds generated"
**Solution:** Check AWS credentials and Bedrock access
```bash
aws bedrock list-foundation-models --region us-east-1
```

### Issue: "Memory file corrupted"
**Solution:** Clear and restart
```bash
rm creativity_agent/outputs/memory/idea_memory.json
python main.py
```

### Issue: "Too many similar ideas generated"
**Solution:** 
1. Increase chaos seeds: `--chaos-seeds 5`
2. Check memory is enabled (default)
3. Review and manually reject repetitive concepts

### Issue: "Ideas too scattered/unfocused"
**Solution:**
1. Reduce chaos seeds: `--chaos-seeds 1`
2. Or disable chaos: `--no-chaos`
3. Keep memory enabled to build coherently

---

## Advanced Usage

### Custom Flow Configuration

Edit `flow_config.json` to:
- Change number of iterations
- Adjust model temperatures
- Modify step sequence
- Use different models

Example: More iterations with chaos
```json
{
  "iterations": 4,
  ...
}
```

### Programmatic Usage

```python
from pathlib import Path
from config import FlowConfig
from agent_flow import CreativityAgentFlow

# Load config
config = FlowConfig.from_json(Path("flow_config.json"))

# Create flow with custom settings
flow = CreativityAgentFlow(
    config,
    enable_memory=True,
    enable_chaos=True,
    chaos_seeds_per_iteration=4
)

# Run
result = flow.run_flow("Your creative prompt")

# Access memory
concepts = flow.memory_manager.memory.get_recent_concepts(limit=10)
print(f"Recent concepts: {concepts}")
```

---

## Performance Notes

### Execution Time
- **No memory, no chaos**: ~2-3 minutes (2 iterations)
- **Memory only**: ~2-3 minutes (minimal overhead)
- **Chaos only**: ~4-6 minutes (web searches add time)
- **Full features**: ~4-6 minutes

### Cost Considerations (AWS Bedrock)
- Each chaos seed = 1 additional LLM call with web search tools
- More chaos seeds = higher cost but better divergence
- Memory adds negligible cost (local storage only)

### Recommended Settings by Use Case

| Use Case | Memory | Chaos Seeds | Iterations |
|----------|--------|-------------|------------|
| Quick brainstorm | Disabled | 2-3 | 1-2 |
| Deep exploration | Enabled | 4-5 | 3-4 |
| Focused refinement | Enabled | 0-1 | 2-3 |
| Comparing approaches | Disabled | 3 | 2 |
| Building on previous work | Enabled | 2-3 | 2-3 |

---

## Next Steps

1. **Review** the comprehensive [ENHANCEMENTS.md](ENHANCEMENTS.md) documentation
2. **Try** the examples above
3. **Experiment** with different chaos seed counts
4. **Monitor** memory accumulation over multiple sessions
5. **Customize** chaos vocabulary for your domain
6. **Integrate** into your creative workflow

Happy creating! 🚀

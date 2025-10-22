# Quick Reference Guide

## Getting Started (5 minutes)

```bash
# 1. Install
cd super-creativity-strands
pip install -e ".[semantic]"

# 2. Configure
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# 3. Run
cd creativity_agent
python main_graph.py --prompt "Your creative challenge"

# 4. Check output
ls outputs/run_*/
cat outputs/run_*/final_output.txt
```

---

## Command Cheat Sheet

### Most Common
```bash
# Full features
python main_graph.py --prompt "Design innovative X"

# Quick test
python main_graph.py --mock --prompt "test"

# High creativity
python main_graph.py --chaos-seeds 8 --prompt "..."

# No chaos (focused)
python main_graph.py --no-chaos --prompt "..."
```

### Advanced Options
```bash
# Custom semantic backend
python main_graph.py --semantic-backend sentence-transformers --prompt "..."

# Disable features
python main_graph.py --no-judge --no-memory --prompt "..."

# Monitor performance
python main_graph.py --prompt "..." 2>&1 | tee run.log
```

---

## Output Structure

```
outputs/run_YYYYMMDD_HHMMSS/
├── chaos_input_iteration_0.txt       ← Random seeds used
├── A_creative_iteration_0.txt        ← First model raw ideas
├── A_refinement_iteration_0.txt      ← First model scored
├── B_creative_iteration_0.txt        ← Second model raw ideas
├── B_refinement_iteration_0.txt      ← Second model scored
├── judge_evaluations_iteration_0.txt ← Judge JSON scores
├── final_output.txt                  ← Synthesized result
└── memory/
    └── ideas.json                    ← Cross-session tracking
```

---

## Performance Guide

| Need | Command | Time | Cost |
|------|---------|------|------|
| **Test** | `--mock` | <1m | $0 |
| **Fast** | `--no-chaos` | 3-5m | ~$0.30 |
| **Normal** | default | 8-12m | ~$0.60 |
| **Quality** | `--chaos-seeds 6` | 15-20m | ~$2.00 |

---

## Troubleshooting

### "AWS credentials not found"
```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1
```

### "Permission denied" (Bedrock)
```bash
# Verify access
aws bedrock list-foundation-models --region us-east-1
```

### "Out of memory"
```bash
python main_graph.py --semantic-backend wordnet --prompt "..."
python main_graph.py --no-observability --prompt "..."
```

### "Unicode encoding error"
- Already fixed in v1.0.0!
- System now uses UTF-8 for all files

---

## Configuration Files

### `flow_config.json`
```json
{
  "iterations": 2,
  "models": {
    "A": {"model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"}
  }
}
```

### `.env`
```bash
AWS_DEFAULT_REGION=us-east-1
ELASTICSEARCH_URI=https://your-elastic.es.us-east-1.aws.found.io/
ELASTICSEARCH_API_KEY=your-key
```

---

## Key Features at a Glance

| Feature | Command | What It Does |
|---------|---------|-------------|
| **Chaos** | (default) | Random tangential concepts |
| **Memory** | (default) | Tracks explored ideas |
| **Judge** | (default) | Independent evaluation |
| **Web Search** | (default) | Research concepts |
| **Cache** | (default) | Reuse search results |
| **Observability** | (default) | ElasticSearch metrics |

---

## Understanding Output

### Stage 1: Chaos Input
```
Random concepts: "mycelium networks", "tessellation", "biomimicry"
```

### Stage 2: Creative Output
```
10-20 diverse ideas from high-temperature models
Each with: concept, benefits, implementation approach
```

### Stage 3: Refinement Output
```
Ideas evaluated on feasibility, originality, impact, substance
Scores 0-10 for each dimension
```

### Stage 4: Judge Output (JSON)
```json
{
  "accepted_ideas": [...],
  "rejected_ideas": [...],
  "top_recommendations": [...],
  "strategic_insights": [...]
}
```

### Stage 5: Final Output
```
Comprehensive report with:
- Top recommendations
- Strategic insights  
- Implementation pathways
- Resource requirements
- Success metrics
```

---

## Memory System

### How It Works
```
Session 1: Generate ideas A, B, C
  ↓ Save to memory

Session 2: "Avoid A, B, C. Find novel directions"
  ↓ Generate ideas D, E, F (different)
  
Session 3: "Avoid A, B, C, D, E, F. Find new ideas"
  ↓ Generate ideas G, H, I
```

### What Gets Tracked
- ✅ Idea names and concepts
- ✅ Acceptance/rejection status
- ✅ Judge scores
- ✅ Timestamp and iteration
- ✅ Key themes and patterns

---

## Semantic Backends

### Sentence Transformers (Best)
```bash
pip install -e ".[semantic]"
python main_graph.py --semantic-backend sentence-transformers --prompt "..."
```
- Highest quality concepts
- 4GB RAM needed
- 2GB disk for models

### Gensim (Good)
```bash
pip install -e ".[gensim]"
python main_graph.py --semantic-backend gensim --prompt "..."
```
- Good balance
- 1GB RAM

### WordNet (Fast)
```bash
pip install -e ".[nltk]"
python main_graph.py --semantic-backend wordnet --prompt "..."
```
- Fastest
- 100MB RAM

### Simple (Minimal)
```bash
python main_graph.py --semantic-backend simple --prompt "..."
```
- Purely random
- No models needed

---

## Common Workflows

### Innovation Workshop
```bash
# Session 1: Exploration
python main_graph.py \
  --chaos-seeds 8 \
  --semantic-backend sentence-transformers \
  --prompt "Design innovative solutions for X"

# Session 2: Next day - build on Day 1 memory
python main_graph.py \
  --chaos-seeds 6 \
  --prompt "Design innovative solutions for X"

# Results automatically avoid Day 1 ideas
```

### Product Development
```bash
# Quick initial ideas
python main_graph.py --no-chaos --prompt "New features"

# Refined with deeper research
python main_graph.py \
  --chaos-seeds 4 \
  --prompt "New features for X"
```

### Strategic Planning
```bash
# Focused on feasibility
python main_graph.py \
  --no-chaos \
  --prompt "Business opportunities"
```

---

## Monitoring & Debugging

### Enable Verbose Logging
```bash
# Check what's happening
tail -f outputs/run_*/creativity_agent.log

# Save full output
python main_graph.py --prompt "..." > run.log 2>&1
```

### Check Cache Performance
```bash
# See what was cached
sqlite3 outputs/global_cache/global_web_cache.db \
  "SELECT query, url_count FROM queries LIMIT 5;"
```

### Verify Output Quality
```bash
# Check judge scores
python -m json.tool outputs/run_*/judge_evaluations_iteration_*.txt

# See accepted ideas
python -c "import json; print(json.dumps(json.load(open('outputs/run_*/memory/ideas.json')), indent=2))"
```

---

## Frequently Asked Questions

**Q: How long does it take?**
- Normal run: 8-12 minutes with all features

**Q: How much does it cost?**
- Normal run: ~$0.50-$1.00 in AWS Bedrock charges

**Q: Can I run it locally?**
- Yes! Need AWS credentials with Bedrock access

**Q: Can I use different models?**
- Yes! Edit `flow_config.json` with other Bedrock models

**Q: How does memory work?**
- Tracks explored ideas to avoid repetition in future sessions

**Q: What if I want no chaos?**
- Use `--no-chaos` for focused, memory-only ideation

**Q: Can I disable ElasticSearch?**
- Yes! Use `--no-observability` if not set up

**Q: Is it production-ready?**
- Yes! Version 1.0.0 is production-grade

---

## Documentation Links

- **Full README**: [README.md](./README.md)
- **Installation**: [INSTALLATION.md](./INSTALLATION.md)
- **Quick Start**: [QUICKSTART.md](./QUICKSTART.md)
- **System Design**: [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md)
- **API Reference**: [API.md](./API.md)
- **Configuration**: [CONFIGURATION.md](./CONFIGURATION.md)
- **Release Notes**: [RELEASE_NOTES.md](./RELEASE_NOTES.md)

---

**Super Creativity Strands - Quick Reference v1.0.0**

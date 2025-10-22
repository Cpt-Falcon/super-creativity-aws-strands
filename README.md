# Super Creativity Strands 🚀

**Production-Ready AI Creativity Engine** | Multi-Agent Orchestration | Graph-Based Flow Control | AWS Bedrock LLMs | Persistent Memory | Chaos-Driven Exploration | Independent Evaluation

> An intelligent, scalable system for serious creative ideation using advanced multi-agent orchestration, persistent exploration memory, divergent thinking acceleration through semantic chaos, and unbiased evaluative feedback with structured output.

---

## 📋 Table of Contents

- [What is Super Creativity?](#what-is-super-creativity)
- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Architecture](#architecture)
- [Documentation](#-documentation)
- [Usage Examples](#-usage-examples)
- [Requirements](#-requirements)
- [Troubleshooting](#-troubleshooting)

---

## What is Super Creativity?

**Super Creativity Strands** is a production-grade AI-powered creative ideation system built on AWS Bedrock and AWS Strands (multi-agent orchestration framework). It combines:

1. **Multi-Agent Collaboration** - Different AI models working together with specialized roles
2. **Divergent Thinking** - Chaos generator creates tangential concepts that spark creativity
3. **Quality Evaluation** - Independent judge evaluates ideas with standardized 4-criteria rubric
4. **Persistent Memory** - Cross-session idea tracking prevents redundancy and builds knowledge
5. **Web-Grounded Research** - All concepts researched and validated against real-world data
6. **Production Observability** - ElasticSearch integration for metrics and historical analysis

**Perfect for:**
- 💡 Innovation workshops and strategic brainstorming
- 🏢 Product development ideation and feature exploration
- 📊 Strategic planning and business model innovation
- 🎨 Creative direction exploration and concept development
- 🔬 Research concept generation and hypothesis development
- 🎯 Problem-solving across teams and disciplines

---

## ✨ Key Features

### 🧠 Multi-Agent Orchestration
- **Diverse Agent Roles**: Creative (high-temp), Refinement (low-temp), Judge (independent)
- **Multiple Model Support**: Run Claude Sonnet, Nova Pro, or other Bedrock models in parallel
- **Graph-Based Flow**: Sophisticated AWS Strands orchestration with conditional routing
- **Iterative Improvement**: Ideas mature through multiple refinement cycles
- **State Management**: Immutable typed state ensures consistency across agent handoffs

### 🎲 Chaos-Driven Divergent Thinking
- **Tangential Concept Seeds**: Semantically relevant but random concepts spark unexpected directions
- **Multiple Semantic Backends**: 
  - `sentence-transformers` - Deep semantic understanding (recommended)
  - `gensim` - Fast word embeddings
  - `wordnet` - Linguistic similarity
  - `simple` - Random concepts
- **Web-Researched Context**: Each seed researched in real-time, grounded in actual applications
- **Prevents Local Optima**: New seeds each iteration prevent idea convergence
- **Configurable Intensity**: Control chaos level with `--chaos-seeds` parameter (1-10)

### 🧠 Persistent Idea Memory
- **Cross-Session Continuity**: Ideas tracked across multiple runs in run-specific JSON database
- **Explored Ideas Registry**: What's already been discovered? What directions are exhausted?
- **Rejection Tracking**: Why were certain ideas rejected? Learn from dead ends
- **Smart Context Injection**: Agents receive explicit guidance on what to avoid
- **Automatic Concept Extraction**: System learns key themes and patterns
- **Manual API Control**: Programmatically manage memory for fine-tuned exploration

### ⚖️ Independent Judge System
- **Claude 4.5 Sonnet Evaluation**: Separate model ensures unbiased assessment (no author bias)
- **4-Criteria Scoring Rubric** (0-10 scale each):
  - 🎯 **Originality**: How novel and unique is the idea?
  - ⚙️ **Technical Feasibility**: Can it realistically be built with current technology?
  - 📈 **Impact Potential**: How significant would the impact be?
  - 💎 **Substance**: How well-developed and specific is the idea?
- **Standardized Evaluation**: Consistent scoring across all models and temperatures
- **Quality Threshold**: Ideas with avg score ≥5.0 accepted, <5.0 logged with reasoning
- **Customizable Criteria**: Edit judge system prompts to change evaluation focus
- **Detailed Reasoning**: Every score includes explanation and feedback

### 📊 Production Observability
- **ElasticSearch Integration**: Every run indexed for historical analysis
- **Comprehensive Metrics**:
  - Per-model performance comparison (Claude vs Nova Pro)
  - Temperature analysis (high creativity vs low precision)
  - Token usage tracking with AWS Bedrock cost estimates
  - Idea statistics (total generated, unique, duplicates, accepted/rejected rates)
  - Quality distribution (% excellent vs acceptable vs rejected)
  - Execution timing analysis (identify bottlenecks)
  - Web cache effectiveness (hit rates and performance gains)
- **Real-time Monitoring**: Track active runs across teams
- **Kibana Dashboards**: Visualize creativity metrics and trends
- **Historical Comparison**: Compare ideation quality across prompts and campaigns

### 🌐 Global Web Cache
- **Cross-Run Persistence**: SQLite database shared across all runs reduces API calls
- **Smart Caching**: Separate tables for search queries vs URL content
- **Performance Optimization**: Dramatically speeds up research phase
- **Cache Analytics**: Hit rate tracking and optimization recommendations

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/super-creativity-strands.git
cd super-creativity-strands

# Install with semantic backend support
pip install -e ".[semantic]"

# Or minimal install
pip install -e .

# Configure environment
cd creativity_agent
cp .env.example .env
# Edit .env with AWS credentials
```

See [INSTALLATION.md](./INSTALLATION.md) for detailed setup with semantic backend options.

### Basic Usage

```bash
# Run with all features enabled
python creativity_agent/main_graph.py --prompt "Design innovative sustainable packaging"

# With custom chaos level
python creativity_agent/main_graph.py --chaos-seeds 6 --prompt "Create new entertainment concepts"

# Memory-focused (no chaos)
python creativity_agent/main_graph.py --no-chaos --prompt "Improve SaaS onboarding"

# Fast testing (mock mode)
python creativity_agent/main_graph.py --mock --prompt "test"
```

### Output Structure

Each run creates a timestamped directory:

```
outputs/run_YYYYMMDD_HHMMSS/
├── A_creative_iteration_0.txt         # Ideas from model A (high temp)
├── A_refinement_iteration_0.txt       # Refined by model A (low temp)  
├── B_creative_iteration_0.txt         # Ideas from model B (high temp)
├── B_refinement_iteration_0.txt       # Refined by model B (low temp)
├── judge_evaluations_iteration_0.txt  # Judge scoring (JSON)
├── chaos_input_iteration_0.txt        # Tangential seeds used
├── final_output.txt                   # Synthesized result
└── memory/
    ├── ideas.json                     # Accepted ideas with metadata
    └── idea_memory.json               # Cross-session memory
```

---

## Architecture

### System Overview

```
USER INPUT (Creative Challenge)
    ↓
┌───────────────────────────────────┐
│   [Iteration Controller]          │ Manages loop iterations
└─────────────────┬─────────────────┘
    ↓
┌───────────────────────────────────┐
│   [Chaos Generator]               │ Semantic tangential concepts + research
└─────────────────┬─────────────────┘
    ↓
├─ ┌─────────────────┐    ┌─────────────────┐ ─┐
│  │ A_Creative      │ →  │ A_Refinement    │  │
│  │ (High Temp)     │    │ (Low Temp)      │  │
│  └─────────────────┘    └────────┬────────┘  ├─ Parallel Agents
│                                  ↓          │
│  ┌─────────────────┐    ┌─────────────────┐  │
│  │ B_Creative      │ →  │ B_Refinement    │  │
│  │ (High Temp)     │    │ (Low Temp)      │  │
│  └─────────────────┘    └────────┬────────┘  │
└─────────────────┬────────────────┘           ─┘
    ↓
┌───────────────────────────────────┐
│   [Independent Judge]             │ Evaluate & score (JSON output)
└─────────────────┬─────────────────┘
    ↓
┌───────────────────────────────────┐
│   [Iteration Controller]          │ Continue or stop?
└─────────────────┬─────────────────┘
    ↓ (if done)
┌───────────────────────────────────┐
│   [Deep Research Agent]           │ Synthesize final output
└─────────────────┬─────────────────┘
    ↓
FINAL OUTPUT (Comprehensive ideas + synthesis)
```

### Data Flow

| Stage | Input Format | Output Format | Purpose |
|-------|-------------|--------------|---------|
| **Chaos** | Original prompt | Plain text | Generate divergent seeds |
| **Creative** | Text (prompt + chaos) | Plain text (ideas) | Generate diverse ideas |
| **Refinement** | Text (ideas) | Plain text (scored) | Validate and organize |
| **Judge** | Text (ideas) | **JSON** (structured) | Evaluate and filter |
| **Final** | JSON results | Formatted text | Synthesize output |

**Key Design**: Data flows naturally between stages. Creative/Refinement output raw TEXT. Judge transforms to JSON. Final synthesizes.

### Component Responsibilities

- **Iteration Controller**: Loop logic, convergence checking
- **Chaos Generator**: Semantic concept generation + research
- **Creative Agents**: High-temperature idea generation with tools
- **Refinement Agents**: Low-temperature refinement and scoring
- **Judge**: Independent 4-criteria evaluation
- **Deep Research**: Final synthesis and recommendations
- **Memory Manager**: Persistent idea tracking
- **Web Cache**: Request deduplication
- **Observability**: Metrics and monitoring

---

## 📖 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[INSTALLATION.md](./INSTALLATION.md)** | Setup with semantic backend options | DevOps, Developers |
| **[QUICKSTART.md](./QUICKSTART.md)** | Practical examples and workflows | Users, Product Managers |
| **[CONFIGURATION.md](./CONFIGURATION.md)** | Config files and tuning | Operators |
| **[SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md)** | Architecture and design principles | Architects, Contributors |
| **[DATA_FLOW_ARCHITECTURE.md](./DATA_FLOW_ARCHITECTURE.md)** | Data formats and transformations | Developers, Debuggers |
| **[GRAPH_FLOWS.md](./GRAPH_FLOWS.md)** | Graph topology and state flow | Developers |
| **[LLM_AS_JUDGE_MEMORY_SYSTEM.md](./LLM_AS_JUDGE_MEMORY_SYSTEM.md)** | Judge and memory systems | Developers |
| **[API.md](./API.md)** | Python API reference | Developers |

---

## 💻 Command-Line Interface

```bash
python creativity_agent/main_graph.py [OPTIONS]

OPTIONS:
  --prompt TEXT                    Creative prompt (or enter interactively)
  --chaos-seeds INT               Number of chaos seeds per iteration (default: 3)
  --semantic-backend TEXT         Word discovery: auto|sentence-transformers|gensim|wordnet|simple
  --no-memory                     Disable idea memory tracking
  --no-chaos                      Disable chaos generation
  --no-judge                      Disable independent judge
  --no-observability              Disable ElasticSearch tracking
  --mock                          Use mock agents for testing (no LLM calls)
  --help                          Show all options
```

### Example Commands

```bash
# Standard: all features enabled
python creativity_agent/main_graph.py --prompt "Your challenge"

# Maximum creativity (high chaos, semantic backend)
python creativity_agent/main_graph.py \
  --chaos-seeds 8 \
  --semantic-backend sentence-transformers \
  --prompt "Design next-generation transportation"

# Focused iteration (memory-based, no chaos)
python creativity_agent/main_graph.py \
  --no-chaos \
  --prompt "Improve existing product"

# Minimal features (fast)
python creativity_agent/main_graph.py \
  --no-memory --no-chaos --no-judge \
  --prompt "Quick ideation"

# Testing without LLM calls
python creativity_agent/main_graph.py --mock --prompt "test"

# Interactive prompt
python creativity_agent/main_graph.py
# Then: "Enter your creative request: "
```

---

## 🎯 Use Cases

### 1. Innovation Sprint
```bash
python creativity_agent/main_graph.py \
  --prompt "Design innovative solutions for urban water scarcity" \
  --chaos-seeds 7 \
  --semantic-backend sentence-transformers
```
**Result**: 30+ diverse, well-researched ideas with independent evaluation

### 2. Product Feature Development
```bash
python creativity_agent/main_graph.py \
  --prompt "New features for our AI assistant to increase engagement" \
  --chaos-seeds 4
```
**Result**: Technically feasible features with refinement and evaluation

### 3. Strategic Business Planning
```bash
python creativity_agent/main_graph.py \
  --no-chaos \
  --prompt "Revenue diversification opportunities for B2B SaaS"
```
**Result**: Focused ideas building on previous sessions, no divergence

### 4. Quick Brainstorm
```bash
python creativity_agent/main_graph.py --mock --prompt "Ideas for team retreat"
```
**Result**: See system in action without waiting for LLM calls

### 5. Multi-Session Campaign
```bash
# Session 1
python creativity_agent/main_graph.py --prompt "AI safety improvements" 

# Session 2 (days later)
python creativity_agent/main_graph.py --prompt "AI safety improvements"
# System remembers from Session 1, avoids repeating ideas
```

---

## ⚙️ Configuration

### flow_config.json
Control models, temperatures, iterations:

```json
{
  "iterations": 2,
  "models": {
    "A": {
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
      "high_temp": 0.7,
      "low_temp": 0.1
    },
    "B": {
      "model_id": "us.anthropic.claude-opus-4-1-20250805-v1:0",
      "high_temp": 0.9,
      "low_temp": 0.0
    }
  }
}
```

### .env
AWS credentials and observability:

```bash
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

ELASTICSEARCH_URI=https://your-elastic.es.us-east-1.aws.found.io/
ELASTICSEARCH_API_KEY=your-key
```

See [CONFIGURATION.md](./CONFIGURATION.md) for complete options.

---

## 🔧 Performance & Costs

| Scenario | Command | Time | Cost |
|----------|---------|------|------|
| **Test** | `--mock` | <1m | $0 |
| **Fast** | `--no-chaos --no-judge` | 3-5m | ~$0.30 |
| **Balanced** | Default (all features) | 8-12m | ~$0.50-0.80 |
| **Quality** | `--chaos-seeds 6` + 3 iterations | 15-20m | ~$1.50-2.00 |
| **Comprehensive** | High chaos + transformers backend | 20-30m | ~$2.50-3.50 |

All costs are AWS Bedrock API charges. See [CONFIGURATION.md](./CONFIGURATION.md) for optimization tips.

---

## 🐛 Troubleshooting

### AWS Bedrock Access Issues
```bash
# Verify credentials are set
aws sts get-caller-identity

# Check Bedrock models are available
aws bedrock list-foundation-models --region us-east-1

# Test direct Bedrock invocation
aws bedrock-runtime invoke-model \
  --model-id "us.anthropic.claude-sonnet-4-20250514-v1:0" \
  --region us-east-1 \
  --body '{"prompt":"test"}' \
  output.txt
```

### Unicode/Encoding Errors
```bash
# Ensure UTF-8 encoding for terminal
export PYTHONIOENCODING=utf-8

# Run with explicit UTF-8
python -c "import sys; sys.stdout.encoding" 
# Should output: utf-8
```

### Out of Memory
```bash
# Use lightweight semantic backend
python creativity_agent/main_graph.py \
  --semantic-backend wordnet \
  --prompt "..."

# Or disable observability
python creativity_agent/main_graph.py \
  --no-observability \
  --prompt "..."
```

### Slow Execution
```bash
# Profile which stage is slow
python creativity_agent/main_graph.py \
  --no-observability \
  --prompt "..."

# Speed up: disable unnecessary features
python creativity_agent/main_graph.py \
  --no-chaos \
  --mock \
  --prompt "test"
```

See [INSTALLATION.md](./INSTALLATION.md) for more troubleshooting.

---

## 📦 Requirements

- **Python 3.9+** (3.11+ recommended)
- **AWS Account** with Bedrock access to Claude/Nova models
- **Core Dependencies**: boto3, strands, pydantic, duckduckgo-search
- **Optional**: sentence-transformers, gensim, nltk (for semantic discovery)

See [pyproject.toml](../pyproject.toml) for complete specifications.

---

## 🎓 How It Works: The Creative Process

### Phase 1: Chaos Generation (Divergent Thinking)
1. Analyze original prompt semantically
2. Generate random but contextual tangential concepts
3. Research each concept to understand real-world applications
4. Create enriched prompts combining challenge + chaos context

### Phase 2: Creative Generation (High Temperature)
1. High-temperature agents (T=0.7-1.0) generate diverse ideas
2. Agents equipped with web search tools for research
3. Memory prevents regenerating previously explored ideas
4. Output: 10-20 novel ideas with supporting evidence

### Phase 3: Refinement (Low Temperature)
1. Low-temperature agents (T=0.1-0.0) filter best ideas
2. Organize ideas with clear structure
3. Extract key concepts for memory
4. Score each idea on quality dimensions
5. Output: Well-organized, scored ideas

### Phase 4: Independent Evaluation (Judge)
1. Separate Claude model scores all ideas
2. 4-criteria rubric: Originality, Feasibility, Impact, Substance
3. Average score ≥5.0 = Accepted, <5.0 = Rejected with reasoning
4. Output: Clean JSON with decisions and explanations

### Phase 5: Iteration or Synthesis
1. If iterations remain: Generate new chaos seeds, loop back
2. If done: Synthesize all accepted ideas into final recommendation
3. Output: Comprehensive report with top ideas and strategic insights

### Memory in Action (Multi-Session)
```
Session 1:
  • Generate ideas A, B, C
  • Judge evaluates: A, B accepted; C rejected
  • Memory saves: A, B as explored

Session 2 (days later):
  • Prompt: "Avoid ideas like A, B. Find novel directions"
  • Generate ideas D, E, F (different from Session 1)
  • Judge evaluates: D, E, F all accepted
  • Memory updates: A, B, D, E, F explored
  
Session 3:
  • Prompt: "Avoid A, B, D, E, F. Find completely new directions"
  • System builds on accumulated knowledge
```

---

## 🚀 Getting Started

1. **[Install](./INSTALLATION.md)** with semantic backend
2. **[Configure](./CONFIGURATION.md)** AWS and models
3. **[Run First Session](./QUICKSTART.md)** with example prompt
4. **[Review Output](./QUICKSTART.md#understanding-output)** in `outputs/` directory
5. **[Monitor Performance](./CONFIGURATION.md#observability)** with Kibana
6. **[Explore API](./API.md)** for programmatic use

---

## 📚 Learn More

- **Deep Dive**: See [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md) for architectural principles
- **Data Science**: See [DATA_FLOW_ARCHITECTURE.md](./DATA_FLOW_ARCHITECTURE.md) for pipeline details
- **Integration**: See [API.md](./API.md) for programmatic integration
- **Production**: See [CONFIGURATION.md](./CONFIGURATION.md) for deployment and scaling

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/description`
3. Commit changes: `git commit -am 'Add feature description'`
4. Push to branch: `git push origin feature/description`
5. Submit a Pull Request

**Development Requirements**:
- Code follows existing style and patterns
- All new features include unit tests
- Documentation is updated
- Type hints are comprehensive
- Run `black`, `isort`, `pylint` before committing

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

## 📞 Support & Questions

- 📖 **Documentation**: Check [docs/](.) folder for comprehensive guides
- 🐛 **Issues**: Report bugs with reproduction steps
- 💬 **Questions**: See [API.md](./API.md) and [QUICKSTART.md](./QUICKSTART.md)
- 🔍 **Debugging**: Enable verbose logging with `--debug` flag

---

## 🙏 Acknowledgments

Built on:
- **AWS Bedrock** for foundation models
- **AWS Strands** for multi-agent orchestration
- **Pydantic** for data validation
- **DuckDuckGo Search** for semantic research

---

**Made with ❤️ for creative innovation at scale**

*Last Updated: October 22, 2025*

*Version: 1.0.0 (Production)*
````
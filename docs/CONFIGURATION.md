# Configuration Guide

## Overview

The system is configured through:
1. **flow_config.json** - Flow structure and model settings
2. **.env** - Environment variables (AWS, ElasticSearch)
3. **Command-line arguments** - Runtime feature toggles
4. **prompts/*** - Agent system prompts

## flow_config.json

Controls the creative flow structure and model configuration.

### Schema

```json
{
  "iterations": <number>,
  "models": {
    "<model_key>": {
      "model_id": "<bedrock_model_id>",
      "high_temp": <float>,
      "low_temp": <float>
    }
  },
  "steps": [...],
  "loop_back_to": "<step_id or null>",
  "final_step": "<step_id>"
}
```

### Examples

#### Single Model (Faster)
```json
{
  "iterations": 2,
  "models": {
    "A": {
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
      "high_temp": 1.0,
      "low_temp": 0.1
    }
  },
  "steps": []
}
```

**Result**: One creative → refinement cycle per iteration, fast execution

#### Dual Model (Diverse Perspectives)
```json
{
  "iterations": 3,
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

**Result**: Two models → different styles, more diverse ideas, longer execution

#### High Temperature Creativity
```json
{
  "models": {
    "A": {
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
      "high_temp": 1.5,
      "low_temp": 0.05
    }
  }
}
```

**Effect**: High-temp set to 1.5 (more creative), Low-temp 0.05 (very focused)

#### Balanced Settings
```json
{
  "models": {
    "A": {
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
      "high_temp": 0.8,
      "low_temp": 0.3
    }
  }
}
```

**Effect**: Less divergence (0.8), less strict refinement (0.3), more balanced

### Available Bedrock Models

#### Claude Family
- `us.anthropic.claude-3-5-sonnet-20241022-v2:0` - Best quality (recommended)
- `us.anthropic.claude-sonnet-4-20250514-v1:0` - Latest Sonnet
- `us.anthropic.claude-3-opus-20240229-v1:0` - Most capable (slower)

#### Amazon Nova
- `us.amazon.nova-pro-1:0` - Balanced quality/speed
- `us.amazon.nova-lite-1:0` - Fast and cheap

#### Other
- `meta.llama3-1-8b-instruct-v1:0` - Open-source option

### Configuration Strategies

#### Strategy 1: Speed (5 minutes)
```json
{
  "iterations": 1,
  "models": {
    "A": {
      "model_id": "us.amazon.nova-lite-1:0",
      "high_temp": 1.0,
      "low_temp": 0.1
    }
  }
}
```

#### Strategy 2: Quality (15 minutes)
```json
{
  "iterations": 3,
  "models": {
    "A": {
      "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
      "high_temp": 1.0,
      "low_temp": 0.1
    }
  }
}
```

#### Strategy 3: Diversity (20 minutes)
```json
{
  "iterations": 2,
  "models": {
    "A": {
      "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
      "high_temp": 1.0,
      "low_temp": 0.1
    },
    "B": {
      "model_id": "us.amazon.nova-pro-1:0",
      "high_temp": 0.95,
      "low_temp": 0.2
    }
  }
}
```

## Environment Variables (.env)

Located in `creativity_agent/.env`

### Required

```bash
# AWS configuration
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### Optional

```bash
# ElasticSearch for observability (required for --no-observability to have effect)
ELASTICSEARCH_URI=https://your-elastic.es.us-east-1.aws.found.io/
ELASTICSEARCH_API_KEY=your-api-key-here

# Bedrock region (if different from default)
AWS_BEDROCK_REGION=us-east-1
```

### Example .env File

```bash
# AWS
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# ElasticSearch
ELASTICSEARCH_URI=https://my-deployment-1234567890.es.us-east-1.aws.found.io/
ELASTICSEARCH_API_KEY=ASDFGHJKLZXCVBNM1234567890=

# Optional
LOG_LEVEL=INFO
OUTPUT_DIR=outputs
```

### Setup Steps

1. **Create .env file**
```bash
cd creativity_agent
cp .env.example .env
```

2. **Edit with your credentials**
```bash
# Use your editor
nano .env
# or
code .env
```

3. **Verify (don't commit to git!)**
```bash
cat .env  # Should show your values
# Add to .gitignore:
echo ".env" >> ../.gitignore
```

## Command-Line Arguments

### Feature Control

```bash
# All features enabled (default)
python main.py --prompt "your prompt"

# Disable memory
python main.py --no-memory --prompt "your prompt"

# Disable chaos
python main.py --no-chaos --prompt "your prompt"

# Disable judge
python main.py --no-judge --prompt "your prompt"

# Disable observability
python main.py --no-observability --prompt "your prompt"

# Minimal (disable all)
python main.py --no-memory --no-chaos --no-judge --no-observability --prompt "your prompt"
```

### Chaos Configuration

```bash
# Custom number of chaos seeds
python main.py --chaos-seeds 5 --prompt "your prompt"
# Generates 5 random tangential concepts per iteration

# Semantic backend selection
python main.py --semantic-backend sentence-transformers --prompt "your prompt"
# Options: auto, sentence-transformers, gensim, wordnet, simple
```

### Observability Configuration

```bash
# Override environment settings
python main.py --es-uri "https://elastic.example.com/" --es-api-key "key" --prompt "your prompt"

# Or set via env vars (preferred)
export ELASTICSEARCH_URI=https://elastic.example.com/
export ELASTICSEARCH_API_KEY=key
python main.py --prompt "your prompt"
```

### Execution Modes

```bash
# Mock mode (no LLM calls, fast debugging)
python main.py --mock --prompt "test"

# Interactive prompt
python main.py
# Will ask for prompt interactively

# Specific prompt
python main.py --prompt "Design an innovative solution"
```

## Prompt Configuration

System prompts are in `creativity_agent/prompts/`

### creative_agent.txt

Used by high-temperature creative expansion agents.

**Key elements**:
- Encourages divergent thinking
- References chaos context (injected)
- References memory context (injected)
- Instructs use of web search tools
- Focuses on novelty and originality

**Injection points**:
```
{CHAOS_CONTEXT}     - Tangential exploration seeds
{MEMORY_CONTEXT}    - Previously explored/rejected ideas
{USER_PROMPT}       - The user's creative request
```

### refinement_agent.txt

Used by low-temperature refinement agents.

**Key elements**:
- Focuses on feasibility and validation
- Structures ideas clearly
- References memory context (injected)
- Instructs use of web search for validation
- Extracts actionable recommendations

**Injection points**:
```
{MEMORY_CONTEXT}     - Previously explored/rejected ideas
{CREATIVE_OUTPUT}    - Output from creative agent
{USER_PROMPT}        - The user's creative request
```

### judge_agent.txt

Used by independent judge for evaluation.

**Scoring criteria**:
- Originality (0-10) - How novel/unique?
- Technical Feasibility (0-10) - Can it be built?
- Impact Potential (0-10) - How useful/important?
- Substance (0-10) - Is it well-thought-out?

**Decision**:
- Average score ≥ 5.0 → Accept
- Average score < 5.0 → Reject

### final_step.txt

Used for final synthesis and deep research.

**Key elements**:
- Synthesizes all ideas from iterations
- Organizes by theme and impact
- Provides actionable recommendations
- Includes supporting research

## Semantic Backend Configuration

The `--semantic-backend` option controls how chaos seeds are discovered.

### Available Backends

| Backend | Quality | Speed | Memory | Download Size | Auto-Select Order |
|---------|---------|-------|--------|---------------|-------------------|
| sentence-transformers | Excellent | Slow | High | 2GB+ | 1st |
| gensim | Good | Medium | Medium | 100MB | 2nd |
| wordnet | Fair | Fast | Low | 10MB | 3rd |
| simple | Poor | Very Fast | Minimal | 0 | 4th |

### Backend Details

#### sentence-transformers (Best Quality)
```bash
python main.py --semantic-backend sentence-transformers --prompt "your prompt"
```
- Uses transformer-based embeddings
- Best semantic similarity
- Requires: `pip install -e ".[semantic]"`
- Download on first use: ~2GB
- Setup time: 30-60 seconds first run

#### gensim (Good/Lightweight)
```bash
python main.py --semantic-backend gensim --prompt "your prompt"
```
- Uses Word2Vec/GloVe vectors
- Good balance
- Requires: `pip install -e ".[gensim]"`
- Download: ~100MB
- Setup time: ~10 seconds first run

#### wordnet (Lightweight)
```bash
python main.py --semantic-backend wordnet --prompt "your prompt"
```
- Uses lexical database
- Fast, doesn't require downloads
- Requires: `pip install -e ".[nltk]"`
- Download: ~10MB (on first use via NLTK)

#### simple (Fallback)
```bash
python main.py --semantic-backend simple --prompt "your prompt"
```
- Pure random selection
- No quality filter
- No dependencies
- Fast

#### auto (Default, Recommended)
```bash
python main.py --prompt "your prompt"
# or explicitly:
python main.py --semantic-backend auto --prompt "your prompt"
```
- Automatically selects available backend
- Order: sentence-transformers > gensim > wordnet > simple
- Best balance of quality and availability

## Performance Tuning

### For Speed

```json
{
  "iterations": 1,
  "models": {
    "A": {
      "model_id": "us.amazon.nova-lite-1:0",
      "high_temp": 0.9,
      "low_temp": 0.1
    }
  }
}
```

```bash
python main.py --no-memory --no-judge --semantic-backend simple --chaos-seeds 2 --prompt "your prompt"
```

**Result**: ~3-5 minutes

### For Quality

```json
{
  "iterations": 3,
  "models": {
    "A": {
      "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
      "high_temp": 1.0,
      "low_temp": 0.1
    }
  }
}
```

```bash
python main.py --semantic-backend sentence-transformers --chaos-seeds 5 --prompt "your prompt"
```

**Result**: ~15-20 minutes, best ideas

### For Diversity

Use multiple models (see configuration strategies above).

## Output Structure

Each run creates:

```
outputs/
├── global_cache/
│   └── global_web_cache.db     # Shared cache across runs
│
└── run_YYYYMMDD_HHMMSS/        # Per-run directory
    ├── A_creative_iteration_0.txt
    ├── A_refinement_iteration_0.txt
    ├── B_creative_iteration_0.txt
    ├── B_refinement_iteration_0.txt
    ├── judge_evaluations_iteration_0.txt
    ├── A_creative_iteration_1.txt
    ├── A_refinement_iteration_1.txt
    ├── B_creative_iteration_1.txt
    ├── B_refinement_iteration_1.txt
    ├── judge_evaluations_iteration_1.txt
    ├── chaos_input_iteration_0.txt
    ├── chaos_input_iteration_1.txt
    ├── final_output.txt
    │
    ├── memory/
    │   └── idea_memory.json     # Persistent idea tracking
    │
    └── web_cache/
        └── run_web_cache.db     # Per-run web cache
```

## Troubleshooting Configuration

### Issue: "Model not found" Error

```
Error: Could not invoke model us.anthropic.claude-sonnet-4...
```

**Solution**: Verify model ID in flow_config.json

```bash
# List available models
aws bedrock list-foundation-models --region us-east-1

# Update flow_config.json with available model
```

### Issue: Slow Semantic Discovery

**Solution**: Switch to faster backend

```bash
python main.py --semantic-backend wordnet --prompt "your prompt"
```

### Issue: Out of Memory with Transformers

**Solution**: Use lightweight backend

```bash
python main.py --semantic-backend gensim --prompt "your prompt"
```

### Issue: ElasticSearch Connection Timeout

**Solution**: Verify URI and API key

```bash
# Test connection
curl -H "Authorization: ApiKey YOUR_API_KEY" https://YOUR_URI/

# If fails, check .env
cat creativity_agent/.env
```

## Quick Configuration Presets

Save these as different config files and swap as needed:

### config.fast.json
```json
{
  "iterations": 1,
  "models": {
    "A": {
      "model_id": "us.amazon.nova-lite-1:0",
      "high_temp": 0.9,
      "low_temp": 0.1
    }
  }
}
```

Usage:
```bash
cp flow_config.json flow_config.backup.json
cp config.fast.json flow_config.json
python main.py --prompt "test"
cp flow_config.backup.json flow_config.json
```

### config.quality.json
```json
{
  "iterations": 3,
  "models": {
    "A": {
      "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
      "high_temp": 1.0,
      "low_temp": 0.1
    }
  }
}
```

### config.balanced.json
```json
{
  "iterations": 2,
  "models": {
    "A": {
      "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
      "high_temp": 0.8,
      "low_temp": 0.2
    },
    "B": {
      "model_id": "us.amazon.nova-pro-1:0",
      "high_temp": 0.9,
      "low_temp": 0.2
    }
  }
}
```

# Installation Guide

## Prerequisites

- Python 3.9 or higher (3.11+ recommended)
- AWS Account with Bedrock access to Claude and/or Nova models
- pip or uv package manager
- Git for cloning the repository

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/super-creativity-strands.git
cd super-creativity-strands

# Install with semantic backends (recommended)
pip install -e ".[semantic]"

# Or minimal install
pip install -e .

# Configure AWS credentials
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Run first creative session
cd creativity_agent
python main_graph.py --prompt "Your creative challenge"
```

## Installation with Semantic Backends

The system includes optional semantic backends for enhanced word discovery in chaos generation.

### Option 1: Best Quality (Sentence Transformers - Recommended)
```bash
pip install -e ".[semantic]"
```
- Uses transformer-based embeddings
- Best quality tangential word discovery (highest precision)
- Higher memory/compute requirements (~4GB RAM)
- Requires ~2GB disk space for model downloads
- Best for: Innovation workshops, high-quality ideation

### Option 2: Good Quality (Gensim - Lightweight)
```bash
pip install -e ".[gensim]"
```
- Uses Word2Vec/GloVe vectors
- Good balance of quality and resource usage
- Lighter than transformers (~1GB RAM)
- Fast loading
- Best for: Production deployments, resource-constrained environments

### Option 3: WordNet (Lightweight & Fast)
```bash
pip install -e ".[nltk]"
```
- Uses lexical database (no ML models needed)
- Fastest option (<100MB)
- Lower quality but good for quick experiments
- Best for: Testing, quick prototyping

### Option 4: Simple Random (Minimal)
```bash
pip install -e .
```
- No external semantic models
- Purely random concept generation
- Minimal dependencies
- Best for: Testing architecture, mock mode

### Option 4: All Backends
```bash
pip install -e ".[all-semantic]"
```
Installs all semantic backends (not recommended unless you need to test all)

### Auto-Selection
If you don't specify, the system will automatically:
1. Try sentence-transformers first
2. Fall back to gensim
3. Fall back to wordnet
4. Use simple random selection if none available

## Environment Setup

### 1. AWS Credentials
Set up your AWS credentials (for Bedrock access):
```bash
# Using AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### 2. ElasticSearch (Optional, for observability)
Create a `.env` file in the `creativity_agent` directory:
```bash
cd creativity_agent
cp .env.example .env
```

Edit `.env`:
```env
# ElasticSearch for observability tracking
ELASTICSEARCH_URI=https://your-elastic-instance.es.us-east-1.aws.found.io/
ELASTICSEARCH_API_KEY=your-api-key-here

# AWS Settings
AWS_DEFAULT_REGION=us-east-1
```

Or export environment variables:
```bash
export ELASTICSEARCH_URI=https://your-elastic-instance.es.us-east-1.aws.found.io/
export ELASTICSEARCH_API_KEY=your-api-key-here
```

## Verification

### Test Basic Installation
```bash
cd creativity_agent
python main.py --help
```

Should display help with all available options.

### Test with Mock Mode (No LLM calls)
```bash
python main.py --mock --prompt "Test prompt"
```

This runs through the full system without calling AWS Bedrock, useful for:
- Testing graph structure
- Verifying all components are installed
- Quick debugging

## Troubleshooting

### ImportError: No module named 'strands'
```bash
# Reinstall with latest strands
pip install --upgrade strands
```

### AWS Bedrock Access Error
```
Error: User: arn:aws:iam::... is not authorized to perform: bedrock:InvokeModel
```
- Verify AWS credentials are set correctly
- Check that your AWS account has Bedrock enabled
- Ensure you're in a region that supports Bedrock (us-east-1, us-west-2, eu-central-1, ap-northeast-1)

### Semantic Backend Issues
```bash
# If sentence-transformers fails
pip install --upgrade sentence-transformers

# If NLTK fails
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

### ElasticSearch Connection Error
```
Error: ConnectionError: Connection refused connecting to https://...
```
- Verify ELASTICSEARCH_URI is correct
- Check that the ElasticSearch cluster is running
- Verify API key has proper permissions

### Out of Memory
If you get OOM errors, especially with sentence-transformers:
```bash
# Use lighter semantic backend
python main.py --semantic-backend gensim

# Or
python main.py --semantic-backend wordnet
```

## Development Setup

For development and testing:
```bash
pip install -e ".[dev,all-semantic]"
```

This installs:
- pytest and pytest-cov for testing
- black for code formatting
- flake8 for linting
- mypy for type checking
- isort for import sorting
- All semantic backends

## Next Steps

See [QUICKSTART.md](./QUICKSTART.md) for usage examples.

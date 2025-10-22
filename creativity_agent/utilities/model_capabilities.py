"""
Model capability detection for streaming and tool use support.
"""

# Models that DON'T support tool use in streaming mode
MODELS_WITHOUT_STREAMING_TOOLS = {
    # Llama models - don't support tool use in streaming
    "us.meta.llama": {
        "supports_tools": True,
        "supports_streaming_tools": False,
        "description": "Llama models support tools but not in streaming mode"
    },
    # Add more models here as needed
}

# Models that support streaming with tools
MODELS_WITH_STREAMING_TOOLS = {
    "us.anthropic.claude": {
        "supports_tools": True,
        "supports_streaming_tools": True,
        "description": "Claude models support tools in streaming mode"
    },
}

def supports_streaming_tools(model_id: str) -> bool:
    """
    Check if a model supports tool use in streaming mode.
    
    Args:
        model_id: The model ID from AWS Bedrock
        
    Returns:
        True if model supports tools in streaming, False otherwise
    """
    # Check against models without streaming tools first
    for prefix, config in MODELS_WITHOUT_STREAMING_TOOLS.items():
        if prefix in model_id:
            return config.get("supports_streaming_tools", False)
    
    # Check against models with streaming tools
    for prefix, config in MODELS_WITH_STREAMING_TOOLS.items():
        if prefix in model_id:
            return config.get("supports_streaming_tools", False)
    
    # Default to False if unknown
    return False

def supports_tools(model_id: str) -> bool:
    """
    Check if a model supports tool use at all.
    
    Args:
        model_id: The model ID from AWS Bedrock
        
    Returns:
        True if model supports tools, False otherwise
    """
    # Check against models without streaming tools
    for prefix, config in MODELS_WITHOUT_STREAMING_TOOLS.items():
        if prefix in model_id:
            return config.get("supports_tools", False)
    
    # Check against models with streaming tools
    for prefix, config in MODELS_WITH_STREAMING_TOOLS.items():
        if prefix in model_id:
            return config.get("supports_tools", False)
    
    # Default to True if unknown (most modern models support tools)
    return True

def get_model_info(model_id: str) -> dict:
    """
    Get information about a model's capabilities.
    
    Args:
        model_id: The model ID from AWS Bedrock
        
    Returns:
        Dict with model capability information
    """
    # Check against models without streaming tools
    for prefix, config in MODELS_WITHOUT_STREAMING_TOOLS.items():
        if prefix in model_id:
            return config
    
    # Check against models with streaming tools
    for prefix, config in MODELS_WITH_STREAMING_TOOLS.items():
        if prefix in model_id:
            return config
    
    # Default info for unknown models
    return {
        "supports_tools": True,
        "supports_streaming_tools": False,
        "description": f"Unknown model {model_id} - assuming limited streaming support"
    }

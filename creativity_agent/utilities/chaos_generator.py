"""
Chaos generator for creating divergent exploration seeds.
Uses high-temperature LLM and web search to discover tangential concepts.
Now with dynamic semantic word discovery using embeddings.
"""

from strands import Agent
from strands.models import BedrockModel
from typing import List, Optional
import logging
import os
from creativity_agent.models import ChaosInput, TangentialConcept
from creativity_agent.tools import bulk_search_web, get_url_content, search_web
from .dynamic_semantic_discovery import DynamicSemanticWordDiscovery

logger = logging.getLogger(__name__)


class ChaosGenerator:
    """
    Generates chaos input for divergent exploration.
    Creates random tangential concepts and researches them via web search.
    Uses dynamic semantic discovery to find contextually relevant tangential words.
    """
    
    def __init__(
        self, 
        model_id: str, 
        temperature: float = 1.0, 
        streaming: bool = True,
        region_name: Optional[str] = None,
        semantic_backend: str = "auto",
        tangent_range: tuple = (0.3, 0.7)
    ):
        """
        Initialize chaos generator.
        
        Args:
            model_id: Bedrock model ID for chaos generation
            temperature: Temperature for random generation (should be high)
            streaming: Whether to use streaming mode (disable for models that don't support it)
            region_name: AWS region name
            semantic_backend: "auto", "sentence-transformers", "gensim", "wordnet", or "simple"
            tangent_range: (min, max) similarity for tangential words (0.3-0.7 is good sweet spot)
        """
        self.model = BedrockModel(
            model_id=model_id,
            temperature=temperature,
            streaming=streaming,
            region_name=region_name or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
        self.agent = Agent(model=self.model, tools=[search_web, get_url_content, bulk_search_web], callback_handler=None)
        
        # Initialize dynamic semantic discovery
        self.word_discoverer = DynamicSemanticWordDiscovery(backend=semantic_backend)
        self.tangent_range = tangent_range
        
        logger.info(
            f"Chaos generator initialized with temperature {temperature}, "
            f"semantic backend: {self.word_discoverer.backend}, "
            f"tangent range: {tangent_range}"
        )
    
    def generate_chaos_seeds(self, prompt: str, num_seeds: int = 3) -> List[str]:
        """
        Generate chaos seed words using dynamic semantic discovery.
        
        Args:
            prompt: The user's original creative request (for semantic analysis)
            num_seeds: Number of words to generate
            
        Returns:
            List of semantically discovered tangential words
        """
        return self.word_discoverer.discover_tangential_words(
            prompt=prompt,
            num_words=num_seeds,
            tangent_range=self.tangent_range
        )
    
    def generate_chaos_input(
        self,
        original_prompt: str,
        num_seeds: int = 3
    ) -> ChaosInput:
        """
        Generate complete chaos input with researched tangential concepts.
        
        Args:
            original_prompt: The user's original creative request
            num_seeds: Number of tangential concepts to explore
            
        Returns:
            ChaosInput with researched tangential concepts
        """
        logger.info("Generating chaos input for divergent exploration")
        
        # Generate semantically selected seed words
        seeds = self.generate_chaos_seeds(original_prompt, num_seeds)
        logger.info(f"Generated chaos seeds: {seeds}")
        
        # Create chaos input
        chaos_input = ChaosInput(
            original_prompt=original_prompt,
            random_seeds=seeds
        )
        
        # Research each seed via LLM + web search
        for seed in seeds:
            try:
                concept = self._research_tangential_concept(seed, original_prompt)
                chaos_input.tangential_concepts.append(concept)
            except Exception as e:
                logger.error(f"Error researching seed '{seed}': {e}")
        
        logger.info(f"Generated {len(chaos_input.tangential_concepts)} tangential concepts")
        return chaos_input
    
    def _research_tangential_concept(
        self,
        seed_word: str,
        original_prompt: str
    ) -> TangentialConcept:
        """
        Research a single tangential concept using LLM and web search.
        
        Args:
            seed_word: The random seed word to research
            original_prompt: The original user prompt for context
            
        Returns:
            TangentialConcept with researched information
        """
        prompt = f"""You are a divergent thinking specialist exploring tangential connections.

Original creative request: {original_prompt}

Random seed word for exploration: "{seed_word}"

YOUR TASK:
1. Think of how "{seed_word}" could inspire creative directions for the original request
2. Optionally use search_web tool ONCE for a quick fact check (not required)
3. Provide a brief context (1 sentence) about what "{seed_word}" represents
4. Explain briefly (1 sentence) how this could inspire creative thinking
5. Keep your ENTIRE response under 100 words

** BE FAST - Use web search sparingly, prefer your knowledge. **

Format your response as:
CONTEXT: [1 sentence about what {seed_word} is]
CONNECTION: [1 sentence about how it inspires the original request]
"""
        
        result = self.agent(prompt)
        content_block = result.message['content'][0]
        response_text = content_block.get('text', '') if isinstance(content_block, dict) else str(content_block)
        
        # Parse response
        context = ""
        relevance = ""
        
        if "CONTEXT:" in response_text and "CONNECTION:" in response_text:
            parts = response_text.split("CONNECTION:")
            context = parts[0].replace("CONTEXT:", "").strip()
            relevance = parts[1].strip()
        else:
            # Fallback: use entire response
            context = response_text[:200]
            relevance = f"Potential tangential inspiration for {original_prompt}"
        
        return TangentialConcept(
            term=seed_word,
            context=context,
            relevance_note=relevance
        )

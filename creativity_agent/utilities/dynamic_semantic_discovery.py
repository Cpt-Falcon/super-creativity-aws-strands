"""
Dynamic semantic word discovery for chaos generation.
Uses embeddings to find semantically related but tangential words.
Supports multiple backends: sentence-transformers, gensim, WordNet.
"""

from typing import List, Set, Optional, Tuple, Any
import random
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DynamicSemanticWordDiscovery:
    """
    Discovers tangential words using semantic similarity from embeddings.
    Finds words that are related but not too similar (tangential sweet spot).
    Dynamically generates candidates based on the user's prompt.
    """
    
    def __init__(
        self,
        backend: str = "auto",
        model_name: Optional[str] = None,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize semantic word discovery.
        
        Args:
            backend: "sentence-transformers", "gensim", "wordnet", or "auto"
            model_name: Specific model to use (backend-dependent)
            cache_dir: Directory for caching embeddings
        """
        self.backend = backend
        self.cache_dir = cache_dir or Path.home() / ".cache" / "super-creativity"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to initialize backend
        self.model: Optional[Any] = None
        self.vocab_cache: Optional[Set[str]] = None  # Backend-specific vocabulary
        
        if backend == "auto":
            self._auto_detect_backend()
        else:
            self._initialize_backend(backend, model_name)
        
        logger.info(f"Semantic word discovery initialized with backend: {self.backend}")
    
    def _auto_detect_backend(self):
        """Auto-detect best available backend."""
        # # Try WordNet first (fastest, most reliable)
        # if self._try_initialize_wordnet():
        #     return
        
        # Try gensim second (good quality, but may be slow/large)
        if self._try_initialize_gensim():
            return
        
        # Try sentence-transformers last (best quality but heaviest)
        if self._try_initialize_sentence_transformers():
            return
        
        # Fallback to simple mode
        logger.warning("No semantic backend available, using simple mode")
        self.backend = "simple"
    
    def _try_initialize_sentence_transformers(self, model_name: Optional[str] = None) -> bool:
        """Try to initialize sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            
            model_name = model_name or "all-MiniLM-L6-v2"  # Fast, good quality
            logger.info(f"Loading sentence-transformers model: {model_name}")
            
            self.model = SentenceTransformer(model_name)
            self.backend = "sentence-transformers"
            
            return True
        except ImportError:
            logger.debug("sentence_transformers not available")
            return False
        except Exception as e:
            logger.debug(f"Failed to initialize sentence-transformers: {e}")
            return False
    
    def _try_initialize_gensim(self) -> bool:
        """Try to initialize gensim with word vectors."""
        try:
            import gensim.downloader as api
            
            # Try smaller models first for speed
            models_to_try = [
                "glove-wiki-gigaword-50",  # 50d, smaller
                "word2vec-google-news-300",  # Larger but common
                "glove-twitter-25"  # Very small, fast
            ]
            
            for model_name in models_to_try:
                try:
                    logger.info(f"Trying gensim model: {model_name}")
                    model = api.load(model_name)
                    self.model = model
                    self.backend = "gensim"
                    
                    # Cache vocabulary for efficient lookup
                    if hasattr(model, 'index_to_key'):
                        self.vocab_cache = set(model.index_to_key)
                    else:
                        self.vocab_cache = set(model.vocab.keys()) if hasattr(model, 'vocab') else set()
                    
                    logger.info(f"Successfully loaded gensim model: {model_name}")
                    return True
                    
                except Exception as e:
                    logger.debug(f"Failed to load {model_name}: {e}")
                    continue
            
            return False
            
        except ImportError:
            logger.debug("gensim not available")
            return False
        except Exception as e:
            logger.debug(f"Failed to initialize gensim: {e}")
            return False

    
    def _initialize_backend(self, backend: str, model_name: Optional[str] = None):
        """Initialize specific backend."""
        if backend == "sentence-transformers":
            if not self._try_initialize_sentence_transformers(model_name):
                raise RuntimeError("Failed to initialize sentence-transformers")
        elif backend == "gensim":
            if not self._try_initialize_gensim():
                raise RuntimeError("Failed to initialize gensim")
        elif backend == "simple":
            self.backend = "simple"
        else:
            raise ValueError(f"Unknown backend: {backend}")
    
    def discover_tangential_words(
        self,
        prompt: str,
        num_words: int = 3,
        tangent_range: Tuple[float, float] = (0.3, 0.7)
    ) -> List[str]:
        """
        Discover tangential words based on prompt semantics.
        Uses WordNet by default for chaos generation, falling back to embeddings or simple extraction if needed.
        Ensures output is tangential, not just key terms.
        """
        # Always prefer WordNet for chaos/tangential generation
        try:
            words = self._discover_with_wordnet(prompt, num_words)
            # If fallback returns only key terms, try embeddings or gensim if available
            if set(words) == set(self._extract_key_terms(prompt)):
                if self.backend == "sentence-transformers" and self.model:
                    emb_words = self._discover_with_sentence_transformers(prompt, num_words, tangent_range)
                    if set(emb_words) != set(self._extract_key_terms(prompt)):
                        return emb_words
                elif self.backend == "gensim" and self.model:
                    gen_words = self._discover_with_gensim(prompt, num_words, tangent_range)
                    if set(gen_words) != set(self._extract_key_terms(prompt)):
                        return gen_words
            return words
        except Exception as e:
            logger.warning(f"WordNet chaos generation failed: {e}, falling back to embeddings/simple.")
            if self.backend == "sentence-transformers" and self.model:
                return self._discover_with_sentence_transformers(prompt, num_words, tangent_range)
            elif self.backend == "gensim" and self.model:
                return self._discover_with_gensim(prompt, num_words, tangent_range)
            else:
                # Fallback: always return nontrivial terms
                key_terms = self._extract_key_terms(prompt)
                # Add some abstract concepts if not enough
                abstract_concepts = [
                    "emergence", "complexity", "adaptation", "resonance", "harmony",
                    "pattern", "structure", "dynamic", "process", "transformation",
                    "evolution", "interaction", "network", "system", "flow",
                    "energy", "information", "connection", "diversity", "innovation"
                ]
                result = key_terms[:max(1, num_words//2)]
                needed = num_words - len(result)
                if needed > 0:
                    result.extend(random.sample(abstract_concepts, min(needed, len(abstract_concepts))))
                logger.info(f"Fallback chaos seeds: {result}")
                return result
    
    def _discover_with_sentence_transformers(
        self,
        prompt: str,
        num_words: int,
        tangent_range: Tuple[float, float]
    ) -> List[str]:
        """
        Discover words using sentence-transformers by finding words
        in the embedding space that are tangential to the prompt.
        """
        if self.model is None:
            logger.warning("Model not initialized, falling back to simple discovery")
            return self._discover_simple(prompt, num_words)
        
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Get prompt embedding
        prompt_embedding = self.model.encode([prompt])[0]
        
        # Extract key terms from prompt to explore
        key_terms = self._extract_key_terms(prompt)
        
        # Generate candidate words through semantic exploration
        candidates = set()
        
        # For each key term, find semantically related words
        for term in key_terms:
            term_embedding = self.model.encode([term])[0]
            
            # Generate semantic variations by exploring embedding space
            # Use common word associations and conceptual expansions
            related_concepts = self._generate_semantic_candidates(term)
            
            for concept in related_concepts:
                concept_embedding = self.model.encode([concept])[0]
                
                # Check if tangential to prompt
                similarity = cosine_similarity(
                    prompt_embedding.reshape(1, -1),
                    concept_embedding.reshape(1, -1)
                )[0][0]
                
                min_sim, max_sim = tangent_range
                if min_sim <= similarity <= max_sim:
                    candidates.add(concept)
        
        # If not enough, relax and add more
        if len(candidates) < num_words:
            logger.info(f"Expanding search with relaxed tangent range")
            for term in key_terms:
                related = self._generate_semantic_candidates(term, broader=True)
                for concept in related:
                    concept_embedding = self.model.encode([concept])[0]
                    similarity = cosine_similarity(
                        prompt_embedding.reshape(1, -1),
                        concept_embedding.reshape(1, -1)
                    )[0][0]
                    
                    if 0.2 <= similarity <= 0.8:
                        candidates.add(concept)
        
        # Sample from candidates
        result = random.sample(list(candidates), min(num_words, len(candidates)))
        
        # Fallback if still not enough
        if len(result) < num_words:
            result.extend(key_terms[:num_words - len(result)])
        
        logger.info(f"Discovered tangential words: {result}")
        return result
    
    def _discover_with_gensim(
        self,
        prompt: str,
        num_words: int,
        tangent_range: Tuple[float, float]
    ) -> List[str]:
        """Discover words using gensim word vectors from prompt."""
        if self.model is None or self.vocab_cache is None:
            logger.warning("Gensim model not initialized, falling back to simple discovery")
            return self._discover_simple(prompt, num_words)
        
        # Extract key terms from prompt
        key_terms = self._extract_key_terms(prompt)
        
        tangential_words = set()
        min_sim, max_sim = tangent_range
        
        for term in key_terms:
            if term in self.vocab_cache:
                # Find words in tangential similarity range
                try:
                    similar = self.model.most_similar(term, topn=30)
                    
                    for word, similarity in similar:
                        if min_sim <= similarity <= max_sim:
                            tangential_words.add(word)
                    
                    if len(tangential_words) >= num_words * 2:
                        break
                except Exception as e:
                    logger.debug(f"Error finding similar words for '{term}': {e}")
        
        # If not enough, try broader search
        if len(tangential_words) < num_words:
            logger.info("Expanding search with relaxed constraints")
            for term in key_terms:
                if term in self.vocab_cache:
                    try:
                        similar = self.model.most_similar(term, topn=50)
                        tangential_words.update([w for w, s in similar if 0.2 <= s <= 0.8])
                    except Exception:
                        pass
        
        result = random.sample(list(tangential_words), min(num_words, len(tangential_words)))
        
        # Fallback to key terms if needed
        if len(result) < num_words:
            result.extend(key_terms[:num_words - len(result)])
        
        logger.info(f"Discovered tangential words: {result}")
        return result
    
    def _words_similar(self, word1: str, word2: str) -> bool:
        """Check if two words are too similar (exact match or simple variations)."""
        w1 = word1.lower().strip()
        w2 = word2.lower().strip()
        
        if w1 == w2:
            return True
        
        # Check if one is contained in the other
        if w1 in w2 or w2 in w1:
            return True
        
        # Check for plural variations
        if w1 + 's' == w2 or w2 + 's' == w1:
            return True
        
        return False
    
    def _discover_simple(self, prompt: str, num_words: int) -> List[str]:
        """Simple fallback: extract key terms from prompt."""
        key_terms = self._extract_key_terms(prompt)
        result = key_terms[:num_words]
        
        logger.info(f"Using simple extraction: {result}")
        return result
    
    def _extract_key_terms(self, prompt: str) -> List[str]:
        """Extract key terms from prompt (nouns, significant words)."""
        # Simple extraction: words longer than 3 chars, lowercase
        words = [
            word.lower().strip('.,!?;:\'\"()[]{}') 
            for word in prompt.split() 
            if len(word) > 3
        ]
        
        # Comprehensive stop words list (conjunctions, pronouns, prepositions, auxiliaries, etc.)
        stop_words = {
            # Pronouns
            'i', 'me', 'my', 'mine', 'myself',
            'you', 'your', 'yours', 'yourself', 'yourselves',
            'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself',
            'it', 'its', 'itself',
            'we', 'us', 'our', 'ours', 'ourselves',
            'they', 'them', 'their', 'theirs', 'themselves',
            'one', 'ones', 'oneself',
            
            # Determiners & Articles
            'the', 'a', 'an', 'this', 'that', 'these', 'those',
            'some', 'any', 'all', 'each', 'every', 'both', 'few', 'many', 'much',
            'another', 'other', 'others', 'such', 'certain',
            
            # Conjunctions
            'and', 'but', 'or', 'nor', 'yet', 'so', 'for',
            'because', 'since', 'unless', 'although', 'though', 'while', 'whereas',
            'if', 'whether', 'either', 'neither',
            
            # Prepositions
            'in', 'on', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
            'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'to', 'from', 'up', 'down', 'of', 'off', 'over', 'under', 'again',
            'across', 'along', 'around', 'behind', 'beneath', 'beside', 'besides',
            'beyond', 'inside', 'outside', 'throughout', 'toward', 'towards',
            'upon', 'within', 'without',
            
            # Auxiliary/Modal Verbs
            'am', 'is', 'are', 'was', 'were', 'been', 'being',
            'have', 'has', 'had', 'having',
            'do', 'does', 'did', 'doing', 'done',
            'will', 'would', 'shall', 'should', 'may', 'might', 'must',
            'can', 'could', 'ought',
            
            # Common Verbs (non-content)
            'be', 'get', 'make', 'go', 'come', 'take', 'give', 'use',
            'work', 'works', 'worked', 'working',
            
            # Question Words
            'what', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why', 'how',
            
            # Vague/Generic Terms
            'thing', 'things', 'something', 'anything', 'everything', 'nothing',
            'someone', 'anyone', 'everyone', 'nobody',
            'somewhere', 'anywhere', 'everywhere', 'nowhere',
            'somehow', 'anyhow',
            
            # Other Common Words
            'not', 'no', 'yes', 'just', 'also', 'only', 'very', 'too',
            'then', 'than', 'now', 'here', 'there', 'more', 'most', 'less', 'least',
            'even', 'still', 'well', 'back', 'way', 'ways', 'right', 'left', 'same',
            'really', 'quite', 'rather', 'pretty', 'enough', 'little', 'bit',
            
            # Polite/Filler Words
            'please', 'thanks', 'thank', 'sorry', 'excuse', 'pardon',
            
            # Common Contractions (expanded)
            'dont', 'doesnt', 'didnt', 'wont', 'wouldnt', 'cant', 'couldnt',
            'isnt', 'arent', 'wasnt', 'werent', 'hasnt', 'havent', 'hadnt',
            'shouldnt', 'mustnt', 'mightnt', 'neednt',
            
            # Request/Action Verbs
            'want', 'need', 'like', 'know', 'think', 'see', 'look', 'feel',
            'help', 'try', 'find', 'tell', 'ask', 'seem', 'become',
            'show', 'allow', 'keep', 'let', 'mean', 'put', 'set', 'turn',
            'follow', 'provide', 'include', 'continue', 'create',
            
            # Time/Frequency
            'always', 'never', 'sometimes', 'often', 'usually', 'rarely',
            'already', 'soon', 'yet', 'today', 'tomorrow', 'yesterday',
            
            # Degree/Extent
            'much', 'many', 'more', 'most', 'less', 'least', 'few', 'fewer', 'fewest',
            'several', 'various', 'different', 'same',
        }
        
        key_terms = [w for w in words if w not in stop_words]
        
        return key_terms
    
    def _generate_semantic_candidates(self, term: str, broader: bool = False) -> List[str]:
        """
        Generate semantically related candidate words for a term.
        Uses dynamic dictionary lookup (WordNet) instead of hardcoded expansions.
        """
        candidates = []
        
        # Try WordNet first for dynamic semantic relationships
        try:

            synsets = wn.synsets(term)
            
            for synset in synsets[:3]:  # Top 3 senses
                # Get synonyms
                for lemma in synset.lemmas()[:3]:
                    if lemma.name() != term:
                        candidates.append(lemma.name().replace('_', ' '))
                
                # Get hypernyms (broader concepts)
                for hypernym in synset.hypernyms()[:2]:
                    for lemma in hypernym.lemmas()[:2]:
                        candidates.append(lemma.name().replace('_', ' '))
                
                # Get hyponyms (more specific concepts)
                if broader:
                    for hyponym in synset.hyponyms()[:2]:
                        for lemma in hyponym.lemmas()[:2]:
                            candidates.append(lemma.name().replace('_', ' '))
                
                # Get related forms (derivationally related)
                for lemma in synset.lemmas()[:2]:
                    for related in lemma.derivationally_related_forms()[:2]:
                        candidates.append(related.name().replace('_', ' '))
                
                # Get part meronyms (parts)
                for meronym in synset.part_meronyms()[:2]:
                    for lemma in meronym.lemmas()[:2]:
                        candidates.append(lemma.name().replace('_', ' '))
        
        except (ImportError, LookupError) as e:
            logger.debug(f"WordNet not available for semantic expansion: {e}")
            # Fall back to simple related concepts
            pass
        
        # Remove duplicates and filter
        unique_candidates = list(dict.fromkeys(candidates))
        
        # Filter out very long compound words
        filtered = [c for c in unique_candidates if len(c) < 20]
        
        return filtered[:15]  # Limit to top 15 candidates

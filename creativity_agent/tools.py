from strands import tool
from ddgs import DDGS
from typing import Literal, Optional
import json
import logging

logger = logging.getLogger(__name__)

# Global web cache instance (set by agent_flow)
_web_cache = None


def set_web_cache(cache):
    """Set the global web cache instance for the current run."""
    global _web_cache
    _web_cache = cache


@tool
def search_web(
    query: str,
    max_results: int = 5,
    backend: Literal["text", "news"] = "text",
) -> str:
    """
    Search the web using DuckDuckGo and return URLs with query-level caching.
    
    This function implements a two-level caching strategy:
    1. Query -> URLs mapping (skips DDGS search if query already searched)
    2. URL -> content mapping (skips web fetch if URL already fetched)
    
    Args:
        query: The search query
        max_results: Maximum number of URLs to return (default: 5, max: 20)
        backend: Search backend ("text" or "news")
        
    Returns:
        JSON array of URLs found for the query
        
    Note:
        This returns URLs only. Use get_urls_content() to fetch actual content.
        Query->URLs mappings are cached to avoid redundant DDGS searches.
        
    Examples:
        - Get URLs: search_web("AI breakthroughs")
        - News URLs: search_web("latest tech news", backend="news")
    """
    try:
        # Limit max_results
        max_results = min(max_results, 20)
        
        # Check if we have URLs cached for this query
        if _web_cache:
            cached_urls = _web_cache.get_urls_for_query(query)
            if cached_urls:
                # Return cached URLs (sorted by hit count, take top max_results)
                urls = [url for url, hits in cached_urls[:max_results]]
                logger.info(f"Query cache HIT for '{query}': {len(urls)} URLs")
                return json.dumps(urls)
        
        # Cache miss - perform DDGS search
        logger.info(f"Query cache MISS for '{query}': performing DDGS search")
        
        with DDGS() as ddgs:
            if backend == "news":
                results = list(ddgs.news(query, max_results=max_results))
            else:
                results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return json.dumps([])
        
        # Extract URLs from results
        urls = []
        for result in results:
            url = result.get('href', result.get('link', ''))
            if url:
                urls.append(url)
        
        # Cache the query -> URLs mapping
        if _web_cache and urls:
            _web_cache.link_query_to_urls(query, urls, f"ddgs-{backend}")
            logger.info(f"Cached query->URLs mapping: '{query}' -> {len(urls)} URLs")
        
        return json.dumps(urls)
        
    except Exception as e:
        logger.error(f"Error during web search: {e}")
        return json.dumps([])


@tool
def get_url_content(url: str, max_chars: Optional[int] = None) -> str:
    """
    Fetch full content from a URL with global URL-based caching.
    
    Args:
        url: The URL to fetch content from
        max_chars: Optional maximum characters to return (for very long pages)
        
    Returns:
        Full text content from the URL
        
    Note:
        This tool uses the global web cache - content is cached by URL across all runs.
        Cached content is returned immediately if available, otherwise content is fetched and cached.
        Use get_urls_content() for fetching multiple URLs at once.
    """
    import urllib.request
    import urllib.error
    from urllib.parse import urlparse
    import re
    
    try:
        # Check cache first
        if _web_cache:
            cached_content = _web_cache.get_url_content(url)
            if cached_content:
                # cached_content is the string directly
                if max_chars and len(cached_content) > max_chars:
                    cached_content = cached_content[:max_chars] + f"\n\n[Content truncated to {max_chars} chars]"
                return cached_content
        
        # Basic URL validation
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return f"Error: Invalid URL format: {url}"
        
        # Fetch with timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; CreativityAgent/1.0)'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')
        
        # Basic HTML stripping (simple approach)
        # In production, consider using BeautifulSoup or html2text
        # Remove script and style tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Cache the content
        if _web_cache:
            _web_cache.cache_url_content(url, content)
        
        # Truncate if requested
        if max_chars and len(content) > max_chars:
            content = content[:max_chars] + f"\n\n[Content truncated to {max_chars} chars]"
        
        return content
        
    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.reason} for URL: {url}"
    except urllib.error.URLError as e:
        return f"URL Error: {e.reason} for URL: {url}"
@tool
def get_urls_content(urls: str, max_chars: Optional[int] = None) -> str:
    """
    Fetch content from multiple URLs with global URL-based caching.
    
    This function implements the second level of caching:
    For each URL, check if content is cached. If not, fetch and cache it.
    
    Args:
        urls: JSON array of URLs to fetch content from, or comma-separated URLs
        max_chars: Optional maximum characters per URL content (for very long pages)
        
    Returns:
        JSON object mapping URLs to their content or error messages
        
    Note:
        This uses the global web cache - content is cached by URL across all runs.
        Cached content is returned immediately if available, otherwise content is fetched and cached.
        
    Examples:
        get_urls_content('["https://example.com", "https://example.org"]')
        get_urls_content("https://example.com, https://example.org")
    """
    try:
        # Parse URLs
        url_list = []
        if urls.strip().startswith('['):
            try:
                url_list = json.loads(urls)
                if not isinstance(url_list, list):
                    return json.dumps({"error": "URLs must be an array of strings"})
            except json.JSONDecodeError:
                return json.dumps({"error": "Invalid JSON format for URLs"})
        else:
            # Split by comma and clean up
            url_list = [u.strip() for u in urls.split(',') if u.strip()]
        
        if len(url_list) == 0:
            return json.dumps({"error": "No URLs provided"})
        
        if len(url_list) > 20:
            return json.dumps({"error": "Maximum 20 URLs per request"})
        
        results = {}
        
        for url in url_list:
            if not isinstance(url, str):
                results[url] = {"error": "URL must be a string"}
                continue
            
            try:
                # Use the existing get_url_content function
                content = get_url_content(url, max_chars)
                
                # Check if it was from cache or freshly fetched
                if "[Retrieved from cache]" in content:
                    results[url] = {
                        "content": content.replace("\n[Retrieved from cache]", ""),
                        "cached": True
                    }
                else:
                    results[url] = {
                        "content": content,
                        "cached": False
                    }
                    
            except Exception as e:
                results[url] = {"error": f"Failed to fetch content: {str(e)}"}
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        logger.error(f"Error in get_urls_content: {e}")
        return json.dumps({"error": f"Error processing URLs: {str(e)}"})
    
@tool   
def bulk_search_web(
    queries: str,
    max_results: int = 5,
    backend: Literal["text", "news"] = "text",
) -> str:
    """
    Perform multiple web searches efficiently in one call.
    Useful when you need to research multiple topics at once.
    
    Args:
        queries: Comma-separated list of search queries OR JSON array. 
                 Examples: 
                 - "quantum computing, AI agents, neural networks"
                 - '["LLM optimization", "attention mechanisms"]'
        max_results: Maximum results per query (default: 5)
        output_format: Format for results ("snippet", "list", or "json")
        backend: Search backend ("text" or "news")
        
    Returns:
        Combined results for all queries with clear separators
        
    Note:
        URLs found in search results are linked to queries for cache analytics.
        Individual URL content will be cached when accessed via get_url_content.
        
    Examples:
        bulk_search_web("LLM optimization, attention mechanisms, transformer architectures", max_results=3)
        bulk_search_web('["quantum computing", "neural networks"]')
    """
    try:
        # Try to parse as JSON first, fall back to comma-separated
        query_list = []
        if queries.strip().startswith('['):
            try:
                query_list = json.loads(queries)
                if not isinstance(query_list, list):
                    return json.dumps({"error": "JSON input must be an array of strings"})
            except json.JSONDecodeError:
                return json.dumps({"error": "Invalid JSON format. Use comma-separated strings or valid JSON array."})
        else:
            # Split by comma and clean up
            query_list = [q.strip() for q in queries.split(',') if q.strip()]
        
        if len(query_list) == 0:
            return json.dumps({"error": "No queries provided"})
        
        if len(query_list) > 10:
            return json.dumps({"error": "Maximum 10 queries per bulk search (to avoid rate limiting)"})
        
        results = {}
        
        for query in query_list:
            if not isinstance(query, str):
                results[query] = {"error": "Query must be a string"}
                continue
            
            # Use the updated search_web function
            urls_json = search_web(query, max_results, backend)
            try:
                urls = json.loads(urls_json)
                results[query] = urls
            except json.JSONDecodeError:
                results[query] = {"error": "Failed to parse search results"}
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        logger.error(f"Error during bulk search: {e}")
        return json.dumps({"error": f"Error during bulk search: {str(e)}"})

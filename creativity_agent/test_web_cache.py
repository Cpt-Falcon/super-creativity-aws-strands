#!/usr/bin/env python3
"""
Quick test to verify web cache is working.
"""

from pathlib import Path
from utilities.global_web_cache import GlobalWebCache
from tools import search_web, set_web_cache

# Create cache
cache_dir = Path(__file__).parent / "outputs" / "test_cache"
cache = GlobalWebCache(cache_dir)
set_web_cache(cache)

# First search - should be MISS and cache it
print("[TEST 1] First search - should MISS and cache")
result1 = search_web("python programming", max_results=3)
print(f"Result length: {len(result1)} chars\n")

# Second search - should be HIT from cache
print("[TEST 2] Same search again - should HIT from cache")
result2 = search_web("python programming", max_results=3)
print(f"Result length: {len(result2)} chars\n")

# Third search - different query - should be MISS
print("[TEST 3] Different search - should MISS and cache")
result3 = search_web("machine learning", max_results=3)
print(f"Result length: {len(result3)} chars\n")

# Print cache stats
print("=" * 80)
print("CACHE STATISTICS")
print("=" * 80)
stats = cache.get_cache_stats()
print(f"Search Cache: {stats['search_cache']['total_entries']} entries, {stats['search_cache']['total_hits']} hits")
print(f"Content Cache: {stats['content_cache']['total_entries']} entries, {stats['content_cache']['total_hits']} hits")

print("\nTop Queries:")
for q in stats['search_cache']['top_queries']:
    print(f"  - {q['query']}: {q['hits']} hits")

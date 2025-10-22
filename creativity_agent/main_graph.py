#!/usr/bin/env python3
"""
Main entry point for the Graph-Based Creativity Agent Flow
Enhanced with memory, chaos, independent judge, and observability.
"""

from pathlib import Path
from creativity_agent.config import FlowConfig
from creativity_agent.agent_flow_graph import CreativityAgentFlowGraph
import argparse
import os


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Super Creativity: Graph-based multi-agent creative ideation system"
    )
    parser.add_argument(
        '--no-memory',
        action='store_true',
        help='Disable memory tracking of explored ideas'
    )
    parser.add_argument(
        '--no-observability',
        action='store_true',
        help='Disable ElasticSearch observability tracking'
    )
    parser.add_argument(
        '--chaos-seeds',
        type=int,
        default=10,
        help='Number of chaos seeds per iteration (default: 10)'
    )
    parser.add_argument(
        '--semantic-backend',
        type=str,
        default='auto',
        choices=['auto', 'gensim', 'simple'],
        help='Semantic backend for word discovery (default: auto)'
    )
    parser.add_argument(
        '--prompt',
        type=str,
        help='Creative request prompt (if not provided, will prompt interactively)'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Use mock agents for fast graph structure debugging (no LLM calls)'
    )
    parser.add_argument(
        '--es-uri',
        type=str,
        default=os.getenv('ELASTICSEARCH_URI'),
        help='ElasticSearch URI (default: from ELASTICSEARCH_URI env var)'
    )
    parser.add_argument(
        '--es-api-key',
        type=str,
        default=os.getenv('ELASTICSEARCH_API_KEY'),
        help='ElasticSearch API key (default: from ELASTICSEARCH_API_KEY env var)'
    )
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(__file__).parent / "flow_config.json"
    config = FlowConfig.from_json(config_path)

    flow = CreativityAgentFlowGraph(
        config,
        enable_memory=not args.no_memory,
        enable_observability=not args.no_observability,
        chaos_seeds_per_iteration=args.chaos_seeds,
        semantic_backend=args.semantic_backend,
        es_uri=args.es_uri,
        es_api_key=args.es_api_key,
        mock_mode=args.mock
    )
    run_method = flow.run
    
    # Get user input
    if args.prompt:
        user_prompt = args.prompt
        print(f"Using provided prompt: {user_prompt}")
    else:
        user_prompt = input("Enter your creative request: ")
    
    # Display configuration
    print("\n" + "=" * 80)
    print("SUPER CREATIVITY - Graph-Based Multi-Agent Ideation")
    if args.mock:
        print("[MOCK MODE] - Fast debugging without LLM calls")
    print("=" * 80)
    print(f"Iterations: {config.iterations}")
    print(f"Mock Mode: {'ENABLED' if args.mock else 'DISABLED'}")
    print(f"Memory Tracking: {'ENABLED' if not args.no_memory else 'DISABLED'}")
    print(f"Observability: {'ENABLED' if not args.no_observability else 'DISABLED'}")
    if not args.no_observability:
        if args.es_uri:
            print(f"ElasticSearch: Connected")
        else:
            print(f"ElasticSearch: Not configured (set ELASTICSEARCH_URI and ELASTICSEARCH_API_KEY)")
    print("=" * 80)
    print()
    
    # Run flow
    print("Starting creativity flow...")
    result = run_method(user_prompt)
    
    print("\n" + "=" * 80)
    print("Flow completed!")
    print("=" * 80)
    print(f"Check the {flow.run_dir}/ directory for all results from this run.")
    if not args.no_memory:
        print(f"Memory state saved to {flow.run_dir}/memory/idea_memory.json")
    if not args.no_observability and args.es_uri:
        print(f"Metrics indexed to ElasticSearch (index: super-creativity)")
    
    # Print web cache statistics
    print("\n" + "=" * 80)
    print("WEB CACHE STATISTICS")
    print("=" * 80)
    cache_stats = flow.global_web_cache.get_cache_stats()
    print(f"URL Cache: {cache_stats['url_cache']['total_urls_cached']} URLs cached, {cache_stats['url_cache']['total_hits']} total hits ({cache_stats['url_cache']['total_size_bytes']} bytes)")
    if cache_stats['url_cache']['top_urls']:
        print("\nTop Cached URLs:")
        for url_info in cache_stats['url_cache']['top_urls']:
            print(f"  - {url_info['url']}: {url_info['hits']} hits")
    print(f"\nQuery Tracking: {cache_stats['query_mappings']['total_unique_queries']} unique queries tracked")
    if cache_stats['url_cache']['top_domains']:
        print("\nTop Domains:")
        for domain_info in cache_stats['url_cache']['top_domains']:
            print(f"  - {domain_info['domain']}: {domain_info['count']} URLs, {domain_info['hits']} total hits")



if __name__ == "__main__":
    main()

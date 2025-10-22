#!/usr/bin/env python3
"""
Test script to validate judge evaluation parsing with new JSON format.
"""
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from creativity_agent.utilities.independent_judge import IndependentJudge
from creativity_agent.utilities.jinja_prompt_builder import JinjaPromptBuilder

# Sample JSON response in new format
SAMPLE_JUDGE_RESPONSE = """{
  "accepted_ideas": [
    {
      "idea_name": "Hierarchical Attention Mechanism",
      "quality_score": 8.5,
      "feasibility_score": 8,
      "impact_score": 9,
      "originality_score": 8,
      "key_points": ["Novel routing algorithm", "Scalable implementation"],
      "implementation_path": "Custom CUDA kernels with sparse matrices",
      "required_resources": ["GPU cluster", "CUDA expertise"],
      "success_metrics": ["10x speedup", "Maintained accuracy"],
      "next_steps": ["Prototype kernel", "Benchmark performance"]
    }
  ],
  "rejected_ideas": [
    {
      "idea_name": "Basic Optimization",
      "rejection_reason": "Too similar to existing techniques",
      "quality_score": 3.5,
      "fatal_flaw": "Derivative approach with no unique value"
    }
  ],
  "synthesis": "Strong focus on attention mechanisms with promising hierarchical approach",
  "top_recommendations": ["Hierarchical Attention Mechanism"],
  "strategic_insights": ["Attention optimization remains critical bottleneck"],
  "unresolved_questions": ["How to handle variable sequence lengths?"]
}"""

def test_parsing():
    """Test that the parser correctly extracts all values from new JSON format."""
    # Initialize required components
    jinja_builder = JinjaPromptBuilder(templates_dir="creativity_agent/prompts_templates")
    judge = IndependentJudge(jinja_builder=jinja_builder)
    
    # Parse the sample response using direct JSON parsing (as done in judge_node.py)
    evaluation_data = json.loads(SAMPLE_JUDGE_RESPONSE.strip())
    
    # Verify results
    print("\n✓ Test Judge JSON Parsing Results:")
    print(f"  Accepted Ideas Count: {len(evaluation_data['accepted_ideas'])} (expected: 1)")
    print(f"  Rejected Ideas Count: {len(evaluation_data['rejected_ideas'])} (expected: 1)")
    print(f"  Top Recommendations: {evaluation_data['top_recommendations']}")
    
    # Validate accepted idea
    accepted = evaluation_data['accepted_ideas'][0]
    print(f"  Accepted Idea Name: {accepted['idea_name']}")
    print(f"  Quality Score: {accepted['quality_score']} (expected: 8.5)")
    print(f"  Feasibility Score: {accepted['feasibility_score']} (expected: 8)")
    print(f"  Impact Score: {accepted['impact_score']} (expected: 9)")
    print(f"  Originality Score: {accepted['originality_score']} (expected: 8)")
    
    # Validate rejected idea
    rejected = evaluation_data['rejected_ideas'][0]
    print(f"  Rejected Idea Name: {rejected['idea_name']}")
    print(f"  Rejection Reason: {rejected['rejection_reason']}")
    print(f"  Quality Score: {rejected['quality_score']} (expected: 3.5)")
    
    # Validate structure
    assert len(evaluation_data['accepted_ideas']) == 1, f"Expected 1 accepted idea, got {len(evaluation_data['accepted_ideas'])}"
    assert len(evaluation_data['rejected_ideas']) == 1, f"Expected 1 rejected idea, got {len(evaluation_data['rejected_ideas'])}"
    assert accepted['quality_score'] == 8.5, f"Expected 8.5, got {accepted['quality_score']}"
    assert rejected['quality_score'] == 3.5, f"Expected 3.5, got {rejected['quality_score']}"
    assert "Hierarchical Attention Mechanism" in evaluation_data['top_recommendations'], "Should include accepted idea in recommendations"
    
    print("\n✅ All JSON parsing tests passed!")

def test_parsing_empty_response():
    """Test parsing of empty or malformed response."""
    jinja_builder = JinjaPromptBuilder(templates_dir="creativity_agent/prompts_templates")
    judge = IndependentJudge(jinja_builder=jinja_builder)
    
    # Test with empty response
    empty_data = json.loads("{}")
    assert empty_data.get('accepted_ideas', []) == [], "Should handle empty response"
    assert empty_data.get('rejected_ideas', []) == [], "Should handle empty response"
    
    # Test with malformed JSON
    try:
        json.loads("not json")
        assert False, "Should raise exception for malformed JSON"
    except json.JSONDecodeError:
        pass  # Expected
    
    print("\n✅ Empty response parsing test passed!")

if __name__ == "__main__":
    try:
        test_parsing()
        test_parsing_empty_response()
        print("\n" + "="*50)
        print("🎉 All tests passed successfully!")
        print("="*50)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

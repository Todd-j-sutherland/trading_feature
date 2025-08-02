#!/usr/bin/env python3
"""
Debug script to check quality assessment output structure
"""

import sys
import os
sys.path.append('/Users/toddsutherland/Repos/trading_feature')

from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
import json

def debug_quality_output():
    """Debug the quality assessment output structure"""
    
    print("🔍 Debugging Quality Assessment Output Structure")
    print("=" * 60)
    
    analyzer = NewsSentimentAnalyzer()
    
    print("Testing with CBA.AX...")
    result = analyzer.analyze_bank_sentiment('CBA.AX')
    
    print(f"\nTop-level keys in result:")
    for key in result.keys():
        print(f"  - {key}")
    
    print(f"\nsentiment_components structure:")
    sentiment_components = result.get('sentiment_components', {})
    for key in sentiment_components.keys():
        print(f"  - {key}")
    
    print(f"\nChecking for quality_assessments at top level...")
    if 'quality_assessments' in result:
        print("✅ Found quality_assessments at top level")
        quality_assessments = result['quality_assessments']
        print(f"Quality assessments keys: {list(quality_assessments.keys())}")
        
        # Show first assessment as example
        if quality_assessments:
            first_component = next(iter(quality_assessments))
            first_assessment = quality_assessments[first_component]
            print(f"\nExample assessment ({first_component}):")
            for key, value in first_assessment.items():
                print(f"  {key}: {value}")
    else:
        print("❌ quality_assessments not found at top level")
    
    print(f"\nChecking for weight_changes at top level...")
    if 'weight_changes' in result:
        print("✅ Found weight_changes at top level")
        weight_changes = result['weight_changes']
        print(f"Weight changes: {weight_changes}")
    else:
        print("❌ weight_changes not found at top level")
        
    print(f"\nChecking for dynamic_weights at top level...")
    if 'dynamic_weights' in result:
        print("✅ Found dynamic_weights at top level")
        dynamic_weights = result['dynamic_weights']
        print(f"Dynamic weights: {dynamic_weights}")
    else:
        print("❌ dynamic_weights not found at top level")

if __name__ == "__main__":
    debug_quality_output()

#!/usr/bin/env python3
"""
Test script for the integrated quality-based weighting system
"""

import sys
import os
sys.path.append('/Users/toddsutherland/Repos/trading_feature')

from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
import json
from datetime import datetime

def test_quality_based_integration():
    """Test the quality-based weighting system integration"""
    
    print("🧪 Testing Quality-Based Weighting System Integration")
    print("=" * 60)
    
    # Initialize the analyzer
    try:
        analyzer = NewsSentimentAnalyzer()
        print("✅ NewsSentimentAnalyzer initialized successfully")
        print(f"✅ Quality weighting system initialized: {analyzer.quality_weighting is not None}")
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        return
    
    # Test with CBA (should have good data)
    print(f"\n📊 Testing sentiment analysis for CBA.AX...")
    
    try:
        result = analyzer.analyze_bank_sentiment('CBA.AX')
        
        print(f"\n📈 CBA.AX Sentiment Analysis Results:")
        print(f"Overall Sentiment Score: {result['overall_sentiment']:.3f}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"News Count: {result['news_count']}")
        
        # Check if quality assessments are included
        if 'quality_assessments' in result['sentiment_components']:
            print(f"\n🎯 Quality-Based Weight Analysis:")
            quality_assessments = result['sentiment_components']['quality_assessments']
            weight_changes = result['sentiment_components']['weight_changes']
            
            for component, assessment in quality_assessments.items():
                grade = assessment['grade']
                score = assessment['score']
                change = weight_changes[component]
                print(f"  {component}: Grade {grade} (Quality: {score:.1%}) → Weight change: {change:+.1f}%")
        
        # Show dynamic weights vs base weights
        if 'weights' in result['sentiment_components']:
            print(f"\n⚖️  Dynamic Weights:")
            weights = result['sentiment_components']['weights']
            for component, weight in weights.items():
                print(f"  {component}: {weight:.1%}")
                
        # Show component contributions
        if 'components' in result['sentiment_components']:
            print(f"\n🔍 Component Contributions:")
            components = result['sentiment_components']['components']
            for component, contribution in components.items():
                print(f"  {component}: {contribution:+.4f}")
        
        # Additional analysis info
        print(f"\n📊 Additional Metrics:")
        print(f"Reddit Posts: {result['reddit_sentiment']['posts_analyzed']}")
        print(f"Reddit Sentiment: {result['reddit_sentiment']['average_sentiment']:.3f}")
        
        if 'marketaux_sentiment' in result:
            marketaux_score = result['marketaux_sentiment'].get('sentiment_score', 0)
            print(f"MarketAux Score: {marketaux_score:.3f}")
        
        if 'ml_confidence' in result:
            print(f"ML Confidence: {result['ml_confidence']:.3f}")
            
        print(f"\n✅ Quality-based weighting system working successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during sentiment analysis: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def test_standalone_quality_system():
    """Test the quality system independently"""
    
    print(f"\n🔬 Testing Standalone Quality Assessment System")
    print("=" * 60)
    
    try:
        from app.core.sentiment.news_analyzer import QualityBasedSentimentWeighting
        
        quality_system = QualityBasedSentimentWeighting()
        print("✅ Quality system initialized")
        
        # Mock data for testing
        mock_news = {
            'news_count': 15,
            'average_sentiment': 0.2,
            'method_breakdown': {
                'transformer': {'confidence': 0.85},
                'vader': {'count': 10},
                'textblob': {'count': 5}
            }
        }
        
        mock_reddit = {
            'posts_analyzed': 8,
            'average_sentiment': 0.15
        }
        
        mock_marketaux = {
            'sentiment_score': 0.35
        }
        
        mock_events = {
            'events_detected': ['event1', 'event2']
        }
        
        # Test quality assessment
        result = quality_system.calculate_dynamic_weights(
            mock_news,
            mock_reddit,
            mock_marketaux,
            mock_events,
            transformer_confidence=0.85,
            ml_confidence=0.6
        )
        
        print(f"\n🎯 Quality Assessment Results:")
        for component, assessment in result['quality_assessments'].items():
            grade = assessment['grade']
            score = assessment['score']
            change = result['weight_changes'][component]
            print(f"  {component}: Grade {grade} (Quality: {score:.1%}) → Weight change: {change:+.1f}%")
        
        print(f"\n⚖️  Dynamic vs Base Weights:")
        base_weights = result['base_weights']
        dynamic_weights = result['weights']
        
        for component in base_weights:
            base = base_weights[component]
            dynamic = dynamic_weights[component]
            change = ((dynamic - base) / base * 100)
            print(f"  {component}: {base:.1%} → {dynamic:.1%} ({change:+.1f}%)")
        
        print(f"\n✅ Standalone quality system working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error in standalone quality test: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Quality-Based Weighting System Integration Test")
    print("=" * 70)
    
    # Test standalone quality system first
    standalone_success = test_standalone_quality_system()
    
    if standalone_success:
        # Test full integration
        integration_success = test_quality_based_integration()
        
        if integration_success:
            print(f"\n🎉 All tests passed! Quality-based weighting system successfully integrated!")
        else:
            print(f"\n⚠️  Integration test failed, but standalone system works")
    else:
        print(f"\n❌ Standalone system test failed")
    
    print("=" * 70)

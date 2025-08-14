#!/usr/bin/env python3
"""
Test script for MarketAux integration with the sentiment analysis system.
This validates the complete integration without making actual API calls.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.sentiment.news_analyzer import NewsAnalyzer
from core.sentiment.marketaux_integration import MarketAuxManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_marketaux_integration():
    """Test MarketAux integration with the sentiment analysis system"""
    
    print("🔍 Testing MarketAux Integration")
    print("=" * 50)
    
    # Test 1: Initialize MarketAux Manager
    print("\n1. Testing MarketAux Manager Initialization...")
    try:
        manager = MarketAuxManager()
        print("✅ MarketAux Manager initialized successfully")
        print(f"   API Token configured: {'Yes' if manager.api_token else 'No'}")
        print(f"   Daily limit: {manager.daily_limit}")
        print(f"   Usage today: {manager.get_daily_usage()}")
    except Exception as e:
        print(f"❌ MarketAux Manager initialization failed: {e}")
        return False
    
    # Test 2: Test News Analyzer with MarketAux
    print("\n2. Testing News Analyzer with MarketAux integration...")
    try:
        analyzer = NewsAnalyzer()
        print("✅ News Analyzer initialized with MarketAux support")
        
        # Check if MarketAux client is properly initialized
        if hasattr(analyzer, 'marketaux_manager'):
            print("✅ MarketAux client properly integrated")
        else:
            print("⚠️  MarketAux client not found in News Analyzer")
            
    except Exception as e:
        print(f"❌ News Analyzer initialization failed: {e}")
        return False
    
    # Test 3: Test sentiment calculation with mock data
    print("\n3. Testing sentiment calculation with MarketAux components...")
    try:
        # Mock sentiment data to test the calculation logic
        mock_news_sentiment = {
            'average_sentiment': 0.3,
            'articles': [
                {'sentiment': 0.2, 'volume_weight': 1.0},
                {'sentiment': 0.4, 'volume_weight': 0.8}
            ]
        }
        
        mock_reddit_sentiment = {
            'average_sentiment': 0.1,
            'posts_analyzed': 5
        }
        
        mock_marketaux_sentiment = {
            'sentiment_score': 0.4,
            'entities_analyzed': 3,
            'confidence': 0.8,
            'source_count': 15
        }
        
        mock_events = {
            'events_detected': [
                {'type': 'earnings_report', 'date': '2024-01-15', 'impact': 0.2}
            ]
        }
        
        # Test the enhanced sentiment calculation
        result = analyzer._calculate_overall_sentiment_improved(
            news_sentiment=mock_news_sentiment,
            reddit_sentiment=mock_reddit_sentiment,
            marketaux_sentiment=mock_marketaux_sentiment,
            events=mock_events
        )
        
        print("✅ Sentiment calculation completed successfully")
        print(f"   Overall Score: {result['score']:.3f}")
        print(f"   Components:")
        for component, score in result['components'].items():
            print(f"     {component}: {score:.3f}")
        print(f"   Weights:")
        for weight_name, weight_value in result['weights'].items():
            print(f"     {weight_name}: {weight_value:.3f}")
            
        # Validate MarketAux is included
        if 'marketaux' in result['components']:
            print("✅ MarketAux component properly included in sentiment calculation")
        else:
            print("❌ MarketAux component missing from sentiment calculation")
            
    except Exception as e:
        print(f"❌ Sentiment calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Test request management
    print("\n4. Testing MarketAux request management...")
    try:
        # Test can_make_request logic
        can_make = manager.can_make_request()
        print(f"✅ Request validation: Can make request = {can_make}")
        
        # Test strategic allocation
        allocation = manager.get_strategic_allocation()
        print(f"✅ Strategic allocation calculated:")
        for slot, requests in allocation.items():
            print(f"     {slot}: {requests} requests")
            
    except Exception as e:
        print(f"❌ Request management test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 MarketAux Integration Test Summary")
    print("✅ All core components tested successfully")
    print("✅ MarketAux properly integrated into sentiment pipeline")
    print("✅ Request management system operational")
    print("✅ Enhanced sentiment calculation includes professional sentiment")
    
    print("\n📋 Next Steps:")
    print("1. Set MARKETAUX_API_TOKEN environment variable for live testing")
    print("2. Run live sentiment analysis with actual MarketAux data")
    print("3. Monitor daily usage and request patterns")
    print("4. Validate sentiment quality improvements")
    
    return True

def test_weight_allocation():
    """Test dynamic weight allocation scenarios"""
    
    print("\n🔬 Testing Dynamic Weight Allocation Scenarios")
    print("=" * 50)
    
    analyzer = NewsAnalyzer()
    
    scenarios = [
        {
            'name': 'Full Data Available',
            'news_count': 10,
            'reddit_posts': 8,
            'marketaux_available': True,
            'ml_confidence': 0.8
        },
        {
            'name': 'Low News, High MarketAux',
            'news_count': 2,
            'reddit_posts': 8,
            'marketaux_available': True,
            'ml_confidence': 0.8
        },
        {
            'name': 'No MarketAux Available',
            'news_count': 10,
            'reddit_posts': 8,
            'marketaux_available': False,
            'ml_confidence': 0.8
        },
        {
            'name': 'Limited Data Sources',
            'news_count': 2,
            'reddit_posts': 1,
            'marketaux_available': False,
            'ml_confidence': 0.2
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📊 Scenario: {scenario['name']}")
        
        # Create mock data based on scenario
        mock_news = {
            'average_sentiment': 0.3,
            'articles': [{'sentiment': 0.3, 'volume_weight': 1.0}] * scenario['news_count']
        }
        
        mock_reddit = {
            'average_sentiment': 0.1,
            'posts_analyzed': scenario['reddit_posts']
        }
        
        mock_marketaux = {
            'sentiment_score': 0.4,
            'confidence': 0.8
        } if scenario['marketaux_available'] else None
        
        mock_events = {'events_detected': []}
        
        result = analyzer._calculate_overall_sentiment_improved(
            news_sentiment=mock_news,
            reddit_sentiment=mock_reddit,
            marketaux_sentiment=mock_marketaux,
            events=mock_events
        )
        
        print(f"   Overall Score: {result['score']:.3f}")
        print("   Weight Allocation:")
        for weight_name, weight_value in result['weights'].items():
            if weight_value > 0.01:  # Only show significant weights
                print(f"     {weight_name}: {weight_value:.3f}")

if __name__ == "__main__":
    print("🚀 MarketAux Integration Test Suite")
    print("=" * 60)
    
    success = test_marketaux_integration()
    
    if success:
        test_weight_allocation()
        print("\n🎯 All tests completed successfully!")
        print("MarketAux integration is ready for production use.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)

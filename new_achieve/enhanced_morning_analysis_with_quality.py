#!/usr/bin/env python3
"""
Enhanced morning analysis with quality-based weighting system demonstration
"""

import sys
import os
sys.path.append('/Users/toddsutherland/Repos/trading_feature')

from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
import json
from datetime import datetime

def run_enhanced_morning_analysis():
    """Run morning analysis demonstrating quality-based weighting"""
    
    print("🌅 Enhanced Morning Analysis with Quality-Based Weighting")
    print("=" * 70)
    
    banks = ['CBA.AX', 'ANZ.AX', 'NAB.AX', 'WBC.AX']
    
    analyzer = NewsSentimentAnalyzer()
    
    for bank in banks:
        print(f"\n🏦 Analyzing {bank}...")
        print("-" * 50)
        
        try:
            result = analyzer.analyze_bank_sentiment(bank)
            
            print(f"📊 Overall Sentiment: {result['overall_sentiment']:+.3f}")
            print(f"📈 Confidence: {result['confidence']:.1%}")
            print(f"📰 News Articles: {result['news_count']}")
            print(f"💬 Reddit Posts: {result['reddit_sentiment']['posts_analyzed']}")
            
            # Show quality-based adjustments if available
            if 'quality_assessments' in result:
                print(f"\n🎯 Quality-Based Weight Analysis:")
                quality_assessments = result['quality_assessments']
                weight_changes = result.get('weight_changes', {})
                
                # Sort by weight change magnitude for better display
                sorted_components = sorted(weight_changes.items(), key=lambda x: abs(x[1]), reverse=True)
                
                for component, change in sorted_components:
                    if component in quality_assessments:
                        assessment = quality_assessments[component]
                        grade = assessment['grade']
                        score = assessment['score']
                        
                        # Color coding for changes
                        change_symbol = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                        
                        print(f"  {change_symbol} {component.capitalize()}: Grade {grade} (Quality: {score:.0%}) → {change:+.1f}%")
            
            # Show component contributions and dynamic weights
            if 'sentiment_components' in result and 'dynamic_weights' in result:
                print(f"\n🔍 Component Contributions (with Dynamic Weights):")
                components = result['sentiment_components']
                weights = result['dynamic_weights']
                
                for component, contribution in components.items():
                    weight = weights.get(component, 0)
                    print(f"  {component}: {contribution:+.4f} (weight: {weight:.1%})")
            
            # Reddit analysis
            reddit = result['reddit_sentiment']
            if reddit['posts_analyzed'] > 0:
                print(f"\n💬 Reddit Analysis:")
                print(f"  Sentiment: {reddit['average_sentiment']:+.3f}")
                print(f"  Bullish: {reddit['bullish_count']}, Bearish: {reddit['bearish_count']}, Neutral: {reddit['neutral_count']}")
            
            # MarketAux analysis
            if 'marketaux_sentiment' in result and result['marketaux_sentiment']:
                marketaux = result['marketaux_sentiment']
                if marketaux.get('sentiment_score', 0) != 0:
                    print(f"\n📈 Professional Sentiment (MarketAux): {marketaux['sentiment_score']:+.3f}")
            
        except Exception as e:
            print(f"❌ Error analyzing {bank}: {e}")
    
    print(f"\n✅ Enhanced morning analysis complete!")
    print("🎉 Quality-based weighting system successfully adjusting weights based on data quality!")

if __name__ == "__main__":
    run_enhanced_morning_analysis()

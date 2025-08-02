#!/usr/bin/env python3
"""
Enhanced Morning Analysis - Demonstrating Reddit + MarketAux Integration Impact
"""

import os
import sys
from datetime import datetime
import logging

# Add app to path 
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_morning_analysis():
    """
    Run comprehensive morning analysis showing Reddit + MarketAux integration impact
    """
    print("🌅 ENHANCED MORNING ANALYSIS - Reddit + MarketAux Integration")
    print("=" * 80)
    print(f"📅 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Import news analyzer with our enhanced sentiment capabilities
        from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
        analyzer = NewsSentimentAnalyzer()
        
        print("✅ Sentiment Analysis System Initialized")
        print(f"   • Reddit Client: {'✅ Connected' if analyzer.reddit else '❌ Not Available'}")
        print(f"   • MarketAux Professional: {'✅ Connected' if analyzer.marketaux_manager else '❌ Not Available'}")
        print()
        
        # Test symbols - Australian big four banks
        test_symbols = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX']
        
        results = {}
        
        print("🏦 BANK SENTIMENT ANALYSIS")
        print("-" * 50)
        
        for symbol in test_symbols:
            print(f"\n📊 Analyzing {symbol}...")
            
            try:
                # Run comprehensive sentiment analysis
                result = analyzer.analyze_bank_sentiment(symbol)
                results[symbol] = result
                
                # Extract key metrics
                overall_sentiment = result.get('overall_sentiment', 0)
                confidence = result.get('confidence', 0)
                news_count = result.get('news_count', 0)
                
                # Reddit metrics
                reddit_data = result.get('reddit_sentiment', {})
                reddit_posts = reddit_data.get('posts_analyzed', 0)
                reddit_sentiment = reddit_data.get('average_sentiment', 0)
                
                # MarketAux metrics
                marketaux_data = result.get('marketaux_sentiment', {})
                marketaux_sentiment = marketaux_data.get('sentiment_score', 0) if marketaux_data else 0
                marketaux_sources = marketaux_data.get('source_count', 0) if marketaux_data else 0
                
                # Determine signal
                if overall_sentiment > 0.1:
                    signal = "🟢 BUY"
                elif overall_sentiment < -0.1:
                    signal = "🔴 SELL"
                else:
                    signal = "🟡 HOLD"
                
                print(f"   Result: {signal}")
                print(f"   Overall Sentiment: {overall_sentiment:.3f}")
                print(f"   Confidence: {confidence:.1%}")
                print(f"   News Articles: {news_count}")
                print(f"   Reddit Posts: {reddit_posts} (sentiment: {reddit_sentiment:.3f})")
                print(f"   MarketAux Sources: {marketaux_sources} (sentiment: {marketaux_sentiment:.3f})")
                
            except Exception as e:
                print(f"   ❌ Error analyzing {symbol}: {e}")
                results[symbol] = None
        
        print("\n" + "=" * 80)
        print("📈 MORNING ANALYSIS SUMMARY")
        print("=" * 80)
        
        successful_analyses = sum(1 for r in results.values() if r is not None)
        total_reddit_posts = sum(r.get('reddit_sentiment', {}).get('posts_analyzed', 0) for r in results.values() if r)
        total_news_articles = sum(r.get('news_count', 0) for r in results.values() if r)
        
        buy_signals = sum(1 for r in results.values() if r and r.get('overall_sentiment', 0) > 0.1)
        sell_signals = sum(1 for r in results.values() if r and r.get('overall_sentiment', 0) < -0.1)
        hold_signals = successful_analyses - buy_signals - sell_signals
        
        print(f"📊 Analysis Coverage: {successful_analyses}/{len(test_symbols)} banks")
        print(f"📰 News Articles Analyzed: {total_news_articles}")
        print(f"🗨️  Reddit Posts Analyzed: {total_reddit_posts}")
        print()
        print(f"📈 Trading Signals:")
        print(f"   🟢 BUY:  {buy_signals} banks")
        print(f"   🔴 SELL: {sell_signals} banks")
        print(f"   🟡 HOLD: {hold_signals} banks")
        print()
        
        # Show individual bank recommendations
        print("🏦 INDIVIDUAL BANK ANALYSIS:")
        print("-" * 50)
        
        for symbol, result in results.items():
            if result:
                sentiment = result.get('overall_sentiment', 0)
                confidence = result.get('confidence', 0)
                
                if sentiment > 0.1:
                    signal = "🟢 BUY"
                    strength = "STRONG" if sentiment > 0.2 else "MODERATE"
                elif sentiment < -0.1:
                    signal = "🔴 SELL"
                    strength = "STRONG" if sentiment < -0.2 else "MODERATE"
                else:
                    signal = "🟡 HOLD"
                    strength = ""
                
                print(f"{symbol}: {signal} {strength}")
                print(f"   Sentiment: {sentiment:.3f}, Confidence: {confidence:.1%}")
                
                # Show component breakdown
                components = result.get('sentiment_components', {})
                if components:
                    print(f"   Components: Reddit={components.get('reddit', 0):.3f}, "
                          f"MarketAux={components.get('marketaux', 0):.3f}, "
                          f"News={components.get('news', 0):.3f}")
            else:
                print(f"{symbol}: ❌ Analysis Failed")
        
        print("\n" + "=" * 80)
        print("✅ MORNING ANALYSIS COMPLETE")
        print(f"🕐 Completed at: {datetime.now().strftime('%H:%M:%S')}")
        
        # Show system status
        print("\n📋 SYSTEM STATUS:")
        if analyzer.reddit:
            print("   ✅ Reddit Sentiment: Working (Social sentiment from AusFinance)")
        else:
            print("   ❌ Reddit Sentiment: Not available")
            
        if analyzer.marketaux_manager:
            stats = analyzer.marketaux_manager.get_usage_stats()
            remaining = stats.get('requests_remaining', 0)
            total = stats.get('daily_limit', 100)
            print(f"   ✅ MarketAux Professional: Working ({remaining}/{total} requests remaining)")
        else:
            print("   ❌ MarketAux Professional: Not available")
        
        print("\n💡 Impact Summary:")
        if total_reddit_posts > 0 and any(r.get('marketaux_sentiment', {}).get('sentiment_score', 0) != 0 for r in results.values() if r):
            print("   🎯 FULL INTEGRATION ACTIVE - Both Reddit and MarketAux providing sentiment data")
            print("   📈 Multi-source sentiment provides more reliable trading signals")
        elif total_reddit_posts > 0:
            print("   🔹 Reddit sentiment working - Social sentiment available")
        elif any(r.get('marketaux_sentiment', {}).get('sentiment_score', 0) != 0 for r in results.values() if r):
            print("   🔹 MarketAux working - Professional news sentiment available")
        else:
            print("   ⚠️  Limited sentiment data - Using traditional news sources only")
        
        return True
        
    except Exception as e:
        print(f"❌ Morning analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_morning_analysis()
    sys.exit(0 if success else 1)

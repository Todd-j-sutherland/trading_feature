#!/usr/bin/env python3
"""
Diagnostic script for morning analysis issues
"""

import sys
import os
import traceback
from datetime import datetime

def diagnose_morning_analysis():
    """Comprehensive diagnostic for morning analysis"""
    print("🔍 MORNING ANALYSIS DIAGNOSTIC")
    print("=" * 50)
    
    # Basic environment check
    print(f"📍 Working Directory: {os.getcwd()}")
    print(f"🐍 Python Version: {sys.version}")
    print(f"📂 Python Path: {sys.path[:3]}...")  # First 3 entries
    
    # Check if enhanced ML components are available
    print("\n🧠 Checking Enhanced ML Components...")
    try:
        from enhanced_ml_system.analyzers.enhanced_morning_analyzer_with_ml import EnhancedMorningAnalyzer
        print("✅ Enhanced ML analyzer import: SUCCESS")
        
        # Initialize analyzer
        analyzer = EnhancedMorningAnalyzer()
        print("✅ Enhanced ML analyzer initialization: SUCCESS")
        
        # Check bank list
        print(f"🏦 Bank list: {list(analyzer.banks.keys())}")
        
    except Exception as e:
        print(f"❌ Enhanced ML analyzer: FAILED - {e}")
        traceback.print_exc()
        return
    
    # Check sentiment analyzer
    print("\n📰 Checking Sentiment Analyzer...")
    try:
        from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
        news_analyzer = NewsSentimentAnalyzer()
        print("✅ News sentiment analyzer import: SUCCESS")
        
        # Test news collection for one bank
        print("📊 Testing news collection for CBA.AX...")
        start_time = datetime.now()
        sentiment_data = news_analyzer.analyze_bank_sentiment('CBA.AX')
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        news_count = sentiment_data.get('news_count', 0)
        overall_sentiment = sentiment_data.get('overall_sentiment', 0)
        
        print(f"   ⏱️  Duration: {duration:.2f} seconds")
        print(f"   📰 News Articles: {news_count}")
        print(f"   😊 Overall Sentiment: {overall_sentiment:.3f}")
        
        if news_count == 0:
            print("   ❌ NO NEWS FOUND - This explains 0 banks analyzed!")
            print("   🔍 Checking news sources...")
            
            # Check individual news sources
            try:
                all_news = news_analyzer.get_all_news(['CBA'], 'CBA.AX')
                print(f"   📡 Raw news collection: {len(all_news)} articles")
                
                if len(all_news) == 0:
                    print("   ❌ No news from any source - network/API issue likely")
                else:
                    print("   ✅ News sources working, filtering issue possible")
                    
            except Exception as e:
                print(f"   ❌ News collection error: {e}")
        else:
            print("   ✅ News collection working properly")
            
    except Exception as e:
        print(f"❌ Sentiment analyzer: FAILED - {e}")
        traceback.print_exc()
        return
    
    # Check technical analyzer
    print("\n📈 Checking Technical Analyzer...")
    try:
        from app.core.analysis.technical import TechnicalAnalyzer, get_market_data
        tech_analyzer = TechnicalAnalyzer()
        print("✅ Technical analyzer import: SUCCESS")
        
        # Test market data for one bank
        print("📊 Testing market data for CBA.AX...")
        market_data = get_market_data('CBA.AX', period='1mo', interval='1h')
        
        if not market_data.empty:
            print(f"   📊 Market data rows: {len(market_data)}")
            print("   ✅ Market data collection working")
        else:
            print("   ❌ No market data found")
            
    except Exception as e:
        print(f"❌ Technical analyzer: FAILED - {e}")
        traceback.print_exc()
    
    # Try running minimal analysis
    print("\n🧪 Running Minimal Analysis Test...")
    try:
        print("🔬 Initializing enhanced analyzer...")
        analyzer = EnhancedMorningAnalyzer()
        
        print("🔬 Running enhanced morning analysis...")
        result = analyzer.run_enhanced_morning_analysis()
        
        if result:
            banks_analyzed = result.get('banks_analyzed', [])
            print(f"✅ Analysis completed: {len(banks_analyzed)} banks analyzed")
            
            if len(banks_analyzed) == 0:
                print("❌ Still 0 banks analyzed - investigating individual bank processing...")
                
                # Test individual bank analysis
                for i, (symbol, name) in enumerate(list(analyzer.banks.items())[:2]):
                    print(f"\n🔍 Testing {symbol} ({name}) individually...")
                    try:
                        sentiment_data = analyzer.sentiment_analyzer.analyze_bank_sentiment(symbol)
                        print(f"   📰 News count: {sentiment_data.get('news_count', 0)}")
                        print(f"   😊 Sentiment: {sentiment_data.get('overall_sentiment', 0):.3f}")
                        
                        if sentiment_data.get('news_count', 0) > 0:
                            print(f"   ✅ {symbol}: Sentiment data OK")
                        else:
                            print(f"   ❌ {symbol}: No sentiment data")
                            
                    except Exception as e:
                        print(f"   ❌ {symbol}: Error - {e}")
                        
            else:
                print("✅ Banks analyzed successfully:")
                for bank in banks_analyzed:
                    print(f"   - {bank}")
                    
        else:
            print("❌ Analysis returned None/empty result")
            
    except Exception as e:
        print(f"❌ Minimal analysis test: FAILED - {e}")
        traceback.print_exc()
    
    print("\n🏁 Diagnostic complete!")

if __name__ == "__main__":
    diagnose_morning_analysis()

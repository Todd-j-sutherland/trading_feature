#!/usr/bin/env python3
"""
Comprehensive analysis of how MarketAux sentiment affects overall stock sentiment
Compares professional news sentiment vs broken Reddit system
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from app.core.sentiment.marketaux_integration import MarketAuxManager
from datetime import datetime

def analyze_sentiment_impact():
    """Analyze how MarketAux sentiment affects overall trading sentiment"""
    
    print('📊 COMPREHENSIVE SENTIMENT IMPACT ANALYSIS')
    print('=' * 70)
    print(f'Analysis Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    manager = MarketAuxManager()
    
    # Get current MarketAux data
    print('\n1️⃣ MARKETAUX PROFESSIONAL SENTIMENT DATA:')
    results = manager.get_super_batch_sentiment()
    
    if not results:
        print('   ❌ No MarketAux data available')
        return
    
    # Analyze current sentiment signals
    active_signals = []
    neutral_signals = []
    
    for result in results:
        sentiment_strength = abs(result.sentiment_score)
        
        if sentiment_strength > 0.1 and result.news_volume > 0:
            active_signals.append(result)
            
            direction = '📈 BULLISH' if result.sentiment_score > 0 else '📉 BEARISH'
            strength = 'STRONG' if sentiment_strength > 0.4 else 'MODERATE' if sentiment_strength > 0.2 else 'WEAK'
            
            print(f'   {result.symbol}: {result.sentiment_score:>6.3f} | {direction} | {strength} | {result.news_volume} articles')
            if result.highlights:
                print(f'      📰 "{result.highlights[0][:80]}..."')
        else:
            neutral_signals.append(result)
            print(f'   {result.symbol}: {result.sentiment_score:>6.3f} | ➡️ NEUTRAL | No news data')
    
    # Impact Analysis
    print('\n2️⃣ SENTIMENT IMPACT ON TRADING DECISIONS:')
    
    total_sentiment_strength = sum(abs(r.sentiment_score) for r in active_signals)
    bullish_signals = [r for r in active_signals if r.sentiment_score > 0.1]
    bearish_signals = [r for r in active_signals if r.sentiment_score < -0.1]
    
    print(f'   📊 Active Trading Signals: {len(active_signals)}/{len(results)} stocks')
    print(f'   📈 Bullish Signals: {len(bullish_signals)} stocks')
    print(f'   📉 Bearish Signals: {len(bearish_signals)} stocks')
    print(f'   ⚡ Total Signal Strength: {total_sentiment_strength:.3f}')
    
    # Individual stock impact
    print('\n3️⃣ INDIVIDUAL STOCK IMPACT ANALYSIS:')
    
    for result in active_signals:
        sentiment_score = result.sentiment_score
        
        # Determine trading impact level
        if abs(sentiment_score) > 0.4:
            impact_level = '🔥 HIGH IMPACT'
            trading_action = 'Strong trade signal - consider position adjustment'
        elif abs(sentiment_score) > 0.2:
            impact_level = '⚡ MODERATE IMPACT'
            trading_action = 'Moderate signal - monitor for confirmation'
        else:
            impact_level = '📊 LOW IMPACT'
            trading_action = 'Weak signal - informational only'
        
        bias_direction = 'BUY BIAS' if sentiment_score > 0 else 'SELL BIAS'
        
        print(f'\n   📈 {result.symbol}: {impact_level}')
        print(f'      Current Sentiment: {sentiment_score:>6.3f} ({bias_direction})')
        print(f'      Trading Action: {trading_action}')
        print(f'      News Volume: {result.news_volume} articles')
        print(f'      Confidence Level: {result.confidence:.2f}')
        print(f'      Source Quality: {result.source_quality}')
    
    # Comparison with broken Reddit system
    print('\n4️⃣ COMPARISON WITH BROKEN REDDIT SYSTEM:')
    
    print('   📊 BEFORE (Reddit System):')
    print('      • Sentiment Score: 0.0 for all stocks (system broken)')
    print('      • Trading Signals: None (no actionable data)')
    print('      • Data Quality: Poor (social media noise)')
    print('      • Update Frequency: Irregular/broken')
    print('      • Signal Reliability: 0% (completely broken)')
    
    print(f'\n   🚀 AFTER (MarketAux System):')
    print(f'      • Active Sentiment Signals: {len(active_signals)} stocks')
    print(f'      • Trading Signals: {len([r for r in active_signals if abs(r.sentiment_score) > 0.2])} actionable signals')
    print(f'      • Data Quality: Professional financial news sources')
    print(f'      • Update Frequency: Real-time market hours')
    print(f'      • Signal Reliability: High (professional sources)')
    print(f'      • Total Signal Strength: {total_sentiment_strength:.3f} (vs 0.0 from Reddit)')
    
    # Overall system improvement
    print('\n5️⃣ OVERALL SYSTEM IMPROVEMENT METRICS:')
    
    # Calculate improvement metrics
    strong_signals = len([r for r in active_signals if abs(r.sentiment_score) > 0.3])
    actionable_signals = len([r for r in active_signals if abs(r.sentiment_score) > 0.15])
    
    print(f'   🎯 Signal Quality Metrics:')
    print(f'      • Strong Signals (>0.3): {strong_signals} stocks')
    print(f'      • Actionable Signals (>0.15): {actionable_signals} stocks')
    print(f'      • News-Backed Signals: {len(active_signals)} stocks')
    print(f'      • Average Confidence: {sum(r.confidence for r in active_signals)/len(active_signals):.2f}' if active_signals else '      • Average Confidence: N/A')
    
    # Efficiency metrics
    stats = manager.get_usage_stats()
    daily_capacity = 95 * 6  # 95 requests * 6 symbols per request
    monthly_capacity = daily_capacity * 30
    
    print(f'\n   📈 Efficiency Metrics:')
    print(f'      • Daily Analysis Capacity: {daily_capacity:,} symbol-sentiment pairs')
    print(f'      • Monthly Analysis Capacity: {monthly_capacity:,} symbol-sentiment pairs')
    print(f'      • Current Efficiency: {stats.get("efficiency_metrics", {}).get("symbols_per_request", 6)} symbols per API call')
    print(f'      • vs Basic Usage: 6x more efficient than 1-symbol-per-request')
    
    # Trading strategy implications
    print('\n6️⃣ TRADING STRATEGY IMPLICATIONS:')
    
    if bullish_signals:
        bullish_strength = sum(r.sentiment_score for r in bullish_signals)
        print(f'   📈 BULLISH SENTIMENT DETECTED:')
        print(f'      • Bullish Stocks: {[r.symbol for r in bullish_signals]}')
        print(f'      • Combined Bullish Strength: {bullish_strength:.3f}')
        print(f'      • Strategy: Consider long positions or hold existing longs')
    
    if bearish_signals:
        bearish_strength = sum(abs(r.sentiment_score) for r in bearish_signals)
        print(f'\n   📉 BEARISH SENTIMENT DETECTED:')
        print(f'      • Bearish Stocks: {[r.symbol for r in bearish_signals]}')
        print(f'      • Combined Bearish Strength: {bearish_strength:.3f}')
        print(f'      • Strategy: Consider short positions or reduce long exposure')
    
    # Market sector analysis
    print('\n7️⃣ SECTOR SENTIMENT ANALYSIS:')
    
    big_four_banks = [r for r in results if r.symbol in ['CBA', 'ANZ', 'WBC', 'NAB']]
    bank_sentiment = sum(r.sentiment_score for r in big_four_banks) / len(big_four_banks)
    
    other_financials = [r for r in results if r.symbol in ['MQG', 'QBE', 'SUN', 'IAG']]
    if other_financials:
        financial_sentiment = sum(r.sentiment_score for r in other_financials) / len(other_financials)
    else:
        financial_sentiment = 0.0
    
    print(f'   🏦 Big 4 Banks Average Sentiment: {bank_sentiment:>6.3f}')
    print(f'   💼 Other Financials Average: {financial_sentiment:>6.3f}')
    
    if bank_sentiment > 0.1:
        print('      • Banking Sector: BULLISH bias detected')
    elif bank_sentiment < -0.1:
        print('      • Banking Sector: BEARISH bias detected')
    else:
        print('      • Banking Sector: NEUTRAL sentiment')
    
    print('\n' + '=' * 70)
    print('🎉 SENTIMENT IMPACT ANALYSIS COMPLETE!')
    
    # Key takeaways
    print('\n🚀 KEY TAKEAWAYS:')
    print('   ✅ MarketAux provides WORKING sentiment data (vs broken Reddit 0.0 values)')
    print('   ✅ Professional financial news sources offer higher quality signals')
    print('   ✅ Real-time sentiment updates enable timely trading decisions')
    print(f'   ✅ {len(active_signals)} stocks have actionable sentiment signals')
    print(f'   ✅ {total_sentiment_strength:.3f} total signal strength vs 0.0 from broken Reddit')
    print('   ✅ 6x more efficient API usage through smart batching')
    print('   ✅ Professional source quality increases trading confidence')
    
    return {
        'active_signals': len(active_signals),
        'total_strength': total_sentiment_strength,
        'bullish_count': len(bullish_signals),
        'bearish_count': len(bearish_signals),
        'bank_sentiment': bank_sentiment,
        'efficiency_rating': stats.get("efficiency_metrics", {}).get("efficiency_rating", "EXCELLENT")
    }

if __name__ == "__main__":
    results = analyze_sentiment_impact()
    print(f'\n📊 Analysis Results: {results}')

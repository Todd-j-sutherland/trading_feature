#!/usr/bin/env python3
"""
Quick Quality Check - Simple quality overview while system is running
"""

import subprocess

def quick_check():
    """Run a quick quality check"""
    
    print("🚀 QUICK QUALITY CHECK")
    print("=" * 50)
    
    # Check latest enhanced features
    cmd = '''ssh root@170.64.199.151 'cd /root/test && sqlite3 data/trading_predictions.db "
    SELECT 
        symbol,
        ROUND(confidence, 3) as conf,
        news_count as news,
        ROUND(sentiment_score, 4) as sentiment,
        ROUND(rsi, 1) as rsi,
        ROUND(current_price, 2) as price
    FROM enhanced_features 
    ORDER BY timestamp DESC 
    LIMIT 7;
    "'  '''
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("📊 LATEST SENTIMENT & TECHNICAL DATA:")
            print("Symbol    Conf   News  Sentiment    RSI   Price")
            print("-" * 50)
            for line in result.stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 6:
                        symbol, conf, news, sentiment, rsi, price = parts[:6]
                        print(f"{symbol:8} {conf:>5} {news:>5} {sentiment:>9} {rsi:>6} {price:>8}")
        else:
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    # Check morning analysis summary
    cmd2 = '''ssh root@170.64.199.151 'cd /root/test && sqlite3 data/trading_predictions.db "
    SELECT 
        timestamp,
        banks_analyzed,
        ROUND(overall_sentiment, 4) as sentiment
    FROM enhanced_morning_analysis 
    ORDER BY timestamp DESC 
    LIMIT 1;
    "' '''
    
    try:
        result = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("🌅 LATEST MORNING ANALYSIS:")
            parts = result.stdout.strip().split('|')
            if len(parts) >= 3:
                timestamp, banks, sentiment = parts[:3]
                print(f"  Time: {timestamp}")
                print(f"  Banks: {len(eval(banks))} analyzed")
                print(f"  Overall Sentiment: {sentiment}")
        else:
            print("🌅 No morning analysis data found")
    except Exception as e:
        print(f"Error checking morning analysis: {e}")
    
    print()
    
    # Check temporal guard
    cmd3 = "ssh root@170.64.199.151 'cd /root/test && python3 morning_temporal_guard.py 2>&1 | grep -E \"PASSED|FAILED\" | tail -1'"
    
    try:
        result = subprocess.run(cmd3, shell=True, capture_output=True, text=True)
        status = result.stdout.strip()
        if "PASSED" in status:
            print("🛡️ TEMPORAL PROTECTION: ✅ ALL CHECKS PASSED")
        elif "FAILED" in status:
            print("🛡️ TEMPORAL PROTECTION: ❌ CHECKS FAILED")
        else:
            print("🛡️ TEMPORAL PROTECTION: ⚠️ Status unclear")
    except Exception as e:
        print(f"🛡️ TEMPORAL PROTECTION: Error checking - {e}")
    
    print()
    print("💡 For detailed monitoring: python3 real_time_quality_monitor.py")

if __name__ == "__main__":
    quick_check()

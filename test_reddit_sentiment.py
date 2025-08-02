#!/usr/bin/env python3
"""
Test script to verify Reddit sentiment functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_reddit_sentiment():
    """Test Reddit sentiment analysis setup"""
    
    print("🔍 REDDIT SENTIMENT ANALYSIS TEST")
    print("=" * 50)
    
    try:
        from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
        
        # Create analyzer instance
        print("1. Creating sentiment analyzer...")
        analyzer = NewsSentimentAnalyzer()
        
        # Check Reddit client status
        print(f"2. Reddit client initialized: {analyzer.reddit is not None}")
        
        if analyzer.reddit is None:
            print("❌ Reddit client is None")
            print("   This means Reddit API credentials are not configured")
            print("   See REDDIT_SENTIMENT_SETUP.md for setup instructions")
        else:
            print("✅ Reddit client is available")
            
        # Test Reddit sentiment function
        print("3. Testing Reddit sentiment function...")
        result = analyzer._get_reddit_sentiment('CBA.AX')
        
        print(f"   Posts analyzed: {result['posts_analyzed']}")
        print(f"   Average sentiment: {result['average_sentiment']}")
        print(f"   Bullish count: {result['bullish_count']}")
        print(f"   Bearish count: {result['bearish_count']}")
        print(f"   Has error: {'error' in result}")
        
        if result['posts_analyzed'] == 0:
            if 'error' in result:
                print(f"❌ Reddit sentiment failed: {result['error']}")
            else:
                print("⚠️  Reddit sentiment returned no posts")
        else:
            print("✅ Reddit sentiment is working!")
            
        # Test environment variables
        print("4. Checking environment variables...")
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT')
        
        print(f"   REDDIT_CLIENT_ID: {'✅ Set' if client_id else '❌ Not set'}")
        print(f"   REDDIT_CLIENT_SECRET: {'✅ Set' if client_secret else '❌ Not set'}")
        print(f"   REDDIT_USER_AGENT: {'✅ Set' if user_agent else '❌ Not set (will use default)'}")
        
        return analyzer.reddit is not None and result['posts_analyzed'] > 0
        
    except Exception as e:
        print(f"❌ Error testing Reddit sentiment: {e}")
        return False

def check_database_reddit_sentiment():
    """Check Reddit sentiment in database"""
    
    print("\n📊 DATABASE REDDIT SENTIMENT CHECK")
    print("=" * 50)
    
    try:
        import sqlite3
        
        conn = sqlite3.connect("data/ml_models/enhanced_training_data.db")
        
        # Check Reddit sentiment distribution
        cursor = conn.execute("""
            SELECT 
                CASE 
                    WHEN reddit_sentiment = 0.0 THEN 'Zero (Broken)'
                    WHEN reddit_sentiment > 0 THEN 'Positive' 
                    WHEN reddit_sentiment < 0 THEN 'Negative'
                    ELSE 'Other'
                END as sentiment_type,
                COUNT(*) as count,
                ROUND(AVG(reddit_sentiment), 4) as avg_value
            FROM enhanced_features 
            GROUP BY 
                CASE 
                    WHEN reddit_sentiment = 0.0 THEN 'Zero (Broken)'
                    WHEN reddit_sentiment > 0 THEN 'Positive' 
                    WHEN reddit_sentiment < 0 THEN 'Negative'
                    ELSE 'Other'
                END
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        
        print("Reddit Sentiment Distribution:")
        total_records = sum(row[1] for row in results)
        
        for sentiment_type, count, avg_value in results:
            percentage = (count / total_records) * 100
            print(f"   {sentiment_type}: {count} records ({percentage:.1f}%) - avg: {avg_value}")
        
        # Check if ALL values are 0.0
        zero_count = next((row[1] for row in results if row[0] == 'Zero (Broken)'), 0)
        
        if zero_count == total_records:
            print(f"\n🚨 CRITICAL: ALL {total_records} Reddit sentiment values are 0.0!")
            print("   This confirms Reddit sentiment collection is completely broken")
        elif zero_count > total_records * 0.8:
            print(f"\n⚠️  WARNING: {zero_count}/{total_records} ({zero_count/total_records*100:.1f}%) Reddit values are 0.0")
        else:
            print(f"\n✅ Reddit sentiment appears to be working! Only {zero_count} zero values out of {total_records}")
        
        conn.close()
        
        return zero_count < total_records * 0.5
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

if __name__ == "__main__":
    print("🧪 REDDIT SENTIMENT DIAGNOSTIC TEST\n")
    
    # Test 1: Reddit client functionality
    reddit_working = test_reddit_sentiment()
    
    # Test 2: Database analysis
    db_has_reddit_data = check_database_reddit_sentiment()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    if reddit_working and db_has_reddit_data:
        print("✅ Reddit sentiment is WORKING properly")
    elif reddit_working and not db_has_reddit_data:
        print("⚠️  Reddit client works but database has no valid data")
        print("   Try running sentiment collection to populate database")
    elif not reddit_working and db_has_reddit_data:
        print("⚠️  Database has Reddit data but client is not working")
        print("   This suggests Reddit worked before but is now broken")
    else:
        print("❌ Reddit sentiment is BROKEN")
        print("   1. Configure Reddit API credentials (see REDDIT_SENTIMENT_SETUP.md)")
        print("   2. Restart the sentiment collection system")
        print("   3. Re-run this test to verify fixes")
    
    print(f"\nTest results: Reddit Client: {reddit_working}, Database: {db_has_reddit_data}")

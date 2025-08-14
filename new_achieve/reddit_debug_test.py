#!/usr/bin/env python3
"""
Reddit Sentiment Debug Test
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add app to path 
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_reddit_connection():
    """Test Reddit connection and sentiment analysis"""
    
    print("🔍 REDDIT SENTIMENT DEBUG TEST")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Environment Check:")
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'TradingAnalysisBot/1.0')
    
    print(f"   Client ID: {'✅ Set' if client_id else '❌ Missing'}")
    print(f"   Client Secret: {'✅ Set' if client_secret else '❌ Missing'}")
    print(f"   User Agent: {user_agent}")
    
    if not client_id or not client_secret:
        print("❌ Reddit credentials missing!")
        return False
    
    # Test Reddit connection
    print("\n🔗 Testing Reddit Connection:")
    try:
        import praw
        
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Test connection
        test_subreddit = reddit.subreddit('AusFinance')
        sub_info = test_subreddit.display_name
        subscriber_count = test_subreddit.subscribers
        
        print(f"   ✅ Connected to r/{sub_info}")
        print(f"   👥 Subscribers: {subscriber_count:,}")
        
    except Exception as e:
        print(f"   ❌ Reddit connection failed: {e}")
        return False
    
    # Test sentiment analysis on a specific symbol
    print("\n📊 Testing Sentiment Analysis:")
    try:
        from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
        
        analyzer = NewsSentimentAnalyzer()
        
        print(f"   Reddit Client Status: {'✅ Available' if analyzer.reddit else '❌ Not Available'}")
        
        if analyzer.reddit:
            # Test manual Reddit sentiment for CBA
            print("   🏦 Testing CBA sentiment...")
            
            # Get the reddit sentiment method
            reddit_result = analyzer._get_reddit_sentiment('CBA.AX')
            
            print(f"   Posts Found: {reddit_result.get('posts_analyzed', 0)}")
            print(f"   Average Sentiment: {reddit_result.get('average_sentiment', 0):.3f}")
            print(f"   Bullish Posts: {reddit_result.get('bullish_count', 0)}")
            print(f"   Bearish Posts: {reddit_result.get('bearish_count', 0)}")
            print(f"   Neutral Posts: {reddit_result.get('neutral_count', 0)}")
            
            # Show top posts if available
            top_posts = reddit_result.get('top_posts', [])
            if top_posts:
                print(f"\n   📰 Top Posts:")
                for i, post in enumerate(top_posts[:3], 1):
                    print(f"      {i}. {post['title'][:60]}... (sentiment: {post['sentiment']:.3f})")
            
            # Check for errors
            if 'error' in reddit_result:
                print(f"   ❌ Error: {reddit_result['error']}")
            
            return reddit_result.get('posts_analyzed', 0) > 0
        else:
            print("   ❌ Reddit client not initialized")
            return False
            
    except Exception as e:
        print(f"   ❌ Sentiment analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_reddit_connection()
    print(f"\n🎯 Test Result: {'✅ PASSED' if success else '❌ FAILED'}")

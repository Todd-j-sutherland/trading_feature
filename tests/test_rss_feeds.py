#!/usr/bin/env python3
"""
Test script to verify RSS feeds are accessible and working
"""

import feedparser
import requests
from datetime import datetime, timedelta
import time
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import Settings

def test_rss_feed(feed_name, feed_url, timeout=10):
    """Test a single RSS feed"""
    try:
        print(f"Testing {feed_name}: {feed_url}")
        
        # Test with requests first to check connectivity
        response = requests.get(feed_url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            return {
                'status': 'FAIL',
                'error': f'HTTP {response.status_code}',
                'entries': 0
            }
        
        # Parse with feedparser
        feed = feedparser.parse(feed_url)
        
        if feed.bozo:
            return {
                'status': 'WARNING',
                'error': f'Feed parse warning: {feed.bozo_exception}',
                'entries': len(feed.entries)
            }
        
        # Check if we got entries
        if len(feed.entries) == 0:
            return {
                'status': 'WARNING',
                'error': 'No entries found',
                'entries': 0
            }
        
        # Check if entries are recent (within last 30 days)
        recent_entries = 0
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for entry in feed.entries[:5]:  # Check first 5 entries
            published = entry.get('published_parsed', None)
            if published:
                pub_date = datetime.fromtimestamp(time.mktime(published))
                if pub_date > cutoff_date:
                    recent_entries += 1
        
        return {
            'status': 'SUCCESS',
            'error': None,
            'entries': len(feed.entries),
            'recent_entries': recent_entries,
            'feed_title': feed.feed.get('title', 'Unknown'),
            'last_updated': feed.feed.get('updated', 'Unknown')
        }
        
    except requests.exceptions.Timeout:
        return {
            'status': 'FAIL',
            'error': 'Connection timeout',
            'entries': 0
        }
    except requests.exceptions.RequestException as e:
        return {
            'status': 'FAIL',
            'error': f'Request error: {str(e)}',
            'entries': 0
        }
    except Exception as e:
        return {
            'status': 'FAIL',
            'error': f'Parse error: {str(e)}',
            'entries': 0
        }

def main():
    """Test all RSS feeds from settings"""
    print("🧪 RSS Feed Connectivity Test")
    print("=" * 60)
    print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    settings = Settings()
    rss_feeds = settings.NEWS_SOURCES['rss_feeds']
    
    results = {
        'SUCCESS': [],
        'WARNING': [],
        'FAIL': []
    }
    
    total_feeds = len(rss_feeds)
    
    for i, (feed_name, feed_url) in enumerate(rss_feeds.items(), 1):
        print(f"[{i}/{total_feeds}] ", end="", flush=True)
        
        result = test_rss_feed(feed_name, feed_url)
        results[result['status']].append((feed_name, result))
        
        # Print result
        status_emoji = {
            'SUCCESS': '✅',
            'WARNING': '⚠️ ',
            'FAIL': '❌'
        }
        
        print(f"{status_emoji[result['status']]} {feed_name}")
        if result['status'] == 'SUCCESS':
            print(f"   📰 {result['entries']} total entries, {result.get('recent_entries', 0)} recent")
            print(f"   📰 Title: {result.get('feed_title', 'Unknown')}")
        else:
            print(f"   ❗ {result['error']}")
        print()
    
    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ SUCCESS: {len(results['SUCCESS'])} feeds")
    print(f"⚠️  WARNING: {len(results['WARNING'])} feeds")
    print(f"❌ FAILED:  {len(results['FAIL'])} feeds")
    print(f"📊 TOTAL:   {total_feeds} feeds")
    
    success_rate = len(results['SUCCESS']) / total_feeds * 100
    print(f"🎯 Success Rate: {success_rate:.1f}%")
    
    if results['FAIL']:
        print(f"\n❌ Failed Feeds:")
        for feed_name, result in results['FAIL']:
            print(f"   • {feed_name}: {result['error']}")
    
    if results['WARNING']:
        print(f"\n⚠️  Warning Feeds:")
        for feed_name, result in results['WARNING']:
            print(f"   • {feed_name}: {result['error']}")
    
    print(f"\n🔗 Working RSS Feeds ({len(results['SUCCESS'])}):")
    for feed_name, result in results['SUCCESS']:
        print(f"   • {feed_name}: {result['entries']} entries")
    
    return success_rate

if __name__ == "__main__":
    success_rate = main()
    
    # Exit with appropriate code
    if success_rate >= 80:
        print(f"\n🎉 RSS feed integration ready! {success_rate:.1f}% success rate")
        sys.exit(0)
    elif success_rate >= 60:
        print(f"\n⚠️  RSS feeds mostly working ({success_rate:.1f}% success). Some feeds may need attention.")
        sys.exit(0)
    else:
        print(f"\n❌ Many RSS feeds failing ({success_rate:.1f}% success). Check internet connection and URLs.")
        sys.exit(1)

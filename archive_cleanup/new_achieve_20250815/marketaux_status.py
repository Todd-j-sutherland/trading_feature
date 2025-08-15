#!/usr/bin/env python3
"""
MarketAux Status Checker
Quick utility to check MarketAux integration status and usage
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from app.core.sentiment.marketaux_integration import MarketAuxManager
    from app.core.sentiment.marketaux_scheduler import MarketAuxScheduler
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def check_api_token():
    """Check if API token is configured"""
    token = os.getenv('MARKETAUX_API_TOKEN')
    if token:
        print(f"✅ API Token: Configured ({token[:8]}...)")
        return True
    else:
        print("❌ API Token: NOT CONFIGURED")
        print("   Add MARKETAUX_API_TOKEN to your .env file")
        return False

def check_usage_stats():
    """Check current usage statistics"""
    try:
        manager = MarketAuxManager()
        stats = manager.get_usage_stats()
        
        print(f"📊 Daily Usage: {stats['requests_made']}/{stats['daily_limit']} ({stats['usage_percentage']:.1f}%)")
        print(f"📊 Remaining: {stats['requests_remaining']} requests")
        
        # Usage breakdown
        if stats['requests_made'] > 0:
            print(f"📊 Last reset: {stats.get('reset_time', 'Unknown')}")
            
        # Check cache
        cache_file = Path("data/marketaux_cache.json")
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    cache_data = json.load(f)
                print(f"📊 Cache entries: {len(cache_data)}")
            except:
                print("📊 Cache entries: 0")
            
        return True
        
    except Exception as e:
        print(f"❌ Usage stats error: {e}")
        return False

def check_cache_status():
    """Check cache file status"""
    cache_file = Path("data/marketaux_cache.json")
    usage_file = Path("data/marketaux_usage.json")
    
    if cache_file.exists():
        try:
            with open(cache_file) as f:
                cache_data = json.load(f)
            print(f"✅ Cache file: {len(cache_data)} entries")
            
            # Check for recent entries
            recent = 0
            now = datetime.now()
            for key, data in cache_data.items():
                try:
                    timestamp = datetime.fromisoformat(data.get('timestamp', ''))
                    if now - timestamp < timedelta(hours=6):
                        recent += 1
                except:
                    pass
            print(f"   Recent entries (< 6h): {recent}")
            
        except Exception as e:
            print(f"❌ Cache file error: {e}")
    else:
        print("⚠️  Cache file: Not found (will be created on first use)")
    
    if usage_file.exists():
        print("✅ Usage file: Exists")
    else:
        print("⚠️  Usage file: Not found (will be created on first use)")

def check_scheduler():
    """Check scheduler configuration"""
    try:
        scheduler = MarketAuxScheduler()
        
        # Get next scheduled time
        now = datetime.now()
        schedule_times = [
            (9, 0, "Pre-market pulse"),
            (10, 15, "Market open"),
            (12, 30, "Midday check"),
            (16, 15, "Market close")
        ]
        
        next_schedule = None
        for hour, minute, name in schedule_times:
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if scheduled_time > now:
                next_schedule = (scheduled_time, name)
                break
        
        if next_schedule:
            time_diff = next_schedule[0] - now
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            print(f"⏰ Next scheduled: {next_schedule[1]} in {hours}h {minutes}m")
        else:
            print("⏰ Next scheduled: Pre-market pulse tomorrow at 09:00")
            
        print("✅ Scheduler: Configured")
        return True
        
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
        return False

def test_basic_functionality():
    """Test basic MarketAux functionality"""
    if not os.getenv('MARKETAUX_API_TOKEN'):
        print("⚠️  Skipping API test (no token configured)")
        return True
        
    try:
        print("🧪 Testing basic functionality...")
        manager = MarketAuxManager()
        
        # Test with CBA (should be in cache or use request)
        result = manager.get_symbol_sentiment("CBA")
        
        if result and result.sentiment_score is not None:
            print(f"✅ API test: SUCCESS")
            print(f"   CBA sentiment: {result.sentiment_score:.3f}")
            print(f"   News count: {result.news_volume}")
            print(f"   Source: {getattr(result, 'source', 'MarketAux')}")
            return True
        else:
            print("❌ API test: No data returned")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def print_integration_status():
    """Print overall integration status"""
    print("\n" + "="*50)
    print("🚀 MARKETAUX INTEGRATION STATUS")
    print("="*50)
    
    # Check each component
    checks = [
        ("API Token", check_api_token),
        ("Usage Stats", check_usage_stats),
        ("Cache System", check_cache_status),
        ("Scheduler", check_scheduler),
        ("Basic Test", test_basic_functionality)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n📋 {name}:")
        if check_func():
            passed += 1
    
    print("\n" + "="*50)
    if passed == total:
        print("🎉 ALL SYSTEMS GO! MarketAux integration is ready!")
        print("\nNext steps:")
        print("1. Run: python -m app.main morning")
        print("2. Check logs for MarketAux sentiment data")
        print("3. Monitor usage with: python marketaux_status.py")
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        print("\nSee errors above and check MARKETAUX_SETUP_GUIDE.md")
    print("="*50)

if __name__ == "__main__":
    print_integration_status()

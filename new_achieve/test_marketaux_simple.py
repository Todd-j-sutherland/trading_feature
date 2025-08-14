#!/usr/bin/env python3
"""
Simple MarketAux Integration Test
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_integration():
    """Test basic MarketAux integration"""
    
    print("🔍 Testing MarketAux Integration")
    print("-" * 40)
    
    # Test 1: Import MarketAux module
    try:
        from app.core.sentiment.marketaux_integration import MarketAuxManager
        print("✅ MarketAux module imported")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Initialize manager
    try:
        manager = MarketAuxManager()
        print("✅ MarketAux manager created")
        
        # Show usage stats
        stats = manager.get_usage_stats()
        print(f"   Daily limit: {stats['daily_limit']}")
        print(f"   Requests remaining: {stats['requests_remaining']}")
        
    except Exception as e:
        print(f"❌ Manager creation failed: {e}")
        return False
    
    # Test 3: Test cache system
    try:
        cache_key = manager._get_cache_key(["CBA"], 6)
        print(f"✅ Cache system working: {cache_key}")
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False
    
    # Test 4: Check if can make requests
    try:
        can_request = manager.can_make_request()
        print(f"✅ Request check: {can_request}")
    except Exception as e:
        print(f"❌ Request check failed: {e}")
        return False
    
    print("\n🎉 Basic integration test passed!")
    print("\n📋 Setup Instructions:")
    print("1. Get free API token: https://www.marketaux.com/register")
    print("2. Add to .env: MARKETAUX_API_TOKEN=your_token")
    print("3. Test with: python -m app.main status")
    
    return True

if __name__ == "__main__":
    test_basic_integration()

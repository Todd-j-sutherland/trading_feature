#!/usr/bin/env python3
"""
Test OAuth-based IG Markets paper trader
Verify that session tokens are properly handled
"""

import sys
import json
sys.path.append(".")

from ig_markets_paper_trader_oauth import IGMarketsPaperTrader

def test_oauth_paper_trader():
    """Test OAuth authentication and market data access"""
    
    print("🔍 Testing OAuth-based IG Markets Paper Trader...")
    
    # Initialize trader
    trader = IGMarketsPaperTrader()
    
    # Check authentication status
    print(f"✅ Authentication Status:")
    print(f"   Access Token: {'✅ Available' if trader.access_token else '❌ Missing'}")
    print(f"   Account ID: {trader.account_id}")
    print(f"   Token Expires: {trader.token_expires_at}")
    
    # Test market data access with a more common EPIC
    test_epics = [
        "IX.D.FTSE.DAILY.IP",     # FTSE 100 Index
        "IX.D.DOW.DAILY.IP",      # Dow Jones Index  
        "IX.D.NASDAQ.DAILY.IP",   # NASDAQ Index
        "CS.D.AUDUSD.TODAY.IP"    # AUD/USD Currency
    ]
    
    print(f"\n🔍 Testing market data access...")
    success_count = 0
    
    for epic in test_epics:
        print(f"Testing {epic}...")
        market_data = trader.get_market_price(epic)
        
        if market_data:
            print(f"   ✅ Success: Bid={market_data.get('bid')}, Offer={market_data.get('offer')}")
            success_count += 1
        else:
            print(f"   ❌ Failed to get market data")
    
    print(f"\n📊 Results:")
    print(f"   Successfully accessed {success_count}/{len(test_epics)} markets")
    
    if success_count > 0:
        print(f"✅ OAuth authentication and market data access working!")
        return True
    else:
        print(f"❌ Market data access still failing")
        return False

if __name__ == "__main__":
    test_oauth_paper_trader()

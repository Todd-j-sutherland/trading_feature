#!/usr/bin/env python3
"""
Test just the exit strategy functionality without hitting rate limits
"""

import sys
import json
from datetime import datetime
sys.path.append(".")

from ig_markets_paper_trader import IGMarketsPaperTrader, PaperTrade

def test_exit_strategy():
    """Test the exit strategy integration"""
    
    print("🔍 Testing Exit Strategy Integration...")
    
    # Create a mock paper trade
    mock_trade = PaperTrade(
        trade_id="test-123",
        prediction_id="pred-123",
        symbol="CBA.AX",
        action="BUY",
        quantity=100,
        entry_price=100.0,
        entry_time=datetime.now(),
        confidence=0.8,
        ig_markets_epic="IX.D.FTSE.DAILY.IP"
    )
    
    # Initialize trader (this will authenticate)
    trader = IGMarketsPaperTrader()
    
    # Test the exit strategy without hitting market data
    current_price = 103.0  # Mock 3% profit
    
    print(f"Testing exit conditions for:")
    print(f"  Symbol: {mock_trade.symbol}")
    print(f"  Entry Price: ${mock_trade.entry_price}")
    print(f"  Current Price: ${current_price}")
    print(f"  Profit: {((current_price - mock_trade.entry_price) / mock_trade.entry_price) * 100:.2f}%")
    
    try:
        exit_decision = trader._check_exit_conditions(mock_trade, current_price)
        
        print(f"\n✅ Exit Strategy Result:")
        print(f"  Should Exit: {exit_decision.get('should_exit')}")
        print(f"  Reason: {exit_decision.get('reason')}")
        print(f"  Confidence: {exit_decision.get('confidence')}")
        print(f"  Urgency: {exit_decision.get('urgency')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Exit strategy test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_exit_strategy()
    if success:
        print("\n✅ Exit strategy integration working correctly!")
    else:
        print("\n❌ Exit strategy integration has issues")

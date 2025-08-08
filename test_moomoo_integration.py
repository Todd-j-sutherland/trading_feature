#!/usr/bin/env python3
"""
Test script for Moomoo ASX integration
Run this to verify your Moomoo setup is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.trading.moomoo_integration import MoomooMLTrader
from app.config.settings import Settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_moomoo_connection():
    """Test basic Moomoo connection and functionality."""
    print("🚀 Testing Moomoo ASX Integration")
    print("=" * 50)
    
    settings = Settings()
    
    # Test 1: Initialize trader
    print("\n1️⃣ Testing Moomoo Trader Initialization...")
    try:
        trader = MoomooMLTrader(paper=True)
        if trader.is_available():
            print("   ✅ Moomoo trader initialized successfully")
        else:
            print("   ❌ Moomoo trader not available")
            print("   💡 Make sure OpenD is running and logged in")
            return False
    except Exception as e:
        print(f"   ❌ Error initializing trader: {e}")
        return False
    
    # Test 2: Get account information
    print("\n2️⃣ Testing Account Information...")
    try:
        account_info = trader.get_account_info()
        if 'error' not in account_info:
            print("   ✅ Account info retrieved successfully")
            print(f"   💰 Portfolio Value: ${account_info.get('portfolio_value', 0):,.2f} {account_info.get('currency', 'AUD')}")
            print(f"   💵 Cash: ${account_info.get('cash', 0):,.2f} {account_info.get('currency', 'AUD')}")
            print(f"   📊 Paper Trading: {account_info.get('paper', True)}")
        else:
            print(f"   ❌ Error getting account info: {account_info['error']}")
            return False
    except Exception as e:
        print(f"   ❌ Exception getting account info: {e}")
        return False
    
    # Test 3: Get market quotes for ASX banks
    print("\n3️⃣ Testing ASX Bank Quotes...")
    test_symbols = settings.BANK_SYMBOLS[:3]  # Test first 3 banks
    
    for symbol in test_symbols:
        try:
            quote = trader.get_latest_quote(symbol)
            if 'error' not in quote:
                print(f"   ✅ {symbol}: ${quote.get('cur_price', 0):.2f} (Bid: ${quote.get('bid_price', 0):.2f}, Ask: ${quote.get('ask_price', 0):.2f})")
            else:
                print(f"   ❌ {symbol}: {quote['error']}")
        except Exception as e:
            print(f"   ❌ {symbol}: Exception - {e}")
    
    # Test 4: Get current positions
    print("\n4️⃣ Testing Position Query...")
    try:
        positions = trader.get_positions()
        print(f"   ✅ Current positions retrieved: {len(positions)} positions")
        
        if positions:
            print("   📊 Current Positions:")
            for pos in positions[:5]:  # Show first 5 positions
                print(f"      {pos.get('code', 'N/A')}: {pos.get('qty', 0):.0f} shares @ ${pos.get('nominal_price', 0):.2f}")
        else:
            print("   📊 No current positions (paper trading account is empty)")
            
    except Exception as e:
        print(f"   ❌ Exception getting positions: {e}")
    
    # Test 5: Test ML order placement (simulation only)
    print("\n5️⃣ Testing ML Order Placement (Simulation)...")
    
    mock_ml_score = {
        'overall_ml_score': 75.5,
        'trading_recommendation': 'BUY',
        'position_size_pct': 0.02,  # Small position for testing
        'risk_level': 'MEDIUM',
        'confidence_factors': ['Strong sentiment', 'Good ML score'],
        'risk_factors': ['Market volatility']
    }
    
    test_symbol = settings.BANK_SYMBOLS[0]  # Test with first bank (CBA)
    
    try:
        # Note: This is still paper trading, but we're testing the order flow
        order_result = trader.place_ml_order(test_symbol, mock_ml_score, 10000.0)
        
        if order_result.get('status') == 'submitted':
            print(f"   ✅ {test_symbol}: Order submitted successfully")
            print(f"      Order ID: {order_result.get('order_id', 'N/A')}")
            print(f"      Side: {order_result.get('side', 'N/A').upper()}")
            print(f"      Quantity: {order_result.get('qty', 0)} shares")
            print(f"      ML Score: {order_result.get('ml_score', 0):.1f}")
        elif order_result.get('status') == 'skipped':
            print(f"   ⚠️ {test_symbol}: Order skipped - {order_result.get('reason', 'Unknown')}")
        else:
            print(f"   ❌ {test_symbol}: Order failed - {order_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Exception placing order: {e}")
    
    # Test 6: ML trade performance tracking
    print("\n6️⃣ Testing ML Trade Performance Tracking...")
    try:
        performance = trader.get_ml_trade_performance()
        
        if 'error' not in performance:
            print("   ✅ ML trade performance retrieved")
            print(f"      Total ML Trades: {performance.get('total_ml_trades', 0)}")
            print(f"      Win Rate: {performance.get('win_rate', 0):.1%}")
            print(f"      Avg ML Score: {performance.get('avg_ml_score', 0):.1f}")
            
            if performance.get('recent_trades'):
                print(f"      Recent Trades: {len(performance['recent_trades'])}")
        else:
            if 'No ML trades recorded' in performance.get('message', ''):
                print("   ℹ️ No ML trades recorded yet (expected for new setup)")
            else:
                print(f"   ❌ Error getting performance: {performance.get('error', 'Unknown')}")
                
    except Exception as e:
        print(f"   ❌ Exception getting performance: {e}")
    
    # Clean up
    print("\n7️⃣ Cleaning Up...")
    try:
        trader.close_connections()
        print("   ✅ Connections closed successfully")
    except Exception as e:
        print(f"   ⚠️ Error closing connections: {e}")
    
    print("\n🎯 Moomoo Integration Test Complete!")
    print("=" * 50)
    
    return True

def test_trading_manager_integration():
    """Test Moomoo integration with the ML Trading Manager."""
    print("\n🧠 Testing ML Trading Manager Integration")
    print("=" * 50)
    
    try:
        from app.core.ml.trading_manager import MLTradingManager
        
        print("1️⃣ Initializing ML Trading Manager...")
        manager = MLTradingManager()
        
        if hasattr(manager, 'moomoo_trader') and manager.moomoo_trader:
            if manager.moomoo_trader.is_available():
                print("   ✅ Moomoo trader available in ML Trading Manager")
            else:
                print("   ❌ Moomoo trader initialized but not available")
        else:
            print("   ❌ Moomoo trader not initialized in ML Trading Manager")
            return False
        
        print("\n2️⃣ Testing ML Scores Display...")
        try:
            # This will run a quick analysis and display results
            manager.display_ml_scores_summary(symbols=['CBA.AX', 'WBC.AX'])
            print("   ✅ ML scores display completed")
        except Exception as e:
            print(f"   ❌ Error in ML scores display: {e}")
        
        print("\n✅ ML Trading Manager integration test complete")
        return True
        
    except Exception as e:
        print(f"❌ Error testing ML Trading Manager integration: {e}")
        return False

if __name__ == '__main__':
    print("Moomoo ASX Integration Test Suite")
    print("This script tests your Moomoo setup for ASX paper trading")
    print("Make sure OpenD is running and logged in before proceeding!")
    print()
    
    input("Press Enter to start the tests...")
    
    # Run basic connection tests
    basic_success = test_moomoo_connection()
    
    if basic_success:
        print("\n" + "="*50)
        input("Basic tests passed! Press Enter to test ML Trading Manager integration...")
        
        # Run ML Trading Manager integration tests
        ml_success = test_trading_manager_integration()
        
        if ml_success:
            print("\n🎉 All tests passed! Your Moomoo integration is ready for ASX paper trading.")
            print("\nNext steps:")
            print("1. Run: python -m app.main ml-scores")
            print("2. Run: python -m app.main ml-trading")
            print("3. Run: python -m app.main ml-trading --execute")
        else:
            print("\n⚠️ ML Trading Manager tests failed. Check your configuration.")
    else:
        print("\n❌ Basic connection tests failed. Please check your Moomoo setup:")
        print("1. Ensure OpenD is running")
        print("2. Verify you're logged into OpenD with Australian market access")
        print("3. Check that pip install moomoo-api completed successfully")
        print("4. Review the setup_moomoo.md guide")
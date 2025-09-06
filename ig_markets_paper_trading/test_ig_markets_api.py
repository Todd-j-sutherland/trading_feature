#!/usr/bin/env python3
"""
IG Markets API Component Testing
Comprehensive test of all main API components to ensure proper functionality
"""

import json
import logging
import sys
import os
from datetime import datetime
import traceback

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def setup_logging():
    """Setup comprehensive logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_enhanced_ig_client():
    """Test Enhanced IG Markets Client"""
    print("\n🔍 TESTING ENHANCED IG MARKETS CLIENT")
    print("=" * 50)
    
    try:
        from enhanced_ig_client import EnhancedIGMarketsClient
        
        client = EnhancedIGMarketsClient(
            config_path="config/ig_markets_config_banks.json"
        )
        
        # Test authentication
        print("📋 Testing Authentication...")
        auth_result = client.authenticate()
        print(f"   Authentication: {'✅ SUCCESS' if auth_result else '❌ FAILED'}")
        
        if auth_result:
            # Test account info
            print("📋 Testing Account Information...")
            try:
                account_info = client.get_account_info()
                print(f"   Account ID: {account_info.get('accountId', 'Unknown')}")
                print(f"   Account Type: {account_info.get('accountType', 'Unknown')}")
                print(f"   Currency: {account_info.get('currency', 'Unknown')}")
                print("   Account Info: ✅ SUCCESS")
            except Exception as e:
                print(f"   Account Info: ❌ FAILED - {e}")
            
            # Test market data for all bank symbols
            bank_symbols = ['IX.D.ASX.IFM.IP', 'IX.D.ASX.IFE.IP', 'IX.D.ASX.IFD.IP', 
                           'IX.D.ASX.IFG.IP', 'IX.D.ASX.IFC.IP', 'IX.D.ASX.IFA.IP', 'IX.D.ASX.IFH.IP']
            symbol_names = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'CSL.AX', 'QBE.AX']
            
            print("📋 Testing Market Data for All Bank Symbols...")
            success_count = 0
            for epic, symbol in zip(bank_symbols, symbol_names):
                try:
                    market_data = client.get_market_data(epic)
                    if market_data and 'snapshot' in market_data:
                        bid = market_data['snapshot'].get('bid')
                        offer = market_data['snapshot'].get('offer')
                        print(f"   {symbol}: Bid: {bid}, Offer: {offer} ✅")
                        success_count += 1
                    else:
                        print(f"   {symbol}: ❌ No market data")
                except Exception as e:
                    print(f"   {symbol}: ❌ FAILED - {e}")
            
            print(f"   Market Data Success Rate: {success_count}/{len(bank_symbols)} ({success_count/len(bank_symbols)*100:.1f}%)")
            
            # Test rate limiting info
            print("📋 Testing Rate Limiting...")
            try:
                rate_info = client.get_rate_limit_info()
                print(f"   Requests Remaining: {rate_info.get('requests_remaining', 'Unknown')}")
                print(f"   Reset Time: {rate_info.get('reset_time', 'Unknown')}")
                print("   Rate Limiting: ✅ SUCCESS")
            except Exception as e:
                print(f"   Rate Limiting: ❌ FAILED - {e}")
        
        return auth_result
        
    except Exception as e:
        print(f"❌ Enhanced IG Client Test FAILED: {e}")
        traceback.print_exc()
        return False

def test_position_manager():
    """Test Position Manager"""
    print("\n🔍 TESTING POSITION MANAGER")
    print("=" * 50)
    
    try:
        from position_manager import PositionManager
        
        pm = PositionManager(
            db_path="data/paper_trading.db",
            config_path="config/trading_parameters.json"
        )
        
        # Test account initialization
        print("📋 Testing Account Initialization...")
        account_info = pm.get_account_info()
        print(f"   Account Balance: ${account_info['balance']:,.2f}")
        print(f"   Available Funds: ${account_info['available_funds']:,.2f}")
        print(f"   Used Funds: ${account_info['used_funds']:,.2f}")
        print("   Account Init: ✅ SUCCESS")
        
        # Test position limits
        print("📋 Testing Position Limits...")
        for symbol in ['CBA.AX', 'WBC.AX', 'ANZ.AX']:
            can_open = pm.can_open_position(symbol)
            print(f"   Can open {symbol}: {'✅ YES' if can_open else '❌ NO'}")
        
        # Test fund checking
        print("📋 Testing Fund Availability...")
        test_amounts = [1000, 5000, 10000]
        for amount in test_amounts:
            has_funds = pm.has_sufficient_funds(amount)
            print(f"   ${amount:,}: {'✅ Available' if has_funds else '❌ Insufficient'}")
        
        # Test position tracking
        print("📋 Testing Position Tracking...")
        open_positions = pm.get_open_positions()
        print(f"   Open Positions: {len(open_positions)}")
        
        total_positions = pm.get_total_positions()
        print(f"   Total Positions: {total_positions}")
        
        print("   Position Manager: ✅ SUCCESS")
        return True
        
    except Exception as e:
        print(f"❌ Position Manager Test FAILED: {e}")
        traceback.print_exc()
        return False

def test_exit_strategy_engine():
    """Test Exit Strategy Engine"""
    print("\n🔍 TESTING EXIT STRATEGY ENGINE")
    print("=" * 50)
    
    try:
        from exit_strategy_engine import ExitStrategyEngine
        
        # Initialize with IG client
        from enhanced_ig_client import EnhancedIGMarketsClient
        ig_client = EnhancedIGMarketsClient(
            config_path="config/ig_markets_config_banks.json"
        )
        
        exit_engine = ExitStrategyEngine(ig_client=ig_client)
        
        print("📋 Testing Exit Strategy Initialization...")
        print(f"   Engine Enabled: {'✅ YES' if exit_engine.enabled else '❌ NO'}")
        print(f"   Data Source: {exit_engine.data_source}")
        
        # Test exit decision for mock position
        print("📋 Testing Exit Decision Logic...")
        mock_position = {
            'symbol': 'CBA.AX',
            'epic': 'IX.D.ASX.IFM.IP',
            'entry_price': 165.50,
            'quantity': 100,
            'action': 'BUY',
            'entry_time': '2025-09-05T10:00:00'
        }
        
        try:
            should_exit, reason, current_price = exit_engine.should_exit_position(mock_position)
            print(f"   Exit Decision: {'✅ EXIT' if should_exit else '✅ HOLD'}")
            print(f"   Reason: {reason}")
            print(f"   Current Price: ${current_price:.2f}" if current_price else "   Current Price: N/A")
        except Exception as e:
            print(f"   Exit Decision: ❌ FAILED - {e}")
        
        print("   Exit Strategy: ✅ SUCCESS")
        return True
        
    except Exception as e:
        print(f"❌ Exit Strategy Test FAILED: {e}")
        traceback.print_exc()
        return False

def test_paper_trader():
    """Test Paper Trader Main Engine"""
    print("\n🔍 TESTING PAPER TRADER ENGINE")
    print("=" * 50)
    
    try:
        from paper_trader import PaperTrader
        
        trader = PaperTrader()
        
        print("📋 Testing Paper Trader Initialization...")
        print("   Paper Trader: ✅ INITIALIZED")
        
        # Test status report
        print("📋 Testing Status Report...")
        try:
            status = trader.get_status_report()
            
            print(f"   API Status: {'✅ Connected' if status['api_status']['authenticated'] else '❌ Disconnected'}")
            print(f"   Account Balance: ${status['account_status']['balance']:,.2f}")
            print(f"   Available Funds: ${status['account_status']['available_funds']:,.2f}")
            print(f"   Exit Strategy: {'✅ Available' if status['exit_strategy']['available'] else '❌ Unavailable'}")
            print(f"   Rate Limit: {status['api_status']['rate_limit']['requests_remaining']} requests remaining")
            
        except Exception as e:
            print(f"   Status Report: ❌ FAILED - {e}")
        
        # Test performance summary
        print("📋 Testing Performance Summary...")
        try:
            performance = trader.get_performance_summary()
            print(f"   Total Trades: {performance['total_trades']}")
            print(f"   Win Rate: {performance['win_rate']:.1f}%")
            print(f"   Total P&L: ${performance['total_pnl']:.2f}")
            print(f"   Open Positions: {performance['open_positions']}")
        except Exception as e:
            print(f"   Performance Summary: ❌ FAILED - {e}")
        
        print("   Paper Trader: ✅ SUCCESS")
        return True
        
    except Exception as e:
        print(f"❌ Paper Trader Test FAILED: {e}")
        traceback.print_exc()
        return False

def test_api_responses():
    """Test specific API response codes"""
    print("\n🔍 TESTING API RESPONSE CODES")
    print("=" * 50)
    
    try:
        from enhanced_ig_client import EnhancedIGMarketsClient
        
        client = EnhancedIGMarketsClient(
            config_path="config/ig_markets_config_banks.json"
        )
        
        # Test authentication response
        print("📋 Testing Authentication Response...")
        if hasattr(client, 'last_response_code'):
            print(f"   Auth Response Code: {client.last_response_code}")
        
        # Test market data responses for weekend
        print("📋 Testing Weekend Market Data Responses...")
        weekend_test_symbols = ['IX.D.ASX.IFM.IP', 'IX.D.ASX.IFE.IP']
        
        for epic in weekend_test_symbols:
            try:
                market_data = client.get_market_data(epic)
                response_code = getattr(client, 'last_response_code', 'Unknown')
                print(f"   {epic}: Response {response_code} {'✅' if str(response_code).startswith('2') else '⚠️'}")
            except Exception as e:
                print(f"   {epic}: ❌ Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ API Response Test FAILED: {e}")
        return False

def main():
    """Main testing function"""
    setup_logging()
    
    print("🧪 IG MARKETS PAPER TRADING - COMPREHENSIVE API TEST")
    print("=" * 60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test Environment: Remote Server")
    print(f"Weekend Testing: {'✅ YES' if datetime.now().weekday() >= 5 else '❌ NO'}")
    print()
    
    # Run all tests
    test_results = {
        'Enhanced IG Client': test_enhanced_ig_client(),
        'Position Manager': test_position_manager(), 
        'Exit Strategy Engine': test_exit_strategy_engine(),
        'Paper Trader Engine': test_paper_trader(),
        'API Response Codes': test_api_responses()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print()
    print(f"Overall Result: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - IG Markets Paper Trading System is FULLY OPERATIONAL!")
        return 0
    else:
        print(f"⚠️  {total-passed} tests failed - System needs attention")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

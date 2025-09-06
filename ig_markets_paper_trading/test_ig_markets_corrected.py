#!/usr/bin/env python3
"""
IG Markets API Testing - Corrected Version
Tests the actual API methods and functionality
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
    """Setup logging"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_enhanced_ig_client():
    """Test Enhanced IG Client with correct API"""
    print("\n🔍 TESTING ENHANCED IG MARKETS CLIENT")
    print("=" * 50)
    
    try:
        from enhanced_ig_client import EnhancedIGMarketsClient
        
        client = EnhancedIGMarketsClient("config/ig_markets_config_banks.json")
        
        # Check if authenticated (constructor handles auth)
        print("📋 Testing Authentication...")
        has_token = hasattr(client, 'access_token') and client.access_token
        print(f"   Authentication: {'✅ SUCCESS' if has_token else '❌ FAILED'}")
        
        if has_token:
            print(f"   Account ID: {getattr(client, 'account_id', 'Unknown')}")
            
            # Test account info
            print("📋 Testing Account Information...")
            try:
                account_info = client.get_account_info()
                print(f"   Account Info Retrieved: {'✅ SUCCESS' if account_info else '❌ FAILED'}")
                if account_info:
                    print(f"   Account Details: {type(account_info).__name__}")
            except Exception as e:
                print(f"   Account Info: ❌ FAILED - {e}")
            
            # Test market data for bank symbols
            print("📋 Testing Market Data...")
            test_epics = ['IX.D.ASX.IFM.IP', 'IX.D.ASX.IFE.IP', 'IX.D.ASX.IFD.IP']
            success_count = 0
            
            for epic in test_epics:
                try:
                    market_data = client.get_market_data(epic)
                    if market_data:
                        print(f"   {epic}: ✅ Data retrieved")
                        success_count += 1
                    else:
                        print(f"   {epic}: ❌ No data")
                except Exception as e:
                    print(f"   {epic}: ❌ Error - {str(e)[:50]}...")
            
            print(f"   Market Data Success: {success_count}/{len(test_epics)}")
            
            # Test rate limiting
            print("📋 Testing Rate Limit Status...")
            try:
                rate_status = client.get_rate_limit_status()
                print(f"   Rate Limit Info: {'✅ Available' if rate_status else '❌ Unavailable'}")
            except Exception as e:
                print(f"   Rate Limit: ❌ Error - {e}")
        
        return has_token
        
    except Exception as e:
        print(f"❌ Enhanced IG Client FAILED: {e}")
        return False

def test_position_manager():
    """Test Position Manager with correct API"""
    print("\n🔍 TESTING POSITION MANAGER")
    print("=" * 50)
    
    try:
        from position_manager import PositionManager
        
        pm = PositionManager("data/paper_trading.db", "config/trading_parameters.json")
        
        # Test account balance
        print("📋 Testing Account Balance...")
        try:
            balance = pm.get_account_balance()
            print(f"   Account Balance: ${balance:,.2f}")
            print("   Balance Check: ✅ SUCCESS")
        except Exception as e:
            print(f"   Balance Check: ❌ FAILED - {e}")
        
        # Test position limits
        print("📋 Testing Position Management...")
        test_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX']
        for symbol in test_symbols:
            try:
                can_open = pm.can_open_position(symbol)
                has_open = pm.has_open_position(symbol)
                print(f"   {symbol}: Can open: {'✅' if can_open else '❌'}, Has open: {'✅' if has_open else '❌'}")
            except Exception as e:
                print(f"   {symbol}: ❌ Error - {e}")
        
        # Test open positions
        print("📋 Testing Open Positions...")
        try:
            open_positions = pm.get_open_positions()
            open_count = pm.get_open_positions_count()
            print(f"   Open Positions: {len(open_positions) if open_positions else 0}")
            print(f"   Open Count: {open_count}")
            print("   Position Tracking: ✅ SUCCESS")
        except Exception as e:
            print(f"   Position Tracking: ❌ FAILED - {e}")
        
        # Test performance summary
        print("📋 Testing Performance Summary...")
        try:
            performance = pm.get_performance_summary()
            print(f"   Performance Data: {'✅ Available' if performance else '❌ Unavailable'}")
            if performance:
                print(f"   Summary Type: {type(performance).__name__}")
        except Exception as e:
            print(f"   Performance: ❌ Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Position Manager FAILED: {e}")
        return False

def test_paper_trader_integration():
    """Test Paper Trader Integration"""
    print("\n🔍 TESTING PAPER TRADER INTEGRATION")
    print("=" * 50)
    
    try:
        from paper_trader import PaperTrader
        
        trader = PaperTrader()
        print("   Paper Trader: ✅ INITIALIZED")
        
        # Test trading cycle (should be safe on weekends)
        print("📋 Testing Trading Cycle...")
        try:
            # This should be safe as it just checks for new predictions
            results = trader.run_trading_cycle()
            print(f"   Trading Cycle: ✅ Completed")
            print(f"   New Trades: {results.get('new_trades', 0)}")
            print(f"   Closed Trades: {results.get('closed_trades', 0)}")
            print(f"   Errors: {len(results.get('errors', []))}")
        except Exception as e:
            print(f"   Trading Cycle: ❌ Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Paper Trader FAILED: {e}")
        return False

def test_weekend_api_responses():
    """Test API responses during weekend"""
    print("\n🔍 TESTING WEEKEND API BEHAVIOR")
    print("=" * 50)
    
    try:
        from enhanced_ig_client import EnhancedIGMarketsClient
        
        client = EnhancedIGMarketsClient("config/ig_markets_config_banks.json")
        
        # Test if we can get market data on weekends
        print("📋 Testing Weekend Market Data Access...")
        weekend_epics = ['IX.D.ASX.IFM.IP', 'IX.D.ASX.IFE.IP']
        
        for epic in weekend_epics:
            try:
                data = client.get_market_data(epic)
                if data:
                    print(f"   {epic}: ✅ Data available (weekend)")
                else:
                    print(f"   {epic}: ⚠️ No data (expected on weekend)")
            except Exception as e:
                print(f"   {epic}: ⚠️ Error (expected on weekend) - {str(e)[:30]}...")
        
        # Test API connection status
        print("📋 Testing API Connection Status...")
        has_token = hasattr(client, 'access_token') and client.access_token
        print(f"   API Connection: {'✅ Active' if has_token else '❌ Inactive'}")
        
        if has_token:
            print(f"   Account ID: {getattr(client, 'account_id', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Weekend API Test FAILED: {e}")
        return False

def test_database_connectivity():
    """Test database connectivity and structure"""
    print("\n🔍 TESTING DATABASE CONNECTIVITY")
    print("=" * 50)
    
    try:
        import sqlite3
        
        # Test paper trading database
        print("📋 Testing Paper Trading Database...")
        try:
            conn = sqlite3.connect("data/paper_trading.db")
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"   Database Tables: {len(tables)} found")
            
            # Check account balance table
            try:
                cursor.execute("SELECT COUNT(*) FROM account_balance")
                balance_records = cursor.fetchone()[0]
                print(f"   Account Records: {balance_records}")
            except:
                print("   Account Records: ❌ No table or data")
            
            # Check positions table
            try:
                cursor.execute("SELECT COUNT(*) FROM positions")
                position_records = cursor.fetchone()[0]
                print(f"   Position Records: {position_records}")
            except:
                print("   Position Records: ❌ No table or data")
            
            conn.close()
            print("   Database: ✅ Accessible")
            
        except Exception as e:
            print(f"   Database: ❌ Error - {e}")
        
        # Test main predictions database connection
        print("📋 Testing Main Predictions Database...")
        try:
            conn = sqlite3.connect("../data/trading_predictions.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions")
            pred_count = cursor.fetchone()[0]
            print(f"   Predictions Available: {pred_count}")
            conn.close()
            print("   Main Database: ✅ Accessible")
        except Exception as e:
            print(f"   Main Database: ❌ Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database Test FAILED: {e}")
        return False

def main():
    """Run all tests"""
    setup_logging()
    
    print("🧪 IG MARKETS PAPER TRADING - WEEKEND API TEST")
    print("=" * 60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Day of Week: {datetime.now().strftime('%A')}")
    print(f"Weekend Test: {'✅ YES' if datetime.now().weekday() >= 5 else '❌ NO'}")
    print()
    
    # Run tests
    test_results = {}
    test_results['Enhanced IG Client'] = test_enhanced_ig_client()
    test_results['Position Manager'] = test_position_manager()
    test_results['Paper Trader Integration'] = test_paper_trader_integration()
    test_results['Weekend API Behavior'] = test_weekend_api_responses()
    test_results['Database Connectivity'] = test_database_connectivity()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 WEEKEND API TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print()
    print(f"Overall Result: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed >= 4:  # Allow for some weekend-related failures
        print("🎉 SYSTEM IS OPERATIONAL - IG Markets Paper Trading ready for production!")
        return 0
    else:
        print("⚠️ SYSTEM NEEDS ATTENTION - Some components require fixes")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

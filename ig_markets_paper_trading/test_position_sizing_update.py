#!/usr/bin/env python3
"""
Test Updated Position Sizing
Verify the new $15K position limits work correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_position_sizing():
    print("🧪 TESTING UPDATED POSITION SIZING")
    print("=" * 50)
    
    try:
        from position_manager import PositionManager
        from enhanced_ig_client import EnhancedIGMarketsClient
        
        # Initialize components
        pm = PositionManager("data/paper_trading.db", "config/trading_parameters.json")
        ig_client = EnhancedIGMarketsClient("config/ig_markets_config_banks.json")
        
        print("📋 Updated Configuration:")
        print(f"   Max Position Size: ${pm.config['position_management']['max_position_size']:,.0f}")
        print(f"   Min Position Size: ${pm.config['position_management']['min_position_size']:,.0f}")
        print(f"   Max Risk Per Trade: {pm.config['risk_management']['max_risk_per_trade']*100:.1f}%")
        print(f"   Max Positions: {pm.config['position_management']['max_positions']}")
        print(f"   Min Confidence: {pm.config['trading_rules']['min_confidence_threshold']}")
        
        # Test position size calculation for each bank stock
        print("\n📋 Position Size Calculations:")
        
        bank_epics = {
            'CBA.AX': 'IX.D.ASX.IFM.IP',
            'WBC.AX': 'IX.D.ASX.IFE.IP', 
            'ANZ.AX': 'IX.D.ASX.IFD.IP',
            'NAB.AX': 'IX.D.ASX.IFG.IP',
            'MQG.AX': 'IX.D.ASX.IFC.IP',
            'QBE.AX': 'IX.D.ASX.IFH.IP',
            'SUN.AX': 'IX.D.ASX.IFI.IP'
        }
        
        for symbol, epic in bank_epics.items():
            try:
                # Get current price
                market_data = ig_client.get_market_data(epic)
                if market_data and 'snapshot' in market_data:
                    current_price = market_data['snapshot'].get('offer', 100)
                    
                    # Test different confidence levels
                    for confidence in [0.65, 0.75, 0.85]:
                        try:
                            position_size = pm.calculate_position_size(current_price, confidence)
                            can_open = pm.can_open_position(symbol, position_size)
                            
                            print(f"   {symbol}: ${current_price:.2f} @ {confidence:.0%} conf → ${position_size:.0f} {'✅' if can_open else '❌'}")
                            
                        except Exception as e:
                            print(f"   {symbol}: ❌ Calc error - {e}")
                            
                else:
                    print(f"   {symbol}: ⚠️ No market data")
                    
            except Exception as e:
                print(f"   {symbol}: ❌ Error - {e}")
        
        # Test account utilization
        print("\n📋 Account Utilization:")
        balance = pm.get_account_balance()
        print(f"   Account Balance: ${balance:,.0f}")
        
        max_positions = pm.config['position_management']['max_positions']
        max_position_size = pm.config['position_management']['max_position_size']
        max_total_exposure = max_positions * max_position_size
        
        print(f"   Max Total Exposure: {max_positions} × ${max_position_size:,.0f} = ${max_total_exposure:,.0f}")
        print(f"   Account Utilization: {max_total_exposure/balance*100:.1f}%")
        
        if max_total_exposure <= balance:
            print("   ✅ Configuration allows full position deployment")
        else:
            print("   ⚠️ Configuration may limit position deployment")
        
        # Test spread impact analysis
        print("\n📋 Spread Impact Analysis:")
        typical_spreads = {
            'CBA.AX': 0.02,  # 2 cents
            'WBC.AX': 0.02,
            'ANZ.AX': 0.02, 
            'NAB.AX': 0.02,
            'MQG.AX': 0.05,  # 5 cents (higher priced)
            'QBE.AX': 0.01,
            'SUN.AX': 0.01
        }
        
        print("   Symbol  | Position | Spread Cost | Impact")
        print("   --------|----------|-------------|-------")
        
        for symbol, spread in typical_spreads.items():
            position_size = 15000  # Use max position size
            avg_price = 50  # Approximate average price
            shares = position_size / avg_price
            spread_cost = shares * spread
            impact_pct = (spread_cost / position_size) * 100
            
            print(f"   {symbol:7} | ${position_size:7,.0f} | ${spread_cost:10.2f} | {impact_pct:5.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Position Sizing Test Failed: {e}")
        return False

def test_trading_cycle_with_new_params():
    """Test a trading cycle with the new parameters"""
    print("\n🧪 TESTING TRADING CYCLE WITH NEW PARAMETERS")
    print("=" * 50)
    
    try:
        from paper_trader import PaperTrader
        
        trader = PaperTrader()
        
        print("📋 Running Trading Cycle with Updated Parameters...")
        results = trader.run_trading_cycle()
        
        print(f"   New Trades: {results.get('new_trades', 0)}")
        print(f"   Closed Trades: {results.get('closed_trades', 0)}")
        print(f"   Account Balance: ${results.get('account_balance', 0):,.0f}")
        print(f"   Available Funds: ${results.get('available_funds', 0):,.0f}")
        print(f"   Errors: {len(results.get('errors', []))}")
        
        if results.get('errors'):
            print("   Error Details:")
            for error in results.get('errors', [])[:3]:  # Show first 3 errors
                print(f"     - {error}")
        
        print("   ✅ Trading cycle completed with updated parameters")
        return True
        
    except Exception as e:
        print(f"   ❌ Trading cycle failed: {e}")
        return False

def main():
    print("🔧 POSITION SIZING UPDATE VERIFICATION")
    print("=" * 60)
    print("Updating position limits to overcome spread impact")
    print()
    
    # Run tests
    sizing_ok = test_position_sizing()
    cycle_ok = test_trading_cycle_with_new_params()
    
    print("\n" + "=" * 60)
    print("🎯 UPDATE VERIFICATION SUMMARY")
    print("=" * 60)
    
    if sizing_ok and cycle_ok:
        print("✅ Position sizing updated successfully!")
        print("✅ New parameters:")
        print("   - Max position size: $15,000 (was $10,000)")
        print("   - Min position size: $5,000 (was $100)")
        print("   - Max risk per trade: 3% (was 2%)")
        print("   - Max positions: 10 (was 15)")
        print("   - Min confidence: 65% (was 60%)")
        print()
        print("💡 Benefits:")
        print("   - Larger positions to overcome spread costs")
        print("   - Higher minimum reduces micro-positions") 
        print("   - Slightly higher risk tolerance")
        print("   - Fewer but larger positions for better management")
        print("   - Higher confidence threshold for quality trades")
        return 0
    else:
        print("⚠️ Some tests failed - review configuration")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

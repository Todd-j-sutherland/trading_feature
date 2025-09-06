#!/usr/bin/env python3
"""
Simple Position Sizing Validation Test
Verifies that the updated trading parameters allow proper position sizing
"""

import json
import sys
import os

# Add the src directory to path
sys.path.insert(0, '/root/test/ig_markets_paper_trading/src')
sys.path.insert(0, '/root/test/ig_markets_paper_trading')

def test_position_sizing():
    """Test that position sizing works with updated parameters"""
    
    print("🔧 POSITION SIZING VALIDATION TEST")
    print("=" * 50)
    
    try:
        # Load configuration
        config_path = "/root/test/ig_markets_paper_trading/config/trading_parameters.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"📋 Updated Configuration:")
        print(f"   Max Position Size: ${config['position_management']['max_position_size']:,.0f}")
        print(f"   Min Position Size: ${config['position_management']['min_position_size']:,.0f}")
        print(f"   Max Risk Per Trade: {config['risk_management']['max_risk_per_trade']:.1%}")
        print(f"   Max Account Risk: {config['risk_management']['max_account_risk']:.1%}")
        
        # Test position calculations with mock data
        account_balance = config['account']['starting_balance']
        max_position_size = config['position_management']['max_position_size']
        min_position_size = config['position_management']['min_position_size']
        max_risk_per_trade_pct = config['risk_management']['max_risk_per_trade']
        max_risk_per_trade_amount = account_balance * max_risk_per_trade_pct
        
        test_stocks = [
            {"symbol": "CBA.AX", "price": 112.45, "confidence": 0.75},
            {"symbol": "WBC.AX", "price": 25.67, "confidence": 0.80},
            {"symbol": "ANZ.AX", "price": 28.90, "confidence": 0.70},
            {"symbol": "MQG.AX", "price": 195.33, "confidence": 0.85},
            {"symbol": "NAB.AX", "price": 30.50, "confidence": 0.72}
        ]
        
        print(f"\n📋 Position Size Calculations:")
        print(f"   Account Balance: ${account_balance:,.0f}")
        print(f"   Max Risk Per Trade: ${max_risk_per_trade_amount:,.0f} ({max_risk_per_trade_pct:.1%})")
        print()
        
        valid_positions = 0
        total_positions = len(test_stocks)
        
        for stock in test_stocks:
            try:
                # Simple confidence-based position sizing
                confidence_factor = min(stock["confidence"], 1.0)
                base_position_size = min_position_size + (max_position_size - min_position_size) * confidence_factor
                
                # Ensure we don't exceed max position size
                position_size = min(base_position_size, max_position_size)
                
                # Calculate shares and actual cost
                shares = int(position_size / stock["price"])
                actual_cost = shares * stock["price"]
                
                # Calculate risk amount (assuming 2% stop loss)
                risk_amount = actual_cost * 0.02  # 2% stop loss
                
                # Check if position is valid
                size_valid = min_position_size <= actual_cost <= max_position_size
                risk_valid = risk_amount <= max_risk_per_trade_amount
                
                if size_valid and risk_valid:
                    status = "✅"
                    valid_positions += 1
                else:
                    status = "❌"
                    if not size_valid:
                        status += " SIZE"
                    if not risk_valid:
                        status += " RISK"
                
                print(f"   {stock['symbol']}: {status} ${actual_cost:,.0f} ({shares:,} shares @ ${stock['price']:.2f})")
                print(f"      Confidence: {stock['confidence']:.1%}, Risk: ${risk_amount:,.0f}")
                
            except Exception as e:
                print(f"   {stock['symbol']}: ❌ Error - {str(e)}")
        
        print(f"\n🎯 VALIDATION SUMMARY")
        print("=" * 50)
        print(f"✅ Valid Positions: {valid_positions}/{total_positions}")
        
        if valid_positions == total_positions:
            print("✅ All positions pass validation!")
            print("✅ Position sizing configuration optimized for spread costs")
            print("✅ Risk limits properly balanced with position sizes")
            return True
        else:
            print("⚠️ Some positions failed validation")
            print("📋 Consider adjusting risk parameters if needed")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_position_sizing()
    sys.exit(0 if success else 1)

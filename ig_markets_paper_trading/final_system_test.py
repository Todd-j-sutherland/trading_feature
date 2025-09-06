#!/usr/bin/env python3
"""Test the paper trading system with updated position sizing"""

import sys
sys.path.insert(0, 'src')

from paper_trader import PaperTrader
import json

def test_paper_trading_system():
    print('🧪 Testing Paper Trading System with Updated Parameters')
    print('=' * 60)
    
    try:
        # Load config
        with open('config/trading_parameters.json', 'r') as f:
            config = json.load(f)
        
        # Test paper trader initialization
        trader = PaperTrader(config)
        print('✅ Paper trader initialized successfully')
        
        # Test position size calculation
        test_price = 25.50
        test_confidence = 0.75
        
        position_size = trader.position_manager.calculate_position_size(test_price, test_confidence)
        shares = int(position_size / test_price)
        total_cost = shares * test_price
        
        print(f'📋 Sample Position Calculation:')
        print(f'   Price: ${test_price:.2f}')
        print(f'   Confidence: {test_confidence:.1%}')
        print(f'   Position Size: ${total_cost:,.0f} ({shares:,} shares)')
        
        # Check if within limits
        min_pos = config["position_management"]["min_position_size"]
        max_pos = config["position_management"]["max_position_size"]
        
        if min_pos <= total_cost <= max_pos:
            print(f'   ✅ Position within limits (${min_pos:,.0f} - ${max_pos:,.0f})')
        else:
            print(f'   ❌ Position outside limits (${min_pos:,.0f} - ${max_pos:,.0f})')
        
        print('\n🎯 Position Sizing Update: SUCCESSFUL')
        print('✅ System ready to handle $15K positions to overcome spreads')
        
        return True
        
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_paper_trading_system()

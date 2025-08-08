#!/usr/bin/env python3
"""
Simple test script for paper trading simulator
"""

import sys
import os
sys.path.append('.')

try:
    from app.core.trading.paper_trading_simulator import PaperTradingSimulator
    
    print("🧪 Testing Paper Trading Simulator")
    print("=" * 50)
    
    # Initialize simulator
    print("⚙️ Initializing simulator...")
    simulator = PaperTradingSimulator(initial_capital=50000.0)
    
    # Test performance metrics
    print("📊 Testing performance metrics...")
    metrics = simulator.get_performance_metrics()
    
    if 'error' in metrics:
        print(f"❌ Error: {metrics['error']}")
    else:
        print("✅ Performance metrics working!")
        print(f"   Initial Capital: ${metrics['initial_capital']:,.2f}")
        print(f"   Portfolio Value: ${metrics['portfolio_value']:,.2f}")
        print(f"   Active Positions: {metrics['active_positions']}")
    
    # Test price retrieval
    print("\n💰 Testing price retrieval...")
    price = simulator.get_current_price('CBA.AX')
    print(f"   CBA.AX price: ${price:.2f}")
    
    print("\n✅ Basic tests completed successfully!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This indicates missing dependencies")
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
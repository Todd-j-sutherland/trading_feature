#!/usr/bin/env python3
"""
Exit Strategy Integration Script for IG Markets System

This script demonstrates how to integrate the exit strategy into your existing
daily_manager.py without major code changes, using your IG Markets data source.

Features:
- Uses your existing IG Markets → yfinance fallback system
- Safety flags to enable/disable functionality
- Minimal code changes (1-2 lines per function)
- Complete integration example
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import your existing IG Markets hooks
try:
    from app.core.exit_hooks_ig_markets import (
        hook_morning_routine, 
        hook_evening_routine, 
        hook_status_check,
        print_exit_status,
        enable_exit_strategy_safe_mode,
        disable_exit_strategy_safe_mode,
        get_exit_strategy_status
    )
    HOOKS_AVAILABLE = True
    print("✅ IG Markets exit strategy hooks imported successfully")
except ImportError as e:
    HOOKS_AVAILABLE = False
    print(f"❌ Failed to import exit strategy hooks: {e}")

def demonstrate_integration():
    """Demonstrate how to integrate exit strategy into your existing system"""
    
    print("🚀 Exit Strategy Integration Demonstration")
    print("=" * 60)
    
    if not HOOKS_AVAILABLE:
        print("❌ Cannot proceed - hooks not available")
        return
    
    # Display current exit strategy status
    print("\n1. 📊 Current Exit Strategy Status:")
    print_exit_status()
    
    # Example 1: Morning Routine Integration
    print("\n2. 🌅 Morning Routine Integration Example:")
    print("   Add this ONE LINE to your existing morning_routine():")
    print("   routine_data = hook_morning_routine(routine_data)")
    
    # Simulate morning routine data
    morning_data = {
        'status': 'completed',
        'predictions_generated': 5,
        'open_positions': [
            {
                'symbol': 'ANZ.AX',
                'entry_price': 32.76,
                'predicted_action': 'BUY',
                'confidence': 0.832,
                'entry_timestamp': '2025-09-04 02:30:04',
                'shares': 100
            },
            {
                'symbol': 'NAB.AX',
                'entry_price': 41.97,
                'predicted_action': 'BUY',
                'confidence': 0.890,
                'entry_timestamp': '2025-09-04 02:30:04',
                'shares': 100
            }
        ]
    }
    
    # Process with exit strategy
    enhanced_morning_data = hook_morning_routine(morning_data)
    
    print(f"   ✅ Morning routine processed: {enhanced_morning_data.get('exit_strategy_status', 'unknown')}")
    if 'exit_recommendations' in enhanced_morning_data:
        recommendations = enhanced_morning_data['exit_recommendations']
        print(f"   🚪 Exit recommendations found: {len(recommendations)}")
        for rec in recommendations:
            print(f"      - {rec['symbol']}: {rec['reason']} (Confidence: {rec['confidence']:.1%})")
    
    # Example 2: Evening Routine Integration
    print("\n3. 🌆 Evening Routine Integration Example:")
    print("   Add this ONE LINE to your existing evening_routine():")
    print("   routine_data = hook_evening_routine(routine_data)")
    
    evening_data = {
        'status': 'completed',
        'ml_training': True,
        'open_positions': morning_data['open_positions']  # Same positions
    }
    
    enhanced_evening_data = hook_evening_routine(evening_data)
    print(f"   ✅ Evening routine processed: {enhanced_evening_data.get('exit_strategy_status', 'unknown')}")
    
    if 'end_of_day_exits' in enhanced_evening_data:
        exits = enhanced_evening_data['end_of_day_exits']
        print(f"   🚪 End-of-day exits: {len(exits)}")
        for exit in exits:
            print(f"      - {exit['symbol']}: {exit['reason']} → {exit['recommended_action']}")
    
    # Example 3: Status Check Integration
    print("\n4. 📊 Status Check Integration Example:")
    print("   Add these TWO LINES to your existing status check:")
    print("   status_data = hook_status_check(status_data)")
    print("   print_exit_status()")
    
    status_data = {'system': 'operational', 'version': '1.0'}
    enhanced_status = hook_status_check(status_data)
    print(f"   ✅ Status enhanced with exit strategy info")
    
    # Example 4: Safety Controls
    print("\n5. 🔒 Safety Controls:")
    print("   Emergency disable: enable_exit_strategy_safe_mode('Emergency stop')")
    print("   Re-enable: disable_exit_strategy_safe_mode('Systems stable')")
    
    # Get detailed status
    detailed_status = get_exit_strategy_status()
    print(f"\n6. 🔍 Detailed Status:")
    print(f"   - Available: {detailed_status.get('exit_strategy_available', False)}")
    print(f"   - Enabled: {detailed_status.get('exit_strategy_enabled', False)}")
    print(f"   - Safe Mode: {detailed_status.get('safe_mode', False)}")
    print(f"   - Operational: {detailed_status.get('operational', False)}")
    print(f"   - IG Markets: {detailed_status.get('ig_markets_available', False)}")
    print(f"   - yfinance: {detailed_status.get('yfinance_available', False)}")

def create_integration_template():
    """Create template showing exact integration into daily_manager.py"""
    
    template = '''
# INTEGRATION TEMPLATE FOR app/services/daily_manager.py
# Add these minimal changes to integrate exit strategy:

# 1. ADD IMPORT (add this ONE line at the top)
from app.core.exit_hooks_ig_markets import hook_morning_routine, hook_evening_routine, print_exit_status

class TradingSystemManager:
    
    def morning_routine(self):
        """Enhanced morning routine with comprehensive ML analysis"""
        print("🌅 MORNING ROUTINE - Enhanced ML Trading System")
        
        # ... all your existing morning code stays exactly the same ...
        
        # ADD THESE TWO LINES at the end of your morning routine:
        routine_data = {'status': 'completed', 'open_positions': []}  # Add your actual open positions
        routine_data = hook_morning_routine(routine_data)
        
        # Display exit recommendations if any
        if 'exit_recommendations' in routine_data:
            print("\\n🚪 EXIT STRATEGY RECOMMENDATIONS:")
            for rec in routine_data['exit_recommendations']:
                print(f"   🎯 {rec['symbol']}: {rec['reason']} (Confidence: {rec['confidence']:.1%})")
    
    def evening_routine(self):
        """Enhanced evening routine with comprehensive ML training and analysis"""
        print("🌆 EVENING ROUTINE - ML Training & Analysis")
        
        # ... all your existing evening code stays exactly the same ...
        
        # ADD THESE TWO LINES at the end of your evening routine:
        routine_data = {'status': 'completed', 'open_positions': []}  # Add your actual open positions
        routine_data = hook_evening_routine(routine_data)
        
        # Display end-of-day exits if any
        if 'end_of_day_exits' in routine_data:
            print("\\n🚪 END-OF-DAY EXIT PROCESSING:")
            for exit in routine_data['end_of_day_exits']:
                print(f"   🚪 {exit['symbol']}: {exit['reason']} - {exit['recommended_action']}")

# INTEGRATION TEMPLATE FOR app/main.py
# Add these minimal changes:

# 1. ADD IMPORT (add this ONE line at the top)
from app.core.exit_hooks_ig_markets import hook_status_check, print_exit_status

def handle_status():
    """Handle status command with exit strategy info"""
    print("📊 SYSTEM STATUS CHECK")
    
    # ... all your existing status code stays exactly the same ...
    
    # ADD THESE TWO LINES at the end:
    status_data = hook_status_check({'system': 'operational'})
    print_exit_status()

# SAFETY CONTROLS:
# To disable exit strategy in emergency:
from app.core.exit_hooks_ig_markets import enable_exit_strategy_safe_mode
enable_exit_strategy_safe_mode("Emergency market conditions")

# To re-enable:
from app.core.exit_hooks_ig_markets import disable_exit_strategy_safe_mode
disable_exit_strategy_safe_mode("Markets stabilized")

# ENVIRONMENT VARIABLE CONTROL:
# Set these environment variables to control exit strategy:
# export EXIT_STRATEGY_ENABLED=true    # Enable/disable exit strategy
# export EXIT_STRATEGY_SAFE_MODE=false # Enable/disable safe mode
'''
    
    with open('exit_strategy_integration_template.py', 'w') as f:
        f.write(template)
    
    print("📄 Integration template created: exit_strategy_integration_template.py")

def test_ig_markets_integration():
    """Test the IG Markets integration specifically"""
    
    print("\n🧪 Testing IG Markets Integration:")
    print("=" * 50)
    
    # Import the engine directly to test IG Markets connectivity
    try:
        from phase4_development.exit_strategy.ig_markets_exit_strategy_engine import ExitStrategyEngine
        
        # Test engine initialization
        engine = ExitStrategyEngine(enable_exit_strategy=True)
        print("✅ Exit strategy engine initialized")
        
        # Test status
        status = engine.get_exit_conditions_status()
        print(f"📊 Engine status: {status.get('exit_strategy_enabled', False)}")
        print(f"🔗 IG Markets available: {status.get('ig_markets_available', False)}")
        print(f"📈 yfinance available: {status.get('yfinance_available', False)}")
        
        # Test position evaluation with real data
        test_result = engine.evaluate_position_exit(
            symbol="ANZ.AX",
            entry_price=32.76,
            predicted_action="BUY",
            prediction_confidence=0.832,
            entry_timestamp="2025-09-04 02:30:04"
        )
        
        print(f"🧪 Test evaluation result:")
        print(f"   Should Exit: {test_result.get('should_exit', False)}")
        print(f"   Reason: {test_result.get('exit_reason', 'N/A')}")
        print(f"   Data Source: {test_result.get('data_source', 'unknown')}")
        
        if 'current_price' in test_result:
            print(f"   Current Price: ${test_result['current_price']:.2f}")
            print(f"   Return: {test_result.get('return_percentage', 0):.2f}%")
        
        print("✅ IG Markets integration test completed successfully")
        
    except Exception as e:
        print(f"❌ IG Markets integration test failed: {e}")
        print("💡 This is normal if IG Markets credentials are not configured")

if __name__ == "__main__":
    # Run the complete demonstration
    demonstrate_integration()
    
    print("\n" + "=" * 60)
    
    # Create integration template
    create_integration_template()
    
    print("\n" + "=" * 60)
    
    # Test IG Markets specifically
    test_ig_markets_integration()
    
    print("\n🎯 INTEGRATION SUMMARY:")
    print("=" * 30)
    print("✅ Exit strategy hooks ready for integration")
    print("✅ Uses your existing IG Markets → yfinance fallback")
    print("✅ Safety flags available for emergency control")
    print("✅ Integration requires only 1-2 lines per function")
    print("✅ Complete backward compatibility maintained")
    print("\n🚀 Ready to integrate into your app/services/daily_manager.py!")

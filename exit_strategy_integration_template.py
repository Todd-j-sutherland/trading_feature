
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
            print("\n🚪 EXIT STRATEGY RECOMMENDATIONS:")
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
            print("\n🚪 END-OF-DAY EXIT PROCESSING:")
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

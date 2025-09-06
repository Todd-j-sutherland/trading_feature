#!/usr/bin/env python3
"""
Main Application Integration Hooks

This module provides minimal integration hooks for IG Markets credentials
and exit strategy plugins with your existing main application.

Plugin approach: 1-3 line additions to existing code for maximum compatibility.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# Import plugins
try:
    from app.core.data.collectors.ig_markets_credentials_plugin import (
        activate_ig_markets_credentials, 
        validate_ig_markets_credentials,
        get_ig_markets_plugin_status
    )
    IG_CREDENTIALS_PLUGIN_AVAILABLE = True
except ImportError:
    IG_CREDENTIALS_PLUGIN_AVAILABLE = False

try:
    from app.core.exit_strategy_plugin import (
        activate_exit_strategy,
        process_morning_exits,
        process_evening_exits, 
        get_exit_strategy_status,
        is_market_hours
    )
    EXIT_STRATEGY_PLUGIN_AVAILABLE = True
except ImportError:
    EXIT_STRATEGY_PLUGIN_AVAILABLE = False

class MainAppIntegration:
    """
    Integration layer for plugins with main application
    """
    
    def __init__(self):
        self.plugins_initialized = False
        self.ig_credentials_active = False
        self.exit_strategy_active = False
    
    def initialize_plugins(self) -> Dict[str, bool]:
        """
        Initialize all available plugins
        
        Returns:
            Dictionary of plugin initialization results
        """
        results = {}
        
        try:
            # Initialize IG Markets credentials plugin
            if IG_CREDENTIALS_PLUGIN_AVAILABLE:
                self.ig_credentials_active = activate_ig_markets_credentials()
                results['ig_credentials'] = self.ig_credentials_active
                
                if self.ig_credentials_active:
                    logger.info("✅ IG Markets credentials plugin initialized")
                    
                    # Validate credentials
                    validation = validate_ig_markets_credentials()
                    if validation['status'] == 'success':
                        logger.info(f"🎯 IG Markets authenticated: Account {validation['account_id']}")
                    else:
                        logger.warning(f"⚠️ IG Markets validation failed: {validation['error']}")
                else:
                    logger.warning("❌ IG Markets credentials plugin failed to initialize")
            else:
                results['ig_credentials'] = False
                logger.info("📊 IG Markets credentials plugin not available")
            
            # Initialize exit strategy plugin
            if EXIT_STRATEGY_PLUGIN_AVAILABLE:
                self.exit_strategy_active = activate_exit_strategy()
                results['exit_strategy'] = self.exit_strategy_active
                
                if self.exit_strategy_active:
                    logger.info("✅ Exit strategy plugin initialized")
                    
                    # Check market hours status
                    market_status = is_market_hours()
                    logger.info(f"📊 Market hours active: {market_status}")
                else:
                    logger.warning("❌ Exit strategy plugin failed to initialize")
            else:
                results['exit_strategy'] = False
                logger.info("📊 Exit strategy plugin not available")
            
            self.plugins_initialized = True
            logger.info(f"🔌 Plugins initialized: {sum(results.values())}/{len(results)} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"Error initializing plugins: {e}")
            return {'error': str(e)}
    
    def enhance_morning_routine(self, routine_data: Dict) -> Dict:
        """
        Enhance morning routine with plugin functionality
        
        Args:
            routine_data: Standard morning routine data
        
        Returns:
            Enhanced routine data with plugin results
        """
        if not self.plugins_initialized:
            return routine_data
        
        try:
            # Add IG Markets status
            if self.ig_credentials_active:
                ig_status = get_ig_markets_plugin_status()
                routine_data['ig_markets_status'] = ig_status
                logger.debug("📊 IG Markets status added to morning routine")
            
            # Process exit strategy
            if self.exit_strategy_active:
                routine_data = process_morning_exits(routine_data)
                logger.debug("🚪 Exit strategy processing added to morning routine")
            
            # Add plugin summary
            routine_data['plugins'] = {
                'ig_credentials_active': self.ig_credentials_active,
                'exit_strategy_active': self.exit_strategy_active,
                'market_hours': is_market_hours() if EXIT_STRATEGY_PLUGIN_AVAILABLE else False
            }
            
            return routine_data
            
        except Exception as e:
            logger.error(f"Error enhancing morning routine: {e}")
            routine_data['plugin_error'] = str(e)
            return routine_data
    
    def enhance_evening_routine(self, routine_data: Dict) -> Dict:
        """
        Enhance evening routine with plugin functionality
        
        Args:
            routine_data: Standard evening routine data
        
        Returns:
            Enhanced routine data with plugin results
        """
        if not self.plugins_initialized:
            return routine_data
        
        try:
            # Process exit strategy for evening
            if self.exit_strategy_active:
                routine_data = process_evening_exits(routine_data)
                logger.debug("🌅 Exit strategy processing added to evening routine")
            
            # Add plugin summary
            routine_data['plugins'] = {
                'ig_credentials_active': self.ig_credentials_active,
                'exit_strategy_active': self.exit_strategy_active,
                'market_hours': is_market_hours() if EXIT_STRATEGY_PLUGIN_AVAILABLE else False
            }
            
            return routine_data
            
        except Exception as e:
            logger.error(f"Error enhancing evening routine: {e}")
            routine_data['plugin_error'] = str(e)
            return routine_data
    
    def enhance_status_check(self, status_data: Dict) -> Dict:
        """
        Enhance status check with plugin information
        
        Args:
            status_data: Standard status data
        
        Returns:
            Enhanced status data with plugin information
        """
        try:
            # Ensure status_data is a dictionary
            if status_data is None:
                status_data = {}
            
            # Add IG Markets status
            if IG_CREDENTIALS_PLUGIN_AVAILABLE:
                ig_status = get_ig_markets_plugin_status()
                status_data['ig_markets'] = ig_status
            
            # Add exit strategy status
            if EXIT_STRATEGY_PLUGIN_AVAILABLE:
                exit_status = get_exit_strategy_status()
                status_data['exit_strategy'] = exit_status
            
            # Add overall plugin status
            status_data['plugins'] = {
                'initialized': self.plugins_initialized,
                'ig_credentials_active': self.ig_credentials_active,
                'exit_strategy_active': self.exit_strategy_active,
                'available_plugins': {
                    'ig_credentials': IG_CREDENTIALS_PLUGIN_AVAILABLE,
                    'exit_strategy': EXIT_STRATEGY_PLUGIN_AVAILABLE
                }
            }
            
            return status_data
            
        except Exception as e:
            logger.error(f"Error enhancing status check: {e}")
            return status_data or {'plugin_error': str(e)}
    
    def get_plugin_summary(self) -> Dict[str, Any]:
        """Get comprehensive plugin status summary"""
        return {
            'plugins_initialized': self.plugins_initialized,
            'ig_credentials': {
                'available': IG_CREDENTIALS_PLUGIN_AVAILABLE,
                'active': self.ig_credentials_active,
                'status': get_ig_markets_plugin_status() if IG_CREDENTIALS_PLUGIN_AVAILABLE else None
            },
            'exit_strategy': {
                'available': EXIT_STRATEGY_PLUGIN_AVAILABLE,
                'active': self.exit_strategy_active,
                'status': get_exit_strategy_status() if EXIT_STRATEGY_PLUGIN_AVAILABLE else None
            },
            'market_context': {
                'market_hours': is_market_hours() if EXIT_STRATEGY_PLUGIN_AVAILABLE else None,
                'ig_markets_prioritized': self.ig_credentials_active
            }
        }

# Global integration instance
main_app_integration = MainAppIntegration()

# Convenience functions for minimal integration
def initialize_app_plugins() -> Dict[str, bool]:
    """Initialize all available plugins - ONE LINE INTEGRATION"""
    return main_app_integration.initialize_plugins()

def enhance_morning_routine(routine_data: Dict) -> Dict:
    """Enhance morning routine with plugins - ONE LINE INTEGRATION"""
    return main_app_integration.enhance_morning_routine(routine_data)

def enhance_evening_routine(routine_data: Dict) -> Dict:
    """Enhance evening routine with plugins - ONE LINE INTEGRATION"""
    return main_app_integration.enhance_evening_routine(routine_data)

def enhance_status_check(status_data: Dict) -> Dict:
    """Enhance status check with plugin info - ONE LINE INTEGRATION"""
    return main_app_integration.enhance_status_check(status_data)

def print_plugin_summary():
    """Print comprehensive plugin status"""
    summary = main_app_integration.get_plugin_summary()
    
    print("\n" + "="*50)
    print("🔌 PLUGIN STATUS SUMMARY")
    print("="*50)
    
    # IG Markets status
    ig_status = summary['ig_credentials']
    ig_emoji = "✅" if ig_status['active'] else "❌" if ig_status['available'] else "📊"
    print(f"{ig_emoji} IG Markets Credentials: {ig_status['active']} (Available: {ig_status['available']})")
    
    if ig_status['status'] and ig_status['active']:
        print(f"   📈 Environment Variables: {ig_status['status']['environment_variables_set']}")
        print(f"   🎯 Demo Mode: {ig_status['status']['demo_mode']}")
    
    # Exit Strategy status  
    exit_status = summary['exit_strategy']
    exit_emoji = "✅" if exit_status['active'] else "❌" if exit_status['available'] else "📊"
    print(f"{exit_emoji} Exit Strategy: {exit_status['active']} (Available: {exit_status['available']})")
    
    if exit_status['status'] and exit_status['active']:
        print(f"   ⏰ Market Hours: {exit_status['status']['market_hours']}")
        print(f"   🎯 Engine Enabled: {exit_status['status']['engine_enabled']}")
    
    # Market context
    market_context = summary['market_context']
    if market_context['market_hours'] is not None:
        market_emoji = "🔔" if market_context['market_hours'] else "🔕"
        print(f"{market_emoji} Market Hours Active: {market_context['market_hours']}")
    
    if market_context['ig_markets_prioritized']:
        print("🎯 Data Source Priority: IG Markets → yfinance fallback")
    else:
        print("📊 Data Source: yfinance only")

# MINIMAL INTEGRATION EXAMPLES FOR YOUR EXISTING CODE:

def integrate_with_main_enhanced():
    """
    Example integration with main_enhanced.py
    
    Add these lines to your existing main_enhanced.py:
    """
    integration_code = '''
# ADD TO IMPORTS:
from app.core.main_app_integration import initialize_app_plugins, enhance_morning_routine, enhance_status_check, print_plugin_summary

# ADD TO main() function start:
def main():
    # ... existing code ...
    
    # ONE LINE PLUGIN INITIALIZATION
    plugin_results = initialize_app_plugins()
    
    # ... rest of existing code ...

# ADD TO morning routine command:
elif args.command == 'market-morning':
    print("🚀 Starting Market-Aware Morning Routine...")
    manager = create_market_aware_manager(config_path=args.config, dry_run=args.dry_run)
    routine_data = manager.enhanced_morning_routine()
    
    # ONE LINE ENHANCEMENT
    routine_data = enhance_morning_routine(routine_data)
    
# ADD TO status command:
elif args.command == 'market-status':
    manager = create_market_aware_manager(config_path=args.config, dry_run=args.dry_run)
    status_data = manager.quick_market_status()
    
    # ONE LINE ENHANCEMENT
    status_data = enhance_status_check(status_data)
    
    # ONE LINE PLUGIN STATUS
    print_plugin_summary()
    '''
    
    return integration_code

if __name__ == "__main__":
    # Test the integration
    logging.basicConfig(level=logging.INFO)
    
    print("🔌 Main App Integration Test")
    print("=" * 50)
    
    # Test plugin initialization
    print("⚡ Initializing plugins...")
    results = initialize_app_plugins()
    
    print(f"📊 Plugin Results: {results}")
    
    # Test routine enhancement
    sample_routine_data = {
        'status': 'completed',
        'open_positions': [{
            'symbol': 'CBA.AX',
            'entry_price': 100.50,
            'predicted_action': 'BUY',
            'prediction_confidence': 0.75,
            'entry_timestamp': '2025-09-05T09:30:00'
        }]
    }
    
    print(f"\n🌅 Testing morning routine enhancement...")
    enhanced_routine = enhance_morning_routine(sample_routine_data)
    
    if 'exit_strategy' in enhanced_routine:
        exit_data = enhanced_routine['exit_strategy']
        print(f"   Exit Strategy Results: {len(exit_data.get('exit_recommendations', []))} recommendations")
    
    # Show comprehensive status
    print_plugin_summary()
    
    print(f"\n" + "="*50)
    print("INTEGRATION CODE FOR main_enhanced.py:")
    print("="*50)
    print(integrate_with_main_enhanced())

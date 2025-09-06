"""
Exit Strategy Hook Integration System (IG Markets Compatible)

This module provides minimal-impact hooks to integrate Phase 4 exit strategy
into your existing app/* code without requiring major changes.

Features:
- Hooks for morning/evening routines using your IG Markets data source
- Status checking integration
- Prediction enhancement hooks
- Safety flags to enable/disable functionality
- Graceful degradation if exit strategy unavailable
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Try to import IG Markets-compatible exit strategy engine
try:
    from phase4_development.exit_strategy.ig_markets_exit_strategy_engine import ExitStrategyEngine
    EXIT_STRATEGY_AVAILABLE = True
except ImportError:
    EXIT_STRATEGY_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global safety flags - can be overridden by environment variables
EXIT_STRATEGY_ENABLED = os.getenv('EXIT_STRATEGY_ENABLED', 'true').lower() == 'true'
EXIT_STRATEGY_SAFE_MODE = os.getenv('EXIT_STRATEGY_SAFE_MODE', 'false').lower() == 'true'

class ExitStrategyHookManager:
    """
    Manages exit strategy hooks with safety controls and IG Markets integration
    """
    
    def __init__(self):
        """Initialize hook manager with safety controls"""
        self._engine = None
        self._initialized = False
        self._last_error = None
        self._safe_mode = EXIT_STRATEGY_SAFE_MODE
        
        # Initialize engine if available and enabled
        if EXIT_STRATEGY_AVAILABLE and EXIT_STRATEGY_ENABLED and not self._safe_mode:
            try:
                self._engine = ExitStrategyEngine(enable_exit_strategy=True)
                self._initialized = True
                logger.info("✅ Exit Strategy Hook Manager initialized with IG Markets support")
            except Exception as e:
                self._last_error = str(e)
                logger.warning(f"⚠️ Exit Strategy initialization failed: {e}")
                logger.info("🔒 Switching to safe mode")
                self._safe_mode = True
        else:
            reasons = []
            if not EXIT_STRATEGY_AVAILABLE:
                reasons.append("engine not available")
            if not EXIT_STRATEGY_ENABLED:
                reasons.append("disabled by flag")
            if self._safe_mode:
                reasons.append("safe mode enabled")
            logger.info(f"🔒 Exit Strategy disabled: {', '.join(reasons)}")
    
    def is_enabled(self) -> bool:
        """Check if exit strategy is enabled and operational"""
        return self._initialized and not self._safe_mode and self._engine is not None
    
    def enable_safe_mode(self, reason: str = "Manual override"):
        """Enable safe mode - disables all exit strategy functionality"""
        self._safe_mode = True
        if self._engine:
            self._engine.disable_exit_strategy(reason)
        logger.warning(f"🔒 SAFE MODE ENABLED: {reason}")
    
    def disable_safe_mode(self, reason: str = "Manual override"):
        """Disable safe mode - re-enables exit strategy functionality"""
        if EXIT_STRATEGY_AVAILABLE and EXIT_STRATEGY_ENABLED:
            try:
                if not self._engine:
                    self._engine = ExitStrategyEngine(enable_exit_strategy=True)
                    self._initialized = True
                else:
                    self._engine.enable_exit_strategy(reason)
                self._safe_mode = False
                logger.info(f"✅ SAFE MODE DISABLED: {reason}")
            except Exception as e:
                logger.error(f"Failed to disable safe mode: {e}")
                self._last_error = str(e)
        else:
            logger.warning("Cannot disable safe mode: exit strategy not available")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of exit strategy system"""
        status = {
            'exit_strategy_available': EXIT_STRATEGY_AVAILABLE,
            'exit_strategy_enabled': EXIT_STRATEGY_ENABLED,
            'safe_mode': self._safe_mode,
            'initialized': self._initialized,
            'operational': self.is_enabled(),
            'last_error': self._last_error
        }
        
        if self._engine:
            try:
                engine_status = self._engine.get_exit_conditions_status()
                status.update(engine_status)
            except Exception as e:
                status['engine_error'] = str(e)
        
        return status
    
    def process_morning_routine(self, routine_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process morning routine with exit strategy recommendations
        
        Args:
            routine_data: Dictionary containing morning routine data
            
        Returns:
            Enhanced routine data with exit recommendations
        """
        if not self.is_enabled():
            routine_data['exit_strategy_status'] = 'disabled'
            return routine_data
        
        try:
            # Get open positions that might need exit evaluation
            open_positions = routine_data.get('open_positions', [])
            
            if open_positions and self._engine:
                # Evaluate positions for exit recommendations
                exit_recommendations = []
                
                for position in open_positions:
                    try:
                        result = self._engine.evaluate_position_exit(
                            symbol=position.get('symbol'),
                            entry_price=position.get('entry_price'),
                            predicted_action=position.get('predicted_action', 'BUY'),
                            prediction_confidence=position.get('confidence', 0.5),
                            entry_timestamp=position.get('entry_timestamp'),
                            shares=position.get('shares', 100)
                        )
                        
                        if result.get('should_exit', False):
                            exit_recommendations.append({
                                'symbol': position.get('symbol'),
                                'reason': result.get('exit_reason'),
                                'confidence': result.get('exit_confidence', 0.0),
                                'urgency': result.get('urgency', 1),
                                'current_price': result.get('current_price'),
                                'return_pct': result.get('return_percentage', 0.0)
                            })
                            
                    except Exception as e:
                        logger.warning(f"Error evaluating position {position.get('symbol', 'unknown')}: {e}")
                
                routine_data['exit_recommendations'] = exit_recommendations
                routine_data['exit_strategy_status'] = 'active'
                
                logger.info(f"🚪 Morning routine: {len(exit_recommendations)} exit recommendations generated")
            else:
                routine_data['exit_strategy_status'] = 'no_positions'
                
        except Exception as e:
            logger.error(f"Error in morning routine exit processing: {e}")
            routine_data['exit_strategy_status'] = 'error'
            routine_data['exit_error'] = str(e)
            self._last_error = str(e)
        
        return routine_data
    
    def process_evening_routine(self, routine_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process evening routine with end-of-day exit processing
        
        Args:
            routine_data: Dictionary containing evening routine data
            
        Returns:
            Enhanced routine data with end-of-day exit actions
        """
        if not self.is_enabled():
            routine_data['exit_strategy_status'] = 'disabled'
            return routine_data
        
        try:
            # Process end-of-day exits
            open_positions = routine_data.get('open_positions', [])
            end_of_day_exits = []
            
            if open_positions and self._engine:
                for position in open_positions:
                    try:
                        # Check if position should be closed at end of day
                        result = self._engine.evaluate_position_exit(
                            symbol=position.get('symbol'),
                            entry_price=position.get('entry_price'),
                            predicted_action=position.get('predicted_action', 'BUY'),
                            prediction_confidence=position.get('confidence', 0.5),
                            entry_timestamp=position.get('entry_timestamp'),
                            shares=position.get('shares', 100)
                        )
                        
                        if result.get('should_exit', False):
                            end_of_day_exits.append({
                                'symbol': position.get('symbol'),
                                'reason': result.get('exit_reason'),
                                'recommended_action': 'EXIT',
                                'confidence': result.get('exit_confidence', 0.0),
                                'final_price': result.get('current_price'),
                                'total_return': result.get('return_percentage', 0.0)
                            })
                            
                    except Exception as e:
                        logger.warning(f"Error processing evening exit for {position.get('symbol', 'unknown')}: {e}")
                
                routine_data['end_of_day_exits'] = end_of_day_exits
                routine_data['exit_strategy_status'] = 'active'
                
                logger.info(f"🌆 Evening routine: {len(end_of_day_exits)} end-of-day exits processed")
            else:
                routine_data['exit_strategy_status'] = 'no_positions'
                
        except Exception as e:
            logger.error(f"Error in evening routine exit processing: {e}")
            routine_data['exit_strategy_status'] = 'error'
            routine_data['exit_error'] = str(e)
            self._last_error = str(e)
        
        return routine_data
    
    def process_status_check(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process status check with exit strategy information
        
        Args:
            status_data: Dictionary containing system status data
            
        Returns:
            Enhanced status data with exit strategy status
        """
        try:
            exit_status = self.get_status()
            status_data['exit_strategy'] = exit_status
            
            if self.is_enabled() and self._engine:
                # Add current exit conditions summary
                conditions_status = self._engine.get_exit_conditions_status()
                status_data['exit_conditions'] = conditions_status
                
        except Exception as e:
            logger.error(f"Error in status check exit processing: {e}")
            status_data['exit_strategy'] = {'error': str(e)}
            self._last_error = str(e)
        
        return status_data
    
    def enhance_prediction_data(self, prediction_data: Dict) -> Dict:
        """
        Enhance prediction data with exit strategy context
        
        Args:
            prediction_data: Dictionary containing prediction data
            
        Returns:
            Enhanced prediction data with exit strategy metadata
        """
        if not self.is_enabled():
            return prediction_data
        
        try:
            # Add exit strategy metadata to prediction
            prediction_data['exit_strategy_metadata'] = {
                'enabled': True,
                'profit_target_pct': 2.8,  # Based on your optimal strategy
                'stop_loss_pct': 2.0,
                'max_hold_hours': 18,
                'entry_timestamp': datetime.now().isoformat(),
                'exit_engine_version': 'ig_markets_v1.0'
            }
            
        except Exception as e:
            logger.warning(f"Error enhancing prediction data: {e}")
            self._last_error = str(e)
        
        return prediction_data

# Global instance for easy access
_hook_manager = None

def get_hook_manager() -> ExitStrategyHookManager:
    """Get global hook manager instance"""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = ExitStrategyHookManager()
    return _hook_manager

# Convenience functions for easy integration into existing code

def hook_morning_routine(routine_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hook for morning routine - add this ONE line to your existing morning routine:
    routine_data = hook_morning_routine(routine_data)
    """
    manager = get_hook_manager()
    return manager.process_morning_routine(routine_data)

def hook_evening_routine(routine_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hook for evening routine - add this ONE line to your existing evening routine:
    routine_data = hook_evening_routine(routine_data)
    """
    manager = get_hook_manager()
    return manager.process_evening_routine(routine_data)

def hook_status_check(status_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hook for status check - add this ONE line to your existing status check:
    status_data = hook_status_check(status_data)
    """
    manager = get_hook_manager()
    return manager.process_status_check(status_data)

def hook_prediction_save(prediction_data: Dict) -> Dict:
    """
    Hook for prediction save - add this ONE line before saving predictions:
    prediction_data = hook_prediction_save(prediction_data)
    """
    manager = get_hook_manager()
    return manager.enhance_prediction_data(prediction_data)

def print_exit_status():
    """
    Print exit strategy status - add this ONE line to status display:
    print_exit_status()
    """
    manager = get_hook_manager()
    status = manager.get_status()
    
    print("\n🚪 EXIT STRATEGY STATUS")
    print("=" * 40)
    
    if status['operational']:
        print("✅ Exit Strategy: ENABLED")
        print(f"📊 Data Source: {'IG Markets' if status.get('ig_markets_available') else 'yfinance'}")
        
        if 'exit_conditions' in status:
            conditions = status['exit_conditions']
            print(f"🎯 Profit Targets: {'✅' if conditions.get('profit_targets') else '❌'}")
            print(f"🛡️ Stop Losses: {'✅' if conditions.get('stop_losses') else '❌'}")
            print(f"⏰ Time Limits: {'✅' if conditions.get('time_limits') else '❌'}")
            print(f"📈 Technical Exits: {'✅' if conditions.get('technical_exits') else '❌'}")
    else:
        print("❌ Exit Strategy: DISABLED")
        if status.get('safe_mode'):
            print("🔒 Reason: Safe mode enabled")
        elif not status.get('exit_strategy_available'):
            print("🔒 Reason: Engine not available")
        elif not status.get('exit_strategy_enabled'):
            print("🔒 Reason: Disabled by flag")
            
        if status.get('last_error'):
            print(f"⚠️ Last Error: {status['last_error']}")

def enable_exit_strategy_safe_mode(reason: str = "Manual safety override"):
    """
    Emergency function to enable safe mode and disable all exit strategy functionality
    Usage: enable_exit_strategy_safe_mode("Market volatility detected")
    """
    manager = get_hook_manager()
    manager.enable_safe_mode(reason)
    print(f"🔒 Exit Strategy Safe Mode ENABLED: {reason}")

def disable_exit_strategy_safe_mode(reason: str = "Manual re-enable"):
    """
    Function to disable safe mode and re-enable exit strategy functionality
    Usage: disable_exit_strategy_safe_mode("Systems stable")
    """
    manager = get_hook_manager()
    manager.disable_safe_mode(reason)
    print(f"✅ Exit Strategy Safe Mode DISABLED: {reason}")

def get_exit_strategy_status() -> Dict[str, Any]:
    """
    Get detailed exit strategy status for programmatic access
    """
    manager = get_hook_manager()
    return manager.get_status()

# Environment variable configuration helpers
def set_exit_strategy_flag(enabled: bool):
    """Set exit strategy enabled flag"""
    global EXIT_STRATEGY_ENABLED
    EXIT_STRATEGY_ENABLED = enabled
    os.environ['EXIT_STRATEGY_ENABLED'] = 'true' if enabled else 'false'
    logger.info(f"Exit strategy flag set to: {enabled}")

def set_safe_mode_flag(safe_mode: bool):
    """Set safe mode flag"""
    global EXIT_STRATEGY_SAFE_MODE
    EXIT_STRATEGY_SAFE_MODE = safe_mode
    os.environ['EXIT_STRATEGY_SAFE_MODE'] = 'true' if safe_mode else 'false'
    logger.info(f"Safe mode flag set to: {safe_mode}")

# Example integration
if __name__ == "__main__":
    # Test the hook system
    print("🔧 Testing Exit Strategy Hook System")
    print("=" * 50)
    
    # Test status
    print_exit_status()
    
    # Test morning routine hook
    test_routine_data = {
        'status': 'completed',
        'open_positions': [
            {
                'symbol': 'ANZ.AX',
                'entry_price': 32.76,
                'predicted_action': 'BUY',
                'confidence': 0.832,
                'entry_timestamp': '2025-09-04 02:30:04',
                'shares': 100
            }
        ]
    }
    
    result = hook_morning_routine(test_routine_data)
    print(f"\n🌅 Morning routine result: {result.get('exit_strategy_status', 'unknown')}")
    
    if 'exit_recommendations' in result:
        print(f"🚪 Exit recommendations: {len(result['exit_recommendations'])}")
    
    print("\n✅ Hook system test completed")

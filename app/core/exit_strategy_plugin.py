#!/usr/bin/env python3
"""
Exit Strategy Plugin for Main Application

This plugin integrates the advanced exit strategy engine with your existing
main application during market hours. Provides BUY exit positions and
market-aware exit timing.

Plugin approach: Minimal integration, maximum compatibility.
"""

import logging
import os
from datetime import datetime, time, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add project paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the exit strategy engine
try:
    from phase4_development.exit_strategy.ig_markets_exit_strategy_engine import ExitStrategyEngine
    EXIT_STRATEGY_AVAILABLE = True
except ImportError:
    EXIT_STRATEGY_AVAILABLE = False

logger = logging.getLogger(__name__)

class ExitStrategyPlugin:
    """
    Plugin to integrate exit strategy with main application
    """
    
    def __init__(self):
        self.engine = None
        self.plugin_active = False
        self.market_hours = {
            'open': time(9, 30),   # ASX opens at 9:30 AM AEST
            'close': time(16, 10)  # ASX closes at 4:10 PM AEST
        }
        
        # Defer engine initialization until activation to avoid early logging
        self.engine = None
        self._engine_initialized = False
    
    def _initialize_engine(self):
        """Initialize the exit strategy engine if available and not already initialized"""
        if self._engine_initialized:
            return
            
        if EXIT_STRATEGY_AVAILABLE:
            try:
                self.engine = ExitStrategyEngine(enable_exit_strategy=True)
                logger.info("✅ Exit Strategy Engine loaded successfully")
                self._engine_initialized = True
            except Exception as e:
                logger.warning(f"Failed to initialize Exit Strategy Engine: {e}")
                self.engine = None
        else:
            logger.info("📊 Exit Strategy Engine not available")
            
        self._engine_initialized = True
    
    def activate(self) -> bool:
        """Activate the exit strategy plugin"""
        try:
            # Initialize engine first if not already done
            self._initialize_engine()
            
            if not self.engine:
                logger.warning("Exit Strategy Engine not available")
                return False
            
            # Set environment variable for exit strategy
            os.environ['EXIT_STRATEGY_ENABLED'] = 'true'
            os.environ['EXIT_STRATEGY_PLUGIN_ACTIVE'] = 'true'
            
            self.plugin_active = True
            logger.info("✅ Exit Strategy Plugin activated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to activate Exit Strategy Plugin: {e}")
            return False
    
    def is_market_hours(self) -> bool:
        """Check if current time is within ASX market hours"""
        try:
            # Get current time in AEST (ASX timezone)
            now = datetime.now()
            current_time = now.time()
            
            # Check if it's a weekday (Monday = 0, Sunday = 6)
            is_weekday = now.weekday() < 5
            
            # Check if within market hours
            is_trading_hours = self.market_hours['open'] <= current_time <= self.market_hours['close']
            
            return is_weekday and is_trading_hours
            
        except Exception as e:
            logger.warning(f"Could not determine market hours: {e}")
            return False
    
    def should_check_exits(self) -> bool:
        """Determine if exit checking should be performed"""
        # Ensure engine is initialized
        self._initialize_engine()
        
        if not self.plugin_active or not self.engine:
            return False
        
        # Check during market hours for BUY positions
        if self.is_market_hours():
            return True
        
        # Also check after hours for risk management
        return True
    
    def check_position_exits(self, positions: List[Dict]) -> List[Dict]:
        """
        Check exit conditions for a list of positions
        
        Args:
            positions: List of position dictionaries with keys:
                - symbol, entry_price, predicted_action, prediction_confidence, entry_timestamp
        
        Returns:
            List of exit recommendations
        """
        if not self.should_check_exits():
            return []
        
        try:
            exit_recommendations = []
            
            # Filter for BUY positions during market hours
            positions_to_check = positions
            if self.is_market_hours():
                # During market hours, prioritize BUY positions
                buy_positions = [p for p in positions if p.get('predicted_action') == 'BUY']
                positions_to_check = buy_positions if buy_positions else positions
            
            logger.info(f"🔍 Checking exit conditions for {len(positions_to_check)} positions...")
            
            # Evaluate each position
            for position in positions_to_check:
                try:
                    exit_result = self.engine.evaluate_position_exit(
                        symbol=position['symbol'],
                        entry_price=position['entry_price'],
                        predicted_action=position['predicted_action'],
                        prediction_confidence=position['prediction_confidence'],
                        entry_timestamp=position['entry_timestamp'],
                        shares=position.get('shares', 100)
                    )
                    
                    if exit_result.get('should_exit', False):
                        exit_recommendation = {
                            'symbol': position['symbol'],
                            'action': 'EXIT',
                            'reason': exit_result['exit_reason'],
                            'confidence': exit_result['exit_confidence'],
                            'current_price': exit_result.get('current_price'),
                            'return_percentage': exit_result.get('return_percentage'),
                            'urgency': exit_result.get('urgency', 1),
                            'details': exit_result.get('details', ''),
                            'data_source': exit_result.get('data_source', 'unknown'),
                            'market_hours': self.is_market_hours(),
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        exit_recommendations.append(exit_recommendation)
                        
                        # Log high-priority exits
                        if exit_result.get('urgency', 1) >= 4:
                            logger.warning(f"🚨 HIGH PRIORITY EXIT: {position['symbol']} - {exit_result['exit_reason']}")
                        else:
                            logger.info(f"🚪 Exit recommendation: {position['symbol']} - {exit_result['exit_reason']}")
                
                except Exception as e:
                    logger.error(f"Error evaluating exit for {position.get('symbol', 'unknown')}: {e}")
            
            return exit_recommendations
            
        except Exception as e:
            logger.error(f"Error in check_position_exits: {e}")
            return []
    
    def process_morning_routine_exits(self, morning_routine_data: Dict) -> Dict:
        """
        Process exit checks during morning routine
        
        Args:
            morning_routine_data: Data from morning routine including positions
        
        Returns:
            Updated routine data with exit recommendations
        """
        if not self.should_check_exits():
            return morning_routine_data
        
        try:
            # Extract positions from morning routine data
            positions = morning_routine_data.get('open_positions', [])
            
            if not positions:
                logger.info("📊 No open positions to check for exits")
                return morning_routine_data
            
            # Check exit conditions
            exit_recommendations = self.check_position_exits(positions)
            
            # Add exit data to routine results
            morning_routine_data['exit_strategy'] = {
                'enabled': True,
                'market_hours': self.is_market_hours(),
                'positions_checked': len(positions),
                'exit_recommendations': exit_recommendations,
                'high_priority_exits': [r for r in exit_recommendations if r['urgency'] >= 4]
            }
            
            # Log summary
            if exit_recommendations:
                logger.info(f"🎯 Morning routine: {len(exit_recommendations)} exit recommendations generated")
                for rec in exit_recommendations:
                    if rec['urgency'] >= 4:
                        logger.warning(f"   ⚠️ HIGH PRIORITY: {rec['symbol']} - {rec['reason']}")
                    else:
                        logger.info(f"   📊 {rec['symbol']} - {rec['reason']} ({rec['return_percentage']:+.2f}%)")
            else:
                logger.info("📊 Morning routine: No exit conditions met, holding positions")
            
            return morning_routine_data
            
        except Exception as e:
            logger.error(f"Error in process_morning_routine_exits: {e}")
            return morning_routine_data
    
    def process_evening_routine_exits(self, evening_routine_data: Dict) -> Dict:
        """
        Process exit checks during evening routine
        
        Args:
            evening_routine_data: Data from evening routine including positions
        
        Returns:
            Updated routine data with exit recommendations  
        """
        if not self.should_check_exits():
            return evening_routine_data
        
        try:
            # Extract positions from evening routine data
            positions = evening_routine_data.get('open_positions', [])
            
            if not positions:
                return evening_routine_data
            
            # Check exit conditions (focus on risk management after hours)
            exit_recommendations = self.check_position_exits(positions)
            
            # Add exit data to routine results
            evening_routine_data['exit_strategy'] = {
                'enabled': True,
                'market_hours': self.is_market_hours(),
                'positions_checked': len(positions),
                'exit_recommendations': exit_recommendations,
                'risk_management_exits': [r for r in exit_recommendations if 'RISK' in r['reason'] or 'STOP_LOSS' in r['reason']]
            }
            
            # Log evening summary
            if exit_recommendations:
                logger.info(f"🌅 Evening routine: {len(exit_recommendations)} exit recommendations for tomorrow")
            
            return evening_routine_data
            
        except Exception as e:
            logger.error(f"Error in process_evening_routine_exits: {e}")
            return evening_routine_data
    
    def get_exit_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive exit strategy status"""
        try:
            # Ensure engine is initialized for status queries
            self._initialize_engine()
            
            base_status = {
                'plugin_active': self.plugin_active,
                'exit_strategy_available': EXIT_STRATEGY_AVAILABLE,
                'engine_enabled': self.engine.is_enabled() if self.engine else False,
                'market_hours': self.is_market_hours(),
                'current_time': datetime.now().isoformat(),
                'market_open': self.market_hours['open'].strftime('%H:%M'),
                'market_close': self.market_hours['close'].strftime('%H:%M')
            }
            
            if self.engine:
                # Get engine status
                engine_status = self.engine.get_exit_conditions_status()
                base_status.update({
                    'exit_conditions': engine_status['exit_conditions'],
                    'configuration': engine_status['configuration'],
                    'data_sources': {
                        'ig_markets_available': engine_status['ig_markets_available'],
                        'yfinance_available': engine_status['yfinance_available']
                    }
                })
            
            return base_status
            
        except Exception as e:
            logger.error(f"Error getting exit status: {e}")
            return {'error': str(e), 'plugin_active': False}
    
    def emergency_disable(self, reason: str = "Emergency stop"):
        """Emergency disable of exit strategy"""
        try:
            if self.engine:
                self.engine.disable_exit_strategy(reason)
            
            self.plugin_active = False
            os.environ['EXIT_STRATEGY_ENABLED'] = 'false'
            
            logger.warning(f"🚨 EXIT STRATEGY EMERGENCY DISABLED: {reason}")
            
        except Exception as e:
            logger.error(f"Error in emergency disable: {e}")
    
    def deactivate(self):
        """Deactivate the exit strategy plugin"""
        try:
            self.plugin_active = False
            
            # Remove environment variables
            for key in ['EXIT_STRATEGY_ENABLED', 'EXIT_STRATEGY_PLUGIN_ACTIVE']:
                if key in os.environ:
                    del os.environ[key]
            
            logger.info("🔌 Exit Strategy Plugin deactivated")
            
        except Exception as e:
            logger.error(f"Error deactivating exit strategy plugin: {e}")

# Global plugin instance
exit_strategy_plugin = ExitStrategyPlugin()

# Convenience functions for integration
def activate_exit_strategy() -> bool:
    """Activate exit strategy plugin"""
    return exit_strategy_plugin.activate()

def check_position_exits(positions: List[Dict]) -> List[Dict]:
    """Check exit conditions for positions"""
    return exit_strategy_plugin.check_position_exits(positions)

def process_morning_exits(routine_data: Dict) -> Dict:
    """Process exits during morning routine"""
    return exit_strategy_plugin.process_morning_routine_exits(routine_data)

def process_evening_exits(routine_data: Dict) -> Dict:
    """Process exits during evening routine"""
    return exit_strategy_plugin.process_evening_routine_exits(routine_data)

def get_exit_strategy_status() -> Dict[str, Any]:
    """Get exit strategy status"""
    return exit_strategy_plugin.get_exit_status_summary()

def emergency_disable_exits(reason: str = "Emergency stop") -> None:
    """Emergency disable exit strategy"""
    exit_strategy_plugin.emergency_disable(reason)

def is_market_hours() -> bool:
    """Check if currently in market hours"""
    return exit_strategy_plugin.is_market_hours()

if __name__ == "__main__":
    # Test the exit strategy plugin
    logging.basicConfig(level=logging.INFO)
    
    print("🚪 Exit Strategy Plugin Test")
    print("=" * 50)
    
    # Test plugin activation
    print("🔌 Activating plugin...")
    activation_success = activate_exit_strategy()
    
    if activation_success:
        print("✅ Plugin activated successfully")
        
        # Test market hours
        market_hours_status = is_market_hours()
        print(f"📊 Market hours: {market_hours_status}")
        
        # Test with sample position
        sample_positions = [{
            'symbol': 'CBA.AX',
            'entry_price': 100.50,
            'predicted_action': 'BUY',
            'prediction_confidence': 0.75,
            'entry_timestamp': '2025-09-05T09:30:00',
            'shares': 100
        }]
        
        print(f"🔍 Testing exit evaluation...")
        exit_recommendations = check_position_exits(sample_positions)
        
        if exit_recommendations:
            print(f"📊 Exit recommendations: {len(exit_recommendations)}")
            for rec in exit_recommendations:
                print(f"   {rec['symbol']}: {rec['action']} - {rec['reason']} (Urgency: {rec['urgency']})")
        else:
            print("📊 No exit conditions met")
        
        # Show comprehensive status
        status = get_exit_strategy_status()
        print(f"\n📈 Exit Strategy Status:")
        print(f"   Plugin Active: {status['plugin_active']}")
        print(f"   Engine Available: {status['exit_strategy_available']}")
        print(f"   Market Hours: {status['market_hours']}")
        print(f"   IG Markets Available: {status.get('data_sources', {}).get('ig_markets_available', 'Unknown')}")
        
    else:
        print("❌ Plugin activation failed")

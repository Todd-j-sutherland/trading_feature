#!/usr/bin/env python3
"""
Exit Strategy Hook System
Minimal impact integration for adding exit strategy to existing app/* code
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class ExitStrategyHookManager:
    """
    Minimal-impact hook manager that integrates exit strategy with existing app structure
    No changes to existing app/* code required - just add hooks where needed
    """
    
    def __init__(self):
        self.hook_enabled = True
        self.exit_engine = None
        self._initialize_exit_engine()
    
    def _initialize_exit_engine(self):
        """Initialize exit strategy engine if available"""
        try:
            # Import Phase 4 exit strategy
            phase4_path = project_root / "phase4_development" / "exit_strategy"
            sys.path.insert(0, str(phase4_path))
            
            from exit_strategy_engine import ExitStrategyEngine
            self.exit_engine = ExitStrategyEngine()
            logger.info("✅ Exit Strategy Hook: Phase 4 engine loaded")
            
        except ImportError as e:
            logger.warning(f"⚠️ Exit Strategy Hook: Phase 4 engine not available: {e}")
            self.hook_enabled = False
    
    def hook_prediction_save(self, prediction_data: Dict) -> Dict:
        """
        Hook: Called when prediction is saved - minimal change to existing code
        Usage: prediction_data = exit_hook.hook_prediction_save(prediction_data)
        """
        if not self.hook_enabled or not self.exit_engine:
            return prediction_data
        
        try:
            # Add exit strategy context to prediction
            prediction_data['exit_strategy'] = {
                'enabled': True,
                'profit_target': self._calculate_profit_target(prediction_data),
                'time_limit': self._calculate_time_limit(prediction_data),
                'stop_loss': self._calculate_stop_loss(prediction_data),
                'entry_timestamp': datetime.now().isoformat()
            }
            
            logger.debug(f"Exit Strategy Hook: Added exit context to {prediction_data.get('symbol', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Exit Strategy Hook error in prediction save: {e}")
        
        return prediction_data
    
    def hook_morning_routine(self, routine_data: Dict) -> Dict:
        """
        Hook: Called during morning routine - check for exit conditions
        Usage: morning_data = exit_hook.hook_morning_routine(morning_data)
        """
        if not self.hook_enabled or not self.exit_engine:
            return routine_data
        
        try:
            # Check for positions that need exit evaluation
            exit_recommendations = self._evaluate_morning_exits()
            
            if exit_recommendations:
                routine_data['exit_recommendations'] = exit_recommendations
                logger.info(f"Exit Strategy Hook: Found {len(exit_recommendations)} exit recommendations")
            
        except Exception as e:
            logger.error(f"Exit Strategy Hook error in morning routine: {e}")
        
        return routine_data
    
    def hook_evening_routine(self, routine_data: Dict) -> Dict:
        """
        Hook: Called during evening routine - process end-of-day exits
        Usage: evening_data = exit_hook.hook_evening_routine(evening_data)
        """
        if not self.hook_enabled or not self.exit_engine:
            return routine_data
        
        try:
            # Process end-of-day exit evaluations
            end_of_day_exits = self._evaluate_end_of_day_exits()
            
            if end_of_day_exits:
                routine_data['end_of_day_exits'] = end_of_day_exits
                logger.info(f"Exit Strategy Hook: Processed {len(end_of_day_exits)} end-of-day exits")
            
        except Exception as e:
            logger.error(f"Exit Strategy Hook error in evening routine: {e}")
        
        return routine_data
    
    def hook_status_check(self, status_data: Dict) -> Dict:
        """
        Hook: Called during status checks - add exit strategy status
        Usage: status_data = exit_hook.hook_status_check(status_data)
        """
        if not self.hook_enabled or not self.exit_engine:
            status_data['exit_strategy_status'] = 'Disabled'
            return status_data
        
        try:
            # Add exit strategy status information
            open_positions = self._get_open_positions_count()
            pending_exits = self._get_pending_exits_count()
            
            status_data['exit_strategy_status'] = {
                'enabled': True,
                'open_positions': open_positions,
                'pending_exits': pending_exits,
                'engine_version': getattr(self.exit_engine, 'version', '1.0.0')
            }
            
        except Exception as e:
            logger.error(f"Exit Strategy Hook error in status check: {e}")
            status_data['exit_strategy_status'] = f'Error: {e}'
        
        return status_data
    
    def _calculate_profit_target(self, prediction_data: Dict) -> float:
        """Calculate profit target based on prediction confidence"""
        confidence = prediction_data.get('confidence', 0.65)
        
        # Use recommended adaptive profit targets
        if confidence >= 0.80:
            return 0.042  # 4.2% for high confidence
        elif confidence >= 0.70:
            return 0.035  # 3.5% for medium confidence
        else:
            return 0.028  # 2.8% for lower confidence
    
    def _calculate_time_limit(self, prediction_data: Dict) -> str:
        """Calculate time limit based on trading session"""
        # Default to end of trading session (3:15 PM AEST)
        entry_time = datetime.now()
        session_end = entry_time.replace(hour=15, minute=15, second=0, microsecond=0)
        
        # If after session, set to next day's session end
        if entry_time > session_end:
            session_end += timedelta(days=1)
        
        return session_end.isoformat()
    
    def _calculate_stop_loss(self, prediction_data: Dict) -> float:
        """Calculate stop loss based on prediction and volatility"""
        confidence = prediction_data.get('confidence', 0.65)
        
        # Base stop loss of 3% (proven optimal from backtesting)
        base_stop = 0.03
        
        # Adjust for confidence
        confidence_factor = 1.0 + (confidence - 0.7) * 0.5
        
        return base_stop * confidence_factor
    
    def _evaluate_morning_exits(self) -> List[Dict]:
        """Evaluate positions for morning exit conditions"""
        if not self.exit_engine:
            return []
        
        try:
            # Get open positions from database
            open_positions = self._get_open_positions()
            exit_recommendations = []
            
            for position in open_positions:
                exit_decision = self.exit_engine.evaluate_exit_conditions(position)
                
                if exit_decision.should_exit:
                    exit_recommendations.append({
                        'symbol': position.get('symbol'),
                        'reason': exit_decision.reason.value,
                        'confidence': exit_decision.confidence,
                        'recommended_action': 'EXIT'
                    })
            
            return exit_recommendations
            
        except Exception as e:
            logger.error(f"Error evaluating morning exits: {e}")
            return []
    
    def _evaluate_end_of_day_exits(self) -> List[Dict]:
        """Evaluate positions for end-of-day exit conditions"""
        if not self.exit_engine:
            return []
        
        try:
            # Force exit evaluation for end of trading session
            open_positions = self._get_open_positions()
            end_of_day_exits = []
            
            for position in open_positions:
                # Check time-based exits for end of session
                if self._is_end_of_session():
                    end_of_day_exits.append({
                        'symbol': position.get('symbol'),
                        'reason': 'TIME_LIMIT',
                        'confidence': 1.0,
                        'recommended_action': 'EXIT'
                    })
            
            return end_of_day_exits
            
        except Exception as e:
            logger.error(f"Error evaluating end-of-day exits: {e}")
            return []
    
    def _get_open_positions(self) -> List[Dict]:
        """Get open positions from database - hooks into existing data"""
        try:
            # Hook into existing prediction database
            import sqlite3
            
            # Try multiple database paths
            db_paths = [
                'predictions.db',
                'data/predictions.db',
                project_root / 'predictions.db'
            ]
            
            for db_path in db_paths:
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Get recent predictions (potential open positions)
                    cursor.execute('''
                        SELECT symbol, timestamp, confidence, predicted_movement 
                        FROM predictions 
                        WHERE timestamp > datetime('now', '-1 day')
                        ORDER BY timestamp DESC
                    ''')
                    
                    positions = []
                    for row in cursor.fetchall():
                        positions.append({
                            'symbol': row[0],
                            'timestamp': row[1],
                            'confidence': row[2],
                            'predicted_movement': row[3]
                        })
                    
                    conn.close()
                    return positions
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []
    
    def _get_open_positions_count(self) -> int:
        """Get count of open positions"""
        return len(self._get_open_positions())
    
    def _get_pending_exits_count(self) -> int:
        """Get count of positions with pending exits"""
        return len(self._evaluate_morning_exits())
    
    def _is_end_of_session(self) -> bool:
        """Check if it's end of trading session"""
        now = datetime.now()
        session_end = now.replace(hour=15, minute=15, second=0, microsecond=0)
        
        # Within 30 minutes of session end
        return now >= (session_end - timedelta(minutes=30))
    
    def print_exit_status(self):
        """Print current exit strategy status"""
        print("\n🚪 EXIT STRATEGY STATUS")
        print("=" * 40)
        
        if not self.hook_enabled:
            print("❌ Exit Strategy: DISABLED")
            print("💡 Install Phase 4 exit strategy to enable")
            return
        
        print("✅ Exit Strategy: ENABLED")
        
        try:
            open_positions = self._get_open_positions_count()
            pending_exits = self._get_pending_exits_count()
            
            print(f"📊 Open Positions: {open_positions}")
            print(f"🚪 Pending Exits: {pending_exits}")
            
            if pending_exits > 0:
                recommendations = self._evaluate_morning_exits()
                for rec in recommendations:
                    print(f"   🎯 {rec['symbol']}: {rec['reason']} (Confidence: {rec['confidence']:.1%})")
            
        except Exception as e:
            print(f"⚠️ Status Error: {e}")

# Global hook instance for easy integration
exit_strategy_hook = ExitStrategyHookManager()

# Convenience functions for easy integration into existing app/* code
def hook_prediction_save(prediction_data: Dict) -> Dict:
    """Convenience function for prediction save hook"""
    return exit_strategy_hook.hook_prediction_save(prediction_data)

def hook_morning_routine(routine_data: Dict) -> Dict:
    """Convenience function for morning routine hook"""
    return exit_strategy_hook.hook_morning_routine(routine_data)

def hook_evening_routine(routine_data: Dict) -> Dict:
    """Convenience function for evening routine hook"""
    return exit_strategy_hook.hook_evening_routine(routine_data)

def hook_status_check(status_data: Dict) -> Dict:
    """Convenience function for status check hook"""
    return exit_strategy_hook.hook_status_check(status_data)

def print_exit_status():
    """Convenience function to print exit status"""
    exit_strategy_hook.print_exit_status()

# Integration helper functions
def add_exit_hook_to_main():
    """
    Helper function to show how to integrate with app/main.py
    No code changes needed - just import and call hooks
    """
    integration_example = """
    # Example integration in app/main.py:
    
    from app.core.exit_hooks import hook_morning_routine, hook_status_check, print_exit_status
    
    def morning_routine():
        # ... existing morning code ...
        routine_data = {'status': 'completed'}
        
        # Add this one line to enable exit strategy
        routine_data = hook_morning_routine(routine_data)
        
        # Print exit recommendations if any
        if 'exit_recommendations' in routine_data:
            print("🚪 EXIT RECOMMENDATIONS:")
            for rec in routine_data['exit_recommendations']:
                print(f"   {rec['symbol']}: {rec['reason']}")
    
    def status_check():
        # ... existing status code ...
        status_data = {'system': 'operational'}
        
        # Add this one line to show exit strategy status
        status_data = hook_status_check(status_data)
        print_exit_status()
    """
    
    print(integration_example)

if __name__ == "__main__":
    print("🔌 Exit Strategy Hook System")
    print("=" * 40)
    print_exit_status()
    print("\n💡 Integration Help:")
    add_exit_hook_to_main()

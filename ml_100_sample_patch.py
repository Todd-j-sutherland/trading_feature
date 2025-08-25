#!/usr/bin/env python3
"""
100-Sample Minimum ML System Patch
Add this method to EnhancedMLPipeline class
"""


def should_use_ml_predictions(self) -> bool:
    """
    Check if we have enough training data to use ML predictions
    Returns True only if we have 100+ balanced samples
    """
    try:
        import sqlite3
        conn = sqlite3.connect('data/trading_predictions.db')
        cursor = conn.cursor()
        
        # Count predictions with outcomes (training data)
        cursor.execute("""
            SELECT predicted_action, COUNT(*) as count
            FROM predictions 
            WHERE model_version NOT LIKE '%emergency%'
            AND entry_price > 0
            GROUP BY predicted_action
        """)
        
        action_counts = dict(cursor.fetchall())
        total_samples = sum(action_counts.values())
        
        # Require 100+ samples AND balanced distribution
        if total_samples < 100:
            self.logger.info(f"ML disabled: Only {total_samples}/100 training samples available")
            return False
        
        # Check balance - each action should have at least 10% of total
        buy_count = action_counts.get('BUY', 0) 
        sell_count = action_counts.get('SELL', 0)
        hold_count = action_counts.get('HOLD', 0)
        
        min_per_action = total_samples * 0.1  # 10% minimum per action
        
        if buy_count < min_per_action or sell_count < min_per_action or hold_count < min_per_action:
            self.logger.info(f"ML disabled: Unbalanced data (BUY:{buy_count}, SELL:{sell_count}, HOLD:{hold_count})")
            return False
        
        self.logger.info(f"ML enabled: {total_samples} balanced samples available")
        return True
        
    except Exception as e:
        self.logger.error(f"Error checking ML readiness: {e}")
        return False
    finally:
        conn.close()


# Usage in enhanced_morning_analyzer_with_ml.py:
# 
# Replace ML prediction logic with:
# if self.enhanced_pipeline.should_use_ml_predictions():
#     # Use ML predictions
#     ml_prediction = self.enhanced_pipeline.predict_enhanced(sentiment_data, symbol)
# else:
#     # Use traditional signals (automatic fallback)
#     ml_prediction = self._traditional_fallback_signals(symbol, current_price)

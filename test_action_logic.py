#!/usr/bin/env python3
"""
Test the new action determination logic with various scenarios
"""

import numpy as np
import sys
sys.path.append('/root/test/app')
sys.path.append('/root/test')

def test_action_logic():
    """Test the new action determination logic"""
    
    try:
        from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
        pipeline = EnhancedMLTrainingPipeline()
        
        print("=== Testing New Action Logic ===")
        
        # Test cases: [direction_1h, direction_4h, direction_1d], magnitude, confidence -> expected action
        test_cases = [
            # Current failing case
            ([0, 1, 0], [0.0, 0.8, 0.0], 0.753, "Current failing case"),
            
            # Strong bullish signals
            ([1, 1, 1], [2.5, 2.8, 2.1], 0.85, "Strong bullish"),
            ([1, 1, 0], [1.2, 1.8, 0.5], 0.7, "Moderate bullish"),
            
            # Strong bearish signals  
            ([0, 0, 0], [2.2, 2.5, 2.0], 0.85, "Strong bearish"),
            ([0, 0, 1], [1.1, 1.5, 0.8], 0.7, "Moderate bearish"),
            
            # Neutral/uncertain cases
            ([1, 0, 1], [0.8, 1.2, 0.5], 0.6, "Mixed signals"),
            ([0, 1, 0], [0.3, 0.5, 0.2], 0.5, "Low confidence"),
            ([1, 1, 0], [0.5, 0.8, 0.3], 0.4, "Very low confidence"),
        ]
        
        for directions, magnitudes, confidence, description in test_cases:
            direction_pred = np.array(directions)
            magnitude_pred = np.array(magnitudes)
            
            action = pipeline._determine_optimal_action(direction_pred, magnitude_pred, confidence)
            avg_direction = np.mean(direction_pred)
            avg_magnitude = np.mean(np.abs(magnitude_pred))
            
            print(f"\n{description}:")
            print(f"  Directions: {directions} (avg: {avg_direction:.2f})")
            print(f"  Magnitudes: {magnitudes} (avg: {avg_magnitude:.2f})")
            print(f"  Confidence: {confidence:.2f}")
            print(f"  Action: {action}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_action_logic()

#!/usr/bin/env python3
"""
Fix the progression tracker to handle mixed data formats
"""

def fix_progression_tracker():
    file_path = 'app/core/ml/tracking/progression_tracker.py'
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Old method (lines 381-395)
    old_method = '''    def _is_successful_prediction(self, prediction: Dict) -> bool:
        """Determine if a prediction was successful"""
        if prediction['status'] != 'completed' or not prediction.get('actual_outcome'):
            return False
        
        predicted_signal = prediction['prediction'].get('signal', 'HOLD')
        actual_outcome = prediction['actual_outcome']
        
        # Simple success criteria - can be made more sophisticated
        if predicted_signal == 'BUY':
            return actual_outcome.get('price_change_percent', 0) > 0
        elif predicted_signal == 'SELL':
            return actual_outcome.get('price_change_percent', 0) < 0
        else:  # HOLD
            return abs(actual_outcome.get('price_change_percent', 0)) < 2  # Less than 2% movement'''
    
    # New fixed method
    new_method = '''    def _is_successful_prediction(self, prediction: Dict) -> bool:
        """Determine if a prediction was successful"""
        if prediction['status'] != 'completed' or not prediction.get('actual_outcome'):
            return False
        
        # Safely get predicted signal from prediction dict or top level
        predicted_signal = 'HOLD'
        if isinstance(prediction.get('prediction'), dict):
            predicted_signal = prediction['prediction'].get('signal', 'HOLD')
        elif 'signal' in prediction:
            predicted_signal = prediction.get('signal', 'HOLD')
        
        actual_outcome = prediction['actual_outcome']
        
        # Handle both dict and float formats for actual_outcome
        if isinstance(actual_outcome, dict):
            # New format: nested dictionary
            price_change_percent = actual_outcome.get('price_change_percent', 0)
        elif isinstance(actual_outcome, (int, float)):
            # Old format: direct float value (convert to percentage)
            price_change_percent = actual_outcome * 100
        else:
            # No valid outcome data
            return False
        
        # Simple success criteria - can be made more sophisticated
        if predicted_signal == 'BUY':
            return price_change_percent > 0
        elif predicted_signal == 'SELL':
            return price_change_percent < 0
        else:  # HOLD
            return abs(price_change_percent) < 2  # Less than 2% movement'''
    
    # Replace the method
    if old_method in content:
        content = content.replace(old_method, new_method)
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(content)
        
        print('✅ Fixed _is_successful_prediction method in progression_tracker.py')
        return True
    else:
        print('❌ Could not find the method to replace')
        return False

if __name__ == '__main__':
    fix_progression_tracker()

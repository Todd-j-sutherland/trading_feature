#!/usr/bin/env python3
"""
Test the fixed dashboard components
"""

import sys
sys.path.insert(0, '/root/test')

def test_fixed_components():
    """Test the fixed dashboard components"""
    
    print('🧪 TESTING FIXED DASHBOARD COMPONENTS')
    print('=' * 50)
    
    try:
        from app.core.ml.tracking.progression_tracker import MLProgressionTracker
        from pathlib import Path
        
        # Create ML tracker
        data_path = Path('/root/test/data/ml_performance')
        ml_tracker = MLProgressionTracker(data_dir=data_path)
        print(f'✅ ML tracker created with {len(ml_tracker.prediction_history)} predictions')
        
        # Test the _is_successful_prediction method with mixed data
        test_predictions = ml_tracker.prediction_history[-10:]
        
        print(f'\n🔍 Testing _is_successful_prediction method:')
        success_count = 0
        
        for i, pred in enumerate(test_predictions):
            try:
                result = ml_tracker._is_successful_prediction(pred)
                success_count += 1 if result else 0
                outcome_type = type(pred.get('actual_outcome')).__name__
                prediction_type = type(pred.get('prediction')).__name__
                print(f'  Record {i+1}: {pred["symbol"]} | Outcome: {outcome_type} | Prediction: {prediction_type} | Success: {result}')
            except Exception as e:
                print(f'  ❌ Record {i+1}: {pred["symbol"]} | ERROR: {e}')
                return False
        
        print(f'\n✅ All {len(test_predictions)} records processed successfully')
        print(f'📊 Success rate: {success_count}/{len(test_predictions)} = {success_count/len(test_predictions)*100:.1f}%')
        
        # Test data handling for display
        print(f'\n🔍 Testing data display formatting:')
        
        for i, pred in enumerate(test_predictions[:3]):  # Test first 3
            print(f'\n  Record {i+1}: {pred["symbol"]}')
            
            # Test signal extraction
            if isinstance(pred.get('prediction'), dict):
                signal = pred['prediction'].get('signal', 'N/A')
                confidence = pred['prediction'].get('confidence', 0)
                print(f'    Signal from dict: {signal} | Confidence: {confidence:.1%}')
            elif 'signal' in pred:
                signal = pred.get('signal', 'N/A')
                confidence = pred.get('confidence', 0)
                print(f'    Signal from top-level: {signal} | Confidence: {confidence:.1%}')
            else:
                print(f'    No signal data available')
            
            # Test outcome formatting
            outcome = pred.get('actual_outcome')
            if isinstance(outcome, dict):
                price_change = outcome.get('price_change_percent', 0)
                outcome_text = f"{price_change:+.2f}%"
                print(f'    Outcome from dict: {outcome_text}')
            elif isinstance(outcome, (int, float)):
                price_change = outcome * 100
                outcome_text = f"{price_change:+.2f}%"
                print(f'    Outcome from float: {outcome_text}')
            elif outcome is None:
                outcome_text = "No Data"
                print(f'    Outcome: {outcome_text}')
            else:
                print(f'    Outcome: Error - {type(outcome)}')
        
        print(f'\n🎉 ALL TESTS PASSED!')
        return True
        
    except Exception as e:
        print(f'\n💥 TEST FAILED: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_fixed_components()

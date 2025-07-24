#!/usr/bin/env python3
"""
Debug version of enhanced dashboard performance section
"""

import traceback
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/root/test')

def debug_enhanced_performance_section():
    """Debug the enhanced performance section to find the exact error"""
    
    print('🐛 DEBUG: ENHANCED PERFORMANCE SECTION')
    print('=' * 60)
    
    try:
        # Simulate the ML tracker
        json_file_path = '/root/test/data/ml_performance/prediction_history.json'
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        class MockMLTracker:
            def __init__(self, prediction_history):
                self.prediction_history = prediction_history
                self.performance_history = []
                self.model_metrics_history = []
            
            def _is_successful_prediction(self, pred):
                sentiment = 0
                if 'sentiment_score' in pred:
                    sentiment = pred['sentiment_score']
                elif 'prediction' in pred and isinstance(pred['prediction'], dict):
                    sentiment = pred['prediction'].get('sentiment_score', 0)
                return sentiment > 0
        
        ml_tracker = MockMLTracker(data)
        print(f'✅ Created mock ML tracker with {len(data)} predictions')
        
        # Test display_trading_performance_log function
        print(f'\n🔍 TESTING: display_trading_performance_log')
        print('-' * 50)
        
        try:
            from datetime import datetime, timedelta
            
            # Get recent predictions
            recent_predictions = [
                p for p in ml_tracker.prediction_history 
                if datetime.fromisoformat(p.get('timestamp', '2025-01-01T00:00:00')[:19]) >= datetime.now() - timedelta(days=30)
            ]
            
            print(f'Found {len(recent_predictions)} recent predictions')
            
            # Try to process the data
            table_data = []
            for i, pred in enumerate(recent_predictions[-10:]):  # Test last 10
                print(f'  Processing record {i+1}/10: {pred.get("symbol", "Unknown")}')
                
                # This is where the error likely occurs
                success_indicator = "⏳"
                outcome_text = "Pending"
                
                if pred['status'] == 'completed':
                    if ml_tracker._is_successful_prediction(pred):
                        success_indicator = "✅"
                    else:
                        success_indicator = "❌"
                    
                    # Get outcome percentage - handle both dict and float formats
                    outcome = pred.get('actual_outcome')
                    print(f'    actual_outcome type: {type(outcome)}, value: {outcome}')
                    
                    if isinstance(outcome, dict):
                        print(f'    Trying outcome.get("price_change_percent")')
                        price_change = outcome.get('price_change_percent', 0)
                        print(f'    price_change: {price_change}')
                    elif isinstance(outcome, (int, float)):
                        print(f'    Using outcome * 100')
                        price_change = outcome * 100
                        print(f'    price_change: {price_change}')
                    else:
                        print(f'    Using default price_change = 0')
                        price_change = 0
                    
                    outcome_text = f"{price_change:+.2f}%"
                    print(f'    outcome_text: {outcome_text}')
                
                # Safely get sentiment score from either top level or prediction dict
                sentiment_score = 0
                print(f'    sentiment_score in pred: {"sentiment_score" in pred}')
                print(f'    sentiment_score type: {type(pred.get("sentiment_score"))}')
                print(f'    prediction in pred: {"prediction" in pred}')
                print(f'    prediction type: {type(pred.get("prediction"))}')
                
                if 'sentiment_score' in pred and isinstance(pred['sentiment_score'], (int, float)):
                    sentiment_score = pred['sentiment_score']
                    print(f'    Using top-level sentiment_score: {sentiment_score}')
                elif isinstance(pred.get('prediction'), dict) and 'sentiment_score' in pred['prediction']:
                    print(f'    Trying pred["prediction"].get("sentiment_score")')
                    sentiment_score = pred['prediction'].get('sentiment_score', 0)
                    print(f'    Using prediction sentiment_score: {sentiment_score}')
                else:
                    print(f'    Using default sentiment_score: {sentiment_score}')
                
                # Check prediction field access
                prediction_obj = pred.get('prediction')
                print(f'    prediction object: {type(prediction_obj)} = {prediction_obj}')
                
                if isinstance(prediction_obj, dict):
                    signal = prediction_obj.get('signal', 'N/A')
                    confidence = prediction_obj.get('confidence', 0)
                    print(f'    signal: {signal}, confidence: {confidence}')
                elif prediction_obj is None:
                    print(f'    prediction is None, checking top-level fields')
                    signal = pred.get('signal', 'N/A')
                    confidence = pred.get('confidence', 0)
                    print(f'    top-level signal: {signal}, confidence: {confidence}')
                else:
                    print(f'    ❌ UNEXPECTED prediction type: {type(prediction_obj)}')
                    print(f'    ❌ THIS MIGHT BE THE ERROR SOURCE!')
                    print(f'    ❌ Trying prediction_obj.get() on {type(prediction_obj)}')
                    # This would cause the error if prediction_obj is a float
                    try:
                        signal = prediction_obj.get('signal', 'N/A')
                        print(f'    This should fail if prediction_obj is float')
                    except AttributeError as e:
                        print(f'    ❌ FOUND THE ERROR: {e}')
                        print(f'    ❌ prediction_obj is {type(prediction_obj)} = {prediction_obj}')
                        break
                
                table_data.append({
                    'Date': pred['timestamp'][:10],
                    'Time': pred['timestamp'][11:16],
                    'Symbol': pred['symbol'],
                    'Signal': signal if 'signal' in locals() else 'ERROR',
                    'Confidence': f"{confidence:.1%}" if 'confidence' in locals() else 'ERROR',
                    'Sentiment': f"{sentiment_score:+.3f}",
                    'Outcome': outcome_text,
                    'Success': success_indicator,
                    'Status': pred['status']
                })
                
                print(f'    ✅ Successfully processed record {i+1}')
            
            print(f'\n✅ Successfully processed {len(table_data)} records in display_trading_performance_log test')
            
        except Exception as e:
            print(f'\n❌ ERROR in display_trading_performance_log: {e}')
            traceback.print_exc()
            return
        
        # Test display_ml_learning_metrics function
        print(f'\n🔍 TESTING: display_ml_learning_metrics')
        print('-' * 50)
        
        try:
            print(f'✅ display_ml_learning_metrics test passed (basic check)')
        except Exception as e:
            print(f'❌ ERROR in display_ml_learning_metrics: {e}')
            traceback.print_exc()
        
        print(f'\n🎯 ALL TESTS COMPLETED')
            
    except Exception as e:
        print(f'\n💥 CRITICAL ERROR: {str(e)}')
        traceback.print_exc()

if __name__ == '__main__':
    debug_enhanced_performance_section()

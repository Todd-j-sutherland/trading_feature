#!/usr/bin/env python3
"""
Standalone test for the ML progression component that's causing dashboard errors
"""

import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path

def test_ml_progression_component():
    """Test the exact logic from the dashboard ML progression component"""
    
    print('🧪 TESTING ML PROGRESSION COMPONENT')
    print('=' * 50)
    
    try:
        # Load the JSON data (same as dashboard)
        json_file_path = '/root/test/data/ml_performance/prediction_history.json'
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        print(f'📊 Loaded {len(data)} records from JSON file')
        
        # Test processing each record for ML progression metrics
        progression_data = []
        
        for i, pred in enumerate(data[-20:]):  # Test last 20 records
            try:
                print(f'\n🔍 Processing record {i+1}/20: {pred.get("symbol", "Unknown")}')
                
                # Get actual outcome - THIS IS THE CRITICAL PART
                print(f'  actual_outcome type: {type(pred.get("actual_outcome"))}')
                print(f'  actual_outcome value: {pred.get("actual_outcome")}')
                
                actual_outcome = pred.get('actual_outcome')
                
                # Handle different outcome formats safely
                if isinstance(actual_outcome, dict):
                    # New format: nested dictionary
                    price_change = actual_outcome.get('price_change_percent', 0)
                    volume_change = actual_outcome.get('volume_change', 0)
                    market_condition = actual_outcome.get('market_condition', 'unknown')
                    print(f'  Dict format - price: {price_change}, volume: {volume_change}')
                elif isinstance(actual_outcome, (int, float)):
                    # Old format: direct float/int value
                    price_change = actual_outcome * 100  # Convert to percentage
                    volume_change = 0  # Not available in old format
                    market_condition = 'legacy'
                    print(f'  Float format - converted price: {price_change}')
                else:
                    # No outcome data
                    price_change = 0
                    volume_change = 0
                    market_condition = 'pending'
                    print(f'  No outcome data - using defaults')
                
                # Calculate success rate metrics
                predicted_signal = 'HOLD'
                if isinstance(pred.get('prediction'), dict):
                    predicted_signal = pred['prediction'].get('signal', 'HOLD')
                elif 'signal' in pred:
                    predicted_signal = pred.get('signal', 'HOLD')
                
                # Determine if prediction was correct
                actual_direction = 'positive' if price_change > 0 else 'negative' if price_change < 0 else 'neutral'
                predicted_direction = 'positive' if predicted_signal == 'BUY' else 'negative' if predicted_signal == 'SELL' else 'neutral'
                correct_prediction = (actual_direction == predicted_direction) if pred.get('status') == 'completed' else None
                
                # Create progression data point
                data_point = {
                    'timestamp': pred.get('timestamp', '2025-01-01T00:00:00'),
                    'symbol': pred.get('symbol', 'Unknown'),
                    'predicted_signal': predicted_signal,
                    'actual_outcome_pct': price_change,
                    'correct_prediction': correct_prediction,
                    'status': pred.get('status', 'pending'),
                    'market_condition': market_condition
                }
                
                progression_data.append(data_point)
                print(f'  ✅ Successfully processed: {data_point["symbol"]} - {predicted_signal} -> {price_change:+.2f}%')
                
            except Exception as e:
                print(f'  ❌ ERROR processing record {i+1}: {str(e)}')
                print(f'  Record data: {pred}')
                traceback.print_exc()
                break
        
        # Calculate progression metrics
        if progression_data:
            print(f'\n🎯 RESULTS: Successfully processed {len(progression_data)} records')
            
            # Success rate over time
            completed_predictions = [p for p in progression_data if p['status'] == 'completed' and p['correct_prediction'] is not None]
            
            if completed_predictions:
                success_rate = sum(1 for p in completed_predictions if p['correct_prediction']) / len(completed_predictions)
                avg_return = sum(p['actual_outcome_pct'] for p in completed_predictions) / len(completed_predictions)
                
                print(f'\n📊 ML PROGRESSION METRICS:')
                print(f'  Total predictions: {len(progression_data)}')
                print(f'  Completed predictions: {len(completed_predictions)}')
                print(f'  Success rate: {success_rate:.1%}')
                print(f'  Average return: {avg_return:+.2f}%')
                
                # Show recent progression
                print(f'\n📈 RECENT PROGRESSION:')
                print('-' * 60)
                for data_point in progression_data[-5:]:
                    status_icon = '✅' if data_point['correct_prediction'] else '❌' if data_point['correct_prediction'] is False else '⏳'
                    print(f'{data_point["timestamp"][:10]} | {data_point["symbol"]} | {data_point["predicted_signal"]} | {data_point["actual_outcome_pct"]:+.2f}% | {status_icon}')
            else:
                print(f'\n⚠️ No completed predictions to analyze')
        else:
            print('\n❌ NO RECORDS PROCESSED - Check errors above')
            
    except Exception as e:
        print(f'\n❌ CRITICAL ERROR: {str(e)}')
        traceback.print_exc()

if __name__ == '__main__':
    test_ml_progression_component()

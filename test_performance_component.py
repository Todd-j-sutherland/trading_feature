#!/usr/bin/env python3
"""
Standalone test for the performance log component that's causing dashboard errors
"""

import json
import pandas as pd
import traceback
from datetime import datetime, timedelta
from pathlib import Path

def test_performance_log_component():
    """Test the exact logic from the dashboard performance component"""
    
    print('🧪 TESTING PERFORMANCE LOG COMPONENT')
    print('=' * 50)
    
    try:
        # Load the JSON data (same as dashboard)
        json_file_path = '/root/test/data/ml_performance/prediction_history.json'
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        print(f'📊 Loaded {len(data)} records from JSON file')
        
        # Simulate ML tracker with prediction history
        class MockMLTracker:
            def __init__(self, prediction_history):
                self.prediction_history = prediction_history
            
            def _is_successful_prediction(self, pred):
                # Simple success logic
                sentiment = 0
                if 'sentiment_score' in pred:
                    sentiment = pred['sentiment_score']
                elif 'prediction' in pred and isinstance(pred['prediction'], dict):
                    sentiment = pred['prediction'].get('sentiment_score', 0)
                return sentiment > 0
        
        ml_tracker = MockMLTracker(data)
        
        # Get recent predictions (last 30 days)
        days_back = 30
        recent_predictions = [
            p for p in ml_tracker.prediction_history 
            if datetime.fromisoformat(p.get('timestamp', '2025-01-01T00:00:00')[:19]) >= datetime.now() - timedelta(days=days_back)
        ]
        
        print(f'📅 Found {len(recent_predictions)} recent predictions')
        
        if not recent_predictions:
            print('❌ No recent predictions found')
            return
        
        # Test the EXACT dashboard logic that's failing
        table_data = []
        
        for i, pred in enumerate(recent_predictions[-10:]):  # Test last 10
            try:
                print(f'\n🔍 Processing record {i+1}/10: {pred.get("symbol", "Unknown")}')
                
                # Success indicator logic
                success_indicator = "⏳"  # Pending
                outcome_text = "Pending"
                
                if pred['status'] == 'completed':
                    if ml_tracker._is_successful_prediction(pred):
                        success_indicator = "✅"
                    else:
                        success_indicator = "❌"
                    
                    # Get outcome percentage - THIS IS WHERE THE ERROR LIKELY OCCURS
                    print(f'  actual_outcome type: {type(pred.get("actual_outcome"))}')
                    print(f'  actual_outcome value: {pred.get("actual_outcome")}')
                    
                    outcome = pred.get('actual_outcome')
                    if isinstance(outcome, dict):
                        price_change = outcome.get('price_change_percent', 0)
                        print(f'  Dict outcome - price_change: {price_change}')
                    elif isinstance(outcome, (int, float)):
                        price_change = outcome * 100  # Convert decimal to percentage
                        print(f'  Float outcome - converted to percentage: {price_change}')
                    else:
                        price_change = 0
                        print(f'  No valid outcome - using default: {price_change}')
                    
                    outcome_text = f"{price_change:+.2f}%"
                
                # Safely get sentiment score
                sentiment_score = 0
                print(f'  sentiment_score in pred: {"sentiment_score" in pred}')
                print(f'  prediction in pred: {"prediction" in pred}')
                
                if 'sentiment_score' in pred and isinstance(pred['sentiment_score'], (int, float)):
                    sentiment_score = pred['sentiment_score']
                    print(f'  Using top-level sentiment_score: {sentiment_score}')
                elif isinstance(pred.get('prediction'), dict) and 'sentiment_score' in pred['prediction']:
                    sentiment_score = pred['prediction'].get('sentiment_score', 0)
                    print(f'  Using prediction sentiment_score: {sentiment_score}')
                else:
                    print(f'  No valid sentiment_score found, using default: {sentiment_score}')
                
                # Create table row - THIS IS THE CRITICAL PART
                row = {
                    'Date': pred['timestamp'][:10] if 'timestamp' in pred else pred.get('date', 'N/A'),
                    'Time': pred['timestamp'][11:16] if 'timestamp' in pred else pred.get('time', 'N/A'),
                    'Symbol': pred['symbol'],
                    'Signal': pred['prediction'].get('signal', 'N/A') if isinstance(pred.get('prediction'), dict) else pred.get('signal', 'N/A'),
                    'Confidence': f"{pred['prediction'].get('confidence', 0):.1%}" if isinstance(pred.get('prediction'), dict) else f"{pred.get('confidence', 0):.1%}",
                    'Sentiment': f"{sentiment_score:+.3f}",
                    'Outcome': outcome_text,
                    'Success': success_indicator,
                    'Status': pred['status']
                }
                
                table_data.append(row)
                print(f'  ✅ Successfully processed: {row["Symbol"]} - {row["Sentiment"]}')
                
            except Exception as e:
                print(f'  ❌ ERROR processing record {i+1}: {str(e)}')
                print(f'  Record data: {pred}')
                traceback.print_exc()
                break
        
        # Display results
        if table_data:
            print(f'\n🎯 RESULTS: Successfully processed {len(table_data)} records')
            print('\n📋 PERFORMANCE TABLE:')
            print('-' * 80)
            for row in table_data:
                print(f'{row["Date"]} | {row["Symbol"]} | {row["Signal"]} | {row["Sentiment"]} | {row["Status"]}')
        else:
            print('\n❌ NO RECORDS PROCESSED - Check errors above')
            
    except Exception as e:
        print(f'\n❌ CRITICAL ERROR: {str(e)}')
        traceback.print_exc()

if __name__ == '__main__':
    test_performance_log_component()

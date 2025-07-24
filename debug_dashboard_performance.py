#!/usr/bin/env python3
"""
Debug version of dashboard performance component with extensive logging
"""

import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path

def debug_performance_log_component():
    """Debug version with extensive error handling and logging"""
    
    print('🐛 DEBUG: PERFORMANCE LOG COMPONENT')
    print('=' * 60)
    
    try:
        # Load the JSON data
        json_file_path = '/root/test/data/ml_performance/prediction_history.json'
        print(f'📂 Loading data from: {json_file_path}')
        
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        print(f'📊 Loaded {len(data)} total records')
        
        # Get recent predictions (last 30 days)
        days_back = 30
        cutoff_date = datetime.now() - timedelta(days=days_back)
        print(f'📅 Looking for predictions after: {cutoff_date}')
        
        recent_predictions = []
        for i, p in enumerate(data):
            try:
                pred_date = datetime.fromisoformat(p.get('timestamp', '2025-01-01T00:00:00')[:19])
                if pred_date >= cutoff_date:
                    recent_predictions.append(p)
            except Exception as e:
                print(f'⚠️  Warning: Could not parse timestamp for record {i}: {e}')
        
        print(f'📅 Found {len(recent_predictions)} recent predictions')
        
        if not recent_predictions:
            print('❌ No recent predictions found')
            return
        
        # Test processing each prediction with detailed debugging
        table_data = []
        last_10_predictions = recent_predictions[-10:]  # Test last 10
        
        print(f'\n🔍 DEBUGGING LAST 10 PREDICTIONS:')
        print('=' * 60)
        
        for i, pred in enumerate(last_10_predictions):
            print(f'\n--- RECORD {i+1}/10 ---')
            print(f'Symbol: {pred.get("symbol", "Unknown")}')
            print(f'Status: {pred.get("status", "Unknown")}')
            print(f'Timestamp: {pred.get("timestamp", "Unknown")}')
            
            try:
                # Debug the prediction field
                print(f'\nDEBUG - prediction field:')
                print(f'  Type: {type(pred.get("prediction"))}')
                print(f'  Value: {pred.get("prediction")}')
                print(f'  Has prediction key: {"prediction" in pred}')
                
                # Debug the sentiment_score field
                print(f'\nDEBUG - sentiment_score field:')
                print(f'  Type: {type(pred.get("sentiment_score"))}')
                print(f'  Value: {pred.get("sentiment_score")}')
                print(f'  Has sentiment_score key: {"sentiment_score" in pred}')
                
                # Debug the actual_outcome field
                print(f'\nDEBUG - actual_outcome field:')
                print(f'  Type: {type(pred.get("actual_outcome"))}')
                print(f'  Value: {pred.get("actual_outcome")}')
                print(f'  Has actual_outcome key: {"actual_outcome" in pred}')
                
                # Try to safely extract sentiment score
                sentiment_score = 0
                print(f'\nTrying to extract sentiment_score:')
                
                if 'sentiment_score' in pred and isinstance(pred['sentiment_score'], (int, float)):
                    sentiment_score = pred['sentiment_score']
                    print(f'  ✅ Using top-level sentiment_score: {sentiment_score}')
                elif isinstance(pred.get('prediction'), dict) and 'sentiment_score' in pred['prediction']:
                    sentiment_score = pred['prediction'].get('sentiment_score', 0)
                    print(f'  ✅ Using prediction.sentiment_score: {sentiment_score}')
                else:
                    print(f'  ⚠️  No valid sentiment_score found, using default: {sentiment_score}')
                
                # Try to safely extract signal
                signal = 'N/A'
                print(f'\nTrying to extract signal:')
                
                if isinstance(pred.get('prediction'), dict):
                    signal = pred['prediction'].get('signal', 'N/A')
                    print(f'  ✅ Using prediction.signal: {signal}')
                elif 'signal' in pred:
                    signal = pred.get('signal', 'N/A')
                    print(f'  ✅ Using top-level signal: {signal}')
                else:
                    print(f'  ⚠️  No valid signal found, using default: {signal}')
                
                # Try to safely extract confidence
                confidence = 0
                print(f'\nTrying to extract confidence:')
                
                if isinstance(pred.get('prediction'), dict):
                    confidence = pred['prediction'].get('confidence', 0)
                    print(f'  ✅ Using prediction.confidence: {confidence}')
                elif 'confidence' in pred:
                    confidence = pred.get('confidence', 0)
                    print(f'  ✅ Using top-level confidence: {confidence}')
                else:
                    print(f'  ⚠️  No valid confidence found, using default: {confidence}')
                
                # Try to safely extract outcome
                outcome_text = 'Pending'
                print(f'\nTrying to extract outcome:')
                
                if pred['status'] == 'completed':
                    outcome = pred.get('actual_outcome')
                    if isinstance(outcome, dict):
                        price_change = outcome.get('price_change_percent', 0)
                        outcome_text = f"{price_change:+.2f}%"
                        print(f'  ✅ Dict outcome: {outcome_text}')
                    elif isinstance(outcome, (int, float)):
                        price_change = outcome * 100  # Convert decimal to percentage
                        outcome_text = f"{price_change:+.2f}%"
                        print(f'  ✅ Float outcome: {outcome_text}')
                    elif outcome is None:
                        outcome_text = 'No Data'
                        print(f'  ⚠️  None outcome: {outcome_text}')
                    else:
                        print(f'  ❌ UNEXPECTED OUTCOME TYPE: {type(outcome)} = {outcome}')
                        outcome_text = 'Error'
                else:
                    print(f'  ℹ️  Status not completed: {outcome_text}')
                
                # Create the table row
                print(f'\nCreating table row:')
                row = {
                    'Date': pred.get('timestamp', '2025-01-01T00:00:00')[:10],
                    'Time': pred.get('timestamp', '2025-01-01T00:00:00')[11:16],
                    'Symbol': pred.get('symbol', 'Unknown'),
                    'Signal': signal,
                    'Confidence': f"{confidence:.1%}",
                    'Sentiment': f"{sentiment_score:+.3f}",
                    'Outcome': outcome_text,
                    'Status': pred.get('status', 'unknown')
                }
                
                table_data.append(row)
                print(f'  ✅ Successfully created row: {row["Symbol"]} | {row["Signal"]} | {row["Sentiment"]}')
                
            except Exception as e:
                print(f'  ❌ ERROR processing record {i+1}: {str(e)}')
                print(f'  📋 Full record data:')
                for key, value in pred.items():
                    print(f'    {key}: {type(value)} = {value}')
                print(f'  🔍 Traceback:')
                traceback.print_exc()
                
                # Stop on first error to debug
                print(f'\n🛑 STOPPING DEBUG ON FIRST ERROR FOR ANALYSIS')
                break
        
        # Display results
        if table_data:
            print(f'\n🎯 SUCCESSFUL PROCESSING: {len(table_data)} records')
            print('\n📋 PROCESSED DATA:')
            print('-' * 80)
            for row in table_data:
                print(f'{row["Date"]} | {row["Symbol"]} | {row["Signal"]} | {row["Sentiment"]} | {row["Status"]}')
        else:
            print('\n❌ NO RECORDS SUCCESSFULLY PROCESSED')
            
    except Exception as e:
        print(f'\n💥 CRITICAL ERROR: {str(e)}')
        traceback.print_exc()

if __name__ == '__main__':
    debug_performance_log_component()

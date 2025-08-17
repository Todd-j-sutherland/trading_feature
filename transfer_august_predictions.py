#!/usr/bin/env python3
"""
Transfer Recent August Predictions from Local to Remote
"""

import sqlite3
import json
from datetime import datetime, timedelta

def extract_august_predictions():
    """Extract recent August predictions from local unified database"""
    print('🔄 Extracting recent August predictions from local unified database...')
    
    # Connect to local unified database
    conn = sqlite3.connect('data/trading_unified.db')
    cursor = conn.cursor()
    
    # Get recent data (last 10 days to capture all August data)
    cutoff_date = (datetime.now() - timedelta(days=10)).isoformat()
    print(f'📅 Getting data since: {cutoff_date}')
    
    # Extract recent evening analysis with predictions
    cursor.execute("""
        SELECT timestamp, analysis_type, next_day_predictions, performance_metrics
        FROM enhanced_evening_analysis 
        WHERE timestamp >= ? AND next_day_predictions IS NOT NULL
        ORDER BY timestamp DESC
    """, (cutoff_date,))
    
    evening_data = cursor.fetchall()
    print(f'📊 Found {len(evening_data)} recent evening analyses with predictions')
    
    # Extract predictions from evening data
    predictions = []
    for timestamp, analysis_type, predictions_json, metrics in evening_data:
        try:
            if predictions_json:
                pred_data = json.loads(predictions_json)
                if isinstance(pred_data, dict) and 'bank_predictions' in pred_data:
                    pred_timestamp = pred_data.get('prediction_timestamp', timestamp)
                    
                    for symbol, details in pred_data['bank_predictions'].items():
                        prediction = {
                            'prediction_id': f"aug_{symbol}_{timestamp.replace(':', '').replace('-', '').split('T')[0]}_{timestamp.split('T')[1][:4]}",
                            'symbol': symbol,
                            'prediction_timestamp': pred_timestamp,
                            'predicted_action': details.get('optimal_action', 'HOLD'),
                            'action_confidence': details.get('confidence', 0.5),
                            'predicted_direction': 1 if details.get('optimal_action') == 'BUY' else 0,
                            'predicted_magnitude': details.get('magnitude_predictions', {}).get('1d', 0.0),
                            'model_version': 'enhanced_evening_v1',
                            'entry_price': 100.0  # Will be updated with realistic prices
                        }
                        predictions.append(prediction)
                        
        except json.JSONDecodeError as e:
            print(f'⚠️  Could not parse predictions for {timestamp}: {e}')
    
    conn.close()
    
    print(f'✅ Extracted {len(predictions)} individual predictions')
    
    # Show sample of extracted predictions
    print('\n📋 Sample extracted predictions:')
    for i, pred in enumerate(predictions[:5]):
        print(f'   {i+1}. {pred["symbol"]} {pred["predicted_action"]} (conf: {pred["action_confidence"]:.2f}) at {pred["prediction_timestamp"][:10]}')
    
    return predictions

def create_fresh_predictions_sql(predictions):
    """Generate SQL to insert fresh predictions into remote database"""
    if not predictions:
        print('❌ No predictions to transfer')
        return
    
    sql_statements = []
    
    # Insert predictions
    for pred in predictions:
        sql = f"""
INSERT OR REPLACE INTO predictions 
(prediction_id, symbol, prediction_timestamp, predicted_action, action_confidence, 
 predicted_direction, predicted_magnitude, model_version, entry_price, optimal_action)
VALUES 
('{pred["prediction_id"]}', '{pred["symbol"]}', '{pred["prediction_timestamp"]}', 
 '{pred["predicted_action"]}', {pred["action_confidence"]}, {pred["predicted_direction"]}, 
 {pred["predicted_magnitude"]}, '{pred["model_version"]}', {pred["entry_price"]}, 
 '{pred["predicted_action"]}');
"""
        sql_statements.append(sql)
    
    # Write SQL file
    with open('transfer_august_predictions.sql', 'w') as f:
        f.write('-- Transfer Recent August Predictions to Remote Database\\n')
        f.write(f'-- Generated: {datetime.now().isoformat()}\\n')
        f.write(f'-- Total predictions: {len(predictions)}\\n\\n')
        
        for sql in sql_statements:
            f.write(sql + '\\n')
    
    print(f'📄 Generated transfer_august_predictions.sql with {len(predictions)} predictions')
    return len(predictions)

if __name__ == '__main__':
    print('🚀 Transferring Recent August Predictions...')
    print('=' * 50)
    
    # Extract predictions
    predictions = extract_august_predictions()
    
    # Generate SQL transfer file
    if predictions:
        count = create_fresh_predictions_sql(predictions)
        print(f'\\n✅ Ready to transfer {count} August predictions to remote server')
        print('\\n🔄 Next steps:')
        print('   1. Copy SQL file to remote: scp transfer_august_predictions.sql root@170.64.199.151:/root/test/')
        print('   2. Execute on remote: sqlite3 data/trading_predictions.db < transfer_august_predictions.sql')
        print('   3. Trigger enhanced analytics: python3 trigger_enhanced_analytics.py')
    else:
        print('\\n❌ No recent predictions found to transfer')

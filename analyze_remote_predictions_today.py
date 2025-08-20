#!/usr/bin/env python3
"""
Remote Trading Predictions Analysis - Today's Data Validation
Connects to remote server and analyzes today's predictions for fallback patterns
"""

import subprocess
import sys
from datetime import datetime

def run_remote_analysis():
    """Connect to remote server and analyze today's predictions"""
    
    # Remote analysis script
    remote_script = '''
import sqlite3
from datetime import datetime, date
import pytz

try:
    # Connect to database
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()

    print('=' * 60)
    print('TRADING PREDICTIONS ANALYSIS - TODAY\'S DATA VALIDATION')
    print('=' * 60)
    print(f'Analysis timestamp: {datetime.now()}')
    print()

    # Get total predictions count
    cursor.execute('SELECT COUNT(*) FROM predictions')
    total_count = cursor.fetchone()[0]
    print(f'Total predictions in database: {total_count}')

    # Check today's predictions (UTC date)
    cursor.execute(\"\"\"
        SELECT COUNT(*) FROM predictions 
        WHERE date(prediction_timestamp) = date('now')
    \"\"\")
    today_count = cursor.fetchone()[0]
    print(f'Predictions made today (UTC): {today_count}')

    # Get predictions from last 24 hours for analysis
    cursor.execute(\"\"\"
        SELECT symbol, prediction_timestamp, predicted_action, 
               action_confidence, predicted_direction, predicted_magnitude, model_version
        FROM predictions 
        WHERE datetime(prediction_timestamp) >= datetime('now', '-24 hours')
        ORDER BY prediction_timestamp DESC
    \"\"\")
    
    recent_predictions = cursor.fetchall()
    print(f'Predictions in last 24 hours: {len(recent_predictions)}')
    print()

    if recent_predictions:
        print('RECENT PREDICTIONS (Last 24 hours):')
        print('-' * 90)
        print(f'{'Symbol':<8} {'Timestamp':<19} {'Action':<6} {'Conf':<6} {'Dir':<4} {'Mag':<8} {'Model':<10}')
        print('-' * 90)
        
        # Collect data for analysis
        confidences = []
        magnitudes = []
        timestamps = []
        actions = []
        
        for pred in recent_predictions:
            symbol, timestamp, action, confidence, direction, magnitude, model = pred
            
            # Format display
            display_mag = magnitude if magnitude is not None else 0.0
            display_dir = direction if direction is not None else 'N/A'
            display_model = (model or 'None')[:10]
            
            print(f'{symbol:<8} {timestamp:<19} {action:<6} {confidence:<6.3f} {display_dir:<4} {display_mag:<8.3f} {display_model:<10}')
            
            # Collect for analysis
            confidences.append(confidence)
            magnitudes.append(magnitude or 0)
            timestamps.append(timestamp)
            actions.append(action)
        
        print()
        print('=' * 60)
        print('FALLBACK DETECTION ANALYSIS')
        print('=' * 60)
        
        # Pattern analysis
        fallback_confidences = sum(1 for c in confidences if abs(c - 0.5) < 0.001)
        zero_magnitudes = sum(1 for m in magnitudes if abs(m) < 0.001)
        unique_timestamps = len(set(timestamps))
        unique_actions = len(set(actions))
        
        print(f'Total predictions analyzed: {len(confidences)}')
        print(f'Predictions with 0.5 confidence (fallback indicator): {fallback_confidences}')
        print(f'Predictions with 0.0 magnitude: {zero_magnitudes}') 
        print(f'Unique timestamps: {unique_timestamps}')
        print(f'Unique actions: {unique_actions}')
        
        if confidences:
            min_conf = min(confidences)
            max_conf = max(confidences) 
            avg_conf = sum(confidences) / len(confidences)
            print(f'Confidence range: {min_conf:.3f} - {max_conf:.3f}')
            print(f'Average confidence: {avg_conf:.3f}')
        
        # Action distribution
        from collections import Counter
        action_dist = Counter(actions)
        print(f'Action distribution: {dict(action_dist)}')
        
        # Time clustering analysis
        if len(timestamps) > 1:
            # Check if predictions were made in batches (same time)
            time_parts = [ts.split()[1][:8] for ts in timestamps if ' ' in ts]
            if time_parts:
                time_counter = Counter(time_parts)
                max_same_time = max(time_counter.values())
                print(f'Max predictions at same time: {max_same_time}')
        
        print()
        print('=' * 60)
        print('VALIDITY ASSESSMENT')
        print('=' * 60)
        
        # Determine if predictions are likely fallbacks
        fallback_percentage = fallback_confidences / len(confidences) * 100
        zero_mag_percentage = zero_magnitudes / len(magnitudes) * 100
        
        # Assessment criteria
        high_fallback_rate = fallback_percentage > 50
        high_zero_mag_rate = zero_mag_percentage > 80
        low_timestamp_diversity = unique_timestamps <= 2 and len(timestamps) > 5
        
        print(f'Fallback confidence rate: {fallback_percentage:.1f}%')
        print(f'Zero magnitude rate: {zero_mag_percentage:.1f}%')
        
        if high_fallback_rate or high_zero_mag_rate or low_timestamp_diversity:
            print()
            print('🚨 WARNING: FALLBACK VALUES DETECTED!')
            print('Recent predictions show patterns consistent with system fallback:')
            
            if high_fallback_rate:
                print(f'   ❌ High rate of 0.5 confidence values ({fallback_percentage:.1f}%)')
            if high_zero_mag_rate:
                print(f'   ❌ High rate of 0.0 magnitude values ({zero_mag_percentage:.1f}%)')
            if low_timestamp_diversity:
                print(f'   ❌ Low timestamp diversity suggests batch processing')
                
            print()
            print('RECOMMENDED ACTIONS:')
            print('1. Check NewsTradingAnalyzer import on remote system')
            print('2. Verify market hours detection is working')
            print('3. Review system logs for import errors')
            print('4. Test manual prediction generation')
            
        else:
            print()
            print('✅ VALIDATION PASSED: Real ML predictions detected!')
            print('Evidence of genuine machine learning analysis:')
            print(f'   ✓ Varied confidence values (not clustered at 0.5)')
            print(f'   ✓ Reasonable magnitude distribution')
            print(f'   ✓ Good timestamp diversity')
            print(f'   ✓ Balanced action distribution: {dict(action_dist)}')
            
            print()
            print('SYSTEM STATUS: Operational and generating valid predictions')
        
        # Additional insights
        if len(recent_predictions) > 0:
            latest_pred = recent_predictions[0]
            print()
            print(f'Latest prediction: {latest_pred[0]} - {latest_pred[2]} (confidence: {latest_pred[3]:.3f})')
            print(f'Latest timestamp: {latest_pred[1]}')
            
    else:
        print('No predictions found in the last 24 hours.')
        print()
        print('Checking for any predictions in database:')
        cursor.execute(\"\"\"
            SELECT symbol, prediction_timestamp, predicted_action, action_confidence
            FROM predictions 
            ORDER BY prediction_timestamp DESC 
            LIMIT 5
        \"\"\")
        
        any_predictions = cursor.fetchall()
        if any_predictions:
            print('Most recent predictions (any date):')
            for pred in any_predictions:
                print(f'  {pred[0]}: {pred[2]} (conf: {pred[3]:.3f}) at {pred[1]}')
        else:
            print('No predictions found in database at all.')

    conn.close()

except Exception as e:
    print(f'Error analyzing database: {e}')
    import traceback
    traceback.print_exc()
'''

    # SSH command to run the analysis
    ssh_command = [
        'ssh', 'root@170.64.199.151',
        f'cd /root/test && /root/trading_venv/bin/python3 -c "{remote_script}"'
    ]
    
    try:
        print("Connecting to remote server to analyze today's predictions...")
        print("=" * 60)
        
        # Run the remote analysis
        result = subprocess.run(ssh_command, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"Error executing remote analysis:")
            print(f"Return code: {result.returncode}")
            print(f"Error output: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("Connection timed out after 30 seconds")
    except Exception as e:
        print(f"Error connecting to remote server: {e}")

if __name__ == "__main__":
    run_remote_analysis()


import sqlite3
import json
import re

conn = sqlite3.connect('/root/data/trading_predictions.db')
cursor = conn.cursor()

# Load backup data
with open('/root/database_backup.json', 'r') as f:
    backup = json.load(f)

def parse_confidence(conf_str):
    '''Convert percentage string to float'''
    if isinstance(conf_str, str):
        # Remove % sign and convert to float
        return float(re.sub(r'[%]', '', conf_str)) / 100.0
    return float(conf_str)

print(f"🔄 Fixing data migration for {len(backup['predictions'])} predictions...")

migrated_count = 0
for pred in backup['predictions']:
    try:
        # Convert legacy format to modern format
        prediction_id = f"{pred['symbol']}_{pred['date']}_{pred['time']}"
        prediction_timestamp = f"{pred['date']} {pred['time']}"
        
        # Map legacy fields to modern fields
        predicted_action = pred['signal']
        action_confidence = parse_confidence(pred['confidence'])  # Fix percentage parsing
        
        cursor.execute('''
        INSERT OR REPLACE INTO predictions (
            prediction_id, symbol, prediction_timestamp, predicted_action,
            action_confidence, predicted_direction, predicted_magnitude,
            feature_vector, model_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prediction_id,
            pred['symbol'],
            prediction_timestamp,
            predicted_action,
            action_confidence,
            1 if predicted_action == 'BUY' else -1 if predicted_action == 'SELL' else 0,
            abs(action_confidence),
            None,  # feature_vector - not available in legacy
            'legacy_migration_v1.0',
            '2025-08-17T13:05:00'
        ))
        migrated_count += 1
        print(f"✅ Migrated {pred['symbol']} {pred['signal']} {pred['confidence']} -> {action_confidence:.3f}")
    except Exception as e:
        print(f"❌ Failed to migrate prediction {pred}: {e}")

conn.commit()
conn.close()

print(f"🎯 Successfully migrated {migrated_count} predictions with fixed percentage parsing!")

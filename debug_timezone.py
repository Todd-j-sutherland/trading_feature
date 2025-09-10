import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/trading_predictions.db')
cursor = conn.cursor()

print('=== Timezone Issue Analysis ===')

# Check current time references
cursor.execute("SELECT datetime('now')")
sqlite_now = cursor.fetchone()[0]
print(f'SQLite now (UTC): {sqlite_now}')

cursor.execute("SELECT datetime('now', '-4 hours')")
four_hours_ago = cursor.fetchone()[0]
print(f'SQLite 4h ago (UTC): {four_hours_ago}')

# Check prediction timestamps
cursor.execute('SELECT prediction_timestamp FROM predictions ORDER BY prediction_timestamp DESC LIMIT 3')
prediction_times = cursor.fetchall()
print(f'\nPrediction timestamps (with timezone):')
for row in prediction_times:
    print(f'  {row[0]}')

# Check if we can convert timezone-aware timestamps
cursor.execute("""
SELECT prediction_timestamp, 
       substr(prediction_timestamp, 1, 19) as utc_part,
       datetime(substr(prediction_timestamp, 1, 19)) as converted
FROM predictions 
ORDER BY prediction_timestamp DESC 
LIMIT 3
""")
conversions = cursor.fetchall()
print(f'\nTimezone conversion analysis:')
for row in conversions:
    print(f'  Original: {row[0]}')
    print(f'  UTC part: {row[1]}') 
    print(f'  Converted: {row[2]}')
    print()

# Test corrected query
print('=== Testing Corrected Query ===')
cursor.execute("""
SELECT COUNT(*) FROM predictions p 
LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id 
WHERE o.prediction_id IS NULL 
  AND datetime(substr(p.prediction_timestamp, 1, 19)) < datetime('now', '-4 hours')
""")
corrected_count = cursor.fetchone()[0]
print(f'Corrected query count: {corrected_count}')

conn.close()

import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/trading_predictions.db')
cursor = conn.cursor()

print('=== Debugging SQL Query Parts ===')

# Check predictions table
cursor.execute('SELECT COUNT(*) FROM predictions')
total_predictions = cursor.fetchone()[0]
print(f'Total predictions: {total_predictions}')

# Check outcomes table  
cursor.execute('SELECT COUNT(*) FROM outcomes')
total_outcomes = cursor.fetchone()[0]
print(f'Total outcomes: {total_outcomes}')

# Check time constraints
print('\n=== Time Constraints ===')
cursor.execute('SELECT datetime(now, -4 hours)')
four_hours_ago = cursor.fetchone()[0]
print(f'4 hours ago: {four_hours_ago}')

cursor.execute('SELECT datetime(now, -72 hours)')
seventy_two_hours_ago = cursor.fetchone()[0]
print(f'72 hours ago: {seventy_two_hours_ago}')

# Test each part of the query
print('\n=== Testing Query Parts ===')

# Part 1: All predictions
cursor.execute('SELECT COUNT(*) FROM predictions p')
all_preds = cursor.fetchone()[0]
print(f'All predictions: {all_preds}')

# Part 2: After LEFT JOIN
cursor.execute('SELECT COUNT(*) FROM predictions p LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id')
after_join = cursor.fetchone()[0]
print(f'After LEFT JOIN: {after_join}')

# Part 3: NULL outcomes only
cursor.execute('SELECT COUNT(*) FROM predictions p LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id WHERE o.prediction_id IS NULL')
null_outcomes = cursor.fetchone()[0]
print(f'NULL outcomes only: {null_outcomes}')

# Part 4: Add time constraints one by one
cursor.execute('''
SELECT COUNT(*) FROM predictions p 
LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id 
WHERE o.prediction_id IS NULL 
  AND p.prediction_timestamp < datetime(now, -4 hours)
''')
old_enough = cursor.fetchone()[0]
print(f'Old enough (>4h): {old_enough}')

cursor.execute('''
SELECT COUNT(*) FROM predictions p 
LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id 
WHERE o.prediction_id IS NULL 
  AND p.prediction_timestamp < datetime(now, -4 hours)
  AND p.prediction_timestamp > datetime(now, -72 hours)
''')
final_count = cursor.fetchone()[0]
print(f'Final query count: {final_count}')

# Show sample timestamps
print('\n=== Sample Prediction Timestamps ===')
cursor.execute('SELECT prediction_timestamp FROM predictions ORDER BY prediction_timestamp DESC LIMIT 5')
for row in cursor.fetchall():
    print(f'  {row[0]}')

conn.close()

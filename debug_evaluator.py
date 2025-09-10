import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/trading_predictions.db')
cursor = conn.cursor()

# Test the exact query the evaluator uses
query = '''
SELECT p.prediction_id, p.symbol, p.prediction_timestamp,
       p.predicted_action, p.action_confidence, p.entry_price
FROM predictions p
LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
WHERE o.prediction_id IS NULL
  AND p.prediction_timestamp < datetime('now', '-4 hours')
  AND p.prediction_timestamp > datetime('now', '-72 hours')
ORDER BY p.prediction_timestamp DESC
LIMIT 50
'''

print('Testing evaluator SQL query:')
cursor.execute(query)
results = cursor.fetchall()

print(f'Query returned {len(results)} predictions')

if len(results) > 0:
    print('First 5 results:')
    for row in results[:5]:
        print(f'  {row[1]} {row[3]} at {row[2]}')
else:
    print('No results - investigating why...')

conn.close()

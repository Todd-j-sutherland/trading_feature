import sqlite3
import re

conn = sqlite3.connect("predictions.db")
cursor = conn.cursor()

query = "SELECT prediction_id, symbol, action_confidence, confidence_breakdown FROM predictions WHERE confidence_breakdown LIKE ? AND action_confidence < 0.8 ORDER BY created_at DESC LIMIT 10"
cursor.execute(query, ("%ML:%",))

records = cursor.fetchall()
print(f"Found {len(records)} records to fix")

for pred_id, symbol, current_conf, breakdown in records:
    final_match = re.search(r"= ([0-9.]+)$", breakdown)
    if final_match:
        new_conf = float(final_match.group(1))
        if new_conf > current_conf:
            print(f"Fixing {symbol}: {current_conf:.3f} -> {new_conf:.3f}")
            cursor.execute("UPDATE predictions SET action_confidence = ? WHERE prediction_id = ?", (new_conf, pred_id))

conn.commit()
conn.close()
print("Fixed ML confidence values")

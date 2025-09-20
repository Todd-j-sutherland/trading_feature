import sqlite3
import re

conn = sqlite3.connect("predictions.db")
cursor = conn.cursor()

cursor.execute("SELECT id, symbol, action_confidence, confidence_breakdown FROM predictions WHERE confidence_breakdown LIKE '%ML:%' AND action_confidence < 0.8 ORDER BY created_at DESC LIMIT 10")

records = cursor.fetchall()
print(f"Found {len(records)} records to fix")

for record_id, symbol, current_conf, breakdown in records:
    final_match = re.search(r"= ([0-9.]+)$", breakdown)
    if final_match:
        new_conf = float(final_match.group(1))
        if new_conf > current_conf:
            print(f"Fixing {symbol}: {current_conf:.3f} -> {new_conf:.3f}")
            cursor.execute("UPDATE predictions SET action_confidence = ? WHERE id = ?", (new_conf, record_id))

conn.commit()
conn.close()
print("Done")

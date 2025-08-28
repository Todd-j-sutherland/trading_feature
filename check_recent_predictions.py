import sqlite3
from datetime import datetime

# Check latest predictions
conn = sqlite3.connect("predictions.db")
cursor = conn.cursor()

# Get count and latest timestamp
cursor.execute("SELECT COUNT(*) FROM predictions")
total = cursor.fetchone()[0]

cursor.execute("SELECT MAX(prediction_timestamp) FROM predictions")
latest = cursor.fetchone()[0]

print(f"📊 Total predictions: {total}")
print(f"🕐 Latest prediction: {latest}")

# Check recent predictions (last 10 minutes)
cursor.execute("""
    SELECT symbol, predicted_action, action_confidence, entry_price, prediction_timestamp 
    FROM predictions 
    WHERE prediction_timestamp > datetime("now", "-10 minutes")
    ORDER BY prediction_timestamp DESC
""")

recent = cursor.fetchall()
print(f"\n📈 Recent predictions (last 10 min): {len(recent)}")

for r in recent:
    symbol, action, conf, price, timestamp = r
    price_str = f"${price:.2f}" if price and price > 0 else "NO PRICE"
    print(f"  {symbol}: {action} (Conf: {conf:.3f}, Price: {price_str}) [{timestamp}]")

conn.close()

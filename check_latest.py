import sqlite3

conn = sqlite3.connect("predictions.db")
cursor = conn.cursor()

cursor.execute("SELECT MAX(prediction_timestamp) FROM predictions")
latest = cursor.fetchone()[0]
print(f"Latest prediction timestamp: {latest}")

cursor.execute("SELECT COUNT(*) FROM predictions")
total = cursor.fetchone()[0]
print(f"Total predictions: {total}")

conn.close()

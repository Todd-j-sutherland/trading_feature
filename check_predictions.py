import sqlite3
from datetime import datetime

conn = sqlite3.connect("predictions.db")
cursor = conn.cursor()

# Get total count
cursor.execute("SELECT COUNT(*) FROM predictions")
total = cursor.fetchone()[0]
print(f"Total predictions: {total}")

# Get recent predictions
cursor.execute("""SELECT symbol, prediction_timestamp, predicted_action, 
                         action_confidence, entry_price 
                  FROM predictions 
                  ORDER BY prediction_timestamp DESC LIMIT 10""")
recent = cursor.fetchall()

print("\nMOST RECENT PREDICTIONS:")
print("=" * 50)
for r in recent:
    symbol, timestamp, action, confidence, price = r
    
    if price and price > 0:
        status = "VALID"
        price_str = f"${price:.2f}"
    else:
        status = "NO PRICE"
        price_str = "N/A"
        
    print(f"{symbol}: {action} (Conf: {confidence:.3f}, Price: {price_str}) [{timestamp}] - {status}")

# Check today specifically
today = datetime.now().strftime("%Y-%m-%d")
cursor.execute("SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = ?", (today,))
today_count = cursor.fetchone()[0]
print(f"\nPredictions from today ({today}): {today_count}")

if today_count > 0:
    cursor.execute("""SELECT symbol, predicted_action, action_confidence, entry_price 
                      FROM predictions WHERE DATE(prediction_timestamp) = ?""", (today,))
    today_rows = cursor.fetchall()
    
    print("\nTODAYS PREDICTIONS SUMMARY:")
    valid_prices = 0
    for row in today_rows:
        symbol, action, conf, price = row
        if price and price > 0:
            valid_prices += 1
            status = "VALID PRICE"
        else:
            status = "NO PRICE"
        print(f"  {symbol}: {action} ({status})")
    
    print(f"\nPredictions with valid prices: {valid_prices}/{today_count}")

conn.close()

import sqlite3
import yfinance as yf
from datetime import datetime

print("TESTING PRICE INTEGRATION AND SAVING")
print("=" * 40)

# Test price fetching
symbol = "CBA.AX"
try:
    ticker = yf.Ticker(symbol)
    hist_data = ticker.history(period="1d")
    if not hist_data.empty:
        entry_price = float(hist_data["Close"].iloc[-1])
        print(f"✅ {symbol}: Got price ${entry_price:.2f}")
    else:
        entry_price = 0.0
        print(f"⚠️ {symbol}: No price data")
except Exception as e:
    entry_price = 0.0
    print(f"❌ {symbol}: Price error: {e}")

print(f"Entry price to save: {entry_price}")

# Test saving to database
conn = sqlite3.connect("predictions.db")
cursor = conn.cursor()

prediction_id = f"test_{symbol}_{datetime.now().strftime("%%Y%%m%%d_%%H%%M%%S")}"
try:
    cursor.execute("""
        INSERT OR REPLACE INTO predictions 
        (prediction_id, symbol, prediction_timestamp, predicted_action,
         action_confidence, predicted_direction, predicted_magnitude,
         model_version, entry_price, optimal_action)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prediction_id,
        symbol,
        datetime.now().isoformat(),
        "BUY",
        0.999,
        1,
        0.05,
        "test_model",
        entry_price,
        "BUY"
    ))
    conn.commit()
    print(f"✅ Test prediction saved with entry_price: {entry_price}")
    
    # Verify it was saved correctly
    cursor.execute("SELECT entry_price FROM predictions WHERE prediction_id = ?", (prediction_id,))
    saved_price = cursor.fetchone()[0]
    print(f"✅ Verified saved price: {saved_price}")
    
except Exception as e:
    print(f"❌ Save error: {e}")
    import traceback
    traceback.print_exc()

conn.close()

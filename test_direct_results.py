#!/usr/bin/env python3
from enhanced_efficient_system_market_aware import MarketAwarePredictor

# Test one symbol 
predictor = MarketAwarePredictor()
result = predictor.make_enhanced_prediction("CBA.AX")

print("=== Direct System Results ===")
print(f"Action: {result["predicted_action"]}")
print(f"Confidence: {result["action_confidence"]:.3f}")
print(f"Breakdown: {result["prediction_details"]["final_score_breakdown"]}")

# Check what gets saved to database
import sqlite3
conn = sqlite3.connect("predictions.db")
cursor = conn.cursor()
cursor.execute("SELECT action_confidence, predicted_action, confidence_breakdown FROM predictions WHERE symbol=CBA.AX ORDER BY created_at DESC LIMIT 1")
row = cursor.fetchone()
if row:
    print(f"\n=== Database Results ===")
    print(f"Saved Action: {row[1]}")
    print(f"Saved Confidence: {row[0]:.3f}")
    print(f"Saved Breakdown: {row[2]}")
else:
    print("No database record found")
conn.close()

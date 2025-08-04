#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime

print("🧹 REMOVING SYNTHETIC OUTCOMES")
print("=" * 50)

db_path = "data/ml_models/enhanced_training_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check before
cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
total_before = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE exit_timestamp = prediction_timestamp")
synthetic_count = cursor.fetchone()[0]

print(f"📊 Before: {total_before} total, {synthetic_count} synthetic")

# Remove synthetic outcomes
if synthetic_count > 0:
    cursor.execute("DELETE FROM enhanced_outcomes WHERE exit_timestamp = prediction_timestamp")
    removed = cursor.rowcount
    conn.commit()
    print(f"✅ Removed {removed} synthetic outcomes")

# Check after
cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
real_outcomes = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM enhanced_features")
features = cursor.fetchone()[0]

print(f"📊 After: {features} features, {real_outcomes} REAL outcomes")
print(f"🎯 Training ready: {'✅ YES' if features >= 50 and real_outcomes >= 50 else '❌ NO'}")

conn.close()
print("✅ CLEANUP COMPLETE - ONLY real market data remains!")

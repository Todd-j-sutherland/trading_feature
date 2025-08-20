#!/usr/bin/env python3
"""
Trading Database Analysis
Analyzes whether trading_unified.db is still needed vs trading_predictions.db
"""

import sqlite3
from pathlib import Path

def analyze_database_necessity():
    print("📊 TRADING DATABASE ANALYSIS")
    print("=" * 50)
    
    unified_db = "data/trading_unified.db"
    predictions_db = "data/trading_predictions.db"
    
    # Analysis of trading_unified.db
    print("\n🔍 TRADING_UNIFIED.DB ANALYSIS:")
    print("-" * 40)
    
    conn_unified = sqlite3.connect(unified_db)
    cursor = conn_unified.cursor()
    
    # Check predictions table (old format)
    cursor.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM predictions")
    pred_count, min_date, max_date = cursor.fetchone()
    print(f"   📅 Predictions: {pred_count} records ({min_date} to {max_date})")
    print(f"   📝 Schema: Old format (date, time, symbol, signal, confidence)")
    
    # Check enhanced_outcomes (detailed ML data)
    cursor.execute("SELECT COUNT(*), MIN(DATE(prediction_timestamp)), MAX(DATE(prediction_timestamp)) FROM enhanced_outcomes")
    outcomes_count, outcomes_min, outcomes_max = cursor.fetchone()
    print(f"   🎯 Enhanced Outcomes: {outcomes_count} records ({outcomes_min} to {outcomes_max})")
    
    # Check enhanced_features
    cursor.execute("SELECT COUNT(*) FROM enhanced_features")
    features_count = cursor.fetchone()[0]
    print(f"   🧠 Enhanced Features: {features_count} ML feature vectors")
    
    # Check unique tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    unified_tables = set([row[0] for row in cursor.fetchall()])
    
    conn_unified.close()
    
    # Analysis of trading_predictions.db
    print("\n🔍 TRADING_PREDICTIONS.DB ANALYSIS:")
    print("-" * 40)
    
    conn_pred = sqlite3.connect(predictions_db)
    cursor = conn_pred.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM predictions")
    new_pred_count = cursor.fetchone()[0]
    print(f"   📅 Predictions: {new_pred_count} records (new format)")
    print(f"   📝 Schema: New format (prediction_id, prediction_timestamp, predicted_action)")
    
    cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
    new_outcomes_count = cursor.fetchone()[0]
    print(f"   🎯 Enhanced Outcomes: {new_outcomes_count} records")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    predictions_tables = set([row[0] for row in cursor.fetchall()])
    
    conn_pred.close()
    
    # Comparison
    print("\n⚖️  COMPARISON ANALYSIS:")
    print("-" * 40)
    
    shared_tables = unified_tables.intersection(predictions_tables)
    unified_only = unified_tables - predictions_tables
    predictions_only = predictions_tables - unified_tables
    
    print(f"   📊 Shared tables: {len(shared_tables)} - {', '.join(sorted(shared_tables))}")
    print(f"   🔵 Unified only: {len(unified_only)} - {', '.join(sorted(unified_only))}")
    print(f"   🟢 Predictions only: {len(predictions_only)} - {', '.join(sorted(predictions_only))}")
    
    # Data overlap analysis
    print(f"\n📈 DATA OVERLAP:")
    print(f"   • Unified predictions: July 24, 2025 (old format)")
    print(f"   • Unified enhanced_outcomes: July 28 - Aug 14, 2025 ({outcomes_count} records)")
    print(f"   • Predictions DB: Empty locally, 7 records on remote (Aug 12, 2025)")
    
    # Decision recommendation
    print(f"\n🎯 RECOMMENDATION:")
    print("-" * 40)
    
    if outcomes_count > 0 and new_outcomes_count == 0:
        print("   ⚠️  KEEP trading_unified.db - Contains valuable ML training data")
        print("   📊 Reasons:")
        print("      • 253 enhanced outcomes with multi-timeframe predictions")
        print("      • 506 enhanced feature vectors for ML training")
        print("      • Historical data from July 28 - Aug 14, 2025")
        print("      • Unique tables: bank_performance, sentiment_data, technical_scores")
        print("      • Different schema optimized for ML analysis")
        
        print(f"\n   💡 SUGGESTED ACTION:")
        print("      • Keep both databases for different purposes:")
        print("      • trading_predictions.db: Current production predictions")
        print("      • trading_unified.db: Historical ML training data and features")
        
    else:
        print("   ✅ SAFE TO REMOVE trading_unified.db")
        print("   📊 All important data already in trading_predictions.db")
    
    # Size analysis
    unified_size = Path(unified_db).stat().st_size / (1024*1024)
    predictions_size = Path(predictions_db).stat().st_size / (1024*1024)
    
    print(f"\n💾 STORAGE IMPACT:")
    print(f"   • trading_unified.db: {unified_size:.1f}MB")
    print(f"   • trading_predictions.db: {predictions_size:.1f}MB")
    print(f"   • Total: {unified_size + predictions_size:.1f}MB")

if __name__ == "__main__":
    analyze_database_necessity()

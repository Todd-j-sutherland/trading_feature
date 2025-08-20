#!/usr/bin/env python3
"""
Analyze and clean up incorrect predictions in the database
"""

import sqlite3
from datetime import datetime, timedelta

def analyze_predictions():
    """Analyze predictions to identify data quality issues"""
    
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    print("🔍 PREDICTION QUALITY ANALYSIS")
    print("=" * 50)
    
    # Get all predictions
    cursor.execute('''
        SELECT prediction_id, symbol, prediction_timestamp, predicted_action, 
               action_confidence, predicted_magnitude, entry_price, model_version
        FROM predictions 
        ORDER BY prediction_timestamp DESC
    ''')
    
    predictions = cursor.fetchall()
    print(f"📊 Total predictions in database: {len(predictions)}")
    
    # Analyze for quality issues
    issues = {
        'confidence_equals_magnitude': 0,
        'zero_entry_price': 0,
        'old_predictions': 0,
        'non_ml_model': 0,
        'suspicious_confidence_range': 0
    }
    
    suspect_predictions = []
    
    for pred in predictions:
        pred_id, symbol, timestamp, action, confidence, magnitude, entry_price, model_version = pred
        
        # Check for confidence = magnitude (classic traditional analysis bug)
        if abs(confidence - magnitude) < 0.001:  # Essentially equal
            issues['confidence_equals_magnitude'] += 1
            suspect_predictions.append((pred_id, 'confidence_equals_magnitude', confidence, magnitude))
        
        # Check for zero entry price
        if entry_price == 0.0:
            issues['zero_entry_price'] += 1
            suspect_predictions.append((pred_id, 'zero_entry_price', entry_price, ''))
        
        # Check for old predictions (more than 30 days)
        pred_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00').replace('+00:00', ''))
        if (datetime.now() - pred_time).days > 30:
            issues['old_predictions'] += 1
            suspect_predictions.append((pred_id, 'old_prediction', timestamp, ''))
        
        # Check for non-ML model versions
        if model_version != 'enhanced_ml_v1':
            issues['non_ml_model'] += 1
            suspect_predictions.append((pred_id, 'non_ml_model', model_version, ''))
        
        # Check for suspicious confidence ranges (traditional analysis often uses 0.6-0.8)
        if 0.6 <= confidence <= 0.8 and abs(confidence - magnitude) < 0.001:
            issues['suspicious_confidence_range'] += 1
    
    print("\n🚨 QUALITY ISSUES DETECTED:")
    print("-" * 30)
    for issue, count in issues.items():
        if count > 0:
            print(f"❌ {issue.replace('_', ' ').title()}: {count}")
    
    print(f"\n📋 SUSPECT PREDICTIONS:")
    print("-" * 30)
    for pred_id, issue_type, value1, value2 in suspect_predictions[:10]:  # Show first 10
        print(f"🔍 {pred_id}: {issue_type} ({value1}, {value2})")
    
    if len(suspect_predictions) > 10:
        print(f"... and {len(suspect_predictions) - 10} more")
    
    # Recommendation
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 20)
    
    if issues['confidence_equals_magnitude'] > 0:
        print("🗑️  Delete predictions where confidence = magnitude (traditional analysis artifacts)")
    
    if issues['old_predictions'] > 0:
        print("🗑️  Delete predictions older than 30 days")
    
    if issues['zero_entry_price'] > 0:
        print("💰 Update entry prices for predictions with 0.0 entry price")
    
    return suspect_predictions

def clean_suspect_predictions():
    """Clean up suspect predictions after user confirmation"""
    
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    print("\n🧹 CLEANING SUSPECT PREDICTIONS")
    print("=" * 40)
    
    # Delete predictions where confidence equals magnitude (traditional analysis artifacts)
    cursor.execute('''
        DELETE FROM predictions 
        WHERE ABS(action_confidence - predicted_magnitude) < 0.001
        AND model_version != 'enhanced_ml_v1'
    ''')
    deleted_traditional = cursor.rowcount
    
    # Delete old predictions (older than 30 days)
    cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
    cursor.execute('''
        DELETE FROM predictions 
        WHERE prediction_timestamp < ?
    ''', (cutoff_date,))
    deleted_old = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"✅ Deleted {deleted_traditional} traditional analysis artifacts")
    print(f"✅ Deleted {deleted_old} old predictions")
    print(f"🎉 Database cleaned!")

if __name__ == '__main__':
    analyze_predictions()
    
    # Uncomment to actually clean (for safety, require manual action)
    # clean_suspect_predictions()

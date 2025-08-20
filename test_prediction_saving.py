#!/usr/bin/env python3
"""
Test the enhanced morning analyzer with error detection
"""

import sqlite3
from datetime import datetime

def test_prediction_saving():
    """Test saving predictions with error detection"""
    
    # Use a separate test database to avoid polluting production data
    test_db_path = 'data/test_predictions.db'
    
    # Simulate different types of ML prediction outputs
    test_cases = [
        {
            'name': 'Valid ML Prediction',
            'symbol': 'CBA.AX',
            'prediction': {
                'optimal_action': 'BUY',
                'confidence_scores': {'average': 0.847, '1h': 0.82, '4h': 0.85, '1d': 0.87},
                'magnitude_predictions': {'1h': 1.2, '4h': 2.1, '1d': 3.5},
                'direction_predictions': {'1h': 1, '4h': 1, '1d': 1}
            }
        },
        {
            'name': 'Missing Confidence Scores',
            'symbol': 'WBC.AX', 
            'prediction': {
                'optimal_action': 'SELL',
                'magnitude_predictions': {'1h': -0.8, '4h': -1.2, '1d': -1.8},
                'direction_predictions': {'1h': 0, '4h': 0, '1d': 0}
            }
        },
        {
            'name': 'Missing Magnitude Predictions',
            'symbol': 'ANZ.AX',
            'prediction': {
                'optimal_action': 'HOLD',
                'confidence_scores': {'average': 0.745},
                'direction_predictions': {'1h': 1, '4h': 0, '1d': 1}
            }
        },
        {
            'name': 'Traditional Analysis Output (Wrong Structure)',
            'symbol': 'NAB.AX',
            'prediction': {
                'final_signal': 'BUY',
                'combined_score': 0.650,
                'overall_confidence': 0.650  # This would cause confidence=magnitude issue
            }
        }
    ]
    
    # Test each case
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Create the predictions table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            prediction_timestamp DATETIME NOT NULL,
            predicted_action TEXT NOT NULL,
            action_confidence REAL NOT NULL,
            predicted_direction INTEGER,
            predicted_magnitude REAL,
            model_version TEXT,
            entry_price REAL DEFAULT 0,
            optimal_action TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("🧪 TESTING PREDICTION SAVING WITH ERROR DETECTION")
    print("=" * 60)
    print(f"📁 Using test database: {test_db_path}")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print("-" * 40)
        
        symbol = test_case['symbol']
        pred = test_case['prediction']
        
        # Simulate the extraction logic from our enhanced analyzer
        prediction_id = f"test_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
        predicted_action = pred.get("optimal_action", "HOLD")
        confidence = pred.get("confidence_scores", {}).get("average", -9999)
        magnitude = pred.get("magnitude_predictions", {}).get("1d", -9999)
        entry_price = 172.40  # Simulate getting price from technical analysis
        
        print(f"   Symbol: {symbol}")
        print(f"   Action: {predicted_action}")
        print(f"   Confidence: {confidence}")
        print(f"   Magnitude: {magnitude}")
        print(f"   Entry Price: {entry_price}")
        
        # Check for error conditions
        errors = []
        if confidence == -9999:
            errors.append("🚨 CONFIDENCE FALLBACK (-9999)")
        if magnitude == -9999:
            errors.append("🚨 MAGNITUDE FALLBACK (-9999)")
        if entry_price == 0.0:
            errors.append("🚨 ENTRY PRICE MISSING (0.0)")
        
        if errors:
            print(f"   ERRORS DETECTED: {', '.join(errors)}")
        else:
            print(f"   ✅ Valid prediction data")
        
        # Save to database
        try:
            cursor.execute("""
                INSERT INTO predictions 
                (prediction_id, symbol, prediction_timestamp, predicted_action, 
                 action_confidence, predicted_direction, predicted_magnitude, 
                 model_version, entry_price, optimal_action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction_id,
                symbol,
                datetime.now().isoformat(),
                predicted_action,
                float(confidence) if confidence != -9999 else -9999.0,
                1 if predicted_action == "BUY" else (-1 if predicted_action == "SELL" else 0),
                float(magnitude) if magnitude != -9999 else -9999.0,
                "enhanced_ml_v1",
                entry_price,
                predicted_action
            ))
            print(f"   💾 Saved to database")
        except Exception as e:
            print(f"   ❌ Database error: {e}")
    
    conn.commit()
    conn.close()
    
    # Show final results
    print(f"\n📊 FINAL TEST DATABASE STATE:")
    print("-" * 30)
    
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT symbol, predicted_action, action_confidence, predicted_magnitude, entry_price
        FROM predictions 
        WHERE prediction_id LIKE 'test_%'
        ORDER BY created_at DESC
    ''')
    
    results = cursor.fetchall()
    for symbol, action, conf, mag, price in results:
        status = []
        if conf == -9999:
            status.append("CONF_ERROR")
        if mag == -9999:
            status.append("MAG_ERROR")
        if price == 0:
            status.append("PRICE_ERROR")
        
        status_str = f" ({', '.join(status)})" if status else " ✅"
        print(f"   {symbol}: {action} | Conf:{conf} | Mag:{mag} | Price:${price}{status_str}")
    
    conn.close()

if __name__ == '__main__':
    test_prediction_saving()

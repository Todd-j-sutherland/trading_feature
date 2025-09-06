#!/usr/bin/env python3
"""
Fixed database query method for IG Markets Paper Trader
Avoids cross-database JOIN issues by querying databases separately
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict

def get_untraded_predictions() -> List[Dict]:
    """Get recent predictions that haven't been paper traded yet"""
    
    # Step 1: Get existing paper trade prediction IDs
    paper_trades_db = "data/ig_markets_paper_trades.db"
    existing_prediction_ids = set()
    
    try:
        conn = sqlite3.connect(paper_trades_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT prediction_id FROM paper_trades")
        for row in cursor.fetchall():
            existing_prediction_ids.add(row[0])
        
        conn.close()
        print(f"Found {len(existing_prediction_ids)} existing paper trades")
        
    except Exception as e:
        print(f"Warning: Could not read paper trades database: {e}")
        existing_prediction_ids = set()
    
    # Step 2: Get recent predictions
    main_db = "data/trading_predictions.db"
    untraded_predictions = []
    
    try:
        conn = sqlite3.connect(main_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM predictions 
            WHERE prediction_timestamp > datetime('now', '-4 hours')
            AND predicted_action IN ('BUY', 'SELL')
            ORDER BY prediction_timestamp DESC
        """)
        
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            prediction = dict(zip(columns, row))
            
            # Only include if not already traded
            if prediction['prediction_id'] not in existing_prediction_ids:
                untraded_predictions.append(prediction)
        
        conn.close()
        print(f"Found {len(untraded_predictions)} new predictions to trade")
        
    except Exception as e:
        print(f"Error reading predictions database: {e}")
        return []
    
    return untraded_predictions

if __name__ == "__main__":
    predictions = get_untraded_predictions()
    print(f"Total untraded predictions: {len(predictions)}")
    
    if predictions:
        print("Sample prediction:")
        sample = predictions[0]
        print(f"  Symbol: {sample.get('symbol')}")
        print(f"  Action: {sample.get('predicted_action')}")
        print(f"  Confidence: {sample.get('action_confidence')}")
        print(f"  Timestamp: {sample.get('prediction_timestamp')}")

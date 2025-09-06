# Add this code to save_predictions_to_database method after the market_aware_predictions insert

            # ALSO save to main predictions table for compatibility with dashboard
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    prediction_timestamp DATETIME NOT NULL,
                    predicted_action TEXT NOT NULL,
                    action_confidence REAL NOT NULL,
                    predicted_direction INTEGER,
                    predicted_magnitude REAL,
                    feature_vector TEXT,
                    model_version TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    entry_price REAL DEFAULT 0,
                    optimal_action TEXT
                )
            ''')
            
            # Save to main predictions table
            for symbol, prediction in predictions.items():
                prediction_id = f"{symbol}_{prediction.timestamp.strftime('%Y%m%d_%H%M%S')}"
                details = prediction.prediction_details
                
                # Map market-aware action to main predictions format
                recommended_action = details.get('recommended_action', 'HOLD')
                predicted_direction = 1 if recommended_action == 'BUY' else (0 if recommended_action == 'HOLD' else -1)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO predictions 
                    (prediction_id, symbol, prediction_timestamp, predicted_action, action_confidence,
                     predicted_direction, predicted_magnitude, feature_vector, model_version, entry_price, optimal_action)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    prediction_id, symbol, prediction.timestamp, recommended_action, prediction.confidence,
                    predicted_direction, prediction.price_change_pct, 
                    f"market_aware_features_{prediction.confidence:.3f}", "market_aware_v2.0",
                    prediction.current_price, recommended_action
                ))

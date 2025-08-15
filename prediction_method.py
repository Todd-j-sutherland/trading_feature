    def _save_predictions_to_table(self, analysis_results: Dict):
        """Save individual predictions to the predictions table"""
        try:
            import sqlite3
            import uuid
            from datetime import datetime
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Save each bank prediction
            ml_preds = analysis_results.get('ml_predictions', {})
            saved_count = 0
            
            for symbol, pred in ml_preds.items():
                prediction_id = f"enhanced_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Get prediction details
                predicted_action = pred.get('optimal_action', 'HOLD')
                confidence = pred.get('action_confidence', 0.5)
                predicted_direction = 1 if predicted_action == 'BUY' else -1 if predicted_action == 'SELL' else 0
                
                try:
                    # Insert prediction with proper error handling
                    cursor.execute("""
                        INSERT OR REPLACE INTO predictions 
                        (prediction_id, symbol, prediction_timestamp, predicted_action, 
                         action_confidence, predicted_direction, predicted_magnitude, 
                         model_version, entry_price, optimal_action)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        prediction_id,
                        symbol,
                        analysis_results['timestamp'],
                        predicted_action,
                        confidence,
                        predicted_direction,
                        pred.get('predicted_return', 0.0),
                        'enhanced_ml_v1',
                        pred.get('current_price', 0.0),
                        predicted_action
                    ))
                    saved_count += 1
                    self.logger.info(f"✅ Saved prediction for {symbol}: {predicted_action} (confidence: {confidence:.3f})")
                except Exception as pred_error:
                    self.logger.warning(f"Failed to save prediction for {symbol}: {pred_error}")
            
            conn.commit()
            conn.close()
            
            if saved_count > 0:
                self.logger.info(f"✅ Saved {saved_count} predictions to predictions table")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save predictions: {e}")

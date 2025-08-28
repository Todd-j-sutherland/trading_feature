#!/usr/bin/env python3
"""
Enhanced ML Prediction System - Post Recovery
Uses trained models to generate trading predictions
"""

import sqlite3
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import json
import os
import logging
import warnings
from pathlib import Path

# Suppress sklearn warnings about feature names
warnings.filterwarnings("ignore", message="X does not have valid feature names")
warnings.filterwarnings("ignore", category=UserWarning)

class EnhancedMLPredictor:
    def __init__(self):
        self.base_dir = "/Users/toddsutherland/Repos/trading_feature"
        self.db_path = os.path.join(self.base_dir, "data", "trading_predictions.db")
        self.models_dir = os.path.join(self.base_dir, "models")
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.models = {}
        
        # Create logs directory
        Path(self.logs_dir).mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Define feature names consistently
        self.feature_names = ['rsi', 'volume_ratio', 'open_price', 'high_price', 'low_price', 'close_price']
        
        self.load_models()
    
    def setup_logging(self):
        """Setup comprehensive logging system"""
        log_file = os.path.join(self.logs_dir, f"ml_predictor_{datetime.now().strftime('%Y%m%d')}.log")
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler for detailed logging
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Setup logger
        self.logger = logging.getLogger('MLPredictor')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Log startup
        self.logger.info("Enhanced ML Predictor initialized")
        self.logger.debug(f"Base directory: {self.base_dir}")
        self.logger.debug(f"Database path: {self.db_path}")
        self.logger.debug(f"Models directory: {self.models_dir}")
        self.logger.debug(f"Logs directory: {self.logs_dir}")
    
    def load_models(self):
        """Load all available ML models with proper error handling"""
        self.logger.info("Loading ML models...")
        
        for period in ['1h', '4h']:
            try:
                dir_path = os.path.join(self.models_dir, f'direction/model_{period}.pkl')
                mag_path = os.path.join(self.models_dir, f'magnitude/model_{period}.pkl')
                
                if os.path.exists(dir_path) and os.path.exists(mag_path):
                    self.models[f'direction_{period}'] = joblib.load(dir_path)
                    self.models[f'magnitude_{period}'] = joblib.load(mag_path)
                    self.logger.info(f"✅ Loaded {period} models successfully")
                    self.logger.debug(f"Direction model: {type(self.models[f'direction_{period}']).__name__}")
                    self.logger.debug(f"Magnitude model: {type(self.models[f'magnitude_{period}']).__name__}")
                else:
                    self.logger.warning(f"⚠️ Models missing for {period} (dir={os.path.exists(dir_path)}, mag={os.path.exists(mag_path)})")
                    
            except Exception as e:
                self.logger.error(f"❌ Error loading {period} models: {e}")
                self.logger.debug(f"Full error details:", exc_info=True)
        
        total_models = len(self.models)
        self.logger.info(f"📊 Total models loaded: {total_models}")
        
        if total_models == 0:
            self.logger.critical("❌ No models loaded! System cannot make predictions.")
        elif total_models < 4:
            self.logger.warning(f"⚠️ Only {total_models}/4 models loaded. Some predictions may fail.")
        else:
            self.logger.info("✅ All models loaded successfully")
        
        print(f"📊 Total models loaded: {total_models}")
    
    def calculate_features(self, data):
        """Calculate features for prediction with error handling"""
        try:
            current = data.iloc[-1]
            
            # RSI calculation (14-period)
            price_changes = data['Close'].pct_change().dropna().tail(14)
            if len(price_changes) > 0:
                gains = price_changes[price_changes > 0].mean()
                losses = abs(price_changes[price_changes < 0].mean())
                rsi = 100 - (100 / (1 + (gains / losses if losses > 0 else 1)))
            else:
                rsi = 50.0  # Neutral RSI if no data
                self.logger.warning("Insufficient price data for RSI calculation, using neutral value")
            
            # Volume ratio (current vs 20-day average)
            volume_avg = data['Volume'].tail(20).mean()
            if volume_avg > 0:
                volume_ratio = current['Volume'] / volume_avg
            else:
                volume_ratio = 1.0  # Neutral ratio
                self.logger.warning("Zero average volume, using neutral ratio")
            
            features = {
                'rsi': float(rsi),
                'volume_ratio': float(volume_ratio),
                'open_price': float(current['Open']),
                'high_price': float(current['High']),
                'low_price': float(current['Low']),
                'close_price': float(current['Close'])
            }
            
            self.logger.debug(f"Calculated features: {features}")
            return features
            
        except Exception as e:
            self.logger.error(f"Error calculating features: {e}")
            self.logger.debug("Full error details:", exc_info=True)
            # Return neutral features as fallback
            return {
                'rsi': 50.0,
                'volume_ratio': 1.0,
                'open_price': 100.0,
                'high_price': 101.0,
                'low_price': 99.0,
                'close_price': 100.0
            }
    
    def generate_prediction(self, symbol):
        """Generate ML prediction for a symbol with comprehensive error handling"""
        try:
            self.logger.info(f"🎯 Starting prediction for {symbol}")
            
            # Get recent data with error handling
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period='1mo', interval='1h')
                
                if len(data) < 20:
                    self.logger.warning(f"⚠️ Insufficient data for {symbol}: {len(data)} rows (need 20+)")
                    print(f"⚠️ {symbol:<8} | Insufficient data")
                    return None
                    
                self.logger.debug(f"✅ Downloaded {len(data)} data points for {symbol}")
                
            except Exception as e:
                self.logger.error(f"❌ Data download failed for {symbol}: {e}")
                print(f"❌ {symbol:<8} | Data download failed")
                return None

            # Calculate features with error handling
            try:
                features = self.calculate_features(data)
                if not features:
                    self.logger.error(f"❌ Feature calculation failed for {symbol}")
                    return None
                    
                # Create feature array with explicit feature names
                feature_names = ['rsi', 'volume_ratio', 'open_price', 'high_price', 'low_price', 'close_price']
                feature_array = np.array([[features[name] for name in feature_names]])
                
                # Create DataFrame for sklearn with proper column names
                feature_df = pd.DataFrame(feature_array, columns=feature_names)
                
                self.logger.debug(f"✅ Features calculated: {features}")
                
            except Exception as e:
                self.logger.error(f"❌ Feature calculation error for {symbol}: {e}")
                return None

            predictions = {}

            # Generate predictions for available models with proper DataFrame input
            for period in ['1h', '4h']:
                try:
                    dir_model_key = f'direction_{period}'
                    mag_model_key = f'magnitude_{period}'
                    
                    if dir_model_key in self.models and mag_model_key in self.models:
                        # Use DataFrame to avoid sklearn warnings about feature names
                        dir_proba = self.models[dir_model_key].predict_proba(feature_df)[0]
                        magnitude = self.models[mag_model_key].predict(feature_df)[0]
                        
                        predictions[period] = {
                            'direction_prob': float(dir_proba[1]),  # Probability of up movement
                            'magnitude': float(magnitude),
                            'confidence': float(max(dir_proba))
                        }
                        
                        self.logger.debug(f"✅ {period} prediction: dir={dir_proba[1]:.3f}, mag={magnitude:.4f}")
                    else:
                        self.logger.warning(f"⚠️ Missing models for {period} (dir={dir_model_key in self.models}, mag={mag_model_key in self.models})")
                        
                except Exception as e:
                    self.logger.error(f"❌ Prediction error for {period} on {symbol}: {e}")
                    continue

            # Generate overall recommendation
            if '4h' in predictions:
                primary = predictions['4h']
                self.logger.debug(f"Using 4h prediction as primary for {symbol}")
            elif '1h' in predictions:
                primary = predictions['1h']
                self.logger.debug(f"Using 1h prediction as primary for {symbol}")
            else:
                self.logger.error(f"❌ No valid predictions generated for {symbol}")
                return None

            # Decision logic with error handling
            try:
                if primary['direction_prob'] > 0.6 and primary['magnitude'] > 0.02:
                    action = 'BUY'
                    confidence = primary['confidence']
                elif primary['direction_prob'] < 0.4 and primary['magnitude'] > 0.02:
                    action = 'SELL'
                    confidence = primary['confidence']
                else:
                    action = 'HOLD'
                    confidence = 0.5

                result = {
                    'symbol': symbol,
                    'predicted_action': action,
                    'action_confidence': float(confidence),
                    'predicted_direction': 1 if primary['direction_prob'] > 0.5 else -1,
                    'predicted_magnitude': float(primary['magnitude']),
                    'features': features,
                    'predictions': predictions,
                    'current_price': float(features['close_price'])
                }
                
                self.logger.info(f"✅ Prediction completed for {symbol}: {action} (confidence: {confidence:.1%})")
                return result
                
            except Exception as e:
                self.logger.error(f"❌ Decision logic error for {symbol}: {e}")
                return None

        except Exception as e:
            self.logger.error(f"❌ Critical error in generate_prediction for {symbol}: {e}")
            self.logger.debug("Full error details:", exc_info=True)
            print(f"❌ {symbol:<8} | Critical error")
            return None
    
    def save_prediction(self, prediction):
        """Save prediction to database with error handling and connection management"""
        try:
            self.logger.debug(f"Saving prediction for {prediction['symbol']}")
            
            # Use context manager for proper connection handling
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                
                prediction_id = f"{prediction['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Check if prediction already exists for today
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute('''
                    SELECT COUNT(*) FROM predictions 
                    WHERE symbol = ? AND date(prediction_timestamp) = ?
                ''', (prediction['symbol'], today))
                
                if cursor.fetchone()[0] > 0:
                    # Update existing prediction instead of creating duplicate
                    cursor.execute('''
                        UPDATE predictions SET
                        predicted_action = ?, action_confidence = ?,
                        predicted_direction = ?, predicted_magnitude = ?,
                        feature_vector = ?, model_version = ?,
                        prediction_timestamp = ?
                        WHERE symbol = ? AND date(prediction_timestamp) = ?
                    ''', (
                        prediction['predicted_action'], prediction['action_confidence'],
                        prediction['predicted_direction'], prediction['predicted_magnitude'],
                        json.dumps(prediction['features']), 'enhanced_ml_v2.0',
                        datetime.now(), prediction['symbol'], today
                    ))
                    self.logger.info(f"📝 Updated existing prediction for {prediction['symbol']}")
                else:
                    # Insert new prediction
                    cursor.execute('''
                        INSERT INTO predictions
                        (prediction_id, symbol, prediction_timestamp, predicted_action,
                         action_confidence, predicted_direction, predicted_magnitude,
                         feature_vector, model_version)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        prediction_id, prediction['symbol'], datetime.now(),
                        prediction['predicted_action'], prediction['action_confidence'],
                        prediction['predicted_direction'], prediction['predicted_magnitude'],
                        json.dumps(prediction['features']), 'enhanced_ml_v2.0'
                    ))
                    self.logger.info(f"💾 Saved new prediction for {prediction['symbol']}")
                
                conn.commit()
            
            # Display result
            price = prediction['current_price']
            action = prediction['predicted_action']
            confidence = prediction['action_confidence']
            
            print(f"✅ {prediction['symbol']:<8} | ${price:>6.2f} | {action:<4} | {confidence:>5.1%}")
            self.logger.info(f"✅ Database operation completed for {prediction['symbol']}: {action} @ ${price:.2f} ({confidence:.1%})")
            
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                self.logger.error(f"🔒 Database locked for {prediction.get('symbol', 'unknown')}: {e}")
                print(f"🔒 {prediction.get('symbol', 'unknown'):<8} | Database locked - prediction generated but not saved")
            else:
                self.logger.error(f"❌ Database error for {prediction.get('symbol', 'unknown')}: {e}")
                print(f"❌ {prediction.get('symbol', 'unknown'):<8} | Database error")
        except Exception as e:
            self.logger.error(f"❌ Save error for {prediction.get('symbol', 'unknown')}: {e}")
            print(f"❌ {prediction.get('symbol', 'unknown'):<8} | Save failed")

    def run_predictions(self, symbols=None):
        """Run predictions for specified symbols with comprehensive logging"""
        try:
            if symbols is None:
                symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX']
            
            self.logger.info(f"🚀 Starting prediction run for {len(symbols)} symbols: {symbols}")
            
            print(f"🚀 ENHANCED ML PREDICTION SYSTEM")
            print(f"=" * 50)
            print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🎯 Generating predictions for {len(symbols)} symbols...")
            print()
            print(f"{'SYMBOL':<8} | {'PRICE':<8} | {'ACTION':<4} | {'CONF':<5}")
            print("-" * 35)
            
            predictions_made = 0
            failed_predictions = []
            
            for symbol in symbols:
                try:
                    prediction = self.generate_prediction(symbol)
                    
                    if prediction:
                        self.save_prediction(prediction)
                        predictions_made += 1
                    else:
                        failed_predictions.append(symbol)
                        print(f"❌ {symbol:<8} | Error generating prediction")
                        self.logger.warning(f"❌ Failed to generate prediction for {symbol}")
                        
                except Exception as e:
                    failed_predictions.append(symbol)
                    print(f"❌ {symbol:<8} | Exception: {str(e)[:20]}...")
                    self.logger.error(f"❌ Exception processing {symbol}: {e}")
            
            print("-" * 35)
            print(f"✅ Generated {predictions_made}/{len(symbols)} predictions")
            
            # Show model performance summary
            success_rate = predictions_made/len(symbols) if symbols else 0
            print(f"\n📊 MODEL SUMMARY:")
            print(f"   Models loaded: {len(self.models)}")
            print(f"   Success rate: {success_rate:.1%}")
            print(f"   Database: Updated with new predictions")
            
            # Log summary
            self.logger.info(f"📊 Prediction run complete: {predictions_made}/{len(symbols)} successful ({success_rate:.1%})")
            if failed_predictions:
                self.logger.warning(f"❌ Failed predictions: {failed_predictions}")
            
            return predictions_made
            
        except Exception as e:
            self.logger.error(f"❌ Critical error in run_predictions: {e}")
            self.logger.debug("Full error details:", exc_info=True)
            print(f"❌ Critical error in prediction run: {e}")
            return 0

if __name__ == "__main__":
    predictor = EnhancedMLPredictor()
    predictor.run_predictions()

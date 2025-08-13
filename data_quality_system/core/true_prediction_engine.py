#!/usr/bin/env python3
"""
True Prediction Engine - Corrected Architecture
Replaces the retrospective labeling system with real predictions
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import uuid
import pickle
import os
from typing import Dict, List, Optional, Tuple
import logging
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

class PredictionStore:
    """Handles storage and retrieval of predictions and outcomes"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the corrected database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Predictions table (IMMUTABLE)
        cursor.execute("""
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
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Outcomes table (separate from predictions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
                outcome_id TEXT PRIMARY KEY,
                prediction_id TEXT NOT NULL,
                actual_return REAL,
                actual_direction INTEGER,
                entry_price REAL,
                exit_price REAL,
                evaluation_timestamp DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
            )
        """)
        
        # Model performance tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_performance (
                evaluation_id TEXT PRIMARY KEY,
                model_version TEXT,
                evaluation_period_start DATETIME,
                evaluation_period_end DATETIME,
                total_predictions INTEGER,
                accuracy_action REAL,
                accuracy_direction REAL,
                mae_magnitude REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_prediction(self, prediction: Dict) -> bool:
        """Save a prediction (immutable once saved)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO predictions (
                    prediction_id, symbol, prediction_timestamp,
                    predicted_action, action_confidence, predicted_direction,
                    predicted_magnitude, feature_vector, model_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction['prediction_id'],
                prediction['symbol'],
                prediction['prediction_timestamp'],
                prediction['predicted_action'],
                prediction['action_confidence'],
                prediction.get('predicted_direction'),
                prediction.get('predicted_magnitude'),
                json.dumps(prediction.get('feature_vector', [])),
                prediction.get('model_version', '1.0')
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logging.error(f"Failed to save prediction: {e}")
            return False
    
    def get_pending_evaluations(self, hours_ago: int = 24) -> List[Dict]:
        """Get predictions that need outcome evaluation"""
        conn = sqlite3.connect(self.db_path)
        
        # Get predictions older than specified hours that don't have outcomes
        query = """
            SELECT p.* FROM predictions p
            LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
            WHERE o.prediction_id IS NULL
            AND datetime(p.prediction_timestamp) <= datetime('now', '-{} hours')
            ORDER BY p.prediction_timestamp ASC
        """.format(hours_ago)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df.to_dict('records')

class TruePredictionEngine:
    """Real prediction engine that makes forward-looking predictions"""
    
    def __init__(self, model_path: str = "models/"):
        self.model_path = model_path
        self.prediction_store = PredictionStore()
        self.model_version = "1.0"
        
        # Load or initialize models
        self.action_model = self._load_or_create_model('action_model.pkl')
        self.direction_model = self._load_or_create_model('direction_model.pkl')
        self.magnitude_model = self._load_or_create_model('magnitude_model.pkl')
        
        self.logger = logging.getLogger(__name__)
        
    def _load_or_create_model(self, model_file: str):
        """Load existing model or create new one"""
        full_path = os.path.join(self.model_path, model_file)
        
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                return pickle.load(f)
        else:
            # Create default model
            if 'action' in model_file:
                return RandomForestClassifier(n_estimators=100, random_state=42)
            elif 'direction' in model_file:
                return RandomForestClassifier(n_estimators=100, random_state=42)
            else:
                return RandomForestRegressor(n_estimators=100, random_state=42)
    
    def make_prediction(self, symbol: str, features: Dict) -> Dict:
        """Make a real prediction NOW (no waiting for outcomes!)"""
        
        prediction_timestamp = datetime.now()
        
        # Prepare feature vector
        feature_vector = self._prepare_features(features)
        
        # Make predictions using trained models
        try:
            # Action prediction
            if hasattr(self.action_model, 'predict_proba'):
                action_proba = self.action_model.predict_proba(feature_vector.reshape(1, -1))[0]
                predicted_action = self.action_model.predict(feature_vector.reshape(1, -1))[0]
                action_confidence = max(action_proba)
            else:
                # Model not trained yet, use rule-based fallback
                predicted_action, action_confidence = self._rule_based_prediction(features)
            
            # Direction prediction
            if hasattr(self.direction_model, 'predict'):
                predicted_direction = self.direction_model.predict(feature_vector.reshape(1, -1))[0]
            else:
                predicted_direction = 1 if features.get('rsi', 50) < 30 else -1 if features.get('rsi', 50) > 70 else 0
            
            # Magnitude prediction
            if hasattr(self.magnitude_model, 'predict'):
                predicted_magnitude = self.magnitude_model.predict(feature_vector.reshape(1, -1))[0]
            else:
                predicted_magnitude = 0.1  # Conservative default
            
        except Exception as e:
            self.logger.warning(f"Model prediction failed, using fallback: {e}")
            predicted_action, action_confidence = self._rule_based_prediction(features)
            predicted_direction = 0
            predicted_magnitude = 0.0
        
        prediction = {
            'prediction_id': str(uuid.uuid4()),
            'symbol': symbol,
            'prediction_timestamp': prediction_timestamp.isoformat(),
            'predicted_action': predicted_action,
            'action_confidence': float(action_confidence),
            'predicted_direction': int(predicted_direction),
            'predicted_magnitude': float(predicted_magnitude),
            'feature_vector': feature_vector.tolist(),
            'model_version': self.model_version
        }
        
        # Store prediction immediately (never change this!)
        self.prediction_store.save_prediction(prediction)
        
        self.logger.info(f"✅ Made prediction for {symbol}: {predicted_action} (confidence: {action_confidence:.3f})")
        
        return prediction
    
    def _prepare_features(self, features: Dict) -> np.ndarray:
        """Convert features dict to numpy array for model input"""
        
        # Define feature order (must match training data)
        feature_names = [
            'sentiment_score', 'confidence', 'news_count', 'reddit_sentiment',
            'rsi', 'macd_line', 'macd_signal', 'macd_histogram',
            'price_vs_sma20', 'price_vs_sma50', 'price_vs_sma200',
            'bollinger_width', 'volume_ratio', 'atr_14', 'volatility_20d',
            'asx200_change', 'vix_level', 'asx_market_hours',
            'monday_effect', 'friday_effect'
        ]
        
        # Extract features in correct order
        feature_vector = []
        for feature_name in feature_names:
            value = features.get(feature_name, 0.0)
            # Handle boolean features
            if isinstance(value, bool):
                value = 1.0 if value else 0.0
            feature_vector.append(float(value))
        
        return np.array(feature_vector)
    
    def _rule_based_prediction(self, features: Dict) -> Tuple[str, float]:
        """Fallback rule-based prediction when models aren't trained"""
        
        rsi = features.get('rsi', 50)
        macd_histogram = features.get('macd_histogram', 0)
        price_vs_sma20 = features.get('price_vs_sma20', 0)
        sentiment = features.get('sentiment_score', 0)
        volume_ratio = features.get('volume_ratio', 1)
        
        # Simple rule-based logic
        bullish_signals = 0
        bearish_signals = 0
        
        if rsi < 30:
            bullish_signals += 1
        elif rsi > 70:
            bearish_signals += 1
            
        if macd_histogram > 0:
            bullish_signals += 1
        elif macd_histogram < 0:
            bearish_signals += 1
            
        if price_vs_sma20 > 2:
            bullish_signals += 1
        elif price_vs_sma20 < -2:
            bearish_signals += 1
            
        if sentiment > 0.1:
            bullish_signals += 1
        elif sentiment < -0.1:
            bearish_signals += 1
        
        if volume_ratio > 2:
            bullish_signals += 0.5
        
        # Determine action
        total_signals = bullish_signals + bearish_signals
        if total_signals > 0:
            confidence = min(0.8, total_signals / 4)
        else:
            confidence = 0.5
        
        if bullish_signals > bearish_signals + 1:
            return 'BUY', confidence
        elif bearish_signals > bullish_signals + 1:
            return 'SELL', confidence
        else:
            return 'HOLD', confidence

class OutcomeEvaluator:
    """Evaluates predictions after outcomes are known"""
    
    def __init__(self, market_data_source: str = "yfinance"):
        self.prediction_store = PredictionStore()
        self.market_data_source = market_data_source
        self.logger = logging.getLogger(__name__)
    
    def evaluate_pending_predictions(self) -> int:
        """Evaluate all pending predictions"""
        
        pending = self.prediction_store.get_pending_evaluations(hours_ago=24)
        evaluated_count = 0
        
        for prediction in pending:
            try:
                outcome = self._calculate_outcome(prediction)
                if outcome:
                    self._store_outcome(outcome)
                    evaluated_count += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to evaluate prediction {prediction['prediction_id']}: {e}")
        
        self.logger.info(f"✅ Evaluated {evaluated_count} predictions")
        return evaluated_count
    
    def _calculate_outcome(self, prediction: Dict) -> Optional[Dict]:
        """Calculate actual outcome for a prediction"""
        
        try:
            import yfinance as yf
            
            symbol = prediction['symbol']
            pred_time = datetime.fromisoformat(prediction['prediction_timestamp'])
            
            # Get market data starting from prediction time
            end_time = pred_time + timedelta(days=2)
            ticker = yf.Ticker(symbol)
            
            # Get hourly data
            hist = ticker.history(start=pred_time.date(), end=end_time.date(), interval='1h')
            
            if len(hist) < 2:
                self.logger.warning(f"Insufficient market data for {symbol} at {pred_time}")
                return None
            
            # Find entry price (closest to prediction time)
            entry_price = hist['Close'].iloc[0]
            
            # Find exit price (24 hours later or closest available)
            target_exit_time = pred_time + timedelta(hours=24)
            
            # Find closest price to target exit time
            if len(hist) >= 24:
                exit_price = hist['Close'].iloc[23]  # 24 hours later
            else:
                exit_price = hist['Close'].iloc[-1]  # Last available
            
            # Calculate actual return
            actual_return = ((exit_price - entry_price) / entry_price) * 100
            actual_direction = 1 if actual_return > 0 else -1 if actual_return < 0 else 0
            
            outcome = {
                'outcome_id': str(uuid.uuid4()),
                'prediction_id': prediction['prediction_id'],
                'actual_return': actual_return,
                'actual_direction': actual_direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'evaluation_timestamp': datetime.now().isoformat()
            }
            
            return outcome
            
        except Exception as e:
            self.logger.error(f"Error calculating outcome: {e}")
            return None
    
    def _store_outcome(self, outcome: Dict) -> bool:
        """Store the calculated outcome"""
        try:
            conn = sqlite3.connect(self.prediction_store.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO outcomes (
                    outcome_id, prediction_id, actual_return, actual_direction,
                    entry_price, exit_price, evaluation_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome['outcome_id'],
                outcome['prediction_id'],
                outcome['actual_return'],
                outcome['actual_direction'],
                outcome['entry_price'],
                outcome['exit_price'],
                outcome['evaluation_timestamp']
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store outcome: {e}")
            return False

def main():
    """Test the corrected prediction engine"""
    
    logging.basicConfig(level=logging.INFO)
    
    # Initialize components
    predictor = TruePredictionEngine()
    evaluator = OutcomeEvaluator()
    
    # Example: Make a prediction (this would be called by your main trading loop)
    sample_features = {
        'sentiment_score': 0.05,
        'confidence': 0.8,
        'news_count': 42,
        'rsi': 45.2,
        'macd_histogram': 0.15,
        'price_vs_sma20': 1.2,
        'price_vs_sma50': 0.8,
        'bollinger_width': 2.1,
        'volume_ratio': 2.5,
        'asx_market_hours': True,
        'monday_effect': True,
        'friday_effect': False
    }
    
    # Make prediction
    prediction = predictor.make_prediction('ANZ.AX', sample_features)
    print(f"Made prediction: {prediction['predicted_action']} with confidence {prediction['action_confidence']:.3f}")
    
    # Evaluate old predictions
    evaluated = evaluator.evaluate_pending_predictions()
    print(f"Evaluated {evaluated} old predictions")

if __name__ == "__main__":
    main()

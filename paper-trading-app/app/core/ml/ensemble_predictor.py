#!/usr/bin/env python3
"""
Ensemble Predictor - RandomForest + LSTM Neural Network
=======================================================

Combines RandomForest and LSTM predictions for enhanced accuracy.
Uses weighted averaging and confidence-based selection to determine
the best prediction for each timeframe.

Features:
- Intelligent ensemble weighting based on model confidence
- Fallback mechanisms when models are unavailable
- Performance tracking and dynamic weight adjustment
- Integration with existing enhanced_training_pipeline
"""

import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime
import logging
import json
import os
from typing import Dict, List, Tuple, Optional

# Import existing models
try:
    from .enhanced_training_pipeline import EnhancedMLTrainingPipeline
except ImportError:
    from enhanced_training_pipeline import EnhancedMLTrainingPipeline

try:
    from .lstm_neural_network import LSTMNeuralNetwork
except ImportError:
    from lstm_neural_network import LSTMNeuralNetwork

logger = logging.getLogger(__name__)

class EnsemblePredictor:
    """
    Ensemble predictor combining RandomForest and LSTM models
    """
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = db_path
        self.models_dir = "data/ml_models/models"
        
        # Initialize component models
        self.rf_pipeline = EnhancedMLTrainingPipeline()
        self.lstm_network = LSTMNeuralNetwork(db_path=db_path)
        
        # Ensemble weights (updated based on performance)
        self.weights = {
            'random_forest': 0.6,  # Stable, proven performer
            'lstm': 0.4           # Neural network for pattern recognition
        }
        
        # Performance tracking
        self.performance_history = []
        self.confidence_threshold = 0.5
        
        # Model availability flags
        self.rf_available = False
        self.lstm_available = False
        
    def check_model_availability(self) -> Dict[str, bool]:
        """Check which models are available"""
        # Check RandomForest models
        rf_direction_path = os.path.join(self.models_dir, 'current_direction_model.pkl')
        rf_magnitude_path = os.path.join(self.models_dir, 'current_magnitude_model.pkl')
        rf_metadata_path = os.path.join(self.models_dir, 'current_enhanced_metadata.json')
        
        self.rf_available = all(os.path.exists(p) for p in [rf_direction_path, rf_magnitude_path, rf_metadata_path])
        
        # Check LSTM models  
        lstm_direction_path = os.path.join(self.models_dir, 'current_lstm_direction.h5')
        lstm_magnitude_path = os.path.join(self.models_dir, 'current_lstm_magnitude.h5')
        lstm_scaler_path = os.path.join(self.models_dir, 'current_lstm_feature_scaler.pkl')
        
        self.lstm_available = all(os.path.exists(p) for p in [lstm_direction_path, lstm_magnitude_path, lstm_scaler_path])
        
        availability = {
            'random_forest': self.rf_available,
            'lstm': self.lstm_available,
            'ensemble': self.rf_available or self.lstm_available
        }
        
        logger.info(f"Model availability: RF={self.rf_available}, LSTM={self.lstm_available}")
        return availability
    
    def get_lstm_sequence_data(self, sentiment_data: Dict, symbol: str) -> Optional[np.ndarray]:
        """
        Prepare sequence data for LSTM prediction
        
        Returns:
            2D array (sequence_length, features) for LSTM input
        """
        try:
            # Get recent feature data for the symbol
            conn = sqlite3.connect(self.db_path)
            
            # Get last sequence_length records for this symbol
            query = '''
                SELECT ef.*
                FROM enhanced_features ef
                WHERE ef.symbol = ?
                ORDER BY ef.timestamp DESC
                LIMIT ?
            '''
            
            df = pd.read_sql_query(query, conn, params=[symbol, self.lstm_network.sequence_length])
            conn.close()
            
            if len(df) < self.lstm_network.sequence_length:
                logger.warning(f"Insufficient historical data for LSTM sequence: {len(df)} records")
                return None
            
            # Extract feature columns (same as LSTM training)
            exclude_cols = ['id', 'symbol', 'timestamp', 'feature_version', 'created_at']
            feature_cols = [col for col in df.columns if col not in exclude_cols]
            
            # Reverse order to get chronological sequence (oldest first)
            sequence_data = df[feature_cols].iloc[::-1].values
            
            # Handle NaN values
            sequence_data = np.nan_to_num(sequence_data, nan=0.0)
            
            return sequence_data
            
        except Exception as e:
            logger.error(f"Error preparing LSTM sequence data for {symbol}: {e}")
            return None
    
    def predict_ensemble(self, sentiment_data: Dict, symbol: str) -> Dict:
        """
        Make ensemble prediction using available models
        
        Args:
            sentiment_data: Sentiment analysis results
            symbol: Stock symbol (e.g., 'CBA.AX')
            
        Returns:
            Combined prediction with confidence scores
        """
        availability = self.check_model_availability()
        
        if not availability['ensemble']:
            return {
                'error': 'No models available for prediction',
                'optimal_action': 'HOLD',
                'confidence_scores': {'average': 0.1}
            }
        
        predictions = {}
        
        # Get RandomForest prediction
        if self.rf_available:
            try:
                rf_pred = self.rf_pipeline.predict_enhanced(sentiment_data, symbol)
                if 'error' not in rf_pred:
                    predictions['random_forest'] = rf_pred
                    logger.debug(f"RandomForest prediction successful for {symbol}")
            except Exception as e:
                logger.warning(f"RandomForest prediction failed for {symbol}: {e}")
        
        # Get LSTM prediction
        if self.lstm_available:
            try:
                sequence_data = self.get_lstm_sequence_data(sentiment_data, symbol)
                if sequence_data is not None:
                    lstm_pred = self.lstm_network.predict_lstm(sequence_data)
                    if 'error' not in lstm_pred:
                        predictions['lstm'] = lstm_pred
                        logger.debug(f"LSTM prediction successful for {symbol}")
            except Exception as e:
                logger.warning(f"LSTM prediction failed for {symbol}: {e}")
        
        if not predictions:
            return {
                'error': 'All prediction models failed',
                'optimal_action': 'HOLD',
                'confidence_scores': {'average': 0.1}
            }
        
        # Combine predictions using ensemble weighting
        return self._combine_predictions(predictions, symbol)
    
    def _combine_predictions(self, predictions: Dict, symbol: str) -> Dict:
        """
        Intelligently combine multiple model predictions
        """
        if len(predictions) == 1:
            # Only one model available, return its prediction
            model_name = list(predictions.keys())[0]
            result = predictions[model_name].copy()
            result['ensemble_method'] = f"single_model_{model_name}"
            result['models_used'] = [model_name]
            return result
        
        # Multiple models available - ensemble combination
        combined_result = {
            'direction_predictions': {'1h': 0, '4h': 0, '1d': 0},
            'magnitude_predictions': {'1h': 0.0, '4h': 0.0, '1d': 0.0},
            'confidence_scores': {'1h': 0.0, '4h': 0.0, '1d': 0.0, 'average': 0.0},
            'models_used': list(predictions.keys()),
            'ensemble_method': 'weighted_average'
        }
        
        timeframes = ['1h', '4h', '1d']
        total_weight = 0
        
        # Calculate weighted averages
        for model_name, prediction in predictions.items():
            if model_name not in self.weights:
                continue
                
            weight = self.weights[model_name]
            total_weight += weight
            
            # Combine direction predictions (weighted voting)
            for tf in timeframes:
                if 'direction_predictions' in prediction:
                    combined_result['direction_predictions'][tf] += prediction['direction_predictions'][tf] * weight
                
                # Combine magnitude predictions (weighted average)
                if 'magnitude_predictions' in prediction:
                    combined_result['magnitude_predictions'][tf] += prediction['magnitude_predictions'][tf] * weight
                
                # Combine confidence scores (weighted average)
                if 'confidence_scores' in prediction:
                    conf_score = prediction['confidence_scores'].get(tf, 0)
                    if conf_score == 0:  # Try alternative key formats
                        conf_score = prediction['confidence_scores'].get('average', 0)
                    combined_result['confidence_scores'][tf] += conf_score * weight
        
        # Normalize by total weight
        if total_weight > 0:
            for tf in timeframes:
                combined_result['direction_predictions'][tf] = int(combined_result['direction_predictions'][tf] / total_weight > 0.5)
                combined_result['magnitude_predictions'][tf] /= total_weight
                combined_result['confidence_scores'][tf] /= total_weight
        
        # Calculate average confidence
        combined_result['confidence_scores']['average'] = np.mean([
            combined_result['confidence_scores'][tf] for tf in timeframes
        ])
        
        # Determine optimal action using ensemble logic
        avg_direction = np.mean([combined_result['direction_predictions'][tf] for tf in timeframes])
        avg_magnitude = np.mean([abs(combined_result['magnitude_predictions'][tf]) for tf in timeframes])
        avg_confidence = combined_result['confidence_scores']['average']
        
        # Enhanced action determination with ensemble confidence
        if avg_direction > 0.6 and avg_magnitude > 0.02 and avg_confidence > 0.7:
            optimal_action = 'BUY'
        elif avg_direction < 0.4 and avg_magnitude > 0.02 and avg_confidence > 0.7:
            optimal_action = 'SELL'
        elif avg_confidence > 0.8 and avg_magnitude > 0.01:
            # High confidence, moderate magnitude
            optimal_action = 'BUY' if avg_direction > 0.5 else 'SELL'
        else:
            optimal_action = 'HOLD'
        
        combined_result['optimal_action'] = optimal_action
        combined_result['timestamp'] = datetime.now().isoformat()
        
        # Add ensemble metadata
        combined_result['ensemble_weights'] = self.weights.copy()
        combined_result['model_contributions'] = {
            model: self.weights.get(model, 0) for model in predictions.keys()
        }
        
        logger.debug(f"Ensemble prediction for {symbol}: {optimal_action} (confidence: {avg_confidence:.3f})")
        
        return combined_result
    
    def update_ensemble_weights(self, performance_data: Dict):
        """
        Update ensemble weights based on recent performance
        
        Args:
            performance_data: Dictionary with model performance metrics
        """
        try:
            # Adjust weights based on recent accuracy
            if 'random_forest' in performance_data and 'lstm' in performance_data:
                rf_accuracy = performance_data['random_forest'].get('accuracy', 0.5)
                lstm_accuracy = performance_data['lstm'].get('accuracy', 0.5)
                
                # Calculate new weights (higher accuracy gets more weight)
                total_accuracy = rf_accuracy + lstm_accuracy
                if total_accuracy > 0:
                    self.weights['random_forest'] = rf_accuracy / total_accuracy
                    self.weights['lstm'] = lstm_accuracy / total_accuracy
                
                logger.info(f"Updated ensemble weights: RF={self.weights['random_forest']:.3f}, LSTM={self.weights['lstm']:.3f}")
            
            # Save updated weights
            self._save_ensemble_config()
            
        except Exception as e:
            logger.error(f"Error updating ensemble weights: {e}")
    
    def _save_ensemble_config(self):
        """Save ensemble configuration"""
        config = {
            'weights': self.weights,
            'confidence_threshold': self.confidence_threshold,
            'last_updated': datetime.now().isoformat(),
            'performance_history': self.performance_history[-10:]  # Keep last 10 records
        }
        
        config_path = os.path.join(self.models_dir, 'ensemble_config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save ensemble config: {e}")
    
    def load_ensemble_config(self):
        """Load ensemble configuration"""
        config_path = os.path.join(self.models_dir, 'ensemble_config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                self.weights = config.get('weights', self.weights)
                self.confidence_threshold = config.get('confidence_threshold', self.confidence_threshold)
                self.performance_history = config.get('performance_history', [])
                
                logger.info("Loaded ensemble configuration")
        except Exception as e:
            logger.warning(f"Could not load ensemble config: {e}")

def create_ensemble_predictor(db_path: str = "data/trading_predictions.db") -> EnsemblePredictor:
    """
    Factory function to create and configure ensemble predictor
    """
    predictor = EnsemblePredictor(db_path=db_path)
    predictor.load_ensemble_config()
    return predictor

# Example usage and testing
if __name__ == "__main__":
    # Test ensemble prediction
    ensemble = create_ensemble_predictor()
    
    # Mock sentiment data for testing
    test_sentiment = {
        'overall_sentiment': 0.1,
        'confidence': 0.75,
        'news_count': 5,
        'sentiment_components': {'news': 0.05, 'social': 0.15},
        'timestamp': datetime.now().isoformat()
    }
    
    # Test prediction for CBA.AX
    result = ensemble.predict_ensemble(test_sentiment, 'CBA.AX')
    
    print("🔮 Ensemble Prediction Test:")
    print(f"Action: {result.get('optimal_action', 'ERROR')}")
    print(f"Confidence: {result.get('confidence_scores', {}).get('average', 0):.3f}")
    print(f"Models used: {result.get('models_used', [])}")
    print(f"Method: {result.get('ensemble_method', 'unknown')}")
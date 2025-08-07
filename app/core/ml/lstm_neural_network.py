#!/usr/bin/env python3
"""
LSTM Neural Network for Enhanced Trading Predictions
====================================================

Implements LSTM (Long Short-Term Memory) neural networks for time series
prediction of stock price movements. Works alongside existing RandomForest
models in an ensemble approach.

Features:
- Sequential pattern recognition for price movements
- Multi-output predictions (1h, 4h, 1d timeframes)
- Ensemble integration with RandomForest
- Handles missing data and NaN values
- Optimized for financial time series

Requirements:
pip install tensorflow pandas numpy scikit-learn
"""

import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import logging
import os
import json
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Scikit-learn imports (always needed)
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_absolute_error, accuracy_score, classification_report

# Neural network imports
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.regularizers import l2
    TENSORFLOW_AVAILABLE = True
    
    # Configure TensorFlow for better performance
    tf.keras.utils.set_random_seed(42)
    tf.config.experimental.enable_op_determinism()
    
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️ TensorFlow not available. Install with: pip install tensorflow")

logger = logging.getLogger(__name__)

class LSTMNeuralNetwork:
    """
    LSTM Neural Network for stock price prediction and trading signal generation
    """
    
    def __init__(self, db_path: str = "data/trading_unified.db", sequence_length: int = 10):
        self.db_path = db_path
        self.sequence_length = sequence_length  # How many time steps to look back
        self.models_dir = "data/ml_models/models"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Model architecture parameters
        self.lstm_units = [128, 64]  # LSTM layer sizes
        self.dense_units = [32, 16]  # Dense layer sizes
        self.dropout_rate = 0.2
        self.l2_reg = 0.001
        
        # Training parameters
        self.batch_size = 16
        self.epochs = 100
        self.validation_split = 0.2
        self.patience = 15
        
        # Scalers for feature normalization
        self.feature_scaler = StandardScaler()
        self.target_scaler = MinMaxScaler(feature_range=(-1, 1))
        
        # Model storage
        self.direction_model = None
        self.magnitude_model = None
        self.ensemble_model = None
        
    def check_tensorflow_availability(self) -> bool:
        """Check if TensorFlow is available"""
        if not TENSORFLOW_AVAILABLE:
            logger.error("TensorFlow not available. Install with: pip install tensorflow")
            return False
        return True
    
    def prepare_sequence_data(self, min_samples: int = 50) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        Prepare sequential data for LSTM training
        
        Returns:
            X: 3D array (samples, sequence_length, features)
            y: Dictionary with target arrays
            metadata: Information about the prepared data
        """
        if not self.check_tensorflow_availability():
            return None, None, None
            
        logger.info("Preparing sequence data for LSTM training...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Get sequential data ordered by time
        query = '''
            SELECT ef.*, eo.price_direction_1h, eo.price_direction_4h, eo.price_direction_1d,
                   eo.price_magnitude_1h, eo.price_magnitude_4h, eo.price_magnitude_1d,
                   eo.optimal_action, eo.confidence_score, eo.symbol as target_symbol
            FROM enhanced_features ef
            INNER JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
            WHERE eo.price_direction_4h IS NOT NULL
            ORDER BY ef.symbol, ef.timestamp
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) < min_samples:
            logger.warning(f"Insufficient data for LSTM: {len(df)} samples (minimum: {min_samples})")
            return None, None, None
        
        # Feature columns (exclude metadata)
        exclude_cols = ['id', 'symbol', 'timestamp', 'feature_version', 'created_at', 
                       'price_direction_1h', 'price_direction_4h', 'price_direction_1d',
                       'price_magnitude_1h', 'price_magnitude_4h', 'price_magnitude_1d',
                       'optimal_action', 'confidence_score', 'target_symbol']
        
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Prepare features and targets
        X_sequences = []
        y_direction = []
        y_magnitude = []
        
        # Group by symbol to maintain temporal order within each stock
        for symbol in df['target_symbol'].unique():
            symbol_data = df[df['target_symbol'] == symbol].sort_values('timestamp')
            
            if len(symbol_data) < self.sequence_length + 1:
                continue  # Skip symbols with insufficient data
            
            # Extract features and targets
            features = symbol_data[feature_cols].values
            directions = symbol_data[['price_direction_1h', 'price_direction_4h', 'price_direction_1d']].values
            magnitudes = symbol_data[['price_magnitude_1h', 'price_magnitude_4h', 'price_magnitude_1d']].values
            
            # Handle NaN values
            features = np.nan_to_num(features, nan=0.0)
            directions = np.nan_to_num(directions, nan=0)
            magnitudes = np.nan_to_num(magnitudes, nan=0.0)
            
            # Create sequences
            for i in range(len(features) - self.sequence_length):
                # Input sequence: last sequence_length time steps
                X_seq = features[i:i + self.sequence_length]
                
                # Target: next time step
                y_dir = directions[i + self.sequence_length]
                y_mag = magnitudes[i + self.sequence_length]
                
                X_sequences.append(X_seq)
                y_direction.append(y_dir)
                y_magnitude.append(y_mag)
        
        if len(X_sequences) < min_samples:
            logger.warning(f"Insufficient sequences for LSTM: {len(X_sequences)} sequences (minimum: {min_samples})")
            return None, None, None
        
        # Convert to numpy arrays
        X = np.array(X_sequences)
        y_direction = np.array(y_direction)
        y_magnitude = np.array(y_magnitude)
        
        # Normalize features
        X_reshaped = X.reshape(-1, X.shape[-1])
        X_scaled = self.feature_scaler.fit_transform(X_reshaped)
        X = X_scaled.reshape(X.shape)
        
        # Scale targets
        y_magnitude = self.target_scaler.fit_transform(y_magnitude)
        
        # Convert direction to binary (0/1 instead of -1/1)
        y_direction = np.where(y_direction == 1, 1, 0)
        
        targets = {
            'direction': y_direction,
            'magnitude': y_magnitude
        }
        
        metadata = {
            'sequences_created': len(X_sequences),
            'sequence_length': self.sequence_length,
            'feature_count': len(feature_cols),
            'feature_columns': feature_cols,
            'symbols_processed': len(df['target_symbol'].unique()),
            'data_range': {
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max()
            }
        }
        
        logger.info(f"Created {len(X)} sequences with {X.shape[2]} features each")
        logger.info(f"Sequence shape: {X.shape}, Direction targets: {y_direction.shape}, Magnitude targets: {y_magnitude.shape}")
        
        return X, targets, metadata
    
    def create_direction_model(self, input_shape: Tuple[int, int]):
        """
        Create LSTM model for price direction prediction (classification)
        
        Args:
            input_shape: (sequence_length, feature_count)
        """
        model = Sequential([
            Input(shape=input_shape),
            
            # First LSTM layer with return sequences
            LSTM(self.lstm_units[0], 
                 return_sequences=True, 
                 dropout=self.dropout_rate,
                 recurrent_dropout=self.dropout_rate,
                 kernel_regularizer=l2(self.l2_reg)),
            BatchNormalization(),
            
            # Second LSTM layer
            LSTM(self.lstm_units[1], 
                 return_sequences=False,
                 dropout=self.dropout_rate,
                 recurrent_dropout=self.dropout_rate,
                 kernel_regularizer=l2(self.l2_reg)),
            BatchNormalization(),
            
            # Dense layers
            Dense(self.dense_units[0], activation='relu', kernel_regularizer=l2(self.l2_reg)),
            Dropout(self.dropout_rate),
            
            Dense(self.dense_units[1], activation='relu', kernel_regularizer=l2(self.l2_reg)),
            Dropout(self.dropout_rate),
            
            # Output layer for 3 timeframes (1h, 4h, 1d) - sigmoid for binary classification
            Dense(3, activation='sigmoid', name='direction_output')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001, clipnorm=1.0),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def create_magnitude_model(self, input_shape: Tuple[int, int]):
        """
        Create LSTM model for price magnitude prediction (regression)
        
        Args:
            input_shape: (sequence_length, feature_count)
        """
        model = Sequential([
            Input(shape=input_shape),
            
            # First LSTM layer
            LSTM(self.lstm_units[0], 
                 return_sequences=True, 
                 dropout=self.dropout_rate,
                 recurrent_dropout=self.dropout_rate,
                 kernel_regularizer=l2(self.l2_reg)),
            BatchNormalization(),
            
            # Second LSTM layer
            LSTM(self.lstm_units[1], 
                 return_sequences=False,
                 dropout=self.dropout_rate,
                 recurrent_dropout=self.dropout_rate,
                 kernel_regularizer=l2(self.l2_reg)),
            BatchNormalization(),
            
            # Dense layers
            Dense(self.dense_units[0], activation='relu', kernel_regularizer=l2(self.l2_reg)),
            Dropout(self.dropout_rate),
            
            Dense(self.dense_units[1], activation='relu', kernel_regularizer=l2(self.l2_reg)),
            Dropout(self.dropout_rate),
            
            # Output layer for 3 timeframes (1h, 4h, 1d) - linear for regression
            Dense(3, activation='tanh', name='magnitude_output')  # tanh for bounded output
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001, clipnorm=1.0),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train_lstm_models(self, X: np.ndarray, y: Dict, validation_split: float = 0.2) -> Dict:
        """
        Train both direction and magnitude LSTM models
        
        Args:
            X: Sequential feature data
            y: Target dictionary with 'direction' and 'magnitude'
            validation_split: Fraction of data to use for validation
            
        Returns:
            Training results and metrics
        """
        if not self.check_tensorflow_availability():
            return {"error": "TensorFlow not available"}
        
        logger.info("Training LSTM models...")
        
        input_shape = (X.shape[1], X.shape[2])  # (sequence_length, features)
        
        # Callbacks for training optimization
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=self.patience, restore_best_weights=True, verbose=1),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-7, verbose=1)
        ]
        
        results = {}
        
        # Train direction model (classification)
        logger.info("Training direction prediction model...")
        self.direction_model = self.create_direction_model(input_shape)
        
        direction_history = self.direction_model.fit(
            X, y['direction'],
            batch_size=self.batch_size,
            epochs=self.epochs,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=0
        )
        
        # Evaluate direction model
        direction_loss = self.direction_model.evaluate(X, y['direction'], verbose=0)
        results['direction'] = {
            'final_loss': direction_loss[0],
            'final_accuracy': direction_loss[1],
            'training_history': direction_history.history
        }
        
        # Train magnitude model (regression)
        logger.info("Training magnitude prediction model...")
        self.magnitude_model = self.create_magnitude_model(input_shape)
        
        magnitude_history = self.magnitude_model.fit(
            X, y['magnitude'],
            batch_size=self.batch_size,
            epochs=self.epochs,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=0
        )
        
        # Evaluate magnitude model
        magnitude_loss = self.magnitude_model.evaluate(X, y['magnitude'], verbose=0)
        results['magnitude'] = {
            'final_loss': magnitude_loss[0],
            'final_mae': magnitude_loss[1],
            'training_history': magnitude_history.history
        }
        
        logger.info(f"LSTM training completed:")
        logger.info(f"  Direction accuracy: {direction_loss[1]:.3f}")
        logger.info(f"  Magnitude MAE: {magnitude_loss[1]:.3f}")
        
        return results
    
    def save_lstm_models(self, metadata: Dict):
        """Save LSTM models with metadata"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version = f"lstm_v_{timestamp}"
        
        # Save direction model
        direction_path = os.path.join(self.models_dir, f"lstm_direction_{version}.h5")
        self.direction_model.save(direction_path)
        
        # Save magnitude model
        magnitude_path = os.path.join(self.models_dir, f"lstm_magnitude_{version}.h5")
        self.magnitude_model.save(magnitude_path)
        
        # Save scalers
        import joblib
        feature_scaler_path = os.path.join(self.models_dir, f"lstm_feature_scaler_{version}.pkl")
        target_scaler_path = os.path.join(self.models_dir, f"lstm_target_scaler_{version}.pkl")
        
        joblib.dump(self.feature_scaler, feature_scaler_path)
        joblib.dump(self.target_scaler, target_scaler_path)
        
        # Create comprehensive metadata
        lstm_metadata = {
            'version': version,
            'training_date': timestamp,
            'model_type': 'lstm_neural_network',
            'architecture': {
                'sequence_length': self.sequence_length,
                'lstm_units': self.lstm_units,
                'dense_units': self.dense_units,
                'dropout_rate': self.dropout_rate,
                'l2_regularization': self.l2_reg
            },
            'training_params': {
                'batch_size': self.batch_size,
                'epochs': self.epochs,
                'validation_split': self.validation_split,
                'patience': self.patience
            },
            'model_paths': {
                'direction_model': direction_path,
                'magnitude_model': magnitude_path,
                'feature_scaler': feature_scaler_path,
                'target_scaler': target_scaler_path
            },
            'data_info': metadata
        }
        
        # Save metadata
        metadata_path = os.path.join(self.models_dir, f"lstm_metadata_{version}.json")
        with open(metadata_path, 'w') as f:
            json.dump(lstm_metadata, f, indent=2)
        
        # Update current model links
        self._update_current_model_links(version)
        
        logger.info(f"LSTM models saved: {version}")
        
    def _update_current_model_links(self, version: str):
        """Update current model symlinks"""
        current_links = {
            'current_lstm_direction.h5': f"lstm_direction_{version}.h5",
            'current_lstm_magnitude.h5': f"lstm_magnitude_{version}.h5",
            'current_lstm_feature_scaler.pkl': f"lstm_feature_scaler_{version}.pkl",
            'current_lstm_target_scaler.pkl': f"lstm_target_scaler_{version}.pkl",
            'current_lstm_metadata.json': f"lstm_metadata_{version}.json"
        }
        
        for current_name, versioned_name in current_links.items():
            current_path = os.path.join(self.models_dir, current_name)
            
            # Remove existing link
            if os.path.exists(current_path) or os.path.islink(current_path):
                os.unlink(current_path)
            
            # Create new link (or copy if symlink fails)
            try:
                os.symlink(versioned_name, current_path)
            except OSError:
                # Fallback to copying
                import shutil
                versioned_path = os.path.join(self.models_dir, versioned_name)
                shutil.copy2(versioned_path, current_path)
    
    def load_lstm_models(self, version: str = "current") -> bool:
        """Load LSTM models from disk"""
        if not self.check_tensorflow_availability():
            return False
            
        try:
            if version == "current":
                direction_path = os.path.join(self.models_dir, 'current_lstm_direction.h5')
                magnitude_path = os.path.join(self.models_dir, 'current_lstm_magnitude.h5')
                feature_scaler_path = os.path.join(self.models_dir, 'current_lstm_feature_scaler.pkl')
                target_scaler_path = os.path.join(self.models_dir, 'current_lstm_target_scaler.pkl')
            else:
                direction_path = os.path.join(self.models_dir, f'lstm_direction_{version}.h5')
                magnitude_path = os.path.join(self.models_dir, f'lstm_magnitude_{version}.h5')
                feature_scaler_path = os.path.join(self.models_dir, f'lstm_feature_scaler_{version}.pkl')
                target_scaler_path = os.path.join(self.models_dir, f'lstm_target_scaler_{version}.pkl')
            
            # Check if files exist
            for path in [direction_path, magnitude_path, feature_scaler_path, target_scaler_path]:
                if not os.path.exists(path):
                    logger.warning(f"LSTM model file not found: {path}")
                    return False
            
            # Load models
            self.direction_model = tf.keras.models.load_model(direction_path)
            self.magnitude_model = tf.keras.models.load_model(magnitude_path)
            
            # Load scalers
            import joblib
            self.feature_scaler = joblib.load(feature_scaler_path)
            self.target_scaler = joblib.load(target_scaler_path)
            
            logger.info(f"LSTM models loaded successfully: {version}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading LSTM models: {e}")
            return False
    
    def predict_lstm(self, feature_sequence: np.ndarray) -> Dict:
        """
        Make predictions using trained LSTM models
        
        Args:
            feature_sequence: 2D array (sequence_length, features) - most recent data first
            
        Returns:
            Dictionary with predictions and confidence scores
        """
        if not self.check_tensorflow_availability():
            return {"error": "TensorFlow not available"}
            
        if self.direction_model is None or self.magnitude_model is None:
            if not self.load_lstm_models():
                return {"error": "LSTM models not available"}
        
        try:
            # Ensure correct shape (1, sequence_length, features)
            if feature_sequence.shape[0] != self.sequence_length:
                logger.warning(f"Sequence length mismatch: expected {self.sequence_length}, got {feature_sequence.shape[0]}")
                return {"error": f"Invalid sequence length: {feature_sequence.shape[0]}"}
            
            # Normalize features
            X_scaled = self.feature_scaler.transform(feature_sequence)
            X_input = X_scaled.reshape(1, self.sequence_length, -1)
            
            # Make predictions
            direction_pred = self.direction_model.predict(X_input, verbose=0)[0]
            magnitude_pred_scaled = self.magnitude_model.predict(X_input, verbose=0)[0]
            
            # Inverse scale magnitude predictions
            magnitude_pred = self.target_scaler.inverse_transform(magnitude_pred_scaled.reshape(1, -1))[0]
            
            # Convert probabilities to binary decisions (threshold = 0.5)
            direction_binary = (direction_pred > 0.5).astype(int)
            
            # Calculate confidence scores
            direction_confidence = np.maximum(direction_pred, 1 - direction_pred)  # Distance from 0.5
            avg_confidence = np.mean(direction_confidence)
            
            # Determine overall action
            avg_direction = np.mean(direction_binary)
            avg_magnitude = np.mean(np.abs(magnitude_pred))
            
            if avg_direction > 0.6 and avg_magnitude > 0.02 and avg_confidence > 0.7:
                action = 'BUY'
            elif avg_direction < 0.4 and avg_magnitude > 0.02 and avg_confidence > 0.7:
                action = 'SELL'
            else:
                action = 'HOLD'
            
            return {
                'direction_predictions': {
                    '1h': int(direction_binary[0]),
                    '4h': int(direction_binary[1]), 
                    '1d': int(direction_binary[2])
                },
                'direction_probabilities': {
                    '1h': float(direction_pred[0]),
                    '4h': float(direction_pred[1]),
                    '1d': float(direction_pred[2])
                },
                'magnitude_predictions': {
                    '1h': float(magnitude_pred[0]),
                    '4h': float(magnitude_pred[1]),
                    '1d': float(magnitude_pred[2])
                },
                'confidence_scores': {
                    '1h': float(direction_confidence[0]),
                    '4h': float(direction_confidence[1]),
                    '1d': float(direction_confidence[2]),
                    'average': float(avg_confidence)
                },
                'optimal_action': action,
                'model_type': 'lstm_neural_network',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LSTM prediction error: {e}")
            return {"error": str(e)}

# Main training function for external use
def train_lstm_model(db_path: str = "data/trading_unified.db", sequence_length: int = 10) -> Dict:
    """
    Main function to train LSTM models
    
    Returns:
        Training results and model performance metrics
    """
    lstm_nn = LSTMNeuralNetwork(db_path=db_path, sequence_length=sequence_length)
    
    # Prepare data
    X, y, metadata = lstm_nn.prepare_sequence_data(min_samples=50)
    
    if X is None:
        return {"error": "Insufficient data for LSTM training"}
    
    # Train models
    training_results = lstm_nn.train_lstm_models(X, y)
    
    if "error" not in training_results:
        # Save models
        lstm_nn.save_lstm_models(metadata)
        
        # Add metadata to results
        training_results['metadata'] = metadata
        training_results['success'] = True
        
        logger.info("LSTM training pipeline completed successfully")
    
    return training_results

if __name__ == "__main__":
    # Test the LSTM implementation
    results = train_lstm_model()
    
    if "error" in results:
        print(f"❌ LSTM training failed: {results['error']}")
    else:
        print("✅ LSTM training completed successfully!")
        print(f"📊 Direction accuracy: {results['direction']['final_accuracy']:.3f}")
        print(f"📊 Magnitude MAE: {results['magnitude']['final_mae']:.3f}")
        print(f"📈 Sequences created: {results['metadata']['sequences_created']}")
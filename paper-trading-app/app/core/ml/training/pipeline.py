#!/usr/bin/env python3
"""
Machine Learning Training Pipeline for Trading Sentiment Analysis
Handles data collection, labeling, training, and model updating
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib
import json
import os
from typing import Dict, List, Tuple, Optional
import logging
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from sklearn.preprocessing import StandardScaler
import sqlite3

logger = logging.getLogger(__name__)

class MLTrainingPipeline:
    """Manages the complete ML training lifecycle"""
    
    def __init__(self, data_dir: str = "data/ml_models"):
        self.data_dir = data_dir
        self.models_dir = os.path.join(data_dir, "models")
        self.training_data_dir = os.path.join(data_dir, "training_data")
        self.ensure_directories()
        
        # Initialize database for training data
        self.db_path = os.path.join(self.data_dir, "training_data.db")
        self.init_database()
        
        # Model versioning
        self.model_version = self.get_latest_model_version()
        
    def ensure_directories(self):
        """Create necessary directories"""
        for dir_path in [self.data_dir, self.models_dir, self.training_data_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def init_database(self):
        """Initialize SQLite database for training data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for storing features and outcomes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                sentiment_score REAL,
                confidence REAL,
                news_count INTEGER,
                reddit_sentiment REAL,
                event_score REAL,
                technical_score REAL,
                ml_features TEXT,  -- JSON string of additional features
                feature_version TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id INTEGER,
                symbol TEXT NOT NULL,
                signal_timestamp DATETIME NOT NULL,
                signal_type TEXT,  -- BUY, SELL, HOLD
                entry_price REAL,
                exit_price REAL,
                exit_timestamp DATETIME,
                return_pct REAL,
                max_drawdown REAL,
                outcome_label INTEGER,  -- 1 for profitable, 0 for loss
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (feature_id) REFERENCES sentiment_features (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version TEXT,
                model_type TEXT,
                training_date DATETIME,
                validation_score REAL,
                test_score REAL,
                precision_score REAL,
                recall_score REAL,
                parameters TEXT,  -- JSON string
                feature_importance TEXT,  -- JSON string
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def collect_training_data(self, sentiment_data: Dict, symbol: str) -> int:
        """
        Store sentiment analysis results for future training
        
        Args:
            sentiment_data: Output from analyze_bank_sentiment
            symbol: Stock symbol
            
        Returns:
            feature_id for linking with outcomes
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract ML features if available
        ml_features = {}
        if 'ml_trading_details' in sentiment_data.get('sentiment_components', {}):
            ml_features = sentiment_data['sentiment_components']['ml_trading_details']
        
        cursor.execute('''
            INSERT INTO sentiment_features 
            (symbol, timestamp, sentiment_score, confidence, news_count, 
             reddit_sentiment, event_score, technical_score, ml_features, feature_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            sentiment_data['timestamp'],
            sentiment_data['overall_sentiment'],
            sentiment_data['confidence'],
            sentiment_data['news_count'],
            sentiment_data.get('reddit_sentiment', {}).get('average_sentiment', 0),
            sentiment_data.get('sentiment_components', {}).get('events', 0),
            0,  # Technical score - to be added
            json.dumps(ml_features),
            "1.0"
        ))
        
        feature_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return feature_id
    
    def record_trading_outcome(self, feature_id: int, outcome_data: Dict):
        """
        Record the actual outcome of a trading signal
        
        Args:
            feature_id: ID from collect_training_data
            outcome_data: Dict containing trade results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate return percentage
        return_pct = ((outcome_data['exit_price'] - outcome_data['entry_price']) / 
                      outcome_data['entry_price']) * 100
        
        # Label: 1 if profitable (including fees), 0 if loss
        # Assuming 0.1% fee per trade (0.2% round trip)
        net_return = return_pct - 0.2
        outcome_label = 1 if net_return > 0 else 0
        
        cursor.execute('''
            INSERT INTO trading_outcomes
            (feature_id, symbol, signal_timestamp, signal_type, entry_price,
             exit_price, exit_timestamp, return_pct, max_drawdown, outcome_label)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            feature_id,
            outcome_data['symbol'],
            outcome_data['signal_timestamp'],
            outcome_data['signal_type'],
            outcome_data['entry_price'],
            outcome_data['exit_price'],
            outcome_data['exit_timestamp'],
            return_pct,
            outcome_data.get('max_drawdown', 0),
            outcome_label
        ))
        
        conn.commit()
        conn.close()
    
    def prepare_training_dataset(self, min_samples: int = 100) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare dataset for training from collected data
        
        Returns:
            X: Feature matrix
            y: Labels (profitable or not)
        """
        conn = sqlite3.connect(self.db_path)
        
        # Join features with outcomes
        query = '''
            SELECT 
                sf.*,
                tro.outcome_label,
                tro.return_pct,
                tro.signal_type
            FROM sentiment_features sf
            INNER JOIN trading_outcomes tro ON sf.id = tro.feature_id
            WHERE tro.outcome_label IS NOT NULL
            ORDER BY sf.timestamp
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) < min_samples:
            logger.warning(f"Insufficient training data: {len(df)} samples (minimum: {min_samples})")
            return None, None
        
        # Prepare features
        feature_columns = [
            'sentiment_score', 'confidence', 'news_count', 
            'reddit_sentiment', 'event_score'
        ]
        
        X = df[feature_columns].copy()
        
        # Add engineered features
        X['sentiment_confidence_interaction'] = X['sentiment_score'] * X['confidence']
        X['news_volume_category'] = pd.cut(X['news_count'], bins=[0, 5, 10, 20, 100], labels=[0, 1, 2, 3])
        X['news_volume_category'] = X['news_volume_category'].astype(int)
        
        # Add time-based features
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        X['hour'] = df['timestamp'].dt.hour
        X['day_of_week'] = df['timestamp'].dt.dayofweek
        X['is_market_hours'] = ((X['hour'] >= 10) & (X['hour'] <= 16)).astype(int)
        
        # Parse ML features from JSON
        if 'ml_features' in df.columns:
            ml_features_expanded = pd.json_normalize(df['ml_features'].apply(json.loads))
            X = pd.concat([X, ml_features_expanded], axis=1)
        
        # Labels
        y = df['outcome_label']
        
        return X, y
    
    def train_models(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, any]:
        """
        Train multiple models and select best performer
        """
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.neural_network import MLPClassifier
        
        # Try to import XGBoost (optional)
        try:
            import xgboost as xgb
            XGBOOST_AVAILABLE = True
        except ImportError:
            XGBOOST_AVAILABLE = False
            logger.warning("XGBoost not available, skipping XGBoost models")
        
        # Time series split for financial data
        # For very small datasets, skip cross-validation
        if len(X) < 10:
            logger.warning(f"Dataset too small ({len(X)} samples) for reliable cross-validation")
            use_cv = False
            tscv = None
        else:
            use_cv = True
            max_splits = min(5, len(X) - 1)
            tscv = TimeSeriesSplit(n_splits=max_splits)
        
        models = {
            'random_forest': RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_split=20,
                class_weight='balanced',
                random_state=42
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=6,
                random_state=42
            ),
            'neural_network': MLPClassifier(
                hidden_layer_sizes=(100, 50),
                activation='relu',
                learning_rate='adaptive',
                max_iter=1000,
                random_state=42
            ),
            'logistic_regression': LogisticRegression(
                class_weight='balanced',
                max_iter=1000,
                random_state=42
            )
        }
        
        # Add XGBoost if available
        if XGBOOST_AVAILABLE:
            models['xgboost'] = xgb.XGBClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=6,
                scale_pos_weight=len(y[y==0])/len(y[y==1]) if len(y[y==1]) > 0 else 1,  # Handle imbalance
                random_state=42
            )
        
        # Scale features for neural network and logistic regression
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        best_model = None
        best_score = -1
        model_scores = {}
        
        for name, model in models.items():
            logger.info(f"Training {name}...")
            
            # Use scaled data for certain models
            if name in ['neural_network', 'logistic_regression']:
                X_train = X_scaled
                use_pandas_indexing = False
            else:
                X_train = X
                use_pandas_indexing = True
            
            # Cross-validation scores
            cv_scores = []
            
            if use_cv and tscv is not None:
                # Use cross-validation for larger datasets
                for train_idx, val_idx in tscv.split(X_train):
                    if use_pandas_indexing:
                        X_cv_train, X_cv_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
                    else:
                        X_cv_train, X_cv_val = X_train[train_idx], X_train[val_idx]
                    y_cv_train, y_cv_val = y.iloc[train_idx], y.iloc[val_idx]
                    
                    model.fit(X_cv_train, y_cv_train)
                    
                    # Use probability for better threshold tuning
                    y_pred_proba = model.predict_proba(X_cv_val)[:, 1]
                    
                    # Find optimal threshold for trading (minimize false positives)
                    best_threshold = 0.5
                    best_precision = 0
                    
                    for threshold in [0.3, 0.4, 0.5, 0.6, 0.7]:
                        y_pred = (y_pred_proba >= threshold).astype(int)
                        if len(set(y_pred)) > 1:  # Ensure we have both classes
                            precision = precision_recall_fscore_support(y_cv_val, y_pred, average='binary')[0]
                            if precision > best_precision:
                                best_precision = precision
                                best_threshold = threshold
                    
                    cv_scores.append(best_precision)
                
                avg_cv_score = np.mean(cv_scores)
                std_cv_score = np.std(cv_scores)
            else:
                # For small datasets, just train on full data and use a basic score
                logger.info(f"Training {name} on full dataset (no cross-validation)")
                model.fit(X_train, y)
                
                # Simple validation score based on training accuracy
                y_pred_proba = model.predict_proba(X_train)
                
                # Handle case where only one class is present
                if y_pred_proba.shape[1] == 1:
                    # Only one class predicted, assign default probabilities
                    avg_cv_score = 0.5  # Default score
                    y_pred = model.predict(X_train)
                else:
                    # Normal case with both classes
                    y_pred_proba_class1 = y_pred_proba[:, 1]
                    y_pred = (y_pred_proba_class1 >= 0.5).astype(int)
                    
                    if len(set(y_pred)) > 1:
                        avg_cv_score = precision_recall_fscore_support(y, y_pred, average='binary')[0]
                    else:
                        avg_cv_score = 0.5  # Default score for single-class prediction
                std_cv_score = 0
            
            model_scores[name] = {
                'avg_cv_score': avg_cv_score,
                'std_cv_score': std_cv_score,
                'model': model
            }
            
            if avg_cv_score > best_score:
                best_score = avg_cv_score
                best_model = name
        
        logger.info(f"Best model: {best_model} with score: {best_score:.4f}")
        
        # Train best model on full dataset
        final_model = models[best_model]
        if best_model in ['neural_network', 'logistic_regression']:
            final_model.fit(X_scaled, y)
            # Save scaler
            joblib.dump(scaler, os.path.join(self.models_dir, 'feature_scaler.pkl'))
        else:
            final_model.fit(X, y)
        
        # Save model and metadata
        self.save_model(final_model, best_model, model_scores[best_model], X.columns.tolist())
        
        return {
            'best_model': best_model,
            'model_scores': model_scores,
            'feature_columns': X.columns.tolist()
        }
    
    def save_model(self, model, model_type: str, performance: Dict, feature_columns: List[str]):
        """Save trained model with metadata"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version = f"v_{timestamp}"
        
        # Save model
        model_path = os.path.join(self.models_dir, f"{model_type}_{version}.pkl")
        joblib.dump(model, model_path)
        
        # Save metadata (extract only serializable parts from performance)
        metadata = {
            'version': version,
            'model_type': model_type,
            'training_date': timestamp,
            'performance': {
                'avg_cv_score': performance.get('avg_cv_score', 0),
                'std_cv_score': performance.get('std_cv_score', 0)
            },
            'feature_columns': feature_columns,
            'model_path': model_path
        }
        
        metadata_path = os.path.join(self.models_dir, f"metadata_{version}.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update current model symlink (handle existing files properly)
        current_model_path = os.path.join(self.models_dir, 'current_model.pkl')
        current_metadata_path = os.path.join(self.models_dir, 'current_metadata.json')
        
        # Remove existing files/symlinks
        for path in [current_model_path, current_metadata_path]:
            if os.path.exists(path) or os.path.islink(path):
                os.unlink(path)  # unlink works for both files and symlinks
        
        # Create new symlinks using relative paths (more robust)
        try:
            os.symlink(os.path.basename(model_path), current_model_path)
            os.symlink(os.path.basename(metadata_path), current_metadata_path)
        except OSError as e:
            # Fallback: copy files instead of symlinks
            logger.warning(f"Symlink failed ({e}), copying files instead")
            import shutil
            shutil.copy2(model_path, current_model_path)
            shutil.copy2(metadata_path, current_metadata_path)
        
        logger.info(f"Model saved: {model_path}")
    
    def get_latest_model_version(self) -> Optional[str]:
        """Get the latest model version"""
        # Try multiple possible metadata file locations
        possible_paths = [
            os.path.join(self.models_dir, 'current_metadata.json'),
            os.path.join(self.data_dir, 'current_metadata.json'),
            os.path.join('data/ml_models/models', 'current_metadata.json'),
            os.path.join('data/ml_models', 'current_metadata.json')
        ]
        
        for metadata_path in possible_paths:
            try:
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    # Try different possible version keys
                    version = metadata.get('version')
                    if version:
                        logger.info(f"Loaded model version '{version}' from {metadata_path}")
                        return version
                    
                    # Fallback: generate version from other metadata
                    if 'training_date' in metadata:
                        version = f"v_{metadata['training_date']}"
                        logger.info(f"Generated version '{version}' from training_date in {metadata_path}")
                        return version
                    
                    if 'created_at' in metadata:
                        # Extract date from ISO format
                        try:
                            from datetime import datetime
                            created = datetime.fromisoformat(metadata['created_at'].replace('Z', '+00:00'))
                            version = f"v_{created.strftime('%Y%m%d_%H%M%S')}"
                            logger.info(f"Generated version '{version}' from created_at in {metadata_path}")
                            return version
                        except:
                            pass
                    
                    # Last resort: use model type and timestamp
                    model_type = metadata.get('model_type', 'unknown')
                    version = f"v_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    logger.warning(f"Generated fallback version '{version}' from {metadata_path}")
                    return version
                        
            except Exception as e:
                logger.warning(f"Error reading metadata from {metadata_path}: {e}")
                continue
        
        # If no metadata files found, return a default version
        logger.warning("No valid metadata files found, using default version")
        return "v_default_no_metadata"
    
    def update_model_online(self, new_samples: List[Tuple[Dict, int]]):
        """
        Online learning - update model with new samples
        
        Args:
            new_samples: List of (features_dict, outcome_label) tuples
        """
        if len(new_samples) < 10:
            logger.info("Insufficient samples for online update")
            return
        
        try:
            # Load current model
            model_path = os.path.join(self.models_dir, 'current_model.pkl')
            if not os.path.exists(model_path):
                logger.warning("No current model found for online update")
                return
            
            model = joblib.load(model_path)
            
            # Check if model supports partial_fit
            if hasattr(model, 'partial_fit'):
                # Prepare new data
                X_new = pd.DataFrame([s[0] for s in new_samples])
                y_new = pd.Series([s[1] for s in new_samples])
                
                # Load scaler if needed
                scaler_path = os.path.join(self.models_dir, 'feature_scaler.pkl')
                if os.path.exists(scaler_path):
                    scaler = joblib.load(scaler_path)
                    X_new = scaler.transform(X_new)
                
                # Update model
                model.partial_fit(X_new, y_new)
                
                # Save updated model
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                updated_path = os.path.join(self.models_dir, f"updated_{timestamp}.pkl")
                joblib.dump(model, updated_path)
                
                logger.info(f"Model updated online with {len(new_samples)} samples")
            else:
                logger.info("Current model doesn't support online learning")
                
        except Exception as e:
            logger.error(f"Error in online model update: {e}")
"""
Enhanced ML Training Pipeline

Implements the machine learning pipeline described in the proposal with features including:
- Sentiment scores and confidence
- News volume and distribution
- Event detection flags
- Time-based features
- Technical indicators
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import ML libraries
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import classification_report, accuracy_score
    from sklearn.preprocessing import StandardScaler
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("ML libraries not available. Install with: pip install scikit-learn")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.info("XGBoost not available (optional)")

class EnhancedMLPipeline:
    """
    Enhanced ML Pipeline for sentiment-based trading prediction.
    """
    
    def __init__(self, data_dir: str = "data/ml_models"):
        """
        Initialize the enhanced ML pipeline.
        
        Args:
            data_dir: Directory to store models and training data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        self.training_data = []
        
        if not ML_AVAILABLE:
            logger.error("ML libraries not available. Pipeline will be limited.")
            return
        
        # Initialize models
        self.models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=42
            ),
            'neural_network': MLPClassifier(
                hidden_layer_sizes=(100, 50),
                max_iter=1000,
                random_state=42,
                early_stopping=True
            )
        }
        
        if XGBOOST_AVAILABLE:
            self.models['xgboost'] = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=42,
                eval_metric='logloss'
            )
        
        self.scalers = {name: StandardScaler() for name in self.models.keys()}
        
        # Try to load existing trained models
        self._load_existing_models()
        
        logger.info(f"Enhanced ML Pipeline initialized with {len(self.models)} models")
    
    
    
    def has_sufficient_training_data(self, min_samples=100):
        """
        Check if we have sufficient training data for ML predictions
        Fresh Start System: Returns False if less than min_samples available
        """
        try:
            import sqlite3
            conn = sqlite3.connect('data/trading_predictions.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM predictions WHERE entry_price > 0')
            sample_count = cursor.fetchone()[0]
            conn.close()
            
            sufficient = sample_count >= min_samples
            logger.info(f'Fresh Start: {sample_count}/{min_samples} samples - ML enabled: {sufficient}')
            return sufficient
        except Exception as e:
            logger.warning(f'Error checking training data: {e}')
            return False
    def extract_features(self, sentiment_data: Dict, market_data: Dict = None, 
                        news_data: List = None) -> Dict[str, float]:
        """
        Extract comprehensive features for ML training.
        
        Args:
            sentiment_data: Sentiment analysis results
            market_data: Market data (price, volume, etc.)
            news_data: Raw news articles
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        # Sentiment features - validate sentiment data quality
        overall_sentiment = sentiment_data.get('overall_sentiment')
        confidence = sentiment_data.get('confidence', 0.0)
        
        # Only proceed if we have valid sentiment data
        if overall_sentiment is None or overall_sentiment == 0.0:
            logger.warning("Missing or invalid sentiment data - skipping prediction")
            return None
            
        features['sentiment_score'] = overall_sentiment
        features['confidence'] = confidence
        features['news_count'] = sentiment_data.get('news_count', 0)
        
        # News volume features
        if news_data:
            features['news_volume'] = len(news_data)
            features['avg_news_length'] = np.mean([len(item.get('content', '')) for item in news_data])
            features['news_sources'] = len(set(item.get('source', 'unknown') for item in news_data))
        else:
            features['news_volume'] = 0
            features['avg_news_length'] = 0
            features['news_sources'] = 0
        
        # Event detection features
        features['has_earnings'] = self._detect_event(news_data, ['earnings', 'profit', 'results'])
        features['has_dividend'] = self._detect_event(news_data, ['dividend', 'payout'])
        features['has_scandal'] = self._detect_event(news_data, ['scandal', 'investigation', 'fine'])
        features['has_upgrade'] = self._detect_event(news_data, ['upgrade', 'outperform'])
        features['has_downgrade'] = self._detect_event(news_data, ['downgrade', 'underperform'])
        
        # Time-based features
        now = datetime.now()
        features['hour_of_day'] = now.hour
        features['day_of_week'] = now.weekday()
        features['is_market_hours'] = 1 if 10 <= now.hour <= 16 else 0
        features['is_weekend'] = 1 if now.weekday() >= 5 else 0
        
        # Market data features (if available)
        if market_data:
            features['current_price'] = market_data.get('price', 0.0)
            features['price_change_pct'] = market_data.get('change_percent', 0.0)
            features['volume'] = market_data.get('volume', 0)
            features['volatility'] = market_data.get('volatility', 0.0)
        else:
            features['current_price'] = 0.0
            features['price_change_pct'] = 0.0
            features['volume'] = 0
            features['volatility'] = 0.0
        
        # Technical indicators (mock values for now)
        features['rsi'] = market_data.get('rsi', 50.0) if market_data else 50.0
        features['macd'] = market_data.get('macd', 0.0) if market_data else 0.0
        features['moving_avg_20'] = market_data.get('ma_20', 0.0) if market_data else 0.0
        
        # Urgency and impact features
        features['urgency_score'] = self._calculate_urgency(news_data)
        features['impact_score'] = abs(features['sentiment_score']) * features['confidence']
        
        return features
    
    def _detect_event(self, news_data: List, keywords: List[str]) -> float:
        """
        Detect if specific events are mentioned in news.
        
        Args:
            news_data: List of news articles
            keywords: Keywords to search for
            
        Returns:
            Binary indicator (1.0 if detected, 0.0 otherwise)
        """
        if not news_data:
            return 0.0
        
        for item in news_data:
            content = (item.get('title', '') + ' ' + item.get('content', '')).lower()
            if any(keyword.lower() in content for keyword in keywords):
                return 1.0
        
        return 0.0
    
    def _calculate_urgency(self, news_data: List) -> float:
        """
        Calculate urgency score based on news recency and keywords.
        
        Args:
            news_data: List of news articles
            
        Returns:
            Urgency score (0.0 to 1.0)
        """
        if not news_data:
            return 0.0
        
        urgent_keywords = ['breaking', 'urgent', 'alert', 'immediate', 'emergency']
        urgency_score = 0.0
        
        for item in news_data:
            content = (item.get('title', '') + ' ' + item.get('content', '')).lower()
            
            # Check for urgent keywords
            keyword_urgency = sum(1 for keyword in urgent_keywords if keyword in content)
            
            # Add recency factor (assuming recent news is more urgent)
            recency_urgency = 0.5  # Placeholder
            
            urgency_score += (keyword_urgency * 0.3) + (recency_urgency * 0.7)
        
        return min(urgency_score / len(news_data), 1.0)
    
    def collect_training_data(self, symbol: str, sentiment_data: Dict, 
                            market_data: Dict = None, news_data: List = None) -> str:
        """
        Collect training data for a prediction.
        
        Args:
            symbol: Stock symbol
            sentiment_data: Sentiment analysis results
            market_data: Market data
            news_data: News articles
            
        Returns:
            Feature ID for outcome tracking
        """
        if not ML_AVAILABLE:
            logger.warning("ML not available, cannot collect training data")
            return ""
        
        # Extract features
        features = self.extract_features(sentiment_data, market_data, news_data)
        
        # Create feature record
        feature_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        training_record = {
            'feature_id': feature_id,
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'features': features,
            'sentiment_data': sentiment_data,
            'outcome': None,  # To be filled later
            'outcome_timestamp': None
        }
        
        # Store for later outcome recording
        self.training_data.append(training_record)
        
        # Save to file
        self._save_training_data()
        
        logger.info(f"Collected training data for {symbol} (ID: {feature_id})")
        return feature_id
    
    def record_trading_outcome(self, feature_id: str, outcome: str, 
                             price_change: float = None) -> bool:
        """
        Record the outcome for a previously collected training sample.
        
        Args:
            feature_id: ID of the training sample
            outcome: 'profitable', 'unprofitable', or 'neutral'
            price_change: Actual price change (optional)
            
        Returns:
            True if outcome was recorded successfully
        """
        if not ML_AVAILABLE:
            return False
        
        # Find the training record
        for record in self.training_data:
            if record['feature_id'] == feature_id:
                record['outcome'] = outcome
                record['outcome_timestamp'] = datetime.now().isoformat()
                if price_change is not None:
                    record['price_change'] = price_change
                
                self._save_training_data()
                logger.info(f"Recorded outcome for {feature_id}: {outcome}")
                return True
        
        logger.warning(f"Feature ID {feature_id} not found for outcome recording")
        return False
    
    def train_models(self, min_samples: int = 100) -> Dict[str, float]:
        """
        Train all ML models with available data.
        
        Args:
            min_samples: Minimum number of samples required for training
            
        Returns:
            Dictionary of model accuracies
        """
        if not ML_AVAILABLE:
            logger.error("ML libraries not available for training")
            return {}
        
        # Load training data
        self._load_training_data()
        
        # Filter for samples with outcomes
        completed_samples = [
            record for record in self.training_data 
            if record.get('outcome') is not None
        ]
        
        if len(completed_samples) < min_samples:
            logger.warning(f"Insufficient training data: {len(completed_samples)}/{min_samples}")
            return {}
        
        # Prepare features and labels
        X, y = self._prepare_training_dataset(completed_samples)
        
        if X is None or len(X) == 0:
            logger.error("Failed to prepare training dataset")
            return {}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train and evaluate models
        accuracies = {}
        
        for name, model in self.models.items():
            try:
                logger.info(f"Training {name}...")
                
                # Scale features
                scaler = self.scalers[name]
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # Train model
                model.fit(X_train_scaled, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                accuracies[name] = accuracy
                
                # Save model and scaler
                self._save_model(name, model, scaler)
                
                logger.info(f"{name} accuracy: {accuracy:.3f}")
                
            except Exception as e:
                logger.error(f"Error training {name}: {e}")
                accuracies[name] = 0.0
        
        logger.info(f"Training completed. Best model: {max(accuracies, key=accuracies.get)}")
        return accuracies
    
    def predict(self, sentiment_data: Dict, market_data: Dict = None, 
               news_data: List = None) -> Dict[str, Any]:
        """
        Make predictions using trained models.
        
        Args:
            sentiment_data: Sentiment analysis results
            market_data: Market data
            news_data: News articles
            
        Returns:
            Dictionary with predictions from all models
        """
        if not ML_AVAILABLE:
            return {'error': 'ML not available'}
        
        # Extract features
        features = self.extract_features(sentiment_data, market_data, news_data)
        
        # Convert to array
        if not self.feature_columns:
            logger.warning("No trained models available")
            return {'error': 'No trained models'}
        
        feature_array = np.array([[features.get(col, 0.0) for col in self.feature_columns]])
        
        predictions = {}
        confidences = {}
        
        for name in self.models.keys():
            try:
                model, scaler = self._load_model(name)
                if model is None:
                    continue
                
                # Scale features and predict
                feature_scaled = scaler.transform(feature_array)
                prediction = model.predict(feature_scaled)[0]
                
                # Get prediction probability if available
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(feature_scaled)[0]
                    confidence = max(proba)
                else:
                    confidence = 0.7  # Default confidence
                
                predictions[name] = prediction
                confidences[name] = confidence
                
            except Exception as e:
                logger.error(f"Error predicting with {name}: {e}")
        
        if not predictions:
            return {'error': 'No predictions available'}
        
        # Ensemble prediction (majority vote)
        prediction_counts = {}
        for pred in predictions.values():
            prediction_counts[pred] = prediction_counts.get(pred, 0) + 1
        
        ensemble_prediction = max(prediction_counts, key=prediction_counts.get)
        ensemble_confidence = np.mean(list(confidences.values()))
        
        return {
            'ensemble_prediction': ensemble_prediction,
            'ensemble_confidence': round(ensemble_confidence, 3),
            'individual_predictions': predictions,
            'individual_confidences': confidences,
            'feature_count': len(features)
        }
    
    def _prepare_training_dataset(self, completed_samples: List) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training dataset from completed samples.
        """
        if not completed_samples:
            return None, None
        
        # Extract features and labels
        feature_dicts = [sample['features'] for sample in completed_samples]
        labels = [sample['outcome'] for sample in completed_samples]
        
        # Get all feature columns
        all_features = set()
        for feature_dict in feature_dicts:
            all_features.update(feature_dict.keys())
        
        self.feature_columns = sorted(list(all_features))
        
        # Convert to arrays
        X = np.array([[features.get(col, 0.0) for col in self.feature_columns] 
                     for features in feature_dicts])
        y = np.array(labels)
        
        return X, y
    
    def _save_training_data(self):
        """Save training data to file."""
        filepath = self.data_dir / 'training_data.json'
        with open(filepath, 'w') as f:
            json.dump(self.training_data, f, indent=2)
    
    def _load_training_data(self):
        """Load training data from SQLite database."""
        try:
            import sqlite3
            db_path = "data/trading_predictions.db"
            if not os.path.exists(db_path):
                logger.warning(f"Training database not found: {db_path}")
                return
            
            conn = sqlite3.connect(db_path)
            
            # Load sentiment features with outcomes
            query = """
            SELECT sf.*, tos.outcome_label, tos.return_pct, tos.created_at as outcome_timestamp
            FROM sentiment_features sf
            LEFT JOIN trading_outcomes tos ON sf.id = tos.feature_id
            """
            
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute("PRAGMA table_info(sentiment_features)")
            columns = [col[1] for col in cursor.fetchall()]
            columns.extend(['outcome_label', 'return_pct', 'outcome_timestamp'])
            
            # Convert to training data format
            self.training_data = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # Extract features (skip metadata columns)
                features = {}
                metadata_cols = ['id', 'symbol', 'timestamp', 'ml_features', 'feature_version', 'created_at', 'outcome_label', 'return_pct', 'outcome_timestamp']
                for col, val in row_dict.items():
                    if col not in metadata_cols and val is not None:
                        features[col] = float(val)
                
                # Map outcome_label to string outcome
                outcome = None
                if row_dict.get('outcome_label') is not None:
                    outcome_map = {0: 'unprofitable', 1: 'profitable', 2: 'neutral'}
                    outcome = outcome_map.get(row_dict.get('outcome_label'), 'neutral')
                
                training_record = {
                    'feature_id': f"{row_dict.get('symbol')}_{row_dict.get('id')}",
                    'symbol': row_dict.get('symbol'),
                    'timestamp': row_dict.get('timestamp'),
                    'features': features,
                    'outcome': outcome,
                    'outcome_timestamp': row_dict.get('outcome_timestamp')
                }
                
                self.training_data.append(training_record)
            
            conn.close()
            logger.info(f"Loaded {len(self.training_data)} training samples from database")
            
        except Exception as e:
            logger.error(f"Error loading training data from database: {e}")
            # Fallback to JSON file
            filepath = self.data_dir / 'training_data.json'
            if filepath.exists():
                with open(filepath, 'r') as f:
                    self.training_data = json.load(f)
            else:
                self.training_data = []
    
    def _save_model(self, name: str, model, scaler):
        """Save trained model and scaler."""
        if not ML_AVAILABLE:
            return
        
        model_path = self.data_dir / f'{name}_model.pkl'
        scaler_path = self.data_dir / f'{name}_scaler.pkl'
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        # Save feature columns
        features_path = self.data_dir / 'feature_columns.json'
        with open(features_path, 'w') as f:
            json.dump(self.feature_columns, f)
    
    def _load_existing_models(self):
        """Load existing trained models if available."""
        try:
            # Load feature columns first
            features_path = self.data_dir / 'feature_columns.json'
            if features_path.exists():
                with open(features_path, 'r') as f:
                    self.feature_columns = json.load(f)
                logger.info(f"Loaded feature columns: {len(self.feature_columns)} features")
            else:
                logger.info("No feature columns file found, will train new models")
                return
            
            # Load each model and scaler
            loaded_count = 0
            for name in list(self.models.keys()):
                model_path = self.data_dir / f'{name}_model.pkl'
                scaler_path = self.data_dir / f'{name}_scaler.pkl'
                
                if model_path.exists() and scaler_path.exists():
                    try:
                        # Load model and scaler
                        self.models[name] = joblib.load(model_path)
                        self.scalers[name] = joblib.load(scaler_path)
                        loaded_count += 1
                        logger.info(f"Loaded trained model: {name}")
                    except Exception as e:
                        logger.warning(f"Failed to load model {name}: {e}")
                        # Keep the untrained model
                else:
                    logger.info(f"No trained model found for {name}, keeping untrained version")
            
            logger.info(f"Loaded {loaded_count}/{len(self.models)} trained models")
            
        except Exception as e:
            logger.error(f"Error loading existing models: {e}")
    
    def _load_model(self, name: str) -> Tuple[Any, Any]:
        """Load trained model and scaler."""
        if not ML_AVAILABLE:
            return None, None
        
        model_path = self.data_dir / f'{name}_model.pkl'
        scaler_path = self.data_dir / f'{name}_scaler.pkl'
        features_path = self.data_dir / 'feature_columns.json'
        
        if not all(path.exists() for path in [model_path, scaler_path, features_path]):
            return None, None
        
        try:
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            
            with open(features_path, 'r') as f:
                self.feature_columns = json.load(f)
            
            return model, scaler
        except Exception as e:
            logger.error(f"Error loading model {name}: {e}")
            return None, None

if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    pipeline = EnhancedMLPipeline()
    
    # Mock data for testing
    sentiment_data = {
        'overall_sentiment': 0.3,
        'confidence': 0.8,
        'news_count': 10
    }
    
    market_data = {
        'price': 95.50,
        'change_percent': 2.1,
        'volume': 1000000,
        'volatility': 0.15
    }
    
    news_data = [
        {'title': 'Bank reports strong earnings', 'content': 'Quarterly results beat expectations'},
        {'title': 'Dividend increase announced', 'content': 'Bank raises dividend by 5%'}
    ]
    
    # Collect training data
    feature_id = pipeline.collect_training_data('CBA.AX', sentiment_data, market_data, news_data)
    print(f"Collected feature ID: {feature_id}")
    
    # Record outcome (in real usage, this would happen later)
    success = pipeline.record_trading_outcome(feature_id, 'profitable', 2.1)
    print(f"Outcome recorded: {success}")

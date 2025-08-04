#!/usr/bin/env python3
"""
Enhanced ML Training Pipeline for ASX Trading System
Implements the requirements from dashboard.instructions.md

Phase 1: Data Integration Enhancement
- Integrates technical indicators with ML pipeline
- Adds price features, volume features, and market context
- Comprehensive feature engineering

Phase 2: Multi-Output Prediction Model
- Price direction and magnitude predictions
- Multiple timeframes (1h, 4h, 1d)
- Confidence scoring and action recommendations

Phase 3: Feature Engineering Pipeline
- Interaction features and time-based features
- Australian market-specific features

Phase 4: Data Validation Framework
- Comprehensive data quality validation
- Temporal alignment verification
- Look-ahead bias prevention
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
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.multioutput import MultiOutputClassifier, MultiOutputRegressor
import sqlite3
import warnings
warnings.filterwarnings('ignore')

try:
    from ..analysis.technical import TechnicalAnalyzer, get_market_data
    from ...config.settings import Settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from app.core.analysis.technical import TechnicalAnalyzer, get_market_data
    from app.config.settings import Settings

logger = logging.getLogger(__name__)

class EnhancedMLTrainingPipeline:
    """Enhanced ML Training Pipeline implementing dashboard.instructions.md requirements"""
    
    def __init__(self, data_dir: str = "data/ml_models"):
        self.data_dir = data_dir
        self.models_dir = os.path.join(data_dir, "models")
        self.training_data_dir = os.path.join(data_dir, "training_data")
        self.ensure_directories()
        
        # Initialize database for training data
        self.db_path = os.path.join(self.data_dir, "enhanced_training_data.db")
        self.init_database()
        
        # Initialize technical analyzer
        self.settings = Settings()
        self.technical_analyzer = TechnicalAnalyzer(self.settings)
        
        # Define required features as per instructions
        self.required_features = {
            'technical_indicators': [
                'rsi', 'macd_line', 'macd_signal', 'macd_histogram',
                'sma_20', 'sma_50', 'sma_200', 'ema_12', 'ema_26',
                'bollinger_upper', 'bollinger_lower', 'bollinger_width'
            ],
            'price_features': [
                'current_price', 'price_change_1h', 'price_change_4h', 
                'price_change_1d', 'price_change_5d', 'price_change_20d',
                'price_vs_sma20', 'price_vs_sma50', 'price_vs_sma200',
                'daily_range', 'atr_14', 'volatility_20d'
            ],
            'volume_features': [
                'volume', 'volume_sma20', 'volume_ratio',
                'on_balance_volume', 'volume_price_trend'
            ],
            'market_context': [
                'asx200_change', 'sector_performance', 'aud_usd_rate',
                'vix_level', 'market_breadth', 'market_momentum'
            ],
            'sentiment_features': [
                'sentiment_score', 'confidence', 'news_count', 
                'reddit_sentiment', 'event_score'
            ]
        }
        
        # Interaction features
        self.interaction_features = {
            'sentiment_momentum': 'sentiment_score * momentum_score',
            'sentiment_rsi': 'sentiment_score * (rsi - 50) / 50',
            'volume_sentiment': 'volume_ratio * sentiment_score',
            'confidence_volatility': 'confidence / (volatility_20d + 0.01)',
            'news_volume_impact': 'news_count * volume_ratio',
            'technical_sentiment_divergence': 'abs(technical_signal - sentiment_score)'
        }
        
        # Time-based features for Australian market
        self.time_features = {
            'asx_market_hours': '1 if 10 <= hour < 16 else 0',
            'asx_opening_hour': '1 if 10 <= hour < 11 else 0',
            'asx_closing_hour': '1 if 15 <= hour < 16 else 0',
            'monday_effect': '1 if day_of_week == 0 else 0',
            'friday_effect': '1 if day_of_week == 4 else 0',
            'month_end': '1 if day >= 25 else 0',
            'quarter_end': '1 if month in [3,6,9,12] and day >= 25 else 0'
        }
        
    def ensure_directories(self):
        """Create necessary directories"""
        for dir_path in [self.data_dir, self.models_dir, self.training_data_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def init_database(self):
        """Initialize SQLite database for enhanced training data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced features table with all required features
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enhanced_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                
                -- Sentiment features
                sentiment_score REAL,
                confidence REAL,
                news_count INTEGER,
                reddit_sentiment REAL,
                event_score REAL,
                
                -- Technical indicators
                rsi REAL,
                macd_line REAL,
                macd_signal REAL,
                macd_histogram REAL,
                sma_20 REAL,
                sma_50 REAL,
                sma_200 REAL,
                ema_12 REAL,
                ema_26 REAL,
                bollinger_upper REAL,
                bollinger_lower REAL,
                bollinger_width REAL,
                
                -- Price features
                current_price REAL,
                price_change_1h REAL,
                price_change_4h REAL,
                price_change_1d REAL,
                price_change_5d REAL,
                price_change_20d REAL,
                price_vs_sma20 REAL,
                price_vs_sma50 REAL,
                price_vs_sma200 REAL,
                daily_range REAL,
                atr_14 REAL,
                volatility_20d REAL,
                
                -- Volume features
                volume REAL,
                volume_sma20 REAL,
                volume_ratio REAL,
                on_balance_volume REAL,
                volume_price_trend REAL,
                
                -- Market context
                asx200_change REAL,
                sector_performance REAL,
                aud_usd_rate REAL,
                vix_level REAL,
                market_breadth REAL,
                market_momentum REAL,
                
                -- Interaction features
                sentiment_momentum REAL,
                sentiment_rsi REAL,
                volume_sentiment REAL,
                confidence_volatility REAL,
                news_volume_impact REAL,
                technical_sentiment_divergence REAL,
                
                -- Time features
                asx_market_hours INTEGER,
                asx_opening_hour INTEGER,
                asx_closing_hour INTEGER,
                monday_effect INTEGER,
                friday_effect INTEGER,
                month_end INTEGER,
                quarter_end INTEGER,
                
                feature_version TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Enhanced outcomes table with multi-output targets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enhanced_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id INTEGER,
                symbol TEXT NOT NULL,
                prediction_timestamp DATETIME NOT NULL,
                
                -- Multi-output targets
                price_direction_1h INTEGER,    -- 1 if price up, 0 if down
                price_direction_4h INTEGER,
                price_direction_1d INTEGER,
                price_magnitude_1h REAL,      -- Percentage change
                price_magnitude_4h REAL,
                price_magnitude_1d REAL,
                volatility_next_1h REAL,      -- Volatility prediction
                
                -- Action classification
                optimal_action TEXT,           -- STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
                confidence_score REAL,         -- Model confidence
                
                -- Trading outcomes
                entry_price REAL,
                exit_price_1h REAL,
                exit_price_4h REAL,
                exit_price_1d REAL,
                exit_timestamp DATETIME,
                return_pct REAL,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (feature_id) REFERENCES enhanced_features (id)
            )
        ''')
        
        # Model performance tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance_enhanced (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version TEXT,
                model_type TEXT,
                training_date DATETIME,
                
                -- Multi-output performance metrics
                direction_accuracy_1h REAL,
                direction_accuracy_4h REAL,
                direction_accuracy_1d REAL,
                magnitude_mae_1h REAL,
                magnitude_mae_4h REAL,
                magnitude_mae_1d REAL,
                
                -- Overall metrics
                precision_score REAL,
                recall_score REAL,
                f1_score REAL,
                
                -- Model metadata
                feature_count INTEGER,
                training_samples INTEGER,
                parameters TEXT,
                feature_importance TEXT,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def collect_enhanced_training_data(self, sentiment_data: Dict, symbol: str) -> int:
        """
        Collect comprehensive training data including all required features
        
        Args:
            sentiment_data: Sentiment analysis results
            symbol: Stock symbol (e.g., 'CBA.AX')
            
        Returns:
            feature_id for linking with outcomes
        """
        try:
            # Get market data for technical analysis
            market_data = get_market_data(symbol, period='3mo', interval='1h')
            
            if market_data.empty:
                logger.warning(f"No market data available for {symbol}")
                return None
            
            # Perform technical analysis
            technical_result = self.technical_analyzer.analyze(symbol, market_data)
            
            # Extract all features
            features = self._extract_comprehensive_features(
                sentiment_data, technical_result, market_data, symbol
            )
            
            # Validate features before storing
            if not self._validate_features(features):
                logger.error(f"Feature validation failed for {symbol}")
                return None
            
            # Store in database
            feature_id = self._store_features_to_db(features, symbol)
            
            logger.info(f"Collected enhanced training data for {symbol} (ID: {feature_id})")
            return feature_id
            
        except Exception as e:
            logger.error(f"Error collecting enhanced training data for {symbol}: {e}")
            return None
    
    def _extract_comprehensive_features(self, sentiment_data: Dict, technical_result: Dict, 
                                      market_data: pd.DataFrame, symbol: str) -> Dict:
        """Extract all required features as per instructions"""
        features = {}
        current_price = technical_result.get('current_price', 0)
        
        # Sentiment features
        features['sentiment_score'] = sentiment_data.get('overall_sentiment', 0)
        features['confidence'] = sentiment_data.get('confidence', 0)
        features['news_count'] = sentiment_data.get('news_count', 0)
        features['reddit_sentiment'] = sentiment_data.get('reddit_sentiment', {}).get('average_sentiment', 0)
        features['event_score'] = sentiment_data.get('sentiment_components', {}).get('events', 0)
        
        # Technical indicators
        indicators = technical_result.get('indicators', {})
        features['rsi'] = indicators.get('rsi', 50)
        
        macd = indicators.get('macd', {})
        features['macd_line'] = macd.get('line', 0)
        features['macd_signal'] = macd.get('signal', 0)
        features['macd_histogram'] = macd.get('histogram', 0)
        
        sma = indicators.get('sma', {})
        features['sma_20'] = sma.get('sma_20', current_price)
        features['sma_50'] = sma.get('sma_50', current_price)
        features['sma_200'] = sma.get('sma_200', current_price)
        
        ema = indicators.get('ema', {})
        features['ema_12'] = ema.get('ema_12', current_price)
        features['ema_26'] = ema.get('ema_26', current_price)
        
        # Bollinger Bands (calculate if not available)
        features.update(self._calculate_bollinger_bands(market_data))
        
        # Price features
        features['current_price'] = current_price
        features.update(self._calculate_price_features(market_data))
        
        # Volume features
        volume_info = indicators.get('volume', {})
        features['volume'] = volume_info.get('current', 0)
        features['volume_ratio'] = volume_info.get('ratio', 1)
        features.update(self._calculate_volume_features(market_data))
        
        # Market context features
        features.update(self._get_market_context_features(symbol))
        
        # Interaction features
        features.update(self._calculate_interaction_features(features))
        
        # Time-based features
        features.update(self._calculate_time_features())
        
        return features
    
    def _calculate_bollinger_bands(self, market_data: pd.DataFrame) -> Dict:
        """Calculate Bollinger Bands"""
        if len(market_data) < 20:
            return {'bollinger_upper': 0, 'bollinger_lower': 0, 'bollinger_width': 0}
        
        sma_20 = market_data['Close'].rolling(window=20).mean()
        std_20 = market_data['Close'].rolling(window=20).std()
        
        bollinger_upper = sma_20 + (2 * std_20)
        bollinger_lower = sma_20 - (2 * std_20)
        bollinger_width = ((bollinger_upper - bollinger_lower) / sma_20) * 100
        
        return {
            'bollinger_upper': float(bollinger_upper.iloc[-1]) if not pd.isna(bollinger_upper.iloc[-1]) else 0,
            'bollinger_lower': float(bollinger_lower.iloc[-1]) if not pd.isna(bollinger_lower.iloc[-1]) else 0,
            'bollinger_width': float(bollinger_width.iloc[-1]) if not pd.isna(bollinger_width.iloc[-1]) else 0
        }
    
    def _calculate_price_features(self, market_data: pd.DataFrame) -> Dict:
        """Calculate comprehensive price features"""
        if len(market_data) < 21:
            return {key: 0 for key in self.required_features['price_features'][1:]}  # Skip current_price
        
        close_prices = market_data['Close']
        high_prices = market_data['High']
        low_prices = market_data['Low']
        
        # Price changes
        price_change_1h = ((close_prices.iloc[-1] - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100 if len(close_prices) >= 2 else 0
        price_change_4h = ((close_prices.iloc[-1] - close_prices.iloc[-5]) / close_prices.iloc[-5]) * 100 if len(close_prices) >= 5 else 0
        price_change_1d = ((close_prices.iloc[-1] - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100 if len(close_prices) >= 2 else 0
        price_change_5d = ((close_prices.iloc[-1] - close_prices.iloc[-6]) / close_prices.iloc[-6]) * 100 if len(close_prices) >= 6 else 0
        price_change_20d = ((close_prices.iloc[-1] - close_prices.iloc[-21]) / close_prices.iloc[-21]) * 100 if len(close_prices) >= 21 else 0
        
        # Price vs moving averages
        sma_20 = close_prices.rolling(window=20).mean()
        sma_50 = close_prices.rolling(window=50).mean() if len(close_prices) >= 50 else sma_20
        sma_200 = close_prices.rolling(window=200).mean() if len(close_prices) >= 200 else sma_20
        
        current_price = close_prices.iloc[-1]
        price_vs_sma20 = ((current_price - sma_20.iloc[-1]) / sma_20.iloc[-1]) * 100 if not pd.isna(sma_20.iloc[-1]) else 0
        price_vs_sma50 = ((current_price - sma_50.iloc[-1]) / sma_50.iloc[-1]) * 100 if not pd.isna(sma_50.iloc[-1]) else 0
        price_vs_sma200 = ((current_price - sma_200.iloc[-1]) / sma_200.iloc[-1]) * 100 if not pd.isna(sma_200.iloc[-1]) else 0
        
        # Daily range and ATR
        daily_range = ((high_prices.iloc[-1] - low_prices.iloc[-1]) / close_prices.iloc[-1]) * 100
        
        # ATR (Average True Range)
        high_low = high_prices - low_prices
        high_close = np.abs(high_prices - close_prices.shift(1))
        low_close = np.abs(low_prices - close_prices.shift(1))
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr_14 = true_range.rolling(window=14).mean().iloc[-1] if len(true_range) >= 14 else daily_range
        
        # Volatility
        returns = close_prices.pct_change()
        volatility_20d = returns.rolling(window=20).std().iloc[-1] * np.sqrt(252) * 100 if len(returns) >= 20 else 0
        
        return {
            'price_change_1h': price_change_1h,
            'price_change_4h': price_change_4h,
            'price_change_1d': price_change_1d,
            'price_change_5d': price_change_5d,
            'price_change_20d': price_change_20d,
            'price_vs_sma20': price_vs_sma20,
            'price_vs_sma50': price_vs_sma50,
            'price_vs_sma200': price_vs_sma200,
            'daily_range': daily_range,
            'atr_14': float(atr_14) if not pd.isna(atr_14) else 0,
            'volatility_20d': float(volatility_20d) if not pd.isna(volatility_20d) else 0
        }
    
    def _calculate_volume_features(self, market_data: pd.DataFrame) -> Dict:
        """Calculate volume-based features"""
        if 'Volume' not in market_data.columns or len(market_data) < 20:
            return {key: 0 for key in self.required_features['volume_features'][2:]}  # Skip volume, volume_ratio
        
        volume = market_data['Volume']
        close_prices = market_data['Close']
        
        # Volume SMA
        volume_sma20 = volume.rolling(window=20).mean().iloc[-1]
        
        # On Balance Volume
        obv = (volume * np.sign(close_prices.diff())).cumsum().iloc[-1]
        
        # Volume Price Trend
        price_change = close_prices.pct_change()
        vpt = (volume * price_change).cumsum().iloc[-1]
        
        return {
            'volume_sma20': float(volume_sma20) if not pd.isna(volume_sma20) else 0,
            'on_balance_volume': float(obv) if not pd.isna(obv) else 0,
            'volume_price_trend': float(vpt) if not pd.isna(vpt) else 0
        }
    
    def _get_market_context_features(self, symbol: str) -> Dict:
        """Get market context features"""
        # Placeholder for now - would need external data sources
        return {
            'asx200_change': 0,      # ASX 200 daily change
            'sector_performance': 0,  # Banking sector performance
            'aud_usd_rate': 0.67,    # AUD/USD exchange rate
            'vix_level': 20,         # VIX equivalent for ASX
            'market_breadth': 0,     # Advance/decline ratio
            'market_momentum': 0     # Market momentum indicator
        }
    
    def _calculate_interaction_features(self, features: Dict) -> Dict:
        """Calculate interaction features"""
        momentum_score = features.get('price_change_1d', 0) + features.get('rsi', 50) - 50
        technical_signal = 1 if features.get('rsi', 50) > 50 else -1
        
        return {
            'sentiment_momentum': features.get('sentiment_score', 0) * momentum_score,
            'sentiment_rsi': features.get('sentiment_score', 0) * (features.get('rsi', 50) - 50) / 50,
            'volume_sentiment': features.get('volume_ratio', 1) * features.get('sentiment_score', 0),
            'confidence_volatility': features.get('confidence', 0) / (features.get('volatility_20d', 0) + 0.01),
            'news_volume_impact': features.get('news_count', 0) * features.get('volume_ratio', 1),
            'technical_sentiment_divergence': abs(technical_signal - features.get('sentiment_score', 0))
        }
    
    def _calculate_time_features(self) -> Dict:
        """Calculate time-based features for Australian market"""
        now = datetime.now()
        
        return {
            'asx_market_hours': 1 if 10 <= now.hour < 16 else 0,
            'asx_opening_hour': 1 if 10 <= now.hour < 11 else 0,
            'asx_closing_hour': 1 if 15 <= now.hour < 16 else 0,
            'monday_effect': 1 if now.weekday() == 0 else 0,
            'friday_effect': 1 if now.weekday() == 4 else 0,
            'month_end': 1 if now.day >= 25 else 0,
            'quarter_end': 1 if now.month in [3, 6, 9, 12] and now.day >= 25 else 0
        }
    
    def _validate_features(self, features: Dict) -> bool:
        """Validate feature quality and ranges"""
        try:
            # Check for NaN or infinite values
            for key, value in features.items():
                if pd.isna(value) or np.isinf(value):
                    logger.warning(f"Invalid value for {key}: {value}")
                    return False
            
            # Validate specific ranges
            validations = {
                'rsi': (0, 100),
                'sentiment_score': (-1, 1),
                'confidence': (0, 1),
                'price_change_1d': (-20, 20),  # ±20% daily limit
                'volume_ratio': (0, 10)  # Max 10x normal volume
            }
            
            for column, (min_val, max_val) in validations.items():
                if column in features:
                    value = features[column]
                    if not (min_val <= value <= max_val):
                        logger.warning(f"{column} out of range: {value} (expected {min_val}-{max_val})")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Feature validation error: {e}")
            return False
    
    def _store_features_to_db(self, features: Dict, symbol: str) -> int:
        """Store features to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create column list and values list
        columns = list(features.keys()) + ['symbol', 'timestamp', 'feature_version']
        values = list(features.values()) + [symbol, datetime.now().isoformat(), '2.0']
        
        # Create placeholders
        placeholders = ', '.join(['?' for _ in values])
        column_names = ', '.join(columns)
        
        cursor.execute(f'''
            INSERT INTO enhanced_features ({column_names})
            VALUES ({placeholders})
        ''', values)
        
        feature_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return feature_id
    
    def record_enhanced_outcomes(self, feature_id: int, symbol: str, outcome_data: Dict):
        """Record multi-output outcomes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO enhanced_outcomes
            (feature_id, symbol, prediction_timestamp, price_direction_1h, price_direction_4h,
             price_direction_1d, price_magnitude_1h, price_magnitude_4h, price_magnitude_1d,
             volatility_next_1h, optimal_action, confidence_score, entry_price,
             exit_price_1h, exit_price_4h, exit_price_1d, exit_timestamp, return_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            feature_id,
            symbol,
            outcome_data['prediction_timestamp'],
            outcome_data.get('price_direction_1h', 0),
            outcome_data.get('price_direction_4h', 0),
            outcome_data.get('price_direction_1d', 0),
            outcome_data.get('price_magnitude_1h', 0),
            outcome_data.get('price_magnitude_4h', 0),
            outcome_data.get('price_magnitude_1d', 0),
            outcome_data.get('volatility_next_1h', 0),
            outcome_data.get('optimal_action', 'HOLD'),
            outcome_data.get('confidence_score', 0.5),
            outcome_data.get('entry_price', 0),
            outcome_data.get('exit_price_1h', 0),
            outcome_data.get('exit_price_4h', 0),
            outcome_data.get('exit_price_1d', 0),
            outcome_data.get('exit_timestamp', datetime.now().isoformat()),
            outcome_data.get('return_pct', 0)
        ))
        
        conn.commit()
        conn.close()
    
    def prepare_enhanced_training_dataset(self, min_samples: int = 50) -> Tuple[pd.DataFrame, Dict]:
        """
        Prepare enhanced dataset with all required features and multi-output targets
        
        Returns:
            X: Feature matrix with all required features
            y: Multi-output targets dictionary
        """
        conn = sqlite3.connect(self.db_path)
        
        # Join enhanced features with outcomes
        query = '''
            SELECT ef.*, eo.price_direction_1h, eo.price_direction_4h, eo.price_direction_1d,
                   eo.price_magnitude_1h, eo.price_magnitude_4h, eo.price_magnitude_1d,
                   eo.optimal_action, eo.confidence_score
            FROM enhanced_features ef
            INNER JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
            WHERE eo.price_direction_4h IS NOT NULL
            ORDER BY ef.timestamp
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) < min_samples:
            logger.warning(f"Insufficient enhanced training data: {len(df)} samples (minimum: {min_samples})")
            return None, None
        
        # Prepare feature matrix - all required features
        all_features = []
        for feature_group in self.required_features.values():
            all_features.extend(feature_group)
        all_features.extend(self.interaction_features.keys())
        all_features.extend(self.time_features.keys())
        
        # Filter to only available columns
        available_features = [f for f in all_features if f in df.columns]
        X = df[available_features].copy()
        
        # Handle missing values
        X = X.fillna(0)
        
        # Prepare multi-output targets
        y = {
            'direction_1h': df['price_direction_1h'].values,
            'direction_4h': df['price_direction_4h'].values,
            'direction_1d': df['price_direction_1d'].values,
            'magnitude_1h': df['price_magnitude_1h'].values,
            'magnitude_4h': df['price_magnitude_4h'].values,
            'magnitude_1d': df['price_magnitude_1d'].values
        }
        
        logger.info(f"Prepared enhanced training dataset: {len(X)} samples, {len(available_features)} features")
        
        return X, y
    
    def train_enhanced_models(self, X: pd.DataFrame, y: Dict) -> Dict:
        """
        Train multi-output models for price direction and magnitude prediction
        """
        from sklearn.metrics import accuracy_score
        
        # Time series split for financial data
        tscv = TimeSeriesSplit(n_splits=3)
        
        results = {}
        
        # Direction prediction models (classification)
        direction_targets = np.column_stack([y['direction_1h'], y['direction_4h'], y['direction_1d']])
        direction_model = MultiOutputClassifier(RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=10,
            class_weight='balanced',
            random_state=42
        ))
        
        # Magnitude prediction models (regression)
        magnitude_targets = np.column_stack([y['magnitude_1h'], y['magnitude_4h'], y['magnitude_1d']])
        magnitude_model = MultiOutputRegressor(RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_split=10,
            random_state=42
        ))
        
        # Cross-validation for direction models
        direction_scores = []
        magnitude_scores = []
        
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            dir_train, dir_val = direction_targets[train_idx], direction_targets[val_idx]
            mag_train, mag_val = magnitude_targets[train_idx], magnitude_targets[val_idx]
            
            # Train direction model
            direction_model.fit(X_train, dir_train)
            dir_pred = direction_model.predict(X_val)
            
            # Calculate accuracy for each timeframe
            dir_accuracy = [accuracy_score(dir_val[:, i], dir_pred[:, i]) for i in range(3)]
            direction_scores.append(dir_accuracy)
            
            # Train magnitude model
            magnitude_model.fit(X_train, mag_train)
            mag_pred = magnitude_model.predict(X_val)
            
            # Calculate MAE for each timeframe
            mag_mae = [mean_absolute_error(mag_val[:, i], mag_pred[:, i]) for i in range(3)]
            magnitude_scores.append(mag_mae)
        
        # Final training on full dataset
        direction_model.fit(X, direction_targets)
        magnitude_model.fit(X, magnitude_targets)
        
        # Save models
        self._save_enhanced_models(direction_model, magnitude_model, X.columns.tolist())
        
        # Calculate average scores
        avg_direction_scores = np.mean(direction_scores, axis=0)
        avg_magnitude_scores = np.mean(magnitude_scores, axis=0)
        
        results = {
            'direction_model': direction_model,
            'magnitude_model': magnitude_model,
            'direction_accuracy': {
                '1h': avg_direction_scores[0],
                '4h': avg_direction_scores[1],
                '1d': avg_direction_scores[2]
            },
            'magnitude_mae': {
                '1h': avg_magnitude_scores[0],
                '4h': avg_magnitude_scores[1],
                '1d': avg_magnitude_scores[2]
            },
            'feature_columns': X.columns.tolist()
        }
        
        logger.info(f"Enhanced models trained successfully")
        logger.info(f"Direction accuracy: 1h={avg_direction_scores[0]:.3f}, 4h={avg_direction_scores[1]:.3f}, 1d={avg_direction_scores[2]:.3f}")
        logger.info(f"Magnitude MAE: 1h={avg_magnitude_scores[0]:.3f}, 4h={avg_magnitude_scores[1]:.3f}, 1d={avg_magnitude_scores[2]:.3f}")
        
        return results
    
    def _save_enhanced_models(self, direction_model, magnitude_model, feature_columns: List[str]):
        """Save enhanced models with metadata"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version = f"enhanced_v_{timestamp}"
        
        # Save models
        direction_path = os.path.join(self.models_dir, f"direction_model_{version}.pkl")
        magnitude_path = os.path.join(self.models_dir, f"magnitude_model_{version}.pkl")
        
        joblib.dump(direction_model, direction_path)
        joblib.dump(magnitude_model, magnitude_path)
        
        # Save metadata
        metadata = {
            'version': version,
            'training_date': timestamp,
            'feature_columns': feature_columns,
            'model_type': 'enhanced_multi_output',
            'direction_model_path': direction_path,
            'magnitude_model_path': magnitude_path
        }
        
        metadata_path = os.path.join(self.models_dir, f"enhanced_metadata_{version}.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update current model links
        current_dir_path = os.path.join(self.models_dir, 'current_direction_model.pkl')
        current_mag_path = os.path.join(self.models_dir, 'current_magnitude_model.pkl')
        current_meta_path = os.path.join(self.models_dir, 'current_enhanced_metadata.json')
        
        # Remove existing links
        for path in [current_dir_path, current_mag_path, current_meta_path]:
            if os.path.exists(path) or os.path.islink(path):
                os.unlink(path)
        
        # Create new links
        try:
            os.symlink(os.path.basename(direction_path), current_dir_path)
            os.symlink(os.path.basename(magnitude_path), current_mag_path)
            os.symlink(os.path.basename(metadata_path), current_meta_path)
        except OSError:
            # Fallback: copy files
            import shutil
            shutil.copy2(direction_path, current_dir_path)
            shutil.copy2(magnitude_path, current_mag_path)
            shutil.copy2(metadata_path, current_meta_path)
        
        logger.info(f"Enhanced models saved: {version}")
    
    def predict_enhanced(self, sentiment_data: Dict, symbol: str) -> Dict:
        """
        Make enhanced predictions using trained models
        
        Returns:
            Dictionary with direction, magnitude, and confidence predictions
        """
        try:
            # Extract features for prediction
            market_data = get_market_data(symbol, period='3mo', interval='1h')
            if market_data.empty:
                return {'error': 'No market data available'}
            
            technical_result = self.technical_analyzer.analyze(symbol, market_data)
            features = self._extract_comprehensive_features(
                sentiment_data, technical_result, market_data, symbol
            )
            
            if not self._validate_features(features):
                return {'error': 'Invalid features'}
            
            # Load models
            direction_model_path = os.path.join(self.models_dir, 'current_direction_model.pkl')
            magnitude_model_path = os.path.join(self.models_dir, 'current_magnitude_model.pkl')
            
            if not (os.path.exists(direction_model_path) and os.path.exists(magnitude_model_path)):
                # Fallback to basic prediction based on sentiment and technical indicators
                return self._fallback_prediction(features, sentiment_data, symbol)
            
            direction_model = joblib.load(direction_model_path)
            magnitude_model = joblib.load(magnitude_model_path)
            
            # Prepare feature vector
            metadata_path = os.path.join(self.models_dir, 'current_enhanced_metadata.json')
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            feature_columns = metadata['feature_columns']
            feature_vector = [features.get(col, 0) for col in feature_columns]
            X = np.array(feature_vector).reshape(1, -1)
            
            # Make predictions
            direction_pred = direction_model.predict(X)[0]
            direction_proba = direction_model.predict_proba(X)
            magnitude_pred = magnitude_model.predict(X)[0]
            
            # Calculate confidence scores
            direction_confidence = [np.max(proba) for proba in direction_proba]
            avg_confidence = np.mean(direction_confidence)
            
            # Determine optimal action
            action = self._determine_optimal_action(direction_pred, magnitude_pred, avg_confidence)
            
            return {
                'direction_predictions': {
                    '1h': int(direction_pred[0]),
                    '4h': int(direction_pred[1]),
                    '1d': int(direction_pred[2])
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
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Enhanced prediction error for {symbol}: {e}")
            return {'error': str(e)}
    
    def _determine_optimal_action(self, direction_pred: np.ndarray, magnitude_pred: np.ndarray, confidence: float) -> str:
        """Determine optimal trading action"""
        # Average direction (1 = up, 0 = down)
        avg_direction = np.mean(direction_pred)
        avg_magnitude = np.mean(np.abs(magnitude_pred))
        
        if avg_direction > 0.6 and avg_magnitude > 2.0 and confidence > 0.8:
            return 'STRONG_BUY'
        elif avg_direction > 0.6 and confidence > 0.6:
            return 'BUY'
        elif avg_direction < 0.4 and avg_magnitude > 2.0 and confidence > 0.8:
            return 'STRONG_SELL'
        elif avg_direction < 0.4 and confidence > 0.6:
            return 'SELL'
        else:
            return 'HOLD'

    def _fallback_prediction(self, features: Dict, sentiment_data: Dict, symbol: str) -> Dict:
        """Fallback prediction when models aren't available"""
        try:
            # Use sentiment and technical indicators for basic prediction
            sentiment_score = sentiment_data.get('overall_sentiment', 0)
            confidence = sentiment_data.get('confidence', 0.5)
            rsi = features.get('rsi', 50)
            momentum_score = features.get('momentum_score', 0)
            
            # Simple rule-based prediction
            # Direction: positive sentiment + technical momentum
            direction_signal = sentiment_score + (momentum_score / 100)
            direction_up = 1 if direction_signal > 0 else 0
            
            # Magnitude: based on sentiment strength and RSI divergence
            rsi_divergence = abs(rsi - 50) / 50  # 0 to 1
            magnitude_base = abs(sentiment_score) * confidence * rsi_divergence
            
            # Scale magnitude to reasonable range (0.5% to 3%)
            magnitude = magnitude_base * 2.5 + 0.5
            if direction_signal < 0:
                magnitude = -magnitude
                
            # Determine action based on signals
            if abs(magnitude) > 2.0 and confidence > 0.7:
                action = 'STRONG_BUY' if magnitude > 0 else 'STRONG_SELL'
            elif abs(magnitude) > 1.0 and confidence > 0.5:
                action = 'BUY' if magnitude > 0 else 'SELL'
            else:
                action = 'HOLD'
            
            return {
                'direction_predictions': {
                    '1h': direction_up,
                    '4h': direction_up,
                    '1d': direction_up
                },
                'magnitude_predictions': {
                    '1h': round(magnitude * 0.3, 2),  # Shorter timeframe, smaller magnitude
                    '4h': round(magnitude * 0.7, 2),
                    '1d': round(magnitude, 2)
                },
                'optimal_action': action,
                'confidence_scores': {
                    'direction': {'1h': confidence, '4h': confidence, '1d': confidence},
                    'magnitude': {'1h': confidence * 0.8, '4h': confidence * 0.9, '1d': confidence},
                    'average': confidence
                },
                'timestamp': datetime.now().isoformat(),
                'prediction_method': 'fallback_rule_based',
                'features_used': {
                    'sentiment_score': sentiment_score,
                    'confidence': confidence,
                    'rsi': rsi,
                    'momentum_score': momentum_score
                }
            }
            
        except Exception as e:
            return {
                'error': f'Fallback prediction failed: {str(e)}',
                'optimal_action': 'HOLD',
                'confidence_scores': {'average': 0.1},
                'direction_predictions': {'1h': 0, '4h': 0, '1d': 0},
                'magnitude_predictions': {'1h': 0.0, '4h': 0.0, '1d': 0.0}
            }
    
# Data Validation Framework
class DataValidator:
    """Comprehensive data validation framework"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_sentiment_data(self, data: Dict) -> bool:
        """Validate sentiment analysis output"""
        required_fields = [
            'overall_sentiment', 'confidence', 'news_count',
            'sentiment_components', 'timestamp'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate ranges
        assert -1 <= data['overall_sentiment'] <= 1, "Sentiment out of range"
        assert 0 <= data['confidence'] <= 1, "Confidence out of range"
        assert data['news_count'] >= 0, "Invalid news count"
        
        return True
    
    def validate_technical_data(self, data: Dict) -> bool:
        """Validate technical analysis output"""
        indicators = data.get('indicators', {})
        
        # RSI should be 0-100
        rsi = indicators.get('rsi', 50)
        assert 0 <= rsi <= 100, f"RSI out of range: {rsi}"
        
        # Price should be positive
        price = data.get('current_price', 0)
        assert price > 0, f"Invalid price: {price}"
        
        # Momentum score should be bounded
        momentum = data.get('momentum', {}).get('score', 0)
        assert -100 <= momentum <= 100, f"Momentum out of range: {momentum}"
        
        return True
    
    def validate_training_data(self, df: pd.DataFrame) -> bool:
        """Validate complete training dataset"""
        # No future data leakage
        for idx, row in df.iterrows():
            if 'timestamp' in row and 'prediction_timestamp' in row:
                feature_time = pd.to_datetime(row['timestamp'])
                outcome_time = pd.to_datetime(row['prediction_timestamp'])
                assert feature_time < outcome_time, f"Future data leak at row {idx}"
        
        # No duplicate entries
        if 'symbol' in df.columns and 'timestamp' in df.columns:
            duplicates = df.duplicated(subset=['symbol', 'timestamp'])
            assert not duplicates.any(), f"Duplicate entries found: {duplicates.sum()}"
        
        return True

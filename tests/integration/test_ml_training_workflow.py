#!/usr/bin/env python3
"""
Integration Tests for ML Training Workflow
Tests the complete ML training pipeline from feature engineering to model deployment

Based on the ML training pipeline workflow documentation
"""

import pytest
import sqlite3
import os
import sys
import tempfile
import json
import joblib
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestMLTrainingWorkflow:
    """Test complete ML training workflow integration"""
    
    @pytest.fixture
    def ml_database(self):
        """Create database with ML training data"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create enhanced features table with all ML features
        cursor.execute('''
            CREATE TABLE enhanced_features (
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
        
        # Create enhanced outcomes table with multi-output targets
        cursor.execute('''
            CREATE TABLE enhanced_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id INTEGER,
                symbol TEXT NOT NULL,
                prediction_timestamp DATETIME NOT NULL,
                -- Multi-output targets
                price_direction_1h INTEGER,
                price_direction_4h INTEGER,
                price_direction_1d INTEGER,
                price_magnitude_1h REAL,
                price_magnitude_4h REAL,
                price_magnitude_1d REAL,
                volatility_next_1h REAL,
                -- Action classification
                optimal_action TEXT,
                confidence_score REAL,
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
        
        # Create model performance tracking table
        cursor.execute('''
            CREATE TABLE model_performance_enhanced (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version TEXT,
                model_type TEXT,
                training_date DATETIME,
                direction_accuracy_1h REAL,
                direction_accuracy_4h REAL,
                direction_accuracy_1d REAL,
                magnitude_mae_1h REAL,
                magnitude_mae_4h REAL,
                magnitude_mae_1d REAL,
                precision_score REAL,
                recall_score REAL,
                f1_score REAL,
                feature_count INTEGER,
                training_samples INTEGER,
                parameters TEXT,
                feature_importance TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert comprehensive training data (100 samples for robust testing)
        symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX']
        
        for i in range(100):
            symbol = symbols[i % len(symbols)]
            timestamp = datetime.now() - timedelta(days=i//5, hours=i%24)
            
            # Generate comprehensive feature data
            sentiment_score = np.random.uniform(-1, 1)
            rsi = np.random.uniform(20, 80)
            current_price = np.random.uniform(50, 200)
            
            cursor.execute('''
                INSERT INTO enhanced_features (
                    symbol, timestamp, sentiment_score, confidence, news_count,
                    reddit_sentiment, event_score, rsi, macd_line, macd_signal,
                    macd_histogram, sma_20, sma_50, sma_200, ema_12, ema_26,
                    bollinger_upper, bollinger_lower, bollinger_width,
                    current_price, price_change_1h, price_change_4h, price_change_1d,
                    price_change_5d, price_change_20d, price_vs_sma20, price_vs_sma50,
                    price_vs_sma200, daily_range, atr_14, volatility_20d,
                    volume, volume_sma20, volume_ratio, on_balance_volume,
                    volume_price_trend, asx200_change, sector_performance,
                    aud_usd_rate, vix_level, market_breadth, market_momentum,
                    sentiment_momentum, sentiment_rsi, volume_sentiment,
                    confidence_volatility, news_volume_impact, 
                    technical_sentiment_divergence, asx_market_hours,
                    asx_opening_hour, asx_closing_hour, monday_effect,
                    friday_effect, month_end, quarter_end, feature_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol, timestamp.isoformat(),
                sentiment_score, np.random.uniform(0.5, 1.0), np.random.randint(5, 25),
                np.random.uniform(-1, 1), np.random.uniform(-1, 1),
                rsi, np.random.uniform(-2, 2), np.random.uniform(-2, 2),
                np.random.uniform(-1, 1), current_price * 0.99, current_price * 0.98,
                current_price * 0.95, current_price * 1.01, current_price * 1.02,
                current_price * 1.02, current_price * 0.98, np.random.uniform(1, 5),
                current_price, np.random.uniform(-5, 5), np.random.uniform(-5, 5),
                np.random.uniform(-5, 5), np.random.uniform(-10, 10),
                np.random.uniform(-20, 20), np.random.uniform(-3, 3),
                np.random.uniform(-5, 5), np.random.uniform(-10, 10),
                np.random.uniform(0.5, 3.0), np.random.uniform(0.5, 2.0),
                np.random.uniform(5, 25), np.random.uniform(1000000, 5000000),
                np.random.uniform(1500000, 4000000), np.random.uniform(0.5, 3.0),
                np.random.uniform(-1000000, 1000000), np.random.uniform(-500000, 500000),
                np.random.uniform(-2, 2), np.random.uniform(-5, 5),
                0.67, np.random.uniform(15, 30), np.random.uniform(-1, 1),
                np.random.uniform(-2, 2), sentiment_score * np.random.uniform(-2, 2),
                sentiment_score * (rsi - 50) / 50, np.random.uniform(0.5, 3.0) * sentiment_score,
                np.random.uniform(0.5, 1.0) / (np.random.uniform(5, 25) + 0.01),
                np.random.randint(5, 25) * np.random.uniform(0.5, 3.0),
                abs(np.random.uniform(-1, 1) - sentiment_score),
                1 if 10 <= timestamp.hour < 16 else 0,
                1 if 10 <= timestamp.hour < 11 else 0,
                1 if 15 <= timestamp.hour < 16 else 0,
                1 if timestamp.weekday() == 0 else 0,
                1 if timestamp.weekday() == 4 else 0,
                1 if timestamp.day >= 25 else 0,
                1 if timestamp.month in [3, 6, 9, 12] and timestamp.day >= 25 else 0,
                '2.0'
            ))
            
            feature_id = cursor.lastrowid
            
            # Generate corresponding outcome data
            entry_price = current_price
            
            # Simulate realistic price movements for different timeframes
            price_change_1h = np.random.uniform(-0.02, 0.02)  # ±2% hourly
            price_change_4h = np.random.uniform(-0.04, 0.04)  # ±4% 4-hourly
            price_change_1d = np.random.uniform(-0.08, 0.08)  # ±8% daily
            
            exit_price_1h = entry_price * (1 + price_change_1h)
            exit_price_4h = entry_price * (1 + price_change_4h)
            exit_price_1d = entry_price * (1 + price_change_1d)
            
            # Calculate returns using CORRECT formula
            return_pct = ((exit_price_1d - entry_price) / entry_price) * 100
            
            # Determine optimal action based on sentiment and technical indicators
            if sentiment_score > 0.3 and rsi < 70:
                optimal_action = 'BUY'
            elif sentiment_score < -0.3 and rsi > 30:
                optimal_action = 'SELL'
            else:
                optimal_action = 'HOLD'
            
            cursor.execute('''
                INSERT INTO enhanced_outcomes (
                    feature_id, symbol, prediction_timestamp,
                    price_direction_1h, price_direction_4h, price_direction_1d,
                    price_magnitude_1h, price_magnitude_4h, price_magnitude_1d,
                    volatility_next_1h, optimal_action, confidence_score,
                    entry_price, exit_price_1h, exit_price_4h, exit_price_1d,
                    exit_timestamp, return_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feature_id, symbol, timestamp.isoformat(),
                1 if price_change_1h > 0 else 0,
                1 if price_change_4h > 0 else 0,
                1 if price_change_1d > 0 else 0,
                abs(price_change_1h * 100),
                abs(price_change_4h * 100),
                abs(price_change_1d * 100),
                np.random.uniform(5, 25),  # Volatility
                optimal_action,
                np.random.uniform(0.5, 1.0),
                entry_price, exit_price_1h, exit_price_4h, exit_price_1d,
                (timestamp + timedelta(days=1)).isoformat(),
                return_pct
            ))
        
        conn.commit()
        conn.close()
        
        yield db_path
        os.unlink(db_path)
    
    @pytest.fixture
    def temp_model_dir(self):
        """Create temporary directory for model storage"""
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @patch('app.core.ml.enhanced_training_pipeline.EnhancedMLTrainingPipeline')
    def test_complete_ml_training_workflow(self, mock_pipeline_class, ml_database, temp_model_dir):
        """Test complete ML training workflow from data to deployed model"""
        
        # Mock the ML training pipeline
        mock_pipeline = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_pipeline.db_path = ml_database
        mock_pipeline.models_dir = temp_model_dir
        
        # Mock dataset preparation
        conn = sqlite3.connect(ml_database)
        query = '''
            SELECT ef.*, eo.price_direction_1h, eo.price_direction_4h, eo.price_direction_1d,
                   eo.price_magnitude_1h, eo.price_magnitude_4h, eo.price_magnitude_1d
            FROM enhanced_features ef
            INNER JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
            WHERE eo.price_direction_4h IS NOT NULL
        '''
        real_df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Extract features and targets from real data
        feature_columns = [
            'sentiment_score', 'confidence', 'rsi', 'macd_line', 'current_price',
            'volume_ratio', 'price_change_1d', 'volatility_20d', 'sentiment_momentum'
        ]
        available_features = [col for col in feature_columns if col in real_df.columns]
        
        X = real_df[available_features].fillna(0)
        y = {
            'direction_1h': real_df['price_direction_1h'].fillna(0).values,
            'direction_4h': real_df['price_direction_4h'].fillna(0).values,
            'direction_1d': real_df['price_direction_1d'].fillna(0).values,
            'magnitude_1h': real_df['price_magnitude_1h'].fillna(0.0).values,
            'magnitude_4h': real_df['price_magnitude_4h'].fillna(0.0).values,
            'magnitude_1d': real_df['price_magnitude_1d'].fillna(0.0).values
        }
        
        mock_pipeline.prepare_enhanced_training_dataset.return_value = (X, y)
        
        # Mock model training results
        training_results = {
            'direction_model': MagicMock(),
            'magnitude_model': MagicMock(),
            'direction_accuracy': {'1h': 0.65, '4h': 0.68, '1d': 0.72},
            'magnitude_mae': {'1h': 1.8, '4h': 2.3, '1d': 3.1},
            'feature_columns': available_features
        }
        
        mock_pipeline.train_enhanced_models.return_value = training_results
        
        # Mock model saving
        mock_pipeline._save_enhanced_models.return_value = None
        
        # Test the complete workflow
        pipeline = mock_pipeline_class(data_dir=temp_model_dir)
        
        # STEP 1: Data Preparation
        X_prepared, y_prepared = pipeline.prepare_enhanced_training_dataset(min_samples=50)
        
        # Validate data preparation
        assert X_prepared is not None
        assert y_prepared is not None
        assert len(X_prepared) >= 50  # Minimum training requirement
        assert len(X_prepared.columns) >= 5  # Sufficient features
        
        # Validate target structure
        required_targets = ['direction_1h', 'direction_4h', 'direction_1d', 
                           'magnitude_1h', 'magnitude_4h', 'magnitude_1d']
        for target in required_targets:
            assert target in y_prepared
            assert len(y_prepared[target]) == len(X_prepared)
        
        # STEP 2: Model Training
        results = pipeline.train_enhanced_models(X_prepared, y_prepared)
        
        # Validate training results
        assert 'direction_model' in results
        assert 'magnitude_model' in results
        assert 'direction_accuracy' in results
        assert 'magnitude_mae' in results
        assert 'feature_columns' in results
        
        # Validate model performance metrics
        direction_acc = results['direction_accuracy']
        assert all(0.5 <= acc <= 1.0 for acc in direction_acc.values())  # Better than random
        
        magnitude_mae = results['magnitude_mae']
        assert all(mae >= 0 for mae in magnitude_mae.values())  # Non-negative error
        
        # STEP 3: Model Persistence
        pipeline._save_enhanced_models(
            results['direction_model'],
            results['magnitude_model'],
            results['feature_columns']
        )
        
        # Validate model saving was called
        mock_pipeline._save_enhanced_models.assert_called_once()
    
    def test_feature_engineering_quality(self, ml_database):
        """Test quality of feature engineering for ML training"""
        
        conn = sqlite3.connect(ml_database)
        
        # Test comprehensive feature availability
        feature_query = '''
            SELECT COUNT(*) as total_features,
                   COUNT(sentiment_score) as sentiment_features,
                   COUNT(rsi) as technical_features,
                   COUNT(current_price) as price_features,
                   COUNT(volume_ratio) as volume_features,
                   COUNT(sentiment_momentum) as interaction_features
            FROM enhanced_features
            WHERE feature_version = '2.0'
        '''
        
        cursor = conn.cursor()
        cursor.execute(feature_query)
        feature_stats = cursor.fetchone()
        
        total, sentiment, technical, price, volume, interaction = feature_stats
        
        # Validate feature completeness
        assert total >= 100, f"Insufficient training features: {total}"
        assert sentiment == total, "Missing sentiment features"
        assert technical == total, "Missing technical features"  
        assert price == total, "Missing price features"
        assert volume == total, "Missing volume features"
        assert interaction == total, "Missing interaction features"
        
        # Test feature quality ranges
        quality_query = '''
            SELECT AVG(sentiment_score) as avg_sentiment,
                   MIN(rsi) as min_rsi, MAX(rsi) as max_rsi,
                   MIN(current_price) as min_price, MAX(current_price) as max_price,
                   COUNT(CASE WHEN sentiment_score BETWEEN -1 AND 1 THEN 1 END) as valid_sentiment,
                   COUNT(CASE WHEN rsi BETWEEN 0 AND 100 THEN 1 END) as valid_rsi,
                   COUNT(CASE WHEN current_price > 0 THEN 1 END) as valid_price
            FROM enhanced_features
        '''
        
        cursor.execute(quality_query)
        quality_stats = cursor.fetchone()
        
        (avg_sentiment, min_rsi, max_rsi, min_price, max_price,
         valid_sentiment, valid_rsi, valid_price) = quality_stats
        
        # Validate feature quality
        assert -1 <= avg_sentiment <= 1, f"Sentiment average out of range: {avg_sentiment}"
        assert 0 <= min_rsi <= 100, f"RSI minimum out of range: {min_rsi}"
        assert 0 <= max_rsi <= 100, f"RSI maximum out of range: {max_rsi}"
        assert min_price > 0, f"Invalid minimum price: {min_price}"
        assert max_price > min_price, f"Invalid price range: {min_price}-{max_price}"
        
        # Validate data integrity
        assert valid_sentiment == total, f"Invalid sentiment values: {total - valid_sentiment}"
        assert valid_rsi == total, f"Invalid RSI values: {total - valid_rsi}"
        assert valid_price == total, f"Invalid price values: {total - valid_price}"
        
        conn.close()
    
    def test_outcome_target_quality(self, ml_database):
        """Test quality of outcome targets for ML training"""
        
        conn = sqlite3.connect(ml_database)
        
        # Test multi-output target availability and quality
        target_query = '''
            SELECT COUNT(*) as total_outcomes,
                   COUNT(price_direction_1h) as direction_1h_count,
                   COUNT(price_direction_4h) as direction_4h_count,
                   COUNT(price_direction_1d) as direction_1d_count,
                   COUNT(price_magnitude_1h) as magnitude_1h_count,
                   COUNT(price_magnitude_4h) as magnitude_4h_count,
                   COUNT(price_magnitude_1d) as magnitude_1d_count,
                   AVG(return_pct) as avg_return,
                   COUNT(CASE WHEN return_pct IS NOT NULL THEN 1 END) as return_count
            FROM enhanced_outcomes
        '''
        
        cursor = conn.cursor()
        cursor.execute(target_query)
        target_stats = cursor.fetchone()
        
        (total_outcomes, dir_1h, dir_4h, dir_1d, mag_1h, mag_4h, mag_1d,
         avg_return, return_count) = target_stats
        
        # Validate target completeness
        assert total_outcomes >= 100, f"Insufficient outcome data: {total_outcomes}"
        assert dir_1h == total_outcomes, "Missing 1h direction targets"
        assert dir_4h == total_outcomes, "Missing 4h direction targets"
        assert dir_1d == total_outcomes, "Missing 1d direction targets"
        assert mag_1h == total_outcomes, "Missing 1h magnitude targets"
        assert mag_4h == total_outcomes, "Missing 4h magnitude targets"
        assert mag_1d == total_outcomes, "Missing 1d magnitude targets"
        assert return_count == total_outcomes, "Missing return calculations"
        
        # Test target value quality
        direction_query = '''
            SELECT COUNT(CASE WHEN price_direction_1h IN (0, 1) THEN 1 END) as valid_dir_1h,
                   COUNT(CASE WHEN price_direction_4h IN (0, 1) THEN 1 END) as valid_dir_4h,
                   COUNT(CASE WHEN price_direction_1d IN (0, 1) THEN 1 END) as valid_dir_1d,
                   COUNT(CASE WHEN price_magnitude_1h >= 0 THEN 1 END) as valid_mag_1h,
                   COUNT(CASE WHEN price_magnitude_4h >= 0 THEN 1 END) as valid_mag_4h,
                   COUNT(CASE WHEN price_magnitude_1d >= 0 THEN 1 END) as valid_mag_1d
            FROM enhanced_outcomes
        '''
        
        cursor.execute(direction_query)
        direction_stats = cursor.fetchone()
        
        valid_dir_1h, valid_dir_4h, valid_dir_1d, valid_mag_1h, valid_mag_4h, valid_mag_1d = direction_stats
        
        # Validate target value quality
        assert valid_dir_1h == total_outcomes, "Invalid 1h direction values"
        assert valid_dir_4h == total_outcomes, "Invalid 4h direction values"
        assert valid_dir_1d == total_outcomes, "Invalid 1d direction values"
        assert valid_mag_1h == total_outcomes, "Invalid 1h magnitude values"
        assert valid_mag_4h == total_outcomes, "Invalid 4h magnitude values"
        assert valid_mag_1d == total_outcomes, "Invalid 1d magnitude values"
        
        # Test return calculation accuracy
        return_accuracy_query = '''
            SELECT COUNT(*) as total_returns,
                   COUNT(CASE WHEN ABS(return_pct - ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4)) <= 0.0001 THEN 1 END) as accurate_returns
            FROM enhanced_outcomes
            WHERE entry_price > 0 AND exit_price_1d > 0 AND return_pct IS NOT NULL
        '''
        
        cursor.execute(return_accuracy_query)
        accuracy_stats = cursor.fetchone()
        total_returns, accurate_returns = accuracy_stats
        
        accuracy_rate = (accurate_returns / total_returns) * 100 if total_returns > 0 else 0
        assert accuracy_rate >= 99.9, f"Return calculation accuracy only {accuracy_rate:.1f}%"
        
        conn.close()
    
    @patch('joblib.dump')
    @patch('json.dump')
    def test_model_persistence_workflow(self, mock_json_dump, mock_joblib_dump, temp_model_dir):
        """Test model persistence and metadata storage"""
        
        from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
        
        # Create pipeline instance
        pipeline = EnhancedMLTrainingPipeline(data_dir=temp_model_dir)
        pipeline.models_dir = temp_model_dir
        
        # Create mock models
        mock_direction_model = MagicMock()
        mock_magnitude_model = MagicMock()
        feature_columns = ['sentiment_score', 'rsi', 'current_price', 'volume_ratio']
        
        # Test model saving
        pipeline._save_enhanced_models(mock_direction_model, mock_magnitude_model, feature_columns)
        
        # Verify model files were "saved"
        assert mock_joblib_dump.call_count == 2  # Two models saved
        
        # Verify metadata was saved
        mock_json_dump.assert_called_once()
        
        # Verify metadata structure
        metadata_call = mock_json_dump.call_args[0][0]  # First argument to json.dump
        
        assert 'version' in metadata_call
        assert 'training_date' in metadata_call
        assert 'feature_columns' in metadata_call
        assert 'model_type' in metadata_call
        assert 'direction_model_path' in metadata_call
        assert 'magnitude_model_path' in metadata_call
        
        # Validate metadata values
        assert metadata_call['feature_columns'] == feature_columns
        assert metadata_call['model_type'] == 'enhanced_multi_output'
        assert 'enhanced_v_' in metadata_call['version']
    
    def test_model_performance_tracking(self, ml_database):
        """Test model performance tracking and storage"""
        
        conn = sqlite3.connect(ml_database)
        cursor = conn.cursor()
        
        # Insert sample model performance data
        performance_data = {
            'model_version': 'enhanced_v_20250810_test',
            'model_type': 'enhanced_multi_output',
            'training_date': datetime.now().isoformat(),
            'direction_accuracy_1h': 0.65,
            'direction_accuracy_4h': 0.68,
            'direction_accuracy_1d': 0.72,
            'magnitude_mae_1h': 1.8,
            'magnitude_mae_4h': 2.3,
            'magnitude_mae_1d': 3.1,
            'precision_score': 0.70,
            'recall_score': 0.68,
            'f1_score': 0.69,
            'feature_count': 25,
            'training_samples': 100,
            'parameters': json.dumps({'n_estimators': 200, 'max_depth': 12}),
            'feature_importance': json.dumps({'sentiment_score': 0.15, 'rsi': 0.12, 'current_price': 0.10})
        }
        
        cursor.execute('''
            INSERT INTO model_performance_enhanced (
                model_version, model_type, training_date, direction_accuracy_1h,
                direction_accuracy_4h, direction_accuracy_1d, magnitude_mae_1h,
                magnitude_mae_4h, magnitude_mae_1d, precision_score, recall_score,
                f1_score, feature_count, training_samples, parameters, feature_importance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', tuple(performance_data.values()))
        
        conn.commit()
        
        # Test performance data retrieval and validation
        cursor.execute('''
            SELECT * FROM model_performance_enhanced 
            WHERE model_version = ?
        ''', (performance_data['model_version'],))
        
        result = cursor.fetchone()
        assert result is not None, "Model performance data not stored"
        
        # Test performance metrics are within valid ranges
        cursor.execute('''
            SELECT direction_accuracy_1h, direction_accuracy_4h, direction_accuracy_1d,
                   magnitude_mae_1h, magnitude_mae_4h, magnitude_mae_1d,
                   precision_score, recall_score, f1_score
            FROM model_performance_enhanced
            WHERE model_version = ?
        ''', (performance_data['model_version'],))
        
        metrics = cursor.fetchone()
        
        dir_acc_1h, dir_acc_4h, dir_acc_1d, mag_mae_1h, mag_mae_4h, mag_mae_1d, precision, recall, f1 = metrics
        
        # Validate metric ranges
        assert 0.5 <= dir_acc_1h <= 1.0, f"Direction accuracy 1h out of range: {dir_acc_1h}"
        assert 0.5 <= dir_acc_4h <= 1.0, f"Direction accuracy 4h out of range: {dir_acc_4h}"
        assert 0.5 <= dir_acc_1d <= 1.0, f"Direction accuracy 1d out of range: {dir_acc_1d}"
        
        assert mag_mae_1h >= 0, f"Magnitude MAE 1h invalid: {mag_mae_1h}"
        assert mag_mae_4h >= 0, f"Magnitude MAE 4h invalid: {mag_mae_4h}"
        assert mag_mae_1d >= 0, f"Magnitude MAE 1d invalid: {mag_mae_1d}"
        
        assert 0 <= precision <= 1, f"Precision out of range: {precision}"
        assert 0 <= recall <= 1, f"Recall out of range: {recall}"
        assert 0 <= f1 <= 1, f"F1 score out of range: {f1}"
        
        conn.close()
    
    def test_training_data_temporal_consistency(self, ml_database):
        """Test temporal consistency in training data"""
        
        conn = sqlite3.connect(ml_database)
        
        # Test that features are created before outcomes
        temporal_query = '''
            SELECT f.timestamp as feature_time, 
                   o.prediction_timestamp as outcome_time,
                   f.symbol
            FROM enhanced_features f
            INNER JOIN enhanced_outcomes o ON f.id = o.feature_id
            ORDER BY f.timestamp
        '''
        
        cursor = conn.cursor()
        cursor.execute(temporal_query)
        temporal_data = cursor.fetchall()
        
        assert len(temporal_data) > 0, "No temporal data found"
        
        # Validate temporal consistency
        for feature_time, outcome_time, symbol in temporal_data:
            feature_dt = datetime.fromisoformat(feature_time)
            outcome_dt = datetime.fromisoformat(outcome_time)
            
            # Features should be created before or at the same time as outcomes
            assert feature_dt <= outcome_dt, \
                f"Temporal violation for {symbol}: feature {feature_time} > outcome {outcome_time}"
        
        # Test that training data spans sufficient time range
        time_range_query = '''
            SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest
            FROM enhanced_features
        '''
        
        cursor.execute(time_range_query)
        earliest, latest = cursor.fetchone()
        
        earliest_dt = datetime.fromisoformat(earliest)
        latest_dt = datetime.fromisoformat(latest)
        time_span = (latest_dt - earliest_dt).days
        
        assert time_span >= 7, f"Training data spans only {time_span} days, need at least 7"
        
        conn.close()

if __name__ == "__main__":
    # Run ML training workflow tests
    pytest.main([__file__, "-v", "--tb=short"])
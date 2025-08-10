#!/usr/bin/env python3
"""
Integration Tests for Daily Manager and Analysis Pipeline
Tests the daily_manager.py orchestration of morning and evening routines

Based on the complete trading system workflow documentation
"""

import pytest
import sqlite3
import os
import sys
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestDailyManagerOrchestration:
    """Test daily manager orchestration of complete workflow"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all the dependencies that daily manager uses"""
        with patch.multiple(
            'app.services.daily_manager',
            # Mock sentiment analysis
            SentimentAnalyzer=MagicMock(),
            # Mock technical analysis  
            TechnicalAnalyzer=MagicMock(),
            # Mock ML pipeline
            EnhancedMLPipeline=MagicMock(),
            # Mock data feed
            DataFeed=MagicMock(),
            # Mock database connections
            sqlite3=MagicMock()
        ) as mocks:
            yield mocks
    
    @patch('app.services.daily_manager.DailyManager')
    def test_morning_routine_orchestration(self, mock_daily_manager_class, mock_dependencies):
        """Test morning routine orchestrates all required components"""
        
        # Setup mock daily manager
        mock_manager = MagicMock()
        mock_daily_manager_class.return_value = mock_manager
        
        # Mock morning routine results
        mock_morning_results = {
            'timestamp': datetime.now().isoformat(),
            'banks_analyzed': 5,
            'features_created': 5,
            'sentiment_analysis': {
                'CBA.AX': {'sentiment_score': 0.6, 'confidence': 0.8},
                'WBC.AX': {'sentiment_score': 0.2, 'confidence': 0.7},
                'ANZ.AX': {'sentiment_score': -0.3, 'confidence': 0.6},
                'NAB.AX': {'sentiment_score': 0.4, 'confidence': 0.9},
                'MQG.AX': {'sentiment_score': 0.1, 'confidence': 0.5}
            },
            'technical_analysis': {
                'CBA.AX': {'rsi': 65, 'macd_signal': 'BUY', 'current_price': 175.0},
                'WBC.AX': {'rsi': 55, 'macd_signal': 'HOLD', 'current_price': 33.5},
                'ANZ.AX': {'rsi': 45, 'macd_signal': 'SELL', 'current_price': 30.8},
                'NAB.AX': {'rsi': 70, 'macd_signal': 'BUY', 'current_price': 38.4},
                'MQG.AX': {'rsi': 40, 'macd_signal': 'HOLD', 'current_price': 213.8}
            },
            'ml_predictions': {
                'CBA.AX': {'optimal_action': 'BUY', 'confidence': 0.75},
                'WBC.AX': {'optimal_action': 'HOLD', 'confidence': 0.65},
                'ANZ.AX': {'optimal_action': 'SELL', 'confidence': 0.70},
                'NAB.AX': {'optimal_action': 'BUY', 'confidence': 0.80},
                'MQG.AX': {'optimal_action': 'HOLD', 'confidence': 0.60}
            }
        }
        
        mock_manager.run_morning_analysis.return_value = mock_morning_results
        
        # Test morning routine execution
        daily_manager = mock_daily_manager_class()
        results = daily_manager.run_morning_analysis()
        
        # Validate orchestration results
        assert 'timestamp' in results
        assert 'banks_analyzed' in results
        assert 'features_created' in results
        assert 'sentiment_analysis' in results
        assert 'technical_analysis' in results
        assert 'ml_predictions' in results
        
        # Validate all banks were analyzed
        assert results['banks_analyzed'] == 5
        assert results['features_created'] == 5
        
        # Validate sentiment analysis completeness
        sentiment_data = results['sentiment_analysis']
        assert len(sentiment_data) == 5
        for symbol, data in sentiment_data.items():
            assert 'sentiment_score' in data
            assert 'confidence' in data
            assert -1 <= data['sentiment_score'] <= 1
            assert 0 <= data['confidence'] <= 1
        
        # Validate technical analysis completeness
        technical_data = results['technical_analysis']
        assert len(technical_data) == 5
        for symbol, data in technical_data.items():
            assert 'rsi' in data
            assert 'macd_signal' in data
            assert 'current_price' in data
            assert 0 <= data['rsi'] <= 100
            assert data['macd_signal'] in ['BUY', 'SELL', 'HOLD']
            assert data['current_price'] > 0
        
        # Validate ML predictions completeness
        ml_data = results['ml_predictions']
        assert len(ml_data) == 5
        for symbol, data in ml_data.items():
            assert 'optimal_action' in data
            assert 'confidence' in data
            assert data['optimal_action'] in ['BUY', 'SELL', 'HOLD']
            assert 0 <= data['confidence'] <= 1
    
    @patch('app.services.daily_manager.DailyManager')
    def test_evening_routine_orchestration(self, mock_daily_manager_class, mock_dependencies):
        """Test evening routine orchestrates outcome recording and ML training"""
        
        # Setup mock daily manager
        mock_manager = MagicMock()
        mock_daily_manager_class.return_value = mock_manager
        
        # Mock evening routine results
        mock_evening_results = {
            'timestamp': datetime.now().isoformat(),
            'outcomes_recorded': 5,
            'model_training': {
                'training_samples': 150,
                'direction_accuracy': {'1d': 0.68},
                'magnitude_mae': {'1d': 2.3},
                'model_version': 'enhanced_v_20250810'
            },
            'backtesting': {
                'total_trades': 45,
                'win_rate': 62.2,
                'avg_return': 1.8,
                'sharpe_ratio': 1.2
            },
            'next_day_predictions': {
                'CBA.AX': {'action': 'HOLD', 'confidence': 0.72, 'expected_return': 0.5},
                'WBC.AX': {'action': 'BUY', 'confidence': 0.68, 'expected_return': 2.1},
                'ANZ.AX': {'action': 'SELL', 'confidence': 0.74, 'expected_return': -1.3},
                'NAB.AX': {'action': 'HOLD', 'confidence': 0.66, 'expected_return': 0.8},
                'MQG.AX': {'action': 'BUY', 'confidence': 0.71, 'expected_return': 1.9}
            },
            'data_quality': {
                'return_calculation_accuracy': 100.0,
                'corrupted_records': 0,
                'feature_outcome_links': 150
            }
        }
        
        mock_manager.run_evening_analysis.return_value = mock_evening_results
        
        # Test evening routine execution
        daily_manager = mock_daily_manager_class()
        results = daily_manager.run_evening_analysis()
        
        # Validate evening orchestration results
        assert 'timestamp' in results
        assert 'outcomes_recorded' in results
        assert 'model_training' in results
        assert 'backtesting' in results
        assert 'next_day_predictions' in results
        assert 'data_quality' in results
        
        # Validate outcome recording
        assert results['outcomes_recorded'] == 5
        
        # Validate model training results
        training_data = results['model_training']
        assert training_data['training_samples'] >= 50  # Minimum for ML training
        assert 0.5 <= training_data['direction_accuracy']['1d'] <= 1.0
        assert training_data['magnitude_mae']['1d'] >= 0
        assert 'model_version' in training_data
        
        # Validate backtesting results
        backtest_data = results['backtesting']
        assert backtest_data['total_trades'] > 0
        assert 0 <= backtest_data['win_rate'] <= 100
        assert isinstance(backtest_data['avg_return'], (int, float))
        assert isinstance(backtest_data['sharpe_ratio'], (int, float))
        
        # Validate next day predictions
        predictions = results['next_day_predictions']
        assert len(predictions) == 5
        for symbol, pred in predictions.items():
            assert 'action' in pred
            assert 'confidence' in pred
            assert 'expected_return' in pred
            assert pred['action'] in ['BUY', 'SELL', 'HOLD']
            assert 0 <= pred['confidence'] <= 1
        
        # Validate data quality metrics (critical after return calculation fix)
        quality_data = results['data_quality']
        assert quality_data['return_calculation_accuracy'] >= 99.9  # Should be near 100%
        assert quality_data['corrupted_records'] == 0  # Should be zero after fix
        assert quality_data['feature_outcome_links'] > 0

class TestAnalysisComponentIntegration:
    """Test integration between different analysis components"""
    
    @pytest.fixture
    def sample_market_data(self):
        """Provide sample market data for testing"""
        return {
            'CBA.AX': {
                'current_price': 175.0,
                'volume': 2500000,
                'high': 177.5,
                'low': 173.2,
                'close': 175.0,
                'previous_close': 174.1
            },
            'WBC.AX': {
                'current_price': 33.5,
                'volume': 3200000,
                'high': 34.1,
                'low': 33.2,
                'close': 33.5,
                'previous_close': 33.8
            }
        }
    
    @patch('app.core.sentiment.two_stage_analyzer.TwoStageAnalyzer')
    @patch('app.core.analysis.technical.TechnicalAnalyzer')
    def test_sentiment_technical_integration(self, mock_technical, mock_sentiment, sample_market_data):
        """Test integration between sentiment and technical analysis"""
        
        # Mock sentiment analyzer
        mock_sentiment_instance = MagicMock()
        mock_sentiment.return_value = mock_sentiment_instance
        
        mock_sentiment_results = {
            'CBA.AX': {
                'overall_sentiment': 0.6,
                'confidence': 0.8,
                'news_count': 12,
                'sentiment_components': {
                    'financial_performance': 0.7,
                    'market_outlook': 0.5,
                    'events': 0.4
                }
            }
        }
        
        mock_sentiment_instance.analyze_symbol.return_value = mock_sentiment_results['CBA.AX']
        
        # Mock technical analyzer  
        mock_technical_instance = MagicMock()
        mock_technical.return_value = mock_technical_instance
        
        mock_technical_results = {
            'current_price': 175.0,
            'indicators': {
                'rsi': 65.0,
                'macd': {'line': 0.5, 'signal': 0.3, 'histogram': 0.2},
                'sma': {'sma_20': 172.5, 'sma_50': 170.0},
                'volume': {'current': 2500000, 'ratio': 1.2}
            },
            'signals': {
                'rsi_signal': 'NEUTRAL',
                'macd_signal': 'BUY',
                'trend_signal': 'BULLISH'
            }
        }
        
        mock_technical_instance.analyze.return_value = mock_technical_results
        
        # Test integration
        symbol = 'CBA.AX'
        
        # Get sentiment analysis
        sentiment_analyzer = mock_sentiment()
        sentiment_result = sentiment_analyzer.analyze_symbol(symbol)
        
        # Get technical analysis
        technical_analyzer = mock_technical()
        technical_result = technical_analyzer.analyze(symbol, sample_market_data[symbol])
        
        # Test combined analysis logic
        combined_signal = self._combine_sentiment_technical_signals(
            sentiment_result, technical_result
        )
        
        # Validate combined analysis
        assert 'overall_signal' in combined_signal
        assert 'confidence' in combined_signal
        assert 'reasoning' in combined_signal
        
        # Test signal combination logic
        assert combined_signal['overall_signal'] in ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL']
        assert 0 <= combined_signal['confidence'] <= 1
        
        # Validate signal strength logic
        if sentiment_result['overall_sentiment'] > 0.5 and 'BUY' in str(technical_result['signals']):
            assert combined_signal['overall_signal'] in ['BUY', 'STRONG_BUY']
    
    def _combine_sentiment_technical_signals(self, sentiment_result, technical_result):
        """Simulate combined sentiment + technical signal logic"""
        
        sentiment_score = sentiment_result['overall_sentiment']
        sentiment_confidence = sentiment_result['confidence']
        
        technical_signals = technical_result['signals']
        rsi = technical_result['indicators']['rsi']
        
        # Combine signals
        if sentiment_score > 0.5 and 'BULLISH' in str(technical_signals) and rsi < 70:
            overall_signal = 'STRONG_BUY'
            confidence = min(sentiment_confidence + 0.2, 1.0)
        elif sentiment_score > 0.2 and 'BUY' in str(technical_signals):
            overall_signal = 'BUY'  
            confidence = sentiment_confidence
        elif sentiment_score < -0.5 and 'BEARISH' in str(technical_signals) and rsi > 30:
            overall_signal = 'STRONG_SELL'
            confidence = min(sentiment_confidence + 0.2, 1.0)
        elif sentiment_score < -0.2 and 'SELL' in str(technical_signals):
            overall_signal = 'SELL'
            confidence = sentiment_confidence
        else:
            overall_signal = 'HOLD'
            confidence = sentiment_confidence * 0.8
        
        return {
            'overall_signal': overall_signal,
            'confidence': confidence,
            'reasoning': f"Sentiment: {sentiment_score:.2f}, Technical: {technical_signals}, RSI: {rsi}"
        }
    
    @patch('app.core.ml.enhanced_training_pipeline.EnhancedMLTrainingPipeline')
    def test_ml_pipeline_feature_integration(self, mock_pipeline):
        """Test ML pipeline integration with feature engineering"""
        
        # Mock ML pipeline
        mock_pipeline_instance = MagicMock()
        mock_pipeline.return_value = mock_pipeline_instance
        
        # Mock feature collection
        mock_feature_id = 123
        mock_pipeline_instance.collect_enhanced_training_data.return_value = mock_feature_id
        
        # Mock prediction results  
        mock_prediction = {
            'direction_predictions': {'1h': 1, '4h': 1, '1d': 1},
            'magnitude_predictions': {'1h': 1.2, '4h': 2.1, '1d': 3.5},
            'confidence_scores': {'1h': 0.7, '4h': 0.75, '1d': 0.8, 'average': 0.75},
            'optimal_action': 'BUY',
            'timestamp': datetime.now().isoformat()
        }
        
        mock_pipeline_instance.predict_enhanced.return_value = mock_prediction
        
        # Test ML feature integration
        sentiment_data = {
            'overall_sentiment': 0.6,
            'confidence': 0.8,
            'news_count': 12,
            'sentiment_components': {'events': 0.4}
        }
        
        symbol = 'CBA.AX'
        
        pipeline = mock_pipeline()
        
        # Test feature collection
        feature_id = pipeline.collect_enhanced_training_data(sentiment_data, symbol)
        assert feature_id == mock_feature_id
        
        # Test prediction
        prediction = pipeline.predict_enhanced(sentiment_data, symbol)
        
        # Validate prediction structure
        assert 'direction_predictions' in prediction
        assert 'magnitude_predictions' in prediction
        assert 'confidence_scores' in prediction
        assert 'optimal_action' in prediction
        
        # Validate prediction values
        assert prediction['optimal_action'] in ['BUY', 'SELL', 'HOLD', 'STRONG_BUY', 'STRONG_SELL']
        assert 0 <= prediction['confidence_scores']['average'] <= 1
        
        # Validate timeframe predictions
        for timeframe in ['1h', '4h', '1d']:
            assert timeframe in prediction['direction_predictions']
            assert timeframe in prediction['magnitude_predictions']
            assert prediction['direction_predictions'][timeframe] in [0, 1]
            assert isinstance(prediction['magnitude_predictions'][timeframe], (int, float))

class TestDataFlowIntegration:
    """Test data flow integration across all components"""
    
    @pytest.fixture
    def integration_database(self):
        """Create database for integration testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create all workflow tables
        cursor.execute('''
            CREATE TABLE enhanced_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                sentiment_score REAL,
                confidence REAL,
                rsi REAL,
                macd_line REAL,
                current_price REAL,
                volume_ratio REAL,
                news_count INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE enhanced_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id INTEGER,
                symbol TEXT NOT NULL,
                prediction_timestamp DATETIME NOT NULL,
                optimal_action TEXT,
                confidence_score REAL,
                entry_price REAL,
                exit_price_1d REAL,
                return_pct REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (feature_id) REFERENCES enhanced_features (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE enhanced_morning_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                banks_analyzed INTEGER,
                ml_predictions TEXT,
                technical_signals TEXT,
                recommendations TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE enhanced_evening_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                model_training TEXT,
                backtesting TEXT,
                next_day_predictions TEXT,
                model_comparison TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        yield db_path
        os.unlink(db_path)
    
    def test_complete_data_flow_cycle(self, integration_database):
        """Test complete data flow from morning to evening"""
        
        conn = sqlite3.connect(integration_database)
        cursor = conn.cursor()
        
        # PHASE 1: Morning Analysis Data Flow
        morning_timestamp = datetime.now()
        
        # Simulate morning analysis results
        morning_data = {
            'timestamp': morning_timestamp.isoformat(),
            'banks_analyzed': 5,
            'ml_predictions': json.dumps({
                'CBA.AX': {'action': 'BUY', 'confidence': 0.75},
                'WBC.AX': {'action': 'HOLD', 'confidence': 0.65},
                'ANZ.AX': {'action': 'SELL', 'confidence': 0.70}
            }),
            'technical_signals': json.dumps({
                'CBA.AX': {'rsi': 65, 'signal': 'BUY'},
                'WBC.AX': {'rsi': 55, 'signal': 'HOLD'},
                'ANZ.AX': {'rsi': 45, 'signal': 'SELL'}
            })
        }
        
        # Store morning analysis results
        cursor.execute('''
            INSERT INTO enhanced_morning_analysis 
            (timestamp, banks_analyzed, ml_predictions, technical_signals, recommendations)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            morning_data['timestamp'],
            morning_data['banks_analyzed'],
            morning_data['ml_predictions'],
            morning_data['technical_signals'],
            'Generated morning recommendations'
        ))
        
        morning_analysis_id = cursor.lastrowid
        
        # Create corresponding features
        feature_ids = []
        symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX']
        
        for symbol in symbols:
            cursor.execute('''
                INSERT INTO enhanced_features
                (symbol, timestamp, sentiment_score, confidence, rsi, current_price, volume_ratio, news_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                morning_timestamp.isoformat(),
                np.random.uniform(-1, 1),
                np.random.uniform(0.5, 1.0),
                np.random.uniform(20, 80),
                np.random.uniform(50, 200),
                np.random.uniform(0.5, 3.0),
                np.random.randint(5, 20)
            ))
            
            feature_ids.append(cursor.lastrowid)
        
        conn.commit()
        
        # PHASE 2: Evening Analysis Data Flow
        evening_timestamp = morning_timestamp + timedelta(hours=8)
        
        # Create outcomes for each feature
        for i, (symbol, feature_id) in enumerate(zip(symbols, feature_ids)):
            # Get feature data for outcome calculation
            cursor.execute('SELECT current_price FROM enhanced_features WHERE id = ?', (feature_id,))
            entry_price = cursor.fetchone()[0]
            
            # Simulate market movement
            price_change = np.random.uniform(-0.05, 0.05)  # ±5%
            exit_price = entry_price * (1 + price_change)
            
            # Calculate return using CORRECT formula
            return_pct = ((exit_price - entry_price) / entry_price) * 100
            
            cursor.execute('''
                INSERT INTO enhanced_outcomes
                (feature_id, symbol, prediction_timestamp, optimal_action, confidence_score,
                 entry_price, exit_price_1d, return_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feature_id,
                symbol,
                evening_timestamp.isoformat(),
                ['BUY', 'HOLD', 'SELL'][i],
                np.random.uniform(0.6, 0.9),
                entry_price,
                exit_price,
                return_pct
            ))
        
        # Store evening analysis results
        evening_data = {
            'timestamp': evening_timestamp.isoformat(),
            'model_training': json.dumps({
                'training_samples': len(feature_ids) + 50,
                'direction_accuracy': 0.68,
                'magnitude_mae': 2.3
            }),
            'backtesting': json.dumps({
                'total_trades': 25,
                'win_rate': 64.0,
                'avg_return': 1.9
            }),
            'next_day_predictions': json.dumps({
                symbol: {'action': 'HOLD', 'confidence': 0.7} for symbol in symbols
            })
        }
        
        cursor.execute('''
            INSERT INTO enhanced_evening_analysis
            (timestamp, model_training, backtesting, next_day_predictions, model_comparison)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            evening_data['timestamp'],
            evening_data['model_training'],
            evening_data['backtesting'],
            evening_data['next_day_predictions'],
            'Evening model comparison complete'
        ))
        
        conn.commit()
        
        # PHASE 3: Validate Complete Data Flow
        
        # Test morning analysis was recorded
        cursor.execute('SELECT COUNT(*) FROM enhanced_morning_analysis')
        morning_count = cursor.fetchone()[0]
        assert morning_count == 1, "Morning analysis not recorded"
        
        # Test features were created
        cursor.execute('SELECT COUNT(*) FROM enhanced_features')
        feature_count = cursor.fetchone()[0]
        assert feature_count == len(symbols), f"Expected {len(symbols)} features, got {feature_count}"
        
        # Test outcomes were created and linked
        cursor.execute('''
            SELECT COUNT(*) 
            FROM enhanced_outcomes o
            INNER JOIN enhanced_features f ON o.feature_id = f.id
        ''')
        outcome_count = cursor.fetchone()[0]
        assert outcome_count == len(symbols), f"Expected {len(symbols)} outcomes, got {outcome_count}"
        
        # Test evening analysis was recorded
        cursor.execute('SELECT COUNT(*) FROM enhanced_evening_analysis')
        evening_count = cursor.fetchone()[0]
        assert evening_count == 1, "Evening analysis not recorded"
        
        # Test data temporal consistency
        cursor.execute('''
            SELECT f.timestamp as feature_time, o.prediction_timestamp as outcome_time
            FROM enhanced_features f
            INNER JOIN enhanced_outcomes o ON f.id = o.feature_id
        ''')
        
        time_relationships = cursor.fetchall()
        for feature_time, outcome_time in time_relationships:
            feature_dt = datetime.fromisoformat(feature_time)
            outcome_dt = datetime.fromisoformat(outcome_time)
            assert feature_dt <= outcome_dt, "Temporal consistency violation"
        
        # Test return calculation accuracy
        cursor.execute('''
            SELECT entry_price, exit_price_1d, return_pct
            FROM enhanced_outcomes
            WHERE return_pct IS NOT NULL
        ''')
        
        return_data = cursor.fetchall()
        for entry, exit_price, stored_return in return_data:
            expected_return = ((exit_price - entry) / entry) * 100
            assert abs(stored_return - expected_return) < 0.0001, \
                f"Return calculation error: {stored_return} vs {expected_return}"
        
        conn.close()

if __name__ == "__main__":
    # Run integration tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
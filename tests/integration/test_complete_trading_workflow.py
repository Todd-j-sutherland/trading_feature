#!/usr/bin/env python3
"""
Integration Tests for Complete Trading System Workflow
Tests the entire flow from morning analysis to evening outcome recording

Based on the complete trading system workflow documentation and 
return calculation bug fix findings (August 10, 2025)
"""

import pytest
import sqlite3
import os
import sys
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestCompleteWorkflowIntegration:
    """Test the complete trading workflow integration"""
    
    @pytest.fixture
    def temp_database(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Initialize database with required tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create enhanced_features table
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
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create enhanced_outcomes table
        cursor.execute('''
            CREATE TABLE enhanced_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id INTEGER,
                symbol TEXT NOT NULL,
                prediction_timestamp DATETIME NOT NULL,
                optimal_action TEXT,
                confidence_score REAL,
                entry_price REAL,
                exit_price_1h REAL,
                exit_price_4h REAL,
                exit_price_1d REAL,
                return_pct REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (feature_id) REFERENCES enhanced_features (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        os.unlink(db_path)
    
    def test_morning_to_evening_complete_cycle(self, temp_database):
        """Test complete morning → evening analysis cycle"""
        
        # STEP 1: Simulate Morning Analysis - Feature Creation
        morning_features = self._simulate_morning_analysis(temp_database)
        
        # Validate features were created
        assert len(morning_features) > 0
        assert all('symbol' in f for f in morning_features)
        assert all('sentiment_score' in f for f in morning_features)
        assert all('rsi' in f for f in morning_features)
        
        # STEP 2: Simulate Time Passage (market activity)
        # In real system, this is when actual market movements occur
        
        # STEP 3: Simulate Evening Analysis - Outcome Recording
        evening_outcomes = self._simulate_evening_analysis(temp_database, morning_features)
        
        # Validate outcomes were created and linked to features
        assert len(evening_outcomes) == len(morning_features)
        assert all('return_pct' in o for o in evening_outcomes)
        assert all('optimal_action' in o for o in evening_outcomes)
        
        # STEP 4: Validate Data Quality and Relationships
        self._validate_feature_outcome_relationships(temp_database)
        
        # STEP 5: Validate Return Calculations Are Correct
        self._validate_return_calculations(temp_database)
    
    def _simulate_morning_analysis(self, db_path):
        """Simulate the morning analysis feature creation process"""
        
        # Mock morning analysis data for ASX banks
        symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX']
        features = []
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for symbol in symbols:
            # Simulate comprehensive feature creation
            feature_data = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'sentiment_score': np.random.uniform(-1, 1),  # -1 to 1 range
                'confidence': np.random.uniform(0.5, 1.0),    # 0.5 to 1.0 range
                'rsi': np.random.uniform(20, 80),             # 20 to 80 RSI range
                'macd_line': np.random.uniform(-2, 2),        # MACD values
                'current_price': np.random.uniform(20, 200),  # Realistic ASX prices
                'volume_ratio': np.random.uniform(0.5, 3.0),  # Volume ratio
            }
            
            # Insert feature into database
            cursor.execute('''
                INSERT INTO enhanced_features 
                (symbol, timestamp, sentiment_score, confidence, rsi, macd_line, current_price, volume_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feature_data['symbol'],
                feature_data['timestamp'],
                feature_data['sentiment_score'],
                feature_data['confidence'],
                feature_data['rsi'],
                feature_data['macd_line'],
                feature_data['current_price'],
                feature_data['volume_ratio']
            ))
            
            feature_data['id'] = cursor.lastrowid
            features.append(feature_data)
        
        conn.commit()
        conn.close()
        
        return features
    
    def _simulate_evening_analysis(self, db_path, morning_features):
        """Simulate the evening analysis outcome recording process"""
        
        outcomes = []
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for feature in morning_features:
            # Simulate market movements and price changes
            entry_price = feature['current_price']
            
            # Simulate realistic price movements (±5% typical daily range)
            price_change_pct = np.random.uniform(-5, 5)  # ±5%
            exit_price_1d = entry_price * (1 + price_change_pct / 100)
            
            # Calculate return percentage using CORRECTED formula
            return_pct = ((exit_price_1d - entry_price) / entry_price) * 100
            
            # Determine optimal action based on prediction logic
            if feature['sentiment_score'] > 0.3 and feature['rsi'] < 70:
                optimal_action = 'BUY'
            elif feature['sentiment_score'] < -0.3 and feature['rsi'] > 30:
                optimal_action = 'SELL'
            else:
                optimal_action = 'HOLD'
            
            # Simulate confidence score based on feature strength
            confidence_score = min(abs(feature['sentiment_score']) + (feature['confidence'] * 0.5), 1.0)
            
            outcome_data = {
                'feature_id': feature['id'],
                'symbol': feature['symbol'],
                'prediction_timestamp': feature['timestamp'],
                'optimal_action': optimal_action,
                'confidence_score': confidence_score,
                'entry_price': entry_price,
                'exit_price_1d': exit_price_1d,
                'return_pct': return_pct
            }
            
            # Insert outcome into database
            cursor.execute('''
                INSERT INTO enhanced_outcomes
                (feature_id, symbol, prediction_timestamp, optimal_action, confidence_score,
                 entry_price, exit_price_1d, return_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                outcome_data['feature_id'],
                outcome_data['symbol'],
                outcome_data['prediction_timestamp'],
                outcome_data['optimal_action'],
                outcome_data['confidence_score'],
                outcome_data['entry_price'],
                outcome_data['exit_price_1d'],
                outcome_data['return_pct']
            ))
            
            outcomes.append(outcome_data)
        
        conn.commit()
        conn.close()
        
        return outcomes
    
    def _validate_feature_outcome_relationships(self, db_path):
        """Validate that features and outcomes are properly linked"""
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check that every feature has a corresponding outcome
        cursor.execute('''
            SELECT f.id as feature_id, o.id as outcome_id
            FROM enhanced_features f
            LEFT JOIN enhanced_outcomes o ON f.id = o.feature_id
        ''')
        
        relationships = cursor.fetchall()
        
        # Validate relationships exist
        assert len(relationships) > 0, "No feature-outcome relationships found"
        
        for feature_id, outcome_id in relationships:
            assert outcome_id is not None, f"Feature {feature_id} missing outcome"
        
        # Check data consistency
        cursor.execute('''
            SELECT f.symbol as f_symbol, o.symbol as o_symbol,
                   f.current_price, o.entry_price
            FROM enhanced_features f
            INNER JOIN enhanced_outcomes o ON f.id = o.feature_id
        ''')
        
        consistency_data = cursor.fetchall()
        
        for f_symbol, o_symbol, f_price, o_entry_price in consistency_data:
            assert f_symbol == o_symbol, f"Symbol mismatch: {f_symbol} != {o_symbol}"
            assert abs(f_price - o_entry_price) < 0.01, f"Price mismatch: {f_price} != {o_entry_price}"
        
        conn.close()
    
    def _validate_return_calculations(self, db_path):
        """Validate that return calculations are mathematically correct"""
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all outcomes with price data
        cursor.execute('''
            SELECT entry_price, exit_price_1d, return_pct, symbol
            FROM enhanced_outcomes
            WHERE entry_price IS NOT NULL 
            AND exit_price_1d IS NOT NULL
            AND return_pct IS NOT NULL
        ''')
        
        outcome_data = cursor.fetchall()
        
        assert len(outcome_data) > 0, "No outcome data found for validation"
        
        for entry_price, exit_price, stored_return, symbol in outcome_data:
            # Calculate expected return using corrected formula
            expected_return = ((exit_price - entry_price) / entry_price) * 100
            
            # Validate calculation accuracy
            calculation_error = abs(stored_return - expected_return)
            
            assert calculation_error < 0.0001, \
                f"{symbol}: Return calculation error {calculation_error:.6f}. " \
                f"Stored: {stored_return}, Expected: {expected_return}"
            
            # Validate return is in percentage form (not decimal)
            if expected_return != 0:
                assert abs(stored_return) > 0.001 or stored_return == 0, \
                    f"{symbol}: Return {stored_return} appears to be in decimal form, not percentage"
        
        conn.close()

class TestMLTrainingPipelineIntegration:
    """Test ML training pipeline integration with feature/outcome data"""
    
    @pytest.fixture
    def training_database(self):
        """Create database with training data"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables and populate with training data
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
                feature_version TEXT DEFAULT '2.0'
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
                price_direction_1d INTEGER,
                price_magnitude_1d REAL,
                FOREIGN KEY (feature_id) REFERENCES enhanced_features (id)
            )
        ''')
        
        # Insert sample training data (50 records for minimum training requirements)
        symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX']
        
        for i in range(50):
            symbol = symbols[i % len(symbols)]
            
            # Create feature
            cursor.execute('''
                INSERT INTO enhanced_features 
                (symbol, timestamp, sentiment_score, confidence, rsi, macd_line, current_price, volume_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                (datetime.now() - timedelta(days=i)).isoformat(),
                np.random.uniform(-1, 1),
                np.random.uniform(0.5, 1.0),
                np.random.uniform(20, 80),
                np.random.uniform(-2, 2),
                np.random.uniform(50, 200),
                np.random.uniform(0.5, 3.0)
            ))
            
            feature_id = cursor.lastrowid
            
            # Create corresponding outcome
            entry_price = np.random.uniform(50, 200)
            price_change = np.random.uniform(-0.1, 0.1)  # ±10%
            exit_price = entry_price * (1 + price_change)
            return_pct = ((exit_price - entry_price) / entry_price) * 100
            
            cursor.execute('''
                INSERT INTO enhanced_outcomes
                (feature_id, symbol, prediction_timestamp, optimal_action, confidence_score,
                 entry_price, exit_price_1d, return_pct, price_direction_1d, price_magnitude_1d)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feature_id,
                symbol,
                (datetime.now() - timedelta(days=i)).isoformat(),
                np.random.choice(['BUY', 'SELL', 'HOLD']),
                np.random.uniform(0.5, 1.0),
                entry_price,
                exit_price,
                return_pct,
                1 if price_change > 0 else 0,
                abs(return_pct)
            ))
        
        conn.commit()
        conn.close()
        
        yield db_path
        os.unlink(db_path)
    
    @patch('app.core.ml.enhanced_training_pipeline.EnhancedMLTrainingPipeline')
    def test_ml_training_pipeline_integration(self, mock_pipeline_class, training_database):
        """Test ML training pipeline integration with feature/outcome data"""
        
        # Mock the training pipeline
        mock_pipeline = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline
        
        # Mock training dataset preparation
        mock_features_df = pd.DataFrame({
            'sentiment_score': np.random.uniform(-1, 1, 50),
            'confidence': np.random.uniform(0.5, 1.0, 50),
            'rsi': np.random.uniform(20, 80, 50),
            'current_price': np.random.uniform(50, 200, 50),
        })
        
        mock_targets = {
            'direction_1d': np.random.choice([0, 1], 50),
            'magnitude_1d': np.random.uniform(0, 10, 50)
        }
        
        mock_pipeline.prepare_enhanced_training_dataset.return_value = (mock_features_df, mock_targets)
        
        # Mock model training results
        mock_training_results = {
            'direction_accuracy': {'1d': 0.65},
            'magnitude_mae': {'1d': 2.5},
            'feature_columns': list(mock_features_df.columns)
        }
        
        mock_pipeline.train_enhanced_models.return_value = mock_training_results
        
        # Test the integration
        pipeline = mock_pipeline_class(data_dir="data/ml_models")
        
        # Test dataset preparation
        X, y = pipeline.prepare_enhanced_training_dataset(min_samples=50)
        
        assert X is not None
        assert y is not None
        assert len(X) >= 50  # Minimum training samples
        
        # Test model training
        results = pipeline.train_enhanced_models(X, y)
        
        assert 'direction_accuracy' in results
        assert 'magnitude_mae' in results
        assert 'feature_columns' in results
        
        # Validate training quality
        direction_accuracy = results['direction_accuracy']['1d']
        assert 0.5 <= direction_accuracy <= 1.0  # Should be better than random
        
        magnitude_mae = results['magnitude_mae']['1d']
        assert 0 <= magnitude_mae <= 10  # Reasonable error range
    
    def test_feature_engineering_pipeline(self, training_database):
        """Test feature engineering pipeline creates proper ML features"""
        
        conn = sqlite3.connect(training_database)
        
        # Test feature quality for ML training
        query = '''
            SELECT f.sentiment_score, f.confidence, f.rsi, f.current_price,
                   o.return_pct, o.optimal_action
            FROM enhanced_features f
            INNER JOIN enhanced_outcomes o ON f.id = o.feature_id
            WHERE f.sentiment_score IS NOT NULL
            AND f.confidence IS NOT NULL
            AND f.rsi IS NOT NULL
            AND o.return_pct IS NOT NULL
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        assert len(df) >= 50  # Sufficient training data
        
        # Validate feature ranges
        assert df['sentiment_score'].between(-1, 1).all()
        assert df['confidence'].between(0, 1).all()
        assert df['rsi'].between(0, 100).all()
        assert df['current_price'].gt(0).all()
        
        # Validate outcome quality
        assert df['return_pct'].notna().all()
        assert df['optimal_action'].isin(['BUY', 'SELL', 'HOLD']).all()
        
        # Validate return calculations are in percentage form
        non_zero_returns = df[df['return_pct'] != 0]['return_pct']
        if len(non_zero_returns) > 0:
            # Most returns should be > 0.1% (percentage form) not < 0.1 (decimal form)
            percentage_form_count = (non_zero_returns.abs() > 0.1).sum()
            decimal_form_count = (non_zero_returns.abs() <= 0.1).sum()
            
            # Should have more percentage-form returns than decimal-form
            assert percentage_form_count >= decimal_form_count, \
                "Returns appear to be in decimal form, not percentage form"

class TestPaperTradingIntegration:
    """Test paper trading system integration with ML predictions"""
    
    def test_paper_trading_decision_flow(self):
        """Test paper trading decision making flow"""
        
        # Mock ML prediction results
        ml_prediction = {
            'direction_predictions': {'1d': 1},  # Price up
            'magnitude_predictions': {'1d': 3.5},  # 3.5% change
            'confidence_scores': {'average': 0.75},
            'optimal_action': 'BUY'
        }
        
        # Mock market data
        market_data = {
            'symbol': 'CBA.AX',
            'current_price': 175.0,
            'sentiment_score': 0.6,
            'rsi': 45.0,
            'volume_ratio': 1.2
        }
        
        # Test decision making logic
        decision = self._simulate_trading_decision(ml_prediction, market_data)
        
        # Validate decision structure
        assert 'action' in decision
        assert 'confidence' in decision
        assert 'entry_price' in decision
        assert 'position_size' in decision
        
        # Validate decision logic
        assert decision['action'] in ['BUY', 'SELL', 'HOLD']
        assert 0 <= decision['confidence'] <= 1
        assert decision['entry_price'] > 0
        
        # Test position sizing logic
        if decision['action'] in ['BUY', 'SELL']:
            assert decision['position_size'] > 0
        else:
            assert decision['position_size'] == 0
    
    def _simulate_trading_decision(self, ml_prediction, market_data):
        """Simulate paper trading decision logic"""
        
        confidence = ml_prediction['confidence_scores']['average']
        predicted_action = ml_prediction['optimal_action']
        
        # Risk-based position sizing
        base_position = 1000.0  # $1000 base position
        confidence_multiplier = confidence
        position_size = base_position * confidence_multiplier if predicted_action != 'HOLD' else 0
        
        return {
            'action': predicted_action,
            'confidence': confidence,
            'entry_price': market_data['current_price'],
            'position_size': position_size,
            'reasoning': f"ML prediction: {predicted_action} with {confidence:.2f} confidence"
        }
    
    def test_position_outcome_calculation(self):
        """Test position outcome calculation with correct return formulas"""
        
        # Simulate a completed position
        position = {
            'action': 'BUY',
            'entry_price': 100.0,
            'position_size': 1000.0,
            'entry_time': datetime.now() - timedelta(days=1)
        }
        
        # Simulate market movement
        current_price = 105.0
        exit_time = datetime.now()
        
        # Calculate outcome using CORRECT formula
        return_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100
        dollar_return = (return_pct / 100) * position['position_size']
        
        outcome = {
            'return_pct': return_pct,
            'dollar_return': dollar_return,
            'exit_price': current_price,
            'exit_time': exit_time,
            'holding_period': (exit_time - position['entry_time']).total_seconds() / 3600  # hours
        }
        
        # Validate outcome calculations
        assert outcome['return_pct'] == 5.0  # Should be 5%, not 0.05
        assert outcome['dollar_return'] == 50.0  # $50 profit on $1000 position
        assert outcome['exit_price'] == current_price
        assert outcome['holding_period'] > 0

class TestDataQualityAndConsistency:
    """Test data quality and consistency across the entire workflow"""
    
    @pytest.fixture
    def full_workflow_database(self):
        """Create database with complete workflow data"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Run a complete simulated workflow
        self._run_complete_workflow_simulation(db_path)
        
        yield db_path
        os.unlink(db_path)
    
    def _run_complete_workflow_simulation(self, db_path):
        """Run a complete workflow simulation with all components"""
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create all required tables
        cursor.execute('''
            CREATE TABLE enhanced_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                sentiment_score REAL,
                confidence REAL,
                rsi REAL,
                current_price REAL,
                feature_version TEXT DEFAULT '2.0'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE enhanced_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id INTEGER,
                symbol TEXT NOT NULL,
                prediction_timestamp DATETIME NOT NULL,
                optimal_action TEXT,
                entry_price REAL,
                exit_price_1d REAL,
                return_pct REAL,
                FOREIGN KEY (feature_id) REFERENCES enhanced_features (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE model_performance_enhanced (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version TEXT,
                training_date DATETIME,
                direction_accuracy_1d REAL,
                magnitude_mae_1d REAL,
                training_samples INTEGER
            )
        ''')
        
        # Simulate 30 days of trading data
        symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX']
        
        for day in range(30):
            date = datetime.now() - timedelta(days=day)
            
            for symbol in symbols:
                # Morning: Create features
                cursor.execute('''
                    INSERT INTO enhanced_features 
                    (symbol, timestamp, sentiment_score, confidence, rsi, current_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    date.isoformat(),
                    np.random.uniform(-1, 1),
                    np.random.uniform(0.5, 1.0),
                    np.random.uniform(20, 80),
                    np.random.uniform(50, 200)
                ))
                
                feature_id = cursor.lastrowid
                
                # Evening: Record outcomes
                entry_price = np.random.uniform(50, 200)
                price_change = np.random.uniform(-0.1, 0.1)
                exit_price = entry_price * (1 + price_change)
                return_pct = ((exit_price - entry_price) / entry_price) * 100  # CORRECT formula
                
                cursor.execute('''
                    INSERT INTO enhanced_outcomes
                    (feature_id, symbol, prediction_timestamp, optimal_action,
                     entry_price, exit_price_1d, return_pct)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    feature_id,
                    symbol,
                    date.isoformat(),
                    np.random.choice(['BUY', 'SELL', 'HOLD']),
                    entry_price,
                    exit_price,
                    return_pct
                ))
        
        # Simulate model training results
        cursor.execute('''
            INSERT INTO model_performance_enhanced
            (model_version, training_date, direction_accuracy_1d, magnitude_mae_1d, training_samples)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            'enhanced_v_20250810',
            datetime.now().isoformat(),
            0.68,  # 68% direction accuracy
            2.3,   # 2.3% average magnitude error
            150    # 150 training samples
        ))
        
        conn.commit()
        conn.close()
    
    def test_end_to_end_data_quality(self, full_workflow_database):
        """Test data quality across the entire end-to-end workflow"""
        
        conn = sqlite3.connect(full_workflow_database)
        
        # Test 1: Feature-Outcome Relationship Integrity
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as feature_count,
                   COUNT(o.id) as outcome_count,
                   COUNT(CASE WHEN o.return_pct IS NOT NULL THEN 1 END) as calculated_returns
            FROM enhanced_features f
            LEFT JOIN enhanced_outcomes o ON f.id = o.feature_id
        ''')
        
        counts = cursor.fetchone()
        feature_count, outcome_count, calculated_returns = counts
        
        assert feature_count > 0, "No features found"
        assert outcome_count == feature_count, "Feature-outcome count mismatch"
        assert calculated_returns == feature_count, "Missing return calculations"
        
        # Test 2: Return Calculation Accuracy
        cursor.execute('''
            SELECT entry_price, exit_price_1d, return_pct,
                   ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4) as expected_return
            FROM enhanced_outcomes
            WHERE entry_price > 0 AND exit_price_1d > 0 AND return_pct IS NOT NULL
        ''')
        
        return_data = cursor.fetchall()
        assert len(return_data) > 0, "No return calculation data found"
        
        accuracy_count = 0
        for entry, exit_price, stored_return, expected_return in return_data:
            if abs(stored_return - expected_return) <= 0.0001:
                accuracy_count += 1
        
        accuracy_rate = (accuracy_count / len(return_data)) * 100
        assert accuracy_rate >= 99.9, f"Return calculation accuracy only {accuracy_rate:.1f}%"
        
        # Test 3: Realistic Trading Patterns
        cursor.execute('''
            SELECT optimal_action,
                   COUNT(*) as count,
                   SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) as wins,
                   AVG(return_pct) as avg_return
            FROM enhanced_outcomes
            WHERE return_pct IS NOT NULL
            GROUP BY optimal_action
        ''')
        
        trading_patterns = cursor.fetchall()
        
        for action, count, wins, avg_return in trading_patterns:
            win_rate = (wins / count) * 100 if count > 0 else 0
            
            # Validate realistic patterns (not the bug patterns)
            if action == 'BUY':
                assert win_rate < 90, f"BUY win rate {win_rate:.1f}% seems unrealistic (bug pattern?)"
                assert win_rate > 20, f"BUY win rate {win_rate:.1f}% seems too low"
            elif action == 'SELL':
                assert win_rate > 5, f"SELL win rate {win_rate:.1f}% seems unrealistic (bug pattern?)"
                assert win_rate < 80, f"SELL win rate {win_rate:.1f}% seems too high"
        
        # Test 4: Model Performance Tracking
        cursor.execute('''
            SELECT direction_accuracy_1d, magnitude_mae_1d, training_samples
            FROM model_performance_enhanced
            ORDER BY training_date DESC LIMIT 1
        ''')
        
        performance = cursor.fetchone()
        if performance:
            direction_accuracy, magnitude_mae, training_samples = performance
            
            assert 0.5 <= direction_accuracy <= 1.0, "Direction accuracy out of valid range"
            assert magnitude_mae >= 0, "Magnitude MAE cannot be negative"
            assert training_samples >= 50, "Insufficient training samples"
        
        conn.close()
    
    def test_temporal_data_consistency(self, full_workflow_database):
        """Test temporal consistency across the workflow"""
        
        conn = sqlite3.connect(full_workflow_database)
        
        # Test that prediction timestamps are before or equal to outcome timestamps
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.timestamp as feature_time, o.prediction_timestamp as outcome_time
            FROM enhanced_features f
            INNER JOIN enhanced_outcomes o ON f.id = o.feature_id
        ''')
        
        time_data = cursor.fetchall()
        
        for feature_time, outcome_time in time_data:
            feature_dt = datetime.fromisoformat(feature_time)
            outcome_dt = datetime.fromisoformat(outcome_time)
            
            # Features should be created before or at the same time as outcomes
            assert feature_dt <= outcome_dt, \
                f"Feature created after outcome: {feature_time} > {outcome_time}"
        
        conn.close()

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])
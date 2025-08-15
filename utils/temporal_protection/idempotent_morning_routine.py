#!/usr/bin/env python3
"""
Idempotent Morning Routine with Data Leakage Prevention

This module ensures the morning routine can be run multiple times without creating
duplicate data or causing data leakage issues. It implements proper deduplication,
transaction safety, and data versioning.
"""

import sqlite3
import hashlib
import json
from datetime import datetime, date, timezone, timedelta
from typing import Dict, List, Optional, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IdempotentDataManager:
    """Manages idempotent operations for trading data"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = db_path
        # Australian timezone (AEST is UTC+10, AEDT is UTC+11)
        # For simplicity, we'll use UTC+10 and adjust manually for DST if needed
        self.australian_tz = timezone(timedelta(hours=10))
        self.today = self.get_australian_date()
        
        # Initialize database with proper constraints
        self._initialize_database()
    
    def get_australian_date(self) -> str:
        """Get current Australian date as string"""
        now = datetime.now(self.australian_tz)
        return now.strftime('%Y-%m-%d')
    
    def get_australian_datetime(self) -> str:
        """Get current Australian datetime as string"""
        now = datetime.now(self.australian_tz)
        return now.strftime('%Y-%m-%d %H:%M:%S')
    
    def _initialize_database(self):
        """Initialize database with proper constraints to prevent data leakage"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create analysis_runs table to track when analysis was run
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_date DATE NOT NULL,
                    analysis_type TEXT NOT NULL,
                    run_timestamp DATETIME NOT NULL,
                    data_hash TEXT,
                    status TEXT DEFAULT 'running',
                    banks_analyzed TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(analysis_date, analysis_type)
                )
            """)
            
            # Add unique constraints to prevent duplicates
            constraints_to_add = [
                ("predictions", "CREATE UNIQUE INDEX IF NOT EXISTS idx_predictions_symbol_date ON predictions(symbol, DATE(prediction_timestamp))"),
                ("enhanced_features", "CREATE UNIQUE INDEX IF NOT EXISTS idx_features_symbol_date ON enhanced_features(symbol, DATE(timestamp))"),
                ("enhanced_outcomes", "CREATE UNIQUE INDEX IF NOT EXISTS idx_outcomes_feature_id ON enhanced_outcomes(feature_id)"),
                ("sentiment_features", "CREATE UNIQUE INDEX IF NOT EXISTS idx_sentiment_symbol_date ON sentiment_features(symbol, DATE(created_at))")
            ]
            
            for table_name, constraint_sql in constraints_to_add:
                try:
                    cursor.execute(constraint_sql)
                    logger.info(f"✅ Applied constraint to {table_name}")
                except sqlite3.OperationalError as e:
                    if "already exists" not in str(e):
                        logger.warning(f"⚠️ Could not apply constraint to {table_name}: {e}")
                except sqlite3.IntegrityError as e:
                    logger.warning(f"⚠️ Constraint conflict on {table_name} (data already exists): {e}")
            
            conn.commit()
    
    def check_analysis_already_run(self, analysis_type: str = "morning") -> bool:
        """Check if analysis has already been run today"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, status, run_timestamp, data_hash
                FROM analysis_runs 
                WHERE analysis_date = ? AND analysis_type = ?
                ORDER BY run_timestamp DESC
                LIMIT 1
            """, (self.today, analysis_type))
            
            result = cursor.fetchone()
            
            if result:
                run_id, status, timestamp, data_hash = result
                logger.info(f"Found existing {analysis_type} analysis for {self.today}: status={status}, time={timestamp}")
                
                if status == 'completed':
                    return True
                elif status == 'running':
                    # Check if it's been running for more than 2 hours (likely crashed)
                    try:
                        run_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        now = datetime.now(self.australian_tz)
                        # Make run_time timezone aware if it isn't
                        if run_time.tzinfo is None:
                            run_time = run_time.replace(tzinfo=self.australian_tz)
                        hours_running = (now - run_time).total_seconds() / 3600
                    except Exception as e:
                        logger.warning(f"Error parsing timestamp: {e}, assuming crashed")
                        hours_running = 3  # Assume crashed
                    
                    if hours_running > 2:
                        logger.warning(f"Analysis appears to have crashed (running for {hours_running:.1f} hours). Allowing restart.")
                        self._mark_analysis_failed(run_id)
                        return False
                    else:
                        logger.info(f"Analysis is currently running (started {hours_running:.1f} hours ago)")
                        return True
            
            return False
    
    def start_analysis_run(self, analysis_type: str = "morning", banks: List[str] = None) -> int:
        """Start a new analysis run and return the run ID"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Generate data hash based on analysis parameters
            hash_data = {
                'date': self.today,
                'type': analysis_type,
                'banks': sorted(banks) if banks else [],
                'timestamp': self.get_australian_datetime()
            }
            data_hash = hashlib.md5(json.dumps(hash_data, sort_keys=True).encode()).hexdigest()
            
            cursor.execute("""
                INSERT OR REPLACE INTO analysis_runs 
                (analysis_date, analysis_type, run_timestamp, data_hash, status, banks_analyzed)
                VALUES (?, ?, ?, ?, 'running', ?)
            """, (
                self.today,
                analysis_type, 
                self.get_australian_datetime(),
                data_hash,
                json.dumps(banks) if banks else None
            ))
            
            run_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Started {analysis_type} analysis run {run_id} for {self.today}")
            return run_id
    
    def complete_analysis_run(self, run_id: int):
        """Mark analysis run as completed"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE analysis_runs 
                SET status = 'completed'
                WHERE id = ?
            """, (run_id,))
            
            conn.commit()
            logger.info(f"Completed analysis run {run_id}")
    
    def _mark_analysis_failed(self, run_id: int):
        """Mark analysis run as failed"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE analysis_runs 
                SET status = 'failed'
                WHERE id = ?
            """, (run_id,))
            
            conn.commit()
    
    def safe_insert_prediction(self, symbol: str, prediction_data: Dict) -> bool:
        """Safely insert prediction with deduplication"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                # Check if prediction already exists for today
                cursor.execute("""
                    SELECT prediction_id FROM predictions 
                    WHERE symbol = ? AND DATE(prediction_timestamp) = ?
                """, (symbol, self.today))
                
                existing = cursor.fetchone()
                if existing:
                    logger.info(f"Prediction for {symbol} on {self.today} already exists, skipping")
                    return False
                
                # Insert new prediction
                cursor.execute("""
                    INSERT INTO predictions (
                        prediction_id, symbol, prediction_timestamp, predicted_action,
                        action_confidence, predicted_direction, predicted_magnitude,
                        feature_vector, model_version, entry_price, optimal_action
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prediction_data['prediction_id'],
                    symbol,
                    prediction_data['prediction_timestamp'],
                    prediction_data['predicted_action'],
                    prediction_data['action_confidence'],
                    prediction_data.get('predicted_direction'),
                    prediction_data.get('predicted_magnitude'),
                    prediction_data.get('feature_vector'),
                    prediction_data.get('model_version', '1.0'),
                    prediction_data.get('entry_price', 0),
                    prediction_data.get('optimal_action')
                ))
                
                conn.commit()
                logger.info(f"✅ Inserted prediction for {symbol}")
                return True
                
            except sqlite3.IntegrityError as e:
                logger.warning(f"⚠️ Prediction for {symbol} already exists: {e}")
                return False
            except Exception as e:
                logger.error(f"❌ Error inserting prediction for {symbol}: {e}")
                conn.rollback()
                return False
    
    def safe_insert_enhanced_features(self, symbol: str, features_data: Dict) -> Optional[int]:
        """Safely insert enhanced features with deduplication"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                # Check if features already exist for today
                cursor.execute("""
                    SELECT id FROM enhanced_features 
                    WHERE symbol = ? AND DATE(timestamp) = ?
                """, (symbol, self.today))
                
                existing = cursor.fetchone()
                if existing:
                    logger.info(f"Enhanced features for {symbol} on {self.today} already exist, skipping")
                    return existing[0]
                
                # Insert new features using actual schema
                insert_sql = """
                    INSERT INTO enhanced_features (
                        symbol, timestamp, sentiment_score, confidence, news_count, 
                        reddit_sentiment, rsi, macd_line, current_price, volatility_20d,
                        volume, asx_market_hours
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_sql, (
                    symbol,
                    features_data['timestamp'],
                    features_data.get('sentiment_score', 0),
                    features_data.get('confidence', 0.8),
                    features_data.get('news_count', 0),
                    features_data.get('reddit_sentiment', 0),
                    features_data.get('rsi', 50),
                    features_data.get('macd_line', 0),
                    features_data.get('current_price', 0),
                    features_data.get('volatility_20d', 0.015),
                    features_data.get('volume', 0),
                    features_data.get('asx_market_hours', 1)
                ))
                
                feature_id = cursor.lastrowid
                conn.commit()
                logger.info(f"✅ Inserted enhanced features for {symbol} (ID: {feature_id})")
                return feature_id
                
            except sqlite3.IntegrityError as e:
                logger.warning(f"⚠️ Enhanced features for {symbol} already exist: {e}")
                # Try to get existing ID
                cursor.execute("""
                    SELECT id FROM enhanced_features 
                    WHERE symbol = ? AND DATE(timestamp) = ?
                """, (symbol, self.today))
                existing = cursor.fetchone()
                return existing[0] if existing else None
            except Exception as e:
                logger.error(f"❌ Error inserting enhanced features for {symbol}: {e}")
                conn.rollback()
                return None
    
    def safe_insert_enhanced_outcomes(self, feature_id: int, outcomes_data: Dict) -> bool:
        """Safely insert enhanced outcomes with deduplication"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                # Check if outcome already exists for this feature
                cursor.execute("""
                    SELECT id FROM enhanced_outcomes WHERE feature_id = ?
                """, (feature_id,))
                
                existing = cursor.fetchone()
                if existing:
                    logger.info(f"Enhanced outcome for feature {feature_id} already exists, skipping")
                    return False
                
                # Insert new outcome
                cursor.execute("""
                    INSERT INTO enhanced_outcomes (
                        feature_id, symbol, prediction_timestamp, price_direction_1h,
                        price_direction_4h, price_direction_1d, price_magnitude_1h,
                        price_magnitude_4h, price_magnitude_1d, volatility_next_1h,
                        optimal_action, confidence_score, entry_price, exit_price_1h,
                        exit_price_4h, exit_price_1d, exit_timestamp, return_pct
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    feature_id,
                    outcomes_data['symbol'],
                    outcomes_data['prediction_timestamp'],
                    outcomes_data.get('price_direction_1h'),
                    outcomes_data.get('price_direction_4h'),
                    outcomes_data.get('price_direction_1d'),
                    outcomes_data.get('price_magnitude_1h'),
                    outcomes_data.get('price_magnitude_4h'),
                    outcomes_data.get('price_magnitude_1d'),
                    outcomes_data.get('volatility_next_1h'),
                    outcomes_data.get('optimal_action'),
                    outcomes_data.get('confidence_score'),
                    outcomes_data.get('entry_price'),
                    outcomes_data.get('exit_price_1h'),
                    outcomes_data.get('exit_price_4h'),
                    outcomes_data.get('exit_price_1d'),
                    outcomes_data.get('exit_timestamp'),
                    outcomes_data.get('return_pct')
                ))
                
                conn.commit()
                logger.info(f"✅ Inserted enhanced outcome for feature {feature_id}")
                return True
                
            except sqlite3.IntegrityError as e:
                logger.warning(f"⚠️ Enhanced outcome for feature {feature_id} already exists: {e}")
                return False
            except Exception as e:
                logger.error(f"❌ Error inserting enhanced outcome for feature {feature_id}: {e}")
                conn.rollback()
                return False
    
    def cleanup_incomplete_runs(self):
        """Clean up incomplete analysis runs older than 24 hours"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Mark old running analyses as failed
            cursor.execute("""
                UPDATE analysis_runs 
                SET status = 'failed'
                WHERE status = 'running' 
                AND run_timestamp < datetime('now', '-24 hours')
            """)
            
            cleaned = cursor.rowcount
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} incomplete analysis runs")
            
            conn.commit()
    
    def get_analysis_summary(self) -> Dict:
        """Get summary of analysis runs"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get runs for last 7 days
            cursor.execute("""
                SELECT 
                    analysis_date,
                    analysis_type,
                    status,
                    COUNT(*) as run_count
                FROM analysis_runs 
                WHERE analysis_date >= date('now', '-7 days')
                GROUP BY analysis_date, analysis_type, status
                ORDER BY analysis_date DESC
            """)
            
            runs = cursor.fetchall()
            
            # Get data counts
            cursor.execute("SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = ?", (self.today,))
            today_predictions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM enhanced_features WHERE DATE(timestamp) = ?", (self.today,))
            today_features = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE DATE(prediction_timestamp) = ?", (self.today,))
            today_outcomes = cursor.fetchone()[0]
            
            return {
                'recent_runs': runs,
                'today_data': {
                    'predictions': today_predictions,
                    'features': today_features,
                    'outcomes': today_outcomes
                },
                'analysis_date': self.today
            }

class IdempotentMorningRoutine:
    """Idempotent morning routine that prevents data leakage"""
    
    def __init__(self):
        self.data_manager = IdempotentDataManager()
        self.banks = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX"]
    
    def run_safe_morning_analysis(self) -> Dict:
        """Run morning analysis safely with deduplication"""
        
        # Step 1: Check if analysis already completed today
        if self.data_manager.check_analysis_already_run("morning"):
            logger.info("✅ Morning analysis already completed for today")
            return {
                'status': 'already_completed',
                'message': 'Morning analysis already run today',
                'summary': self.data_manager.get_analysis_summary()
            }
        
        # Step 2: Clean up any incomplete runs
        self.data_manager.cleanup_incomplete_runs()
        
        # Step 3: Start new analysis run
        run_id = self.data_manager.start_analysis_run("morning", self.banks)
        
        try:
            results = {
                'status': 'success',
                'run_id': run_id,
                'timestamp': self.data_manager.get_australian_datetime(),
                'banks_processed': [],
                'errors': []
            }
            
            # Step 4: Process each bank safely
            for symbol in self.banks:
                try:
                    logger.info(f"Processing {symbol}...")
                    
                    # This would call the actual analysis functions
                    # For now, we'll simulate the data structure
                    prediction_data = self._generate_sample_prediction(symbol)
                    features_data = self._generate_sample_features(symbol)
                    outcomes_data = self._generate_sample_outcomes(symbol)
                    
                    # Safe insertions with deduplication
                    pred_success = self.data_manager.safe_insert_prediction(symbol, prediction_data)
                    feature_id = self.data_manager.safe_insert_enhanced_features(symbol, features_data)
                    
                    if feature_id:
                        outcomes_data['feature_id'] = feature_id
                        outcome_success = self.data_manager.safe_insert_enhanced_outcomes(feature_id, outcomes_data)
                    else:
                        outcome_success = False
                    
                    results['banks_processed'].append({
                        'symbol': symbol,
                        'prediction_inserted': pred_success,
                        'features_inserted': bool(feature_id),
                        'outcome_inserted': outcome_success,
                        'feature_id': feature_id
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    results['errors'].append(f"{symbol}: {str(e)}")
            
            # Step 5: Mark analysis as completed
            self.data_manager.complete_analysis_run(run_id)
            
            logger.info(f"✅ Morning analysis completed successfully for {len(results['banks_processed'])} banks")
            return results
            
        except Exception as e:
            logger.error(f"❌ Morning analysis failed: {e}")
            self.data_manager._mark_analysis_failed(run_id)
            return {
                'status': 'failed',
                'error': str(e),
                'run_id': run_id
            }
    
    def _generate_sample_prediction(self, symbol: str) -> Dict:
        """Generate sample prediction data (replace with actual analysis)"""
        import uuid
        
        return {
            'prediction_id': str(uuid.uuid4()),
            'prediction_timestamp': self.data_manager.get_australian_datetime(),
            'predicted_action': 'HOLD',
            'action_confidence': 0.75,
            'predicted_direction': 1,
            'predicted_magnitude': 0.02,
            'feature_vector': json.dumps([0.1, 0.2, 0.3]),
            'model_version': '2.0',
            'entry_price': 100.0,
            'optimal_action': 'HOLD'
        }
    
    def _generate_sample_features(self, symbol: str) -> Dict:
        """Generate sample features data (replace with actual analysis)"""
        
        return {
            'timestamp': self.data_manager.get_australian_datetime(),
            'sentiment_score': 0.1,
            'confidence': 0.8,
            'news_count': 5,
            'reddit_sentiment': 0.05,
            'rsi': 55.0,
            'macd_line': 0.5,
            'current_price': 100.0,
            'volatility_20d': 0.02,
            'volume': 1000000,
            'asx_market_hours': 1
        }
    
    def _generate_sample_outcomes(self, symbol: str) -> Dict:
        """Generate sample outcomes data (replace with actual analysis)"""
        
        return {
            'symbol': symbol,
            'prediction_timestamp': self.data_manager.get_australian_datetime(),
            'price_direction_1h': 1,
            'price_direction_4h': 1,
            'price_direction_1d': 0,
            'price_magnitude_1h': 0.005,
            'price_magnitude_4h': 0.01,
            'price_magnitude_1d': -0.005,
            'volatility_next_1h': 0.01,
            'optimal_action': 'HOLD',
            'confidence_score': 0.75,
            'entry_price': 100.0,
            'exit_price_1h': None,
            'exit_price_4h': None,
            'exit_price_1d': None,
            'exit_timestamp': None,
            'return_pct': None
        }

def main():
    """Test the idempotent morning routine"""
    
    print("🛡️ IDEMPOTENT MORNING ROUTINE TEST")
    print("=" * 50)
    
    routine = IdempotentMorningRoutine()
    
    # Run once
    print("Running morning analysis (first time)...")
    result1 = routine.run_safe_morning_analysis()
    print(f"Result 1: {result1['status']}")
    
    # Run again (should detect duplicate)
    print("\nRunning morning analysis (second time)...")
    result2 = routine.run_safe_morning_analysis()
    print(f"Result 2: {result2['status']}")
    
    # Show summary
    print("\nAnalysis Summary:")
    summary = routine.data_manager.get_analysis_summary()
    print(f"Today's data: {summary['today_data']}")
    
    return result1, result2

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Unified SQL Data Manager

Replaces scattered JSON files with centralized SQL operations.
Provides clean interface for all data operations in the trading system.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import pandas as pd

logger = logging.getLogger(__name__)

class TradingDataManager:
    """Centralized data manager for all trading system data"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to unified database
            project_root = Path(__file__).parent.parent.parent.parent
            self.db_path = project_root / "data" / "trading_unified.db"
        else:
            self.db_path = Path(db_path)
        
        # Ensure database exists and has schema
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with schema if it doesn't exist"""
        if not self.db_path.exists():
            logger.info(f"Creating new database: {self.db_path}")
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create schema (same as consolidation script)
            with self.get_connection() as conn:
                conn.executescript(self._get_schema_sql())
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    # SENTIMENT DATA OPERATIONS
    
    def save_sentiment_data(self, symbol: str, sentiment_score: float, 
                          confidence: float, news_count: int = 0,
                          stage_1_score: Optional[float] = None,
                          stage_2_score: Optional[float] = None,
                          economic_context: Optional[str] = None,
                          timestamp: Optional[datetime] = None) -> int:
        """Save bank sentiment analysis results"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO bank_sentiment 
                (symbol, timestamp, sentiment_score, confidence, news_count,
                 stage_1_score, stage_2_score, economic_context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, timestamp, sentiment_score, confidence, news_count,
                  stage_1_score, stage_2_score, economic_context))
            conn.commit()
            return cursor.lastrowid
    
    def get_latest_sentiment(self, symbol: Optional[str] = None, 
                           hours_back: int = 24) -> List[Dict]:
        """Get recent sentiment data"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with self.get_connection() as conn:
            if symbol:
                cursor = conn.execute("""
                    SELECT * FROM bank_sentiment 
                    WHERE symbol = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (symbol, cutoff_time))
            else:
                cursor = conn.execute("""
                    SELECT * FROM bank_sentiment 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (cutoff_time,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_sentiment_history(self, symbol: str, days_back: int = 30) -> pd.DataFrame:
        """Get sentiment history as DataFrame for analysis"""
        cutoff_time = datetime.now() - timedelta(days=days_back)
        
        with self.get_connection() as conn:
            df = pd.read_sql_query("""
                SELECT * FROM bank_sentiment 
                WHERE symbol = ? AND timestamp >= ?
                ORDER BY timestamp
            """, conn, params=(symbol, cutoff_time))
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
    
    # ML PREDICTION OPERATIONS
    
    def save_ml_prediction(self, symbol: str, prediction_type: str,
                          predicted_value: float, confidence_score: float,
                          model_version: str, features: Dict[str, Any],
                          timestamp: Optional[datetime] = None) -> int:
        """Save ML model predictions"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ml_predictions 
                (symbol, timestamp, prediction_type, predicted_value, 
                 confidence_score, model_version, features, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (symbol, timestamp, prediction_type, predicted_value,
                  confidence_score, model_version, json.dumps(features)))
            conn.commit()
            return cursor.lastrowid
    
    def update_prediction_outcome(self, prediction_id: int, actual_value: float):
        """Update prediction with actual outcome"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE ml_predictions 
                SET actual_value = ?, status = 'completed'
                WHERE id = ?
            """, (actual_value, prediction_id))
            conn.commit()
    
    def get_ml_predictions(self, symbol: Optional[str] = None,
                          prediction_type: Optional[str] = None,
                          status: str = 'all') -> List[Dict]:
        """Get ML predictions with optional filtering"""
        query = "SELECT * FROM ml_predictions WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if prediction_type:
            query += " AND prediction_type = ?"
            params.append(prediction_type)
        
        if status != 'all':
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY timestamp DESC"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # TRADING SIGNALS OPERATIONS
    
    def save_trading_signal(self, symbol: str, signal_type: str, strength: float,
                           ml_confidence: float, technical_score: float,
                           sentiment_score: float, economic_regime: str,
                           reasoning: str, timestamp: Optional[datetime] = None) -> int:
        """Save trading signals"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trading_signals 
                (symbol, timestamp, signal_type, strength, ml_confidence,
                 technical_score, sentiment_score, economic_regime, reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, timestamp, signal_type, strength, ml_confidence,
                  technical_score, sentiment_score, economic_regime, reasoning))
            conn.commit()
            return cursor.lastrowid
    
    def get_active_signals(self, hours_back: int = 6) -> List[Dict]:
        """Get recent trading signals"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM trading_signals 
                WHERE timestamp >= ? AND executed = FALSE
                ORDER BY strength DESC, timestamp DESC
            """, (cutoff_time,))
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_signal_executed(self, signal_id: int):
        """Mark a trading signal as executed"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE trading_signals 
                SET executed = TRUE
                WHERE id = ?
            """, (signal_id,))
            conn.commit()
    
    # POSITION TRACKING OPERATIONS
    
    def save_position(self, symbol: str, entry_date: datetime, position_type: str,
                     entry_price: float, position_size: int, ml_confidence: float,
                     sentiment_at_entry: float) -> int:
        """Save new trading position"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO positions 
                (symbol, entry_date, position_type, entry_price, position_size,
                 ml_confidence, sentiment_at_entry)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol, entry_date, position_type, entry_price, position_size,
                  ml_confidence, sentiment_at_entry))
            conn.commit()
            return cursor.lastrowid
    
    def close_position(self, position_id: int, exit_date: datetime,
                      exit_price: float, exit_reason: str):
        """Close an existing position"""
        with self.get_connection() as conn:
            # Calculate P&L
            cursor = conn.cursor()
            cursor.execute("SELECT entry_price, position_size FROM positions WHERE id = ?", 
                          (position_id,))
            row = cursor.fetchone()
            
            if row:
                entry_price, position_size = row
                profit_loss = (exit_price - entry_price) * position_size
                return_pct = ((exit_price - entry_price) / entry_price) * 100
                
                cursor.execute("""
                    UPDATE positions 
                    SET exit_date = ?, exit_price = ?, exit_reason = ?,
                        profit_loss = ?, return_percentage = ?
                    WHERE id = ?
                """, (exit_date, exit_price, exit_reason, profit_loss, return_pct, position_id))
                conn.commit()
                return profit_loss
        return 0
    
    def get_positions(self, status: str = 'all') -> List[Dict]:
        """Get positions (open, closed, or all)"""
        if status == 'open':
            query = "SELECT * FROM positions WHERE exit_date IS NULL ORDER BY entry_date DESC"
        elif status == 'closed':
            query = "SELECT * FROM positions WHERE exit_date IS NOT NULL ORDER BY exit_date DESC"
        else:
            query = "SELECT * FROM positions ORDER BY entry_date DESC"
        
        with self.get_connection() as conn:
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall trading performance summary"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_positions,
                    COUNT(CASE WHEN exit_date IS NOT NULL THEN 1 END) as closed_positions,
                    COUNT(CASE WHEN exit_date IS NULL THEN 1 END) as open_positions,
                    COALESCE(SUM(profit_loss), 0) as total_pnl,
                    COUNT(CASE WHEN profit_loss > 0 THEN 1 END) as winning_trades,
                    COUNT(CASE WHEN profit_loss < 0 THEN 1 END) as losing_trades,
                    COALESCE(AVG(CASE WHEN profit_loss > 0 THEN profit_loss END), 0) as avg_win,
                    COALESCE(AVG(CASE WHEN profit_loss < 0 THEN profit_loss END), 0) as avg_loss,
                    COALESCE(AVG(return_percentage), 0) as avg_return_pct
                FROM positions
            """)
            
            row = cursor.fetchone()
            if row:
                summary = dict(row)
                
                # Calculate win rate
                closed = summary['closed_positions']
                if closed > 0:
                    summary['win_rate'] = (summary['winning_trades'] / closed) * 100
                else:
                    summary['win_rate'] = 0
                
                # Calculate profit factor
                if summary['avg_loss'] != 0:
                    summary['profit_factor'] = abs(summary['avg_win'] / summary['avg_loss'])
                else:
                    summary['profit_factor'] = float('inf') if summary['avg_win'] > 0 else 0
                
                return summary
            
        return {}
    
    # CACHE OPERATIONS (replaces JSON cache)
    
    def cache_data(self, key: str, data: Any, ttl_hours: int = 24) -> bool:
        """Cache data with TTL"""
        expiry_date = datetime.now() + timedelta(hours=ttl_hours)
        
        with self.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO market_data_cache 
                    (cache_key, data, expiry_date)
                    VALUES (?, ?, ?)
                """, (key, json.dumps(data), expiry_date))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error caching data for key {key}: {e}")
                return False
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve cached data if not expired"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT data FROM market_data_cache 
                WHERE cache_key = ? AND expiry_date > ?
            """, (key, datetime.now()))
            
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row['data'])
                except json.JSONDecodeError:
                    logger.error(f"Error decoding cached data for key {key}")
            
        return None
    
    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM market_data_cache 
                WHERE expiry_date <= ?
            """, (datetime.now(),))
            conn.commit()
            return cursor.rowcount
    
    # NEWS OPERATIONS
    
    def save_news_article(self, title: str, content: str, url: str,
                         published_date: datetime, source: str,
                         symbol: Optional[str] = None,
                         sentiment_score: Optional[float] = None,
                         confidence: Optional[float] = None) -> int:
        """Save news article with analysis"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO news_articles 
                    (symbol, title, content, url, published_date, source,
                     sentiment_score, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, title, content, url, published_date, source,
                      sentiment_score, confidence))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # URL already exists
                return 0
    
    def get_recent_news(self, symbol: Optional[str] = None, 
                       hours_back: int = 24) -> List[Dict]:
        """Get recent news articles"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with self.get_connection() as conn:
            if symbol:
                cursor = conn.execute("""
                    SELECT * FROM news_articles 
                    WHERE symbol = ? AND published_date >= ?
                    ORDER BY published_date DESC
                """, (symbol, cutoff_time))
            else:
                cursor = conn.execute("""
                    SELECT * FROM news_articles 
                    WHERE published_date >= ?
                    ORDER BY published_date DESC
                """, (cutoff_time,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # SYSTEM METRICS
    
    def log_metric(self, metric_name: str, value: float, category: str = 'general'):
        """Log system performance metric"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO system_metrics (metric_name, metric_value, category)
                VALUES (?, ?, ?)
            """, (metric_name, value, category))
            conn.commit()
    
    def get_metrics(self, category: Optional[str] = None, 
                   hours_back: int = 24) -> List[Dict]:
        """Get system metrics"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with self.get_connection() as conn:
            if category:
                cursor = conn.execute("""
                    SELECT * FROM system_metrics 
                    WHERE category = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (category, cutoff_time))
            else:
                cursor = conn.execute("""
                    SELECT * FROM system_metrics 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (cutoff_time,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def _get_schema_sql(self) -> str:
        """Get database schema SQL"""
        return """
        -- Unified Trading Database Schema
        
        CREATE TABLE IF NOT EXISTS bank_sentiment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            sentiment_score REAL,
            confidence REAL,
            news_count INTEGER,
            stage_1_score REAL,
            stage_2_score REAL,
            economic_context TEXT,
            UNIQUE(symbol, timestamp)
        );
        
        CREATE TABLE IF NOT EXISTS ml_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            prediction_type TEXT,
            predicted_value REAL,
            actual_value REAL,
            confidence_score REAL,
            model_version TEXT,
            features TEXT,
            status TEXT DEFAULT 'pending',
            UNIQUE(symbol, timestamp, prediction_type)
        );
        
        CREATE TABLE IF NOT EXISTS trading_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            signal_type TEXT,
            strength REAL,
            ml_confidence REAL,
            technical_score REAL,
            sentiment_score REAL,
            economic_regime TEXT,
            reasoning TEXT,
            executed BOOLEAN DEFAULT FALSE
        );
        
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            entry_date DATETIME NOT NULL,
            exit_date DATETIME,
            position_type TEXT,
            entry_price REAL,
            exit_price REAL,
            position_size INTEGER,
            ml_confidence REAL,
            sentiment_at_entry REAL,
            exit_reason TEXT,
            profit_loss REAL,
            return_percentage REAL
        );
        
        CREATE TABLE IF NOT EXISTS market_data_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT NOT NULL UNIQUE,
            data TEXT NOT NULL,
            expiry_date DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS ml_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            version TEXT NOT NULL,
            file_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            accuracy REAL,
            precision_score REAL,
            recall_score REAL,
            is_current BOOLEAN DEFAULT FALSE,
            model_type TEXT,
            UNIQUE(model_name, version)
        );
        
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT UNIQUE,
            published_date DATETIME,
            source TEXT,
            sentiment_score REAL,
            confidence REAL,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            category TEXT
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_bank_sentiment_symbol_time ON bank_sentiment(symbol, timestamp);
        CREATE INDEX IF NOT EXISTS idx_ml_predictions_symbol_time ON ml_predictions(symbol, timestamp);
        CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol_time ON trading_signals(symbol, timestamp);
        CREATE INDEX IF NOT EXISTS idx_positions_symbol_entry ON positions(symbol, entry_date);
        CREATE INDEX IF NOT EXISTS idx_cache_key ON market_data_cache(cache_key);
        CREATE INDEX IF NOT EXISTS idx_cache_expiry ON market_data_cache(expiry_date);
        CREATE INDEX IF NOT EXISTS idx_models_current ON ml_models(is_current);
        CREATE INDEX IF NOT EXISTS idx_news_symbol_date ON news_articles(symbol, published_date);
        """


# Global instance for easy access
data_manager = TradingDataManager()

# Convenience functions for common operations
def get_latest_sentiment_all_banks() -> Dict[str, Dict]:
    """Get latest sentiment for all bank symbols"""
    bank_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'QBE.AX', 'SUN.AX']
    result = {}
    
    for symbol in bank_symbols:
        sentiment_data = data_manager.get_latest_sentiment(symbol, hours_back=6)
        if sentiment_data:
            result[symbol] = sentiment_data[0]  # Most recent
    
    return result

def get_trading_dashboard_data() -> Dict[str, Any]:
    """Get all data needed for trading dashboard"""
    return {
        'sentiment': get_latest_sentiment_all_banks(),
        'active_signals': data_manager.get_active_signals(),
        'open_positions': data_manager.get_positions(status='open'),
        'performance': data_manager.get_performance_summary(),
        'recent_predictions': data_manager.get_ml_predictions(status='pending')
    }

def cleanup_old_data(days_to_keep: int = 30):
    """Clean up old data to maintain performance"""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    with data_manager.get_connection() as conn:
        # Clean old sentiment data
        conn.execute("DELETE FROM bank_sentiment WHERE timestamp < ?", (cutoff_date,))
        
        # Clean old completed predictions
        conn.execute("""
            DELETE FROM ml_predictions 
            WHERE timestamp < ? AND status = 'completed'
        """, (cutoff_date,))
        
        # Clean old executed signals
        conn.execute("""
            DELETE FROM trading_signals 
            WHERE timestamp < ? AND executed = TRUE
        """, (cutoff_date,))
        
        # Clean old news articles
        conn.execute("DELETE FROM news_articles WHERE published_date < ?", (cutoff_date,))
        
        # Clean expired cache
        data_manager.cleanup_expired_cache()
        
        conn.commit()
        
    logger.info(f"Cleaned up data older than {days_to_keep} days")
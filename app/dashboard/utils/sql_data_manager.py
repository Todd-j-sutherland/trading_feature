"""
SQL-First Dashboard Data Manager
Replaces JSON file-based data loading with direct SQL queries for consistency and reliability
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter
import logging

logger = logging.getLogger(__name__)

class SQLDashboardManager:
    """Direct SQL-based data manager for dashboard - eliminates JSON file inconsistencies"""
    
    def __init__(self, db_path: str = "data/ml_models/training_data.db"):
        self.db_path = Path(db_path)
        self.connection = None
        
        # Verify database exists
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        logger.info(f"SQLDashboardManager initialized with database: {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory for dict-like access"""
        if self.connection is None or self.connection.total_changes == -1:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def get_recent_predictions(self, days_back: int = 7, symbols: List[str] = None) -> List[Dict]:
        """
        Get recent predictions directly from SQL database
        This replaces the unreliable JSON prediction_history.json file
        """
        conn = self.get_connection()
        
        # Build query
        base_query = """
        SELECT 
            'LIVE_DB_' || symbol || '_' || strftime('%Y%m%d_%H%M%S', timestamp) as id,
            timestamp,
            symbol,
            sentiment_score,
            confidence,
            news_count,
            reddit_sentiment,
            event_score,
            technical_score,
            ml_features,
            CASE 
                WHEN sentiment_score > 0.05 THEN 'BUY'
                WHEN sentiment_score < -0.05 THEN 'SELL' 
                ELSE 'HOLD'
            END as signal,
            COALESCE(status, 'pending') as status,
            actual_outcome
        FROM sentiment_features 
        WHERE timestamp >= date('now', '-{} days')
        """.format(days_back)
        
        if symbols:
            placeholders = ','.join('?' for _ in symbols)
            base_query += f" AND symbol IN ({placeholders})"
        
        base_query += " ORDER BY timestamp DESC"
        
        try:
            if symbols:
                cursor = conn.execute(base_query, symbols)
            else:
                cursor = conn.execute(base_query)
            
            predictions = []
            for row in cursor.fetchall():
                # Convert to dashboard format
                prediction_record = {
                    "id": row['id'],
                    "timestamp": row['timestamp'],
                    "symbol": row['symbol'],
                    "prediction": {
                        "signal": row['signal'],
                        "confidence": float(row['confidence'] or 0),
                        "sentiment_score": float(row['sentiment_score'] or 0),
                        "pattern_strength": abs(float(row['sentiment_score'] or 0)) * 1.5,
                        "ml_features": row['ml_features']
                    },
                    "features": {
                        "news_count": int(row['news_count'] or 0),
                        "reddit_sentiment": float(row['reddit_sentiment'] or 0),
                        "event_score": float(row['event_score'] or 0),
                        "technical_score": float(row['technical_score'] or 0)
                    },
                    "actual_outcome": row["actual_outcome"] if "actual_outcome" in row.keys() else None,
                    "status": row['status'],
                    "data_source": "live_database"
                }
                predictions.append(prediction_record)
            
            logger.info(f"Retrieved {len(predictions)} predictions from database")
            return predictions
            
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving predictions: {e}")
            return []
    
    def get_today_predictions(self) -> List[Dict]:
        """Get today's predictions specifically"""
        conn = self.get_connection()
        
        query = """
        SELECT 
            symbol,
            timestamp,
            sentiment_score,
            confidence,
            news_count,
            CASE 
                WHEN sentiment_score > 0.05 THEN 'BUY'
                WHEN sentiment_score < -0.05 THEN 'SELL' 
                ELSE 'HOLD'
            END as signal
        FROM sentiment_features 
        WHERE DATE(timestamp) = DATE('now')
        ORDER BY timestamp DESC
        """
        
        try:
            cursor = conn.execute(query)
            results = cursor.fetchall()
            
            predictions = []
            for row in results:
                pred = {
                    "date": row['timestamp'][:10],
                    "time": row['timestamp'][11:16], 
                    "symbol": row['symbol'],
                    "signal": row['signal'],
                    "confidence": f"{row['confidence']:.1%}",
                    "sentiment": f"{row['sentiment_score']:+.3f}",
                    "status": row["status"],
                    "news_count": row['news_count']
                }
                predictions.append(pred)
            
            return predictions
            
        except sqlite3.Error as e:
            logger.error(f"Database error getting today's predictions: {e}")
            return []
    
    def get_confidence_distribution(self, days_back: int = 7) -> Dict:
        """Get confidence value distribution for quality analysis"""
        conn = self.get_connection()
        
        query = """
        SELECT 
            confidence,
            COUNT(*) as count,
            symbol,
            DATE(timestamp) as date
        FROM sentiment_features 
        WHERE timestamp >= date('now', '-{} days')
        GROUP BY confidence, symbol, DATE(timestamp)
        ORDER BY timestamp DESC
        """.format(days_back)
        
        try:
            cursor = conn.execute(query)
            results = cursor.fetchall()
            
            # Analyze confidence diversity
            confidence_values = [row['confidence'] for row in results]
            unique_confidences = len(set(confidence_values))
            
            return {
                "total_records": len(results),
                "unique_confidence_values": unique_confidences,
                "confidence_range": {
                    "min": min(confidence_values) if confidence_values else 0,
                    "max": max(confidence_values) if confidence_values else 0
                },
                "distribution": dict(Counter(confidence_values)),
                "quality_score": "GOOD" if unique_confidences > 3 else "POOR" if unique_confidences == 1 else "FAIR"
            }
            
        except sqlite3.Error as e:
            logger.error(f"Database error analyzing confidence: {e}")
            return {"error": str(e)}
    
    def get_prediction_timeline(self, symbol: str = None, hours_back: int = 24) -> List[Dict]:
        """Get prediction timeline for trend analysis"""
        conn = self.get_connection()
        
        base_query = """
        SELECT 
            timestamp,
            symbol,
            sentiment_score,
            confidence,
            news_count
        FROM sentiment_features 
        WHERE timestamp >= datetime('now', '-{} hours')
        """.format(hours_back)
        
        if symbol:
            base_query += " AND symbol = ?"
            params = (symbol,)
        else:
            params = ()
        
        base_query += " ORDER BY timestamp ASC"
        
        try:
            cursor = conn.execute(base_query, params)
            results = cursor.fetchall()
            
            timeline = []
            for row in results:
                timeline.append({
                    "timestamp": row['timestamp'],
                    "symbol": row['symbol'],
                    "sentiment": row['sentiment_score'],
                    "confidence": row['confidence'],
                    "news_count": row['news_count']
                })
            
            return timeline
            
        except sqlite3.Error as e:
            logger.error(f"Database error getting timeline: {e}")
            return []
    
    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics"""
        conn = self.get_connection()
        
        try:
            # Total records
            total_records = conn.execute("SELECT COUNT(*) FROM sentiment_features").fetchone()[0]
            
            # Date range
            date_range = conn.execute("""
                SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest 
                FROM sentiment_features
            """).fetchone()
            
            # Today's records
            today_count = conn.execute("""
                SELECT COUNT(*) FROM sentiment_features 
                WHERE DATE(timestamp) = DATE('now')
            """).fetchone()[0]
            
            # Symbol distribution
            symbol_dist = conn.execute("""
                SELECT symbol, COUNT(*) as count 
                FROM sentiment_features 
                GROUP BY symbol 
                ORDER BY count DESC
            """).fetchall()
            
            # Recent activity (last 24 hours)
            recent_activity = conn.execute("""
                SELECT COUNT(*) FROM sentiment_features 
                WHERE timestamp >= datetime('now', '-24 hours')
            """).fetchone()[0]
            
            return {
                "total_records": total_records,
                "date_range": {
                    "earliest": date_range['earliest'],
                    "latest": date_range['latest']
                },
                "today_records": today_count,
                "recent_activity_24h": recent_activity,
                "symbol_distribution": {row['symbol']: row['count'] for row in symbol_dist},
                "data_quality": "LIVE_DATABASE" if recent_activity > 0 else "STALE"
            }
            
        except sqlite3.Error as e:
            logger.error(f"Database error getting stats: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None


class DashboardDataManagerSQL:
    """Enhanced dashboard data manager using SQL as primary source"""
    
    def __init__(self):
        self.sql_manager = SQLDashboardManager()
        logger.info("DashboardDataManagerSQL initialized - SQL-first architecture active")
    
    def load_sentiment_data(self, symbols: List[str] = None) -> Dict[str, List[Dict]]:
        """
        Load sentiment data directly from SQL database
        This replaces the old JSON file-based loading
        """
        if symbols is None:
            symbols = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
        
        # Get recent predictions from SQL
        predictions = self.sql_manager.get_recent_predictions(days_back=7, symbols=symbols)
        
        # Group by symbol
        sentiment_data = {}
        for symbol in symbols:
            symbol_predictions = [p for p in predictions if p['symbol'] == symbol]
            sentiment_data[symbol] = symbol_predictions
        
        return sentiment_data
    
    def get_latest_analysis(self, data: List[Dict]) -> Dict:
        """Get the most recent analysis from the data"""
        if not data:
            return {}
        
        # Sort by timestamp and get latest
        sorted_data = sorted(data, key=lambda x: x.get('timestamp', ''), reverse=True)
        return sorted_data[0] if sorted_data else {}
    
    def get_prediction_log(self, days_back: int = 30) -> List[Dict]:
        """Get prediction log for dashboard performance tracking"""
        return self.sql_manager.get_recent_predictions(days_back=days_back)
    
    def get_data_quality_report(self) -> Dict:
        """Get comprehensive data quality report"""
        stats = self.sql_manager.get_database_stats()
        confidence_analysis = self.sql_manager.get_confidence_distribution()
        
        return {
            "database_stats": stats,
            "confidence_analysis": confidence_analysis,
            "data_source": "SQL_DATABASE",
            "reliability": "HIGH" if stats.get("recent_activity_24h", 0) > 0 else "LOW"
        }


def create_sql_migration_script():
    """Create script to migrate from JSON to SQL-first dashboard"""
    
    migration_script = '''
# Migration from JSON-based to SQL-based dashboard
# This script updates the dashboard to use SQL as the primary data source

## Step 1: Update dashboard imports
# Replace: from app.dashboard.utils.data_manager import DataManager
# With:    from app.dashboard.utils.sql_data_manager import DashboardDataManagerSQL

## Step 2: Update dashboard initialization
# Replace: self.data_manager = DataManager()  
# With:    self.data_manager = DashboardDataManagerSQL()

## Step 3: Data loading now uses SQL directly
# The same method calls (load_sentiment_data, get_latest_analysis) work
# But now they query the live SQL database instead of stale JSON files

## Benefits:
# ✅ Single source of truth (SQL database)
# ✅ ACID compliance and consistency  
# ✅ No more duplicate/stale data issues
# ✅ Real-time data from evening routine
# ✅ Better performance with SQL indexes
# ✅ Automated data validation
'''
    
    return migration_script


if __name__ == "__main__":
    # Test the SQL data manager
    sql_manager = SQLDashboardManager()
    
    print("🔍 SQL DATABASE ANALYSIS")
    print("=" * 50)
    
    # Get database stats
    stats = sql_manager.get_database_stats()
    print(f"Total records: {stats['total_records']}")
    print(f"Latest data: {stats['date_range']['latest']}")
    print(f"Today's records: {stats['today_records']}")
    
    # Get today's predictions
    today_preds = sql_manager.get_today_predictions()
    print(f"\nToday's predictions: {len(today_preds)}")
    
    for pred in today_preds[:5]:
        print(f"  {pred['time']} | {pred['symbol']:8} | {pred['signal']:4} | {pred['confidence']:>6}")
    
    # Get confidence analysis
    conf_analysis = sql_manager.get_confidence_distribution()
    print(f"\nConfidence analysis:")
    print(f"  Unique values: {conf_analysis['unique_confidence_values']}")
    print(f"  Quality: {conf_analysis['quality_score']}")
    
    sql_manager.close()

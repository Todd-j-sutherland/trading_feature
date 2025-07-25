#!/usr/bin/env python3
"""
Test script for individual dashboard components
This allows testing each section independently as per requirements
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Database configuration
DATABASE_PATH = "data/ml_models/training_data.db"
ASX_BANKS = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "MQG.AX", "SUN.AX", "QBE.AX"]

class ComponentTestError(Exception):
    """Custom exception for component testing"""
    pass

def test_database_connection():
    """Test database connectivity"""
    print("🔍 Testing Database Connection...")
    
    db_path = Path(DATABASE_PATH)
    if not db_path.exists():
        raise ComponentTestError(f"Database not found: {DATABASE_PATH}")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        
        # Test basic query
        cursor = conn.execute("SELECT COUNT(*) as count FROM sentiment_features")
        result = cursor.fetchone()
        
        print(f"✅ Database connected successfully")
        print(f"   Total sentiment records: {result['count']}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        raise ComponentTestError(f"Database connection failed: {e}")

def test_ml_performance_component():
    """Test ML performance metrics component independently"""
    print("\n🤖 Testing ML Performance Component...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # Test ML metrics query
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_predictions,
                AVG(confidence) as avg_confidence,
                COUNT(CASE WHEN sentiment_score > 0.05 THEN 1 END) as buy_signals,
                COUNT(CASE WHEN sentiment_score < -0.05 THEN 1 END) as sell_signals
            FROM sentiment_features 
            WHERE timestamp >= date('now', '-7 days')
        """)
        
        row = cursor.fetchone()
        
        if not row or row['total_predictions'] == 0:
            raise ComponentTestError("No prediction data found in the last 7 days")
        
        print(f"✅ ML Performance Component Test Passed")
        print(f"   Predictions (7d): {row['total_predictions']}")
        print(f"   Average Confidence: {row['avg_confidence']:.1%}")
        print(f"   Buy Signals: {row['buy_signals']}")
        print(f"   Sell Signals: {row['sell_signals']}")
        
        return {
            'total_predictions': row['total_predictions'],
            'avg_confidence': float(row['avg_confidence'] or 0),
            'buy_signals': row['buy_signals'],
            'sell_signals': row['sell_signals']
        }
        
    except sqlite3.Error as e:
        raise ComponentTestError(f"ML Performance component failed: {e}")
    finally:
        conn.close()

def test_sentiment_component():
    """Test current sentiment scores component independently"""
    print("\n📊 Testing Sentiment Component...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # Test sentiment query for each bank
        cursor = conn.execute("""
            SELECT 
                s1.symbol,
                s1.timestamp,
                s1.sentiment_score,
                s1.confidence,
                s1.news_count,
                CASE 
                    WHEN s1.sentiment_score > 0.05 THEN 'BUY'
                    WHEN s1.sentiment_score < -0.05 THEN 'SELL'
                    ELSE 'HOLD'
                END as signal
            FROM sentiment_features s1
            INNER JOIN (
                SELECT symbol, MAX(timestamp) as max_timestamp
                FROM sentiment_features
                WHERE symbol IN ({})
                GROUP BY symbol
            ) s2 ON s1.symbol = s2.symbol AND s1.timestamp = s2.max_timestamp
            ORDER BY s1.symbol
        """.format(','.join('?' * len(ASX_BANKS))), ASX_BANKS)
        
        results = cursor.fetchall()
        
        if not results:
            raise ComponentTestError("No current sentiment data found for any banks")
        
        print(f"✅ Sentiment Component Test Passed")
        print(f"   Banks with data: {len(results)}")
        
        for row in results:
            signal_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}[row['signal']]
            print(f"   {row['symbol']}: {signal_emoji} {row['signal']} "
                  f"(Sentiment: {row['sentiment_score']:+.4f}, "
                  f"Confidence: {row['confidence']:.1%})")
        
        return results
        
    except sqlite3.Error as e:
        raise ComponentTestError(f"Sentiment component failed: {e}")
    finally:
        conn.close()

def test_ml_features_component():
    """Test ML feature analysis component independently"""
    print("\n🔍 Testing ML Features Component...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # Test feature analysis query
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_records,
                AVG(CASE WHEN news_count > 0 THEN 1.0 ELSE 0.0 END) as news_usage,
                AVG(CASE WHEN reddit_sentiment IS NOT NULL THEN 1.0 ELSE 0.0 END) as reddit_usage,
                AVG(CASE WHEN event_score IS NOT NULL THEN 1.0 ELSE 0.0 END) as event_usage,
                AVG(CASE WHEN technical_score IS NOT NULL THEN 1.0 ELSE 0.0 END) as technical_usage,
                AVG(news_count) as avg_news_count
            FROM sentiment_features 
            WHERE timestamp >= date('now', '-7 days')
        """)
        
        row = cursor.fetchone()
        
        if not row or row['total_records'] == 0:
            raise ComponentTestError("No ML feature data found")
        
        print(f"✅ ML Features Component Test Passed")
        print(f"   Records analyzed: {row['total_records']}")
        print(f"   News usage: {row['news_usage']*100:.1f}%")
        print(f"   Reddit usage: {row['reddit_usage']*100:.1f}%")
        print(f"   Event usage: {row['event_usage']*100:.1f}%")
        print(f"   Technical usage: {row['technical_usage']*100:.1f}%")
        print(f"   Avg news count: {row['avg_news_count']:.1f}")
        
        return {
            'total_records': row['total_records'],
            'news_usage': float(row['news_usage'] or 0) * 100,
            'reddit_usage': float(row['reddit_usage'] or 0) * 100,
            'event_usage': float(row['event_usage'] or 0) * 100,
            'technical_usage': float(row['technical_usage'] or 0) * 100,
            'avg_news_count': float(row['avg_news_count'] or 0)
        }
        
    except sqlite3.Error as e:
        raise ComponentTestError(f"ML Features component failed: {e}")
    finally:
        conn.close()

def test_technical_analysis_component():
    """Test technical analysis component independently"""
    print("\n📈 Testing Technical Analysis Component...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # Test technical analysis query
        cursor = conn.execute("""
            SELECT 
                s1.symbol,
                s1.technical_score,
                s1.event_score,
                s1.reddit_sentiment
            FROM sentiment_features s1
            INNER JOIN (
                SELECT symbol, MAX(timestamp) as max_timestamp
                FROM sentiment_features
                WHERE symbol IN ({})
                GROUP BY symbol
            ) s2 ON s1.symbol = s2.symbol AND s1.timestamp = s2.max_timestamp
            ORDER BY s1.symbol
        """.format(','.join('?' * len(ASX_BANKS))), ASX_BANKS)
        
        results = cursor.fetchall()
        
        if not results:
            raise ComponentTestError("No technical analysis data found")
        
        print(f"✅ Technical Analysis Component Test Passed")
        print(f"   Banks analyzed: {len(results)}")
        
        for row in results:
            print(f"   {row['symbol']}: Technical={row['technical_score']:.3f}, "
                  f"Event={row['event_score']:.3f}, "
                  f"Reddit={row['reddit_sentiment']:.3f}")
        
        return results
        
    except sqlite3.Error as e:
        raise ComponentTestError(f"Technical Analysis component failed: {e}")
    finally:
        conn.close()

def test_all_components():
    """Run all component tests"""
    print("🧪 DASHBOARD COMPONENT TESTS")
    print("=" * 50)
    
    try:
        # Test database connection
        test_database_connection()
        
        # Test each component independently
        ml_metrics = test_ml_performance_component()
        sentiment_data = test_sentiment_component()
        feature_analysis = test_ml_features_component()
        technical_data = test_technical_analysis_component()
        
        print("\n✅ ALL COMPONENT TESTS PASSED")
        print("=" * 50)
        print("Dashboard is ready to run!")
        print(f"Run: streamlit run dashboard.py")
        
        return True
        
    except ComponentTestError as e:
        print(f"\n❌ COMPONENT TEST FAILED: {e}")
        print("Please fix the issue before running the dashboard.")
        return False
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_all_components()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test script to verify dashboard fixes
"""

import sqlite3
import pandas as pd
import sys
from datetime import datetime

# Add current directory to path for imports
sys.path.append('.')

def test_database_connection():
    """Test database connection and table structure"""
    try:
        conn = sqlite3.connect('data/ml_models/enhanced_training_data.db')
        
        # Check tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"✅ Database connected. Tables: {tables}")
        
        # Check data availability
        cursor.execute("SELECT COUNT(*) FROM enhanced_features")
        feature_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        outcome_count = cursor.fetchone()[0]
        
        print(f"📊 Features: {feature_count}, Outcomes: {outcome_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_prediction_timeline_query():
    """Test the corrected prediction timeline query"""
    try:
        conn = sqlite3.connect('data/ml_models/enhanced_training_data.db')
        
        query = """
            SELECT 
                ef.timestamp,
                ef.symbol,
                CASE 
                    WHEN ef.rsi < 30 THEN 'BUY'
                    WHEN ef.rsi > 70 THEN 'SELL'
                    ELSE 'HOLD'
                END as signal,
                ef.rsi,
                ef.sentiment_score,
                ef.rsi as technical_score,
                eo.return_pct as actual_outcome,
                CASE 
                    WHEN eo.return_pct IS NOT NULL THEN 'COMPLETED'
                    ELSE 'PENDING'
                END as status,
                CASE 
                    WHEN eo.return_pct IS NOT NULL THEN
                        CASE 
                            WHEN (ef.rsi < 30 AND eo.return_pct > 0) OR 
                                 (ef.rsi > 70 AND eo.return_pct < 0) OR
                                 (ef.rsi BETWEEN 30 AND 70 AND ABS(eo.return_pct) < 0.5) 
                            THEN 'CORRECT' 
                            ELSE 'WRONG' 
                        END
                    ELSE 'PENDING'
                END as accuracy,
                ef.news_count,
                ef.confidence as sentiment_confidence
            FROM enhanced_features ef
            LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
            WHERE ef.timestamp >= datetime('now', '-7 days')
            ORDER BY ef.timestamp DESC
            LIMIT 50
        """
        
        cursor = conn.execute(query)
        results = cursor.fetchall()
        
        print(f"✅ Timeline query successful: {len(results)} rows")
        
        if results:
            # Show sample data
            print("📈 Sample data:")
            for i, row in enumerate(results[:3]):
                print(f"   {i+1}. {row[1]} - {row[2]} (RSI: {row[3]:.1f}, Sentiment: {row[4]:.3f})")
        
        conn.close()
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Timeline query error: {e}")
        return False

def test_enhanced_confidence():
    """Test enhanced confidence calculation"""
    try:
        from enhance_confidence_calculation import get_enhanced_confidence
        
        # Test data
        test_cases = [
            {"rsi": 25, "sentiment": {"news_count": 15, "confidence": 0.8}, "symbol": "CBA.AX"},
            {"rsi": 65, "sentiment": {"news_count": 10, "confidence": 0.6}, "symbol": "WBC.AX"},
            {"rsi": 80, "sentiment": {"news_count": 8, "confidence": 0.7}, "symbol": "ANZ.AX"}
        ]
        
        print("✅ Enhanced confidence test:")
        for case in test_cases:
            sentiment_data = {
                'news_count': case['sentiment']['news_count'],
                'confidence': case['sentiment']['confidence'],
                'method_breakdown': {},
                'quality_assessment': {'overall_grade': 'B'}
            }
            
            confidence = get_enhanced_confidence(case['rsi'], sentiment_data, case['symbol'])
            print(f"   {case['symbol']}: RSI {case['rsi']:.1f} → Confidence {confidence:.1%}")
            
        return True
        
    except Exception as e:
        print(f"❌ Enhanced confidence error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Dashboard Fix Validation")
    print("=" * 40)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Timeline Query", test_prediction_timeline_query), 
        ("Enhanced Confidence", test_enhanced_confidence)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 40)
    print("📋 Test Summary:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False
    
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n💡 Dashboard should now work correctly!")
        print("   Run: streamlit run dashboard.py")
    else:
        print("\n🔧 Fix the failing tests before running dashboard")

if __name__ == "__main__":
    main()

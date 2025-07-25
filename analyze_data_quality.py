#!/usr/bin/env python3
"""
Data Quality Analysis - Deep Investigation

This script identifies data quality issues including:
- Suspicious confidence patterns
- Duplicate/identical values
- Missing Reddit sentiment data
- Empty model_performance table
"""

import sqlite3
import pandas as pd
from collections import Counter
import numpy as np
from datetime import datetime

def analyze_confidence_anomalies():
    """Analyze confidence value patterns for anomalies"""
    
    print("🔍 CONFIDENCE PATTERN ANALYSIS")
    print("=" * 50)
    
    conn = sqlite3.connect("data/ml_models/training_data.db")
    
    # Get confidence distribution
    df = pd.read_sql_query("""
        SELECT symbol, confidence, COUNT(*) as count,
               MIN(timestamp) as first_seen,
               MAX(timestamp) as last_seen
        FROM sentiment_features 
        GROUP BY symbol, confidence 
        ORDER BY symbol, confidence
    """, conn)
    
    print("📊 Confidence Distribution by Symbol:")
    for symbol in df['symbol'].unique():
        symbol_data = df[df['symbol'] == symbol]
        print(f"\n{symbol}:")
        for _, row in symbol_data.iterrows():
            print(f"   {row['confidence']:.3f}: {row['count']} times ({row['first_seen'][:10]} to {row['last_seen'][:10]})")
    
    # Check for suspiciously high repetition
    print("\n🚨 SUSPICIOUS PATTERNS:")
    for _, row in df.iterrows():
        if row['count'] > 50:  # More than 50 identical confidence values is suspicious
            print(f"❌ {row['symbol']}: confidence {row['confidence']:.3f} appears {row['count']} times (SUSPICIOUS)")
    
    # Check confidence variance by symbol
    print("\n📈 CONFIDENCE VARIANCE ANALYSIS:")
    variance_df = pd.read_sql_query("""
        SELECT symbol, 
               COUNT(DISTINCT confidence) as unique_confidences,
               AVG(confidence) as avg_confidence,
               MIN(confidence) as min_confidence,
               MAX(confidence) as max_confidence,
               (MAX(confidence) - MIN(confidence)) as confidence_range
        FROM sentiment_features 
        GROUP BY symbol
    """, conn)
    
    for _, row in variance_df.iterrows():
        print(f"{row['symbol']}: {row['unique_confidences']} unique values, range: {row['confidence_range']:.3f}")
        if row['unique_confidences'] <= 3:
            print(f"   🚨 WARNING: Only {row['unique_confidences']} unique confidence values!")
    
    conn.close()

def analyze_duplicate_values():
    """Analyze for duplicate/identical values that shouldn't be identical"""
    
    print("\n🔍 DUPLICATE VALUES ANALYSIS")
    print("=" * 50)
    
    conn = sqlite3.connect("data/ml_models/training_data.db")
    
    # Check for identical sentiment scores
    print("📊 Sentiment Score Duplicates:")
    df = pd.read_sql_query("""
        SELECT sentiment_score, COUNT(*) as count,
               GROUP_CONCAT(DISTINCT symbol) as symbols
        FROM sentiment_features 
        GROUP BY sentiment_score 
        HAVING COUNT(*) > 5
        ORDER BY count DESC
        LIMIT 10
    """, conn)
    
    for _, row in df.iterrows():
        print(f"   Score {row['sentiment_score']:.6f}: {row['count']} times across symbols: {row['symbols']}")
        if row['count'] > 10:
            print(f"      🚨 SUSPICIOUS: {row['count']} identical sentiment scores")
    
    # Check for identical news counts
    print("\n📰 News Count Patterns:")
    news_df = pd.read_sql_query("""
        SELECT news_count, COUNT(*) as count,
               GROUP_CONCAT(DISTINCT symbol) as symbols
        FROM sentiment_features 
        GROUP BY news_count 
        ORDER BY count DESC
        LIMIT 10
    """, conn)
    
    for _, row in news_df.iterrows():
        print(f"   News count {row['news_count']}: {row['count']} times")
    
    conn.close()

def analyze_reddit_sentiment():
    """Analyze Reddit sentiment data quality"""
    
    print("\n🔍 REDDIT SENTIMENT ANALYSIS")
    print("=" * 50)
    
    conn = sqlite3.connect("data/ml_models/training_data.db")
    
    # Check Reddit sentiment distribution
    df = pd.read_sql_query("""
        SELECT reddit_sentiment, COUNT(*) as count
        FROM sentiment_features 
        GROUP BY reddit_sentiment 
        ORDER BY count DESC
    """, conn)
    
    print("📊 Reddit Sentiment Distribution:")
    for _, row in df.iterrows():
        print(f"   {row['reddit_sentiment']}: {row['count']} records")
    
    # Check if all values are 0
    zero_count = df[df['reddit_sentiment'] == 0.0]['count'].sum() if len(df[df['reddit_sentiment'] == 0.0]) > 0 else 0
    total_count = df['count'].sum()
    
    if zero_count == total_count:
        print(f"🚨 CRITICAL: ALL {total_count} Reddit sentiment values are 0.0!")
        print("   This indicates Reddit sentiment feature is not working")
    
    conn.close()

def analyze_model_performance_table():
    """Analyze model_performance table"""
    
    print("\n🔍 MODEL PERFORMANCE TABLE ANALYSIS")
    print("=" * 50)
    
    conn = sqlite3.connect("data/ml_models/training_data.db")
    
    # Check if table has any data
    cursor = conn.execute("SELECT COUNT(*) as count FROM model_performance")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("🚨 ISSUE: model_performance table is completely empty")
        print("   This table should contain ML model evaluation metrics")
        
        # Check if we have recent ML predictions that should have triggered performance updates
        cursor = conn.execute("""
            SELECT COUNT(*) as recent_predictions 
            FROM sentiment_features 
            WHERE timestamp >= date('now', '-7 days')
        """)
        recent = cursor.fetchone()[0]
        
        print(f"   Recent predictions: {recent}")
        if recent > 0:
            print("   🔧 RECOMMENDATION: Model performance tracking needs to be implemented")
    else:
        print(f"✅ Table has {count} records")
    
    conn.close()

def analyze_temporal_patterns():
    """Analyze temporal patterns that might indicate data generation issues"""
    
    print("\n🔍 TEMPORAL PATTERN ANALYSIS")
    print("=" * 50)
    
    conn = sqlite3.connect("data/ml_models/training_data.db")
    
    # Check for patterns in timestamps
    df = pd.read_sql_query("""
        SELECT symbol, confidence, sentiment_score, timestamp,
               LAG(timestamp) OVER (PARTITION BY symbol ORDER BY timestamp) as prev_timestamp
        FROM sentiment_features 
        WHERE timestamp >= date('now', '-1 day')
        ORDER BY timestamp DESC
        LIMIT 20
    """, conn)
    
    print("📅 Recent Temporal Patterns (Last 20 records):")
    for _, row in df.iterrows():
        print(f"   {row['timestamp'][:19]} | {row['symbol']} | conf: {row['confidence']:.3f} | sent: {row['sentiment_score']:.6f}")
    
    # Check for exact timestamp duplicates
    dup_df = pd.read_sql_query("""
        SELECT timestamp, COUNT(*) as count
        FROM sentiment_features 
        GROUP BY timestamp 
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 5
    """, conn)
    
    if len(dup_df) > 0:
        print(f"\n🚨 DUPLICATE TIMESTAMPS FOUND:")
        for _, row in dup_df.iterrows():
            print(f"   {row['timestamp']}: {row['count']} records")
    
    conn.close()

def generate_data_quality_report():
    """Generate comprehensive data quality report"""
    
    print("\n📋 DATA QUALITY SUMMARY REPORT")
    print("=" * 60)
    
    conn = sqlite3.connect("data/ml_models/training_data.db")
    
    # Overall statistics
    stats = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT symbol) as unique_symbols,
            COUNT(DISTINCT confidence) as unique_confidences,
            MIN(timestamp) as earliest_record,
            MAX(timestamp) as latest_record,
            AVG(confidence) as avg_confidence,
            COUNT(CASE WHEN reddit_sentiment = 0.0 THEN 1 END) as zero_reddit_count
        FROM sentiment_features
    """, conn).iloc[0]
    
    print(f"📊 OVERALL STATISTICS:")
    print(f"   Total Records: {stats['total_records']}")
    print(f"   Unique Symbols: {stats['unique_symbols']}")
    print(f"   Unique Confidence Values: {stats['unique_confidences']}")
    print(f"   Date Range: {stats['earliest_record'][:10]} to {stats['latest_record'][:10]}")
    print(f"   Average Confidence: {stats['avg_confidence']:.3f}")
    print(f"   Zero Reddit Sentiment Records: {stats['zero_reddit_count']}")
    
    # Data quality issues
    print(f"\n🚨 IDENTIFIED ISSUES:")
    
    if stats['unique_confidences'] < 10:
        print(f"   ❌ Too few unique confidence values ({stats['unique_confidences']})")
    
    if stats['zero_reddit_count'] == stats['total_records']:
        print(f"   ❌ All Reddit sentiment values are 0.0 - feature not working")
    
    # Check model performance table
    cursor = conn.execute("SELECT COUNT(*) FROM model_performance")
    perf_count = cursor.fetchone()[0]
    if perf_count == 0:
        print(f"   ❌ model_performance table is empty")
    
    print(f"\n✅ RECOMMENDATIONS:")
    print(f"   1. Investigate confidence value generation - should be more varied")
    print(f"   2. Fix Reddit sentiment data collection - all values are 0.0")
    print(f"   3. Implement model performance tracking")
    print(f"   4. Add data validation checks to prevent duplicate identical values")
    
    conn.close()

def main():
    """Main analysis function"""
    
    print("🔍 COMPREHENSIVE DATA QUALITY ANALYSIS")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        analyze_confidence_anomalies()
        analyze_duplicate_values()
        analyze_reddit_sentiment()
        analyze_model_performance_table()
        analyze_temporal_patterns()
        generate_data_quality_report()
        
        print(f"\n🎯 ANALYSIS COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

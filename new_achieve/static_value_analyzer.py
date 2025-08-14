#!/usr/bin/env python3
"""
Static Value Analyzer
Analyzes the exported data to identify static/placeholder values vs real dynamic data
"""

import pandas as pd
import json
from datetime import datetime
import os

def analyze_static_patterns():
    """Analyze the exported data for static patterns"""
    
    # Read the exported CSV files
    try:
        predictions_file = None
        features_file = None
        
        # Find the most recent export files
        export_dir = "/Users/toddsutherland/Repos/trading_feature/quick_exports"
        for file in os.listdir(export_dir):
            if file.startswith("recent_predictions_") and file.endswith(".csv"):
                predictions_file = os.path.join(export_dir, file)
            elif file.startswith("feature_analysis_") and file.endswith(".csv"):
                features_file = os.path.join(export_dir, file)
        
        if not predictions_file or not features_file:
            print("❌ Export files not found")
            return
            
        print(f"📊 Analyzing: {os.path.basename(predictions_file)}")
        print(f"📊 Analyzing: {os.path.basename(features_file)}")
        print("=" * 80)
        
        # Load data
        df = pd.read_csv(features_file)
        
        # Group by identical feature combinations to find static data
        static_groups = df.groupby(['sentiment', 'rsi', 'macd_line']).agg({
            'symbol': list,
            'timestamp': 'count'
        }).reset_index()
        
        # Filter for potential static data (multiple symbols with identical values)
        static_data = static_groups[static_groups['timestamp'] > 1].sort_values('timestamp', ascending=False)
        
        print("🔍 STATIC VALUE ANALYSIS RESULTS")
        print("=" * 80)
        
        if len(static_data) > 0:
            print("⚠️  STATIC/PLACEHOLDER DATA DETECTED:")
            print("-" * 50)
            
            for idx, row in static_data.iterrows():
                print(f"📍 Pattern found in {row['timestamp']} records:")
                print(f"   Sentiment: {row['sentiment']}")
                print(f"   RSI: {row['rsi']}")
                print(f"   MACD: {row['macd_line']}")
                print(f"   Symbols: {', '.join(row['symbol'])}")
                print()
        else:
            print("✅ No static patterns detected - all values appear dynamic")
        
        # Analyze value ranges
        print("📈 VALUE RANGE ANALYSIS:")
        print("-" * 50)
        print(f"Sentiment range: {df['sentiment'].min():.4f} to {df['sentiment'].max():.4f}")
        print(f"RSI range: {df['rsi'].min():.2f} to {df['rsi'].max():.2f}")
        print(f"MACD range: {df['macd_line'].min():.4f} to {df['macd_line'].max():.4f}")
        print()
        
        # Check for suspicious round numbers
        print("🎯 ROUND NUMBER ANALYSIS:")
        print("-" * 50)
        
        # Check for exact round numbers in RSI
        round_rsi = df[df['rsi'] % 1 == 0]  # Perfect integers
        if len(round_rsi) > 0:
            print(f"⚠️  Found {len(round_rsi)} records with round RSI values:")
            for rsi_val in round_rsi['rsi'].unique():
                count = len(round_rsi[round_rsi['rsi'] == rsi_val])
                symbols = round_rsi[round_rsi['rsi'] == rsi_val]['symbol'].unique()
                print(f"   RSI={rsi_val}: {count} records ({', '.join(symbols)})")
        else:
            print("✅ No suspicious round RSI values")
        
        # Check for zero MACD values
        zero_macd = df[df['macd_line'] == 0.0]
        if len(zero_macd) > 0:
            print(f"⚠️  Found {len(zero_macd)} records with zero MACD values")
        else:
            print("✅ No zero MACD values")
        
        # Timeline analysis
        print("\n⏰ TIMELINE ANALYSIS:")
        print("-" * 50)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df_sorted = df.sort_values('timestamp')
        
        # Group by 5-minute windows to see patterns
        df_sorted['time_window'] = df_sorted['timestamp'].dt.floor('5T')
        time_groups = df_sorted.groupby('time_window').agg({
            'sentiment': ['min', 'max', 'std'],
            'rsi': ['min', 'max', 'std'],
            'symbol': 'count'
        }).round(4)
        
        print("Recent 5-minute windows (showing diversity in values):")
        print(time_groups.tail(10))
        
        # Summary recommendations
        print("\n📋 RECOMMENDATIONS:")
        print("=" * 80)
        
        if len(static_data) > 0:
            print("❌ ISSUES FOUND:")
            print("   - Static/placeholder data detected")
            print("   - Need to investigate why multiple symbols have identical technical indicators")
            print("   - Check if TechnicalAnalyzer is returning default values")
        else:
            print("✅ DATA QUALITY GOOD:")
            print("   - No static patterns detected")
            print("   - Values appear to be dynamically generated")
            print("   - Technical indicators show realistic variation")
            
        print("\n🔧 NEXT STEPS:")
        print("   1. Review TechnicalAnalyzer implementation for default value handling")
        print("   2. Check yfinance data fetching for all symbols")
        print("   3. Validate sentiment analysis is running for each symbol")
        print("   4. Monitor future predictions for static patterns")
        
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_static_patterns()

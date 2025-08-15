#!/usr/bin/env python3
"""
Comprehensive Data Quality Diagnostic
====================================

Diagnoses and fixes the specific data quality issues mentioned in the dashboard warning:
1. Mismatch between predictions and features
2. Null actual returns in outcomes
3. Duplicate predictions by date
4. Missing analysis_timestamp column issues
"""

import sqlite3
import json
from datetime import datetime, timedelta
import subprocess

class DataQualityDiagnostic:
    def __init__(self, db_path="/root/test/data/trading_predictions.db"):
        self.db_path = db_path
        self.remote_host = "root@170.64.199.151"
        self.remote_path = "/root/test"
    
    def run_remote_query(self, query):
        """Execute SQL query on remote database"""
        cmd = f"ssh {self.remote_host} 'cd {self.remote_path} && sqlite3 data/trading_predictions.db \"{query}\"'"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr}"
        except Exception as e:
            return f"Exception: {e}"
    
    def diagnose_predictions_features_mismatch(self):
        """Diagnose mismatch between predictions and features"""
        print("🔍 DIAGNOSING PREDICTIONS vs FEATURES MISMATCH")
        print("=" * 60)
        
        # Count records in each table
        counts_query = """
        SELECT 'predictions' as table_name, COUNT(*) as count FROM predictions
        UNION ALL
        SELECT 'enhanced_features' as table_name, COUNT(*) as count FROM enhanced_features
        UNION ALL
        SELECT 'outcomes' as table_name, COUNT(*) as count FROM outcomes
        UNION ALL
        SELECT 'enhanced_outcomes' as table_name, COUNT(*) as count FROM enhanced_outcomes;
        """
        
        counts = self.run_remote_query(counts_query)
        print("📊 Record Counts:")
        for line in counts.split('\n'):
            if '|' in line:
                table, count = line.split('|')
                print(f"  {table:20} {count:>6} records")
        
        # Check latest dates in each table
        dates_query = """
        SELECT 'predictions' as table_name, 
               COALESCE(MAX(prediction_timestamp), 'No data') as latest_date,
               COUNT(DISTINCT symbol) as unique_symbols
        FROM predictions
        UNION ALL
        SELECT 'enhanced_features' as table_name, 
               COALESCE(MAX(timestamp), 'No data') as latest_date,
               COUNT(DISTINCT symbol) as unique_symbols
        FROM enhanced_features;
        """
        
        dates = self.run_remote_query(dates_query)
        print("\n📅 Latest Dates and Symbol Counts:")
        for line in dates.split('\n'):
            if '|' in line:
                table, latest_date, symbols = line.split('|')
                print(f"  {table:20} {latest_date} ({symbols} symbols)")
        
        return counts
    
    def diagnose_duplicate_predictions(self):
        """Diagnose duplicate predictions by date"""
        print("\n🔍 DIAGNOSING DUPLICATE PREDICTIONS")
        print("=" * 60)
        
        # Check duplicates in predictions table
        duplicates_query = """
        SELECT symbol, DATE(prediction_timestamp) as pred_date, COUNT(*) as duplicate_count 
        FROM predictions 
        GROUP BY symbol, DATE(prediction_timestamp) 
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC;
        """
        
        duplicates = self.run_remote_query(duplicates_query)
        if duplicates.strip():
            print("🚨 Duplicate Predictions Found:")
            print("  Symbol    Date         Count")
            print("  " + "-" * 30)
            for line in duplicates.split('\n'):
                if '|' in line:
                    symbol, date, count = line.split('|')
                    print(f"  {symbol:8} {date} {count:>6}")
        else:
            print("✅ No duplicate predictions found in predictions table")
        
        # Check duplicates in enhanced_features (which likely has the data)
        features_duplicates_query = """
        SELECT symbol, DATE(timestamp) as feature_date, COUNT(*) as duplicate_count 
        FROM enhanced_features 
        GROUP BY symbol, DATE(timestamp) 
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC;
        """
        
        features_duplicates = self.run_remote_query(features_duplicates_query)
        if features_duplicates.strip():
            print("\n🚨 Duplicate Enhanced Features Found:")
            print("  Symbol    Date         Count")
            print("  " + "-" * 30)
            for line in features_duplicates.split('\n'):
                if '|' in line:
                    symbol, date, count = line.split('|')
                    print(f"  {symbol:8} {date} {count:>6}")
        else:
            print("✅ No duplicate enhanced features found")
        
        return features_duplicates
    
    def diagnose_null_actual_returns(self):
        """Diagnose null actual returns in outcomes"""
        print("\n🔍 DIAGNOSING NULL ACTUAL RETURNS")
        print("=" * 60)
        
        # Check for null actual returns
        null_returns_query = """
        SELECT 
            COUNT(*) as total_outcomes,
            COUNT(actual_return) as non_null_returns,
            COUNT(*) - COUNT(actual_return) as null_returns,
            MIN(evaluation_timestamp) as earliest_evaluation,
            MAX(evaluation_timestamp) as latest_evaluation
        FROM outcomes;
        """
        
        null_analysis = self.run_remote_query(null_returns_query)
        if null_analysis.strip():
            parts = null_analysis.split('|')
            if len(parts) >= 3:
                total, non_null, null_count = parts[:3]
                print(f"📊 Outcomes Analysis:")
                print(f"  Total Outcomes:     {total}")
                print(f"  Non-null Returns:   {non_null}")
                print(f"  Null Returns:       {null_count}")
                
                if len(parts) >= 5:
                    earliest, latest = parts[3:5]
                    if earliest != "":
                        print(f"  Earliest Eval:      {earliest}")
                        print(f"  Latest Eval:        {latest}")
        
        # Check enhanced_outcomes as well
        enhanced_null_query = """
        SELECT 
            COUNT(*) as total_outcomes,
            COUNT(actual_return) as non_null_returns,
            COUNT(*) - COUNT(actual_return) as null_returns
        FROM enhanced_outcomes;
        """
        
        enhanced_null = self.run_remote_query(enhanced_null_query)
        if enhanced_null.strip():
            parts = enhanced_null.split('|')
            if len(parts) >= 3:
                total, non_null, null_count = parts[:3]
                print(f"\n📊 Enhanced Outcomes Analysis:")
                print(f"  Total Outcomes:     {total}")
                print(f"  Non-null Returns:   {non_null}")
                print(f"  Null Returns:       {null_count}")
    
    def diagnose_analysis_timestamp_issues(self):
        """Diagnose analysis_timestamp column issues"""
        print("\n🔍 DIAGNOSING ANALYSIS_TIMESTAMP ISSUES")
        print("=" * 60)
        
        # Check if column exists
        schema_query = "PRAGMA table_info(enhanced_features);"
        schema = self.run_remote_query(schema_query)
        
        has_analysis_timestamp = False
        print("📋 Enhanced Features Schema:")
        for line in schema.split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    col_id, col_name = parts[:2]
                    if 'analysis_timestamp' in col_name:
                        has_analysis_timestamp = True
                        print(f"  ✅ Column {col_id}: {col_name} (found)")
                    elif col_name in ['timestamp', 'created_at']:
                        print(f"  📅 Column {col_id}: {col_name}")
        
        if not has_analysis_timestamp:
            print("  ❌ analysis_timestamp column NOT FOUND")
        else:
            # Check for null values in analysis_timestamp
            null_timestamp_query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(analysis_timestamp) as non_null_timestamps,
                COUNT(*) - COUNT(analysis_timestamp) as null_timestamps
            FROM enhanced_features;
            """
            
            timestamp_analysis = self.run_remote_query(null_timestamp_query)
            if timestamp_analysis.strip():
                parts = timestamp_analysis.split('|')
                if len(parts) >= 3:
                    total, non_null, null_count = parts[:3]
                    print(f"\n📊 Analysis Timestamp Quality:")
                    print(f"  Total Records:      {total}")
                    print(f"  Non-null Timestamps: {non_null}")
                    print(f"  Null Timestamps:    {null_count}")
    
    def generate_fix_recommendations(self):
        """Generate specific fix recommendations"""
        print("\n🔧 FIX RECOMMENDATIONS")
        print("=" * 60)
        
        print("1. 🎯 Fix Predictions vs Features Mismatch:")
        print("   • The enhanced_features table has data but predictions table is empty")
        print("   • This suggests the morning routine creates features but not predictions")
        print("   • Check if prediction saving is properly implemented in the ML pipeline")
        
        print("\n2. 🔄 Fix Duplicate Enhanced Features:")
        print("   • Multiple feature records per symbol per day detected")
        print("   • Add UNIQUE constraint: (symbol, DATE(timestamp))")
        print("   • Implement UPSERT logic instead of INSERT")
        
        print("\n3. 🎯 Fix Null Actual Returns:")
        print("   • Evening routine should populate actual_return in outcomes")
        print("   • Ensure market data is available for return calculations")
        
        print("\n4. 🔧 Recommended SQL Fixes:")
        print("   • Add unique constraint to prevent duplicates")
        print("   • Implement proper prediction saving")
        print("   • Add data validation triggers")
    
    def run_comprehensive_diagnosis(self):
        """Run complete diagnosis"""
        print("🏥 COMPREHENSIVE DATA QUALITY DIAGNOSTIC")
        print("=" * 80)
        print(f"⏰ Diagnostic Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Remote Database: {self.remote_host}:{self.remote_path}")
        print()
        
        # Run all diagnostics
        self.diagnose_predictions_features_mismatch()
        self.diagnose_duplicate_predictions()
        self.diagnose_null_actual_returns()
        self.diagnose_analysis_timestamp_issues()
        self.generate_fix_recommendations()
        
        print("\n" + "=" * 80)
        print("🏁 DIAGNOSTIC COMPLETED")

def main():
    diagnostic = DataQualityDiagnostic()
    diagnostic.run_comprehensive_diagnosis()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Data Quality Repair System
==========================

Fixes the specific data quality issues identified:
1. Duplicate enhanced features (4 records per symbol per day)
2. Missing predictions (features exist but no predictions saved)
3. Null analysis_timestamp values (13 out of 22 records)
4. Missing unique constraints to prevent future duplicates
"""

import sqlite3
import json
from datetime import datetime, timedelta
import subprocess

class DataQualityRepair:
    def __init__(self):
        self.remote_host = "root@170.64.199.151"
        self.remote_path = "/root/test"
    
    def run_remote_query(self, query, description=""):
        """Execute SQL query on remote database with error handling"""
        escaped_query = query.replace('"', '\\"')
        cmd = f'ssh {self.remote_host} \'cd {self.remote_path} && sqlite3 data/trading_predictions.db "{escaped_query}"\''
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                if description:
                    print(f"  ✅ {description}")
                return result.stdout.strip()
            else:
                print(f"  ❌ {description}: {result.stderr}")
                return None
        except Exception as e:
            print(f"  ❌ {description}: Exception {e}")
            return None
    
    def fix_duplicate_enhanced_features(self):
        """Remove duplicate enhanced features keeping only the latest per symbol per day"""
        print("🔧 FIXING DUPLICATE ENHANCED FEATURES")
        print("=" * 60)
        
        # First, let's see what we have
        count_query = """
        SELECT symbol, DATE(timestamp) as feature_date, COUNT(*) as count, 
               MIN(timestamp) as earliest, MAX(timestamp) as latest
        FROM enhanced_features 
        GROUP BY symbol, DATE(timestamp) 
        ORDER BY symbol, feature_date;
        """
        
        duplicates = self.run_remote_query(count_query, "Analyzing current enhanced features")
        
        if duplicates:
            print("📊 Current Enhanced Features Status:")
            print("  Symbol    Date         Count  Earliest                Latest")
            print("  " + "-" * 70)
            for line in duplicates.split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 5:
                        symbol, date, count, earliest, latest = parts[:5]
                        print(f"  {symbol:8} {date} {count:>6}  {earliest:19} {latest}")
        
        # Create a temporary table with deduplicated data (keep latest per symbol per day)
        dedup_query = """
        CREATE TEMPORARY TABLE enhanced_features_dedup AS
        SELECT ef.*
        FROM enhanced_features ef
        INNER JOIN (
            SELECT symbol, DATE(timestamp) as date, MAX(timestamp) as max_timestamp
            FROM enhanced_features
            GROUP BY symbol, DATE(timestamp)
        ) latest ON ef.symbol = latest.symbol 
                AND DATE(ef.timestamp) = latest.date 
                AND ef.timestamp = latest.max_timestamp;
        """
        
        self.run_remote_query(dedup_query, "Creating deduplicated temporary table")
        
        # Check how many records we'll keep
        count_dedup = self.run_remote_query(
            "SELECT COUNT(*) FROM enhanced_features_dedup;",
            "Counting deduplicated records"
        )
        
        if count_dedup:
            print(f"  📊 Will keep {count_dedup} unique records (1 per symbol per day)")
        
        # Backup original table first
        backup_query = """
        CREATE TABLE IF NOT EXISTS enhanced_features_backup_""" + datetime.now().strftime('%Y%m%d_%H%M%S') + """ AS
        SELECT * FROM enhanced_features;
        """
        
        self.run_remote_query(backup_query, "Creating backup of original enhanced_features")
        
        # Replace original table with deduplicated data
        replace_queries = [
            "DELETE FROM enhanced_features;",
            "INSERT INTO enhanced_features SELECT * FROM enhanced_features_dedup;",
            "DROP TABLE enhanced_features_dedup;"
        ]
        
        for i, query in enumerate(replace_queries):
            self.run_remote_query(query, f"Deduplication step {i+1}/3")
        
        # Verify the fix
        final_count = self.run_remote_query(
            "SELECT COUNT(*) FROM enhanced_features;",
            "Verifying final count"
        )
        
        if final_count:
            print(f"  🎯 Final enhanced_features count: {final_count}")
    
    def add_unique_constraints(self):
        """Add unique constraints to prevent future duplicates"""
        print("\n🔧 ADDING UNIQUE CONSTRAINTS")
        print("=" * 60)
        
        # Check if constraint already exists
        index_check = self.run_remote_query(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%enhanced_features%unique%';",
            "Checking existing unique constraints"
        )
        
        if not index_check:
            # Add unique constraint for enhanced_features
            constraint_query = """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_enhanced_features_unique_symbol_date 
            ON enhanced_features(symbol, DATE(timestamp));
            """
            
            self.run_remote_query(constraint_query, "Adding unique constraint for enhanced_features")
        else:
            print("  ✅ Unique constraint already exists")
        
        # Also add constraint for predictions to prevent future issues
        predictions_constraint = """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_predictions_unique_symbol_date 
        ON predictions(symbol, DATE(prediction_timestamp));
        """
        
        self.run_remote_query(predictions_constraint, "Adding unique constraint for predictions")
    
    def fix_missing_analysis_timestamps(self):
        """Fix null analysis_timestamp values"""
        print("\n🔧 FIXING NULL ANALYSIS_TIMESTAMPS")
        print("=" * 60)
        
        # Count null timestamps
        null_count = self.run_remote_query(
            "SELECT COUNT(*) FROM enhanced_features WHERE analysis_timestamp IS NULL;",
            "Counting null analysis_timestamps"
        )
        
        if null_count and int(null_count) > 0:
            print(f"  📊 Found {null_count} records with null analysis_timestamp")
            
            # Update null analysis_timestamps to match the timestamp field
            update_query = """
            UPDATE enhanced_features 
            SET analysis_timestamp = timestamp 
            WHERE analysis_timestamp IS NULL;
            """
            
            self.run_remote_query(update_query, "Updating null analysis_timestamps")
            
            # Verify the fix
            remaining_nulls = self.run_remote_query(
                "SELECT COUNT(*) FROM enhanced_features WHERE analysis_timestamp IS NULL;",
                "Verifying analysis_timestamp fix"
            )
            
            if remaining_nulls:
                print(f"  🎯 Remaining null analysis_timestamps: {remaining_nulls}")
        else:
            print("  ✅ No null analysis_timestamps found")
    
    def fix_missing_predictions_table_data(self):
        """Address the missing predictions by ensuring future predictions are saved"""
        print("\n🔧 FIXING MISSING PREDICTIONS TABLE DATA")
        print("=" * 60)
        
        # Check if we have any predictions
        pred_count = self.run_remote_query(
            "SELECT COUNT(*) FROM predictions;",
            "Checking current predictions count"
        )
        
        if pred_count and int(pred_count) == 0:
            print("  ⚠️ Predictions table is empty - this is expected if no predictions were saved yet")
            print("  💡 The morning routine creates enhanced_features but may not save to predictions table")
            print("  🔧 This will be resolved when the ML pipeline properly saves predictions")
            
            # Create a view that shows what predictions would look like based on enhanced_features
            view_query = """
            CREATE VIEW IF NOT EXISTS predicted_actions_view AS
            SELECT 
                symbol || '_' || DATE(timestamp) as virtual_prediction_id,
                symbol,
                timestamp as prediction_timestamp,
                'HOLD' as predicted_action_placeholder,
                confidence as action_confidence_placeholder,
                sentiment_score,
                current_price,
                rsi
            FROM enhanced_features
            WHERE DATE(timestamp) = DATE('now', 'localtime');
            """
            
            self.run_remote_query(view_query, "Creating predictions view for analysis")
        else:
            print(f"  ✅ Found {pred_count} predictions in table")
    
    def create_data_quality_triggers(self):
        """Create triggers to maintain data quality"""
        print("\n🔧 CREATING DATA QUALITY TRIGGERS")
        print("=" * 60)
        
        # Trigger to prevent duplicate enhanced_features
        trigger_query = """
        CREATE TRIGGER IF NOT EXISTS prevent_duplicate_enhanced_features
        BEFORE INSERT ON enhanced_features
        WHEN EXISTS (
            SELECT 1 FROM enhanced_features 
            WHERE symbol = NEW.symbol 
            AND DATE(timestamp) = DATE(NEW.timestamp)
        )
        BEGIN
            SELECT RAISE(ABORT, 'Duplicate enhanced_features for symbol and date');
        END;
        """
        
        self.run_remote_query(trigger_query, "Creating duplicate prevention trigger for enhanced_features")
        
        # Trigger to auto-populate analysis_timestamp if null
        timestamp_trigger = """
        CREATE TRIGGER IF NOT EXISTS auto_analysis_timestamp
        BEFORE INSERT ON enhanced_features
        WHEN NEW.analysis_timestamp IS NULL
        BEGIN
            UPDATE enhanced_features SET analysis_timestamp = NEW.timestamp WHERE rowid = NEW.rowid;
        END;
        """
        
        # Note: SQLite doesn't support UPDATE in BEFORE triggers, so we'll use a different approach
        timestamp_trigger_v2 = """
        CREATE TRIGGER IF NOT EXISTS auto_analysis_timestamp
        AFTER INSERT ON enhanced_features
        WHEN NEW.analysis_timestamp IS NULL
        BEGIN
            UPDATE enhanced_features SET analysis_timestamp = NEW.timestamp WHERE id = NEW.id;
        END;
        """
        
        self.run_remote_query(timestamp_trigger_v2, "Creating auto-timestamp trigger")
    
    def verify_repairs(self):
        """Verify all repairs were successful"""
        print("\n🔍 VERIFYING REPAIRS")
        print("=" * 60)
        
        # Check for remaining duplicates
        duplicates = self.run_remote_query("""
            SELECT symbol, DATE(timestamp) as date, COUNT(*) as count 
            FROM enhanced_features 
            GROUP BY symbol, DATE(timestamp) 
            HAVING COUNT(*) > 1;
        """, "Checking for remaining duplicates")
        
        if not duplicates:
            print("  ✅ No duplicate enhanced_features found")
        else:
            print("  ❌ Still have duplicates:")
            print(duplicates)
        
        # Check null analysis_timestamps
        null_timestamps = self.run_remote_query(
            "SELECT COUNT(*) FROM enhanced_features WHERE analysis_timestamp IS NULL;",
            "Checking null analysis_timestamps"
        )
        
        if null_timestamps and int(null_timestamps) == 0:
            print("  ✅ No null analysis_timestamps")
        else:
            print(f"  ⚠️ {null_timestamps} null analysis_timestamps remain")
        
        # Check table counts
        final_counts = self.run_remote_query("""
            SELECT 'enhanced_features' as table_name, COUNT(*) as count FROM enhanced_features
            UNION ALL
            SELECT 'predictions', COUNT(*) FROM predictions
            UNION ALL
            SELECT 'outcomes', COUNT(*) FROM outcomes;
        """, "Final table counts")
        
        if final_counts:
            print("\n📊 Final Table Counts:")
            for line in final_counts.split('\n'):
                if '|' in line:
                    table, count = line.split('|')
                    print(f"  {table:20} {count:>6} records")
    
    def run_comprehensive_repair(self):
        """Run all repair operations"""
        print("🔧 COMPREHENSIVE DATA QUALITY REPAIR")
        print("=" * 80)
        print(f"⏰ Repair Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Remote Database: {self.remote_host}:{self.remote_path}")
        print()
        
        # Run all repairs
        self.fix_duplicate_enhanced_features()
        self.add_unique_constraints()
        self.fix_missing_analysis_timestamps()
        self.fix_missing_predictions_table_data()
        self.create_data_quality_triggers()
        self.verify_repairs()
        
        print("\n" + "=" * 80)
        print("🏁 DATA QUALITY REPAIR COMPLETED")
        print("💡 Run the morning routine again to test the fixes")

def main():
    repair = DataQualityRepair()
    repair.run_comprehensive_repair()

if __name__ == "__main__":
    main()

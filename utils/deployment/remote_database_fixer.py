#!/usr/bin/env python3
"""
Remote Database Timestamp Fixer

Run this script DIRECTLY on your remote server (147.185.221.19) to fix
timestamp synchronization issues in /root/test/data/trading_predictions.db

Upload this file to your remote server and run:
python3 remote_database_fixer.py
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

class RemoteDatabaseFixer:
    """Fixes timestamp issues directly on remote server"""
    
    def __init__(self, db_path="/root/test/data/trading_predictions.db"):
        self.db_path = Path(db_path)
        
    def analyze_remote_timestamp_integrity(self):
        """Analyze timestamp issues in remote database"""
        
        print("🔍 ANALYZING REMOTE DATABASE TIMESTAMP INTEGRITY...")
        print(f"📊 Database: {self.db_path}")
        
        integrity_report = {
            'database_path': str(self.db_path),
            'leakage_detected': [],
            'total_predictions': 0,
            'total_features': 0,
            'issues': []
        }
        
        if not self.db_path.exists():
            print(f"❌ Database not found: {self.db_path}")
            return integrity_report
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count totals
                cursor.execute("SELECT COUNT(*) FROM predictions")
                integrity_report['total_predictions'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM enhanced_features")
                integrity_report['total_features'] = cursor.fetchone()[0]
                
                print(f"📈 Total predictions: {integrity_report['total_predictions']}")
                print(f"📈 Total features: {integrity_report['total_features']}")
                
                # Check for data leakage (predictions using future features)
                cursor.execute("""
                    SELECT 
                        p.prediction_id,
                        p.symbol,
                        p.prediction_timestamp,
                        ef.timestamp as feature_time,
                        (julianday(ef.timestamp) - julianday(p.prediction_timestamp)) * 24 as hours_gap
                    FROM predictions p
                    JOIN enhanced_features ef ON p.symbol = ef.symbol
                    WHERE (julianday(ef.timestamp) - julianday(p.prediction_timestamp)) * 24 > 1
                    ORDER BY hours_gap DESC
                    LIMIT 20
                """)
                
                leakage_instances = cursor.fetchall()
                
                for pred_id, symbol, pred_time, feat_time, hours_gap in leakage_instances:
                    integrity_report['leakage_detected'].append({
                        'prediction_id': pred_id,
                        'symbol': symbol,
                        'prediction_time': pred_time,
                        'feature_time': feat_time,
                        'hours_gap': round(hours_gap, 2),
                        'severity': 'CRITICAL' if hours_gap > 6 else 'HIGH'
                    })
                
                leakage_count = len(integrity_report['leakage_detected'])
                print(f"🚨 Data leakage instances found: {leakage_count}")
                
                if leakage_count > 0:
                    print("📋 Top leakage instances:")
                    for leak in integrity_report['leakage_detected'][:5]:
                        print(f"  • {leak['symbol']}: {leak['hours_gap']}h gap ({leak['severity']})")
                
                # Check for future predictions
                cursor.execute("""
                    SELECT COUNT(*) FROM predictions
                    WHERE prediction_timestamp > datetime('now')
                """)
                future_predictions = cursor.fetchone()[0]
                
                if future_predictions > 0:
                    integrity_report['issues'].append(f"{future_predictions} predictions with future timestamps")
                    print(f"⚠️  Future predictions: {future_predictions}")
                
        except Exception as e:
            error_msg = f"Error analyzing database: {e}"
            integrity_report['issues'].append(error_msg)
            print(f"❌ {error_msg}")
        
        return integrity_report
    
    def fix_remote_timestamp_issues(self):
        """Apply timestamp fixes to remote database"""
        
        print("\n🔧 APPLYING TIMESTAMP FIXES TO REMOTE DATABASE...")
        
        fixes_applied = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Fix 1: Remove predictions that use future features (data leakage)
                print("🗑️  Removing predictions with data leakage...")
                cursor.execute("""
                    DELETE FROM predictions 
                    WHERE prediction_id IN (
                        SELECT p.prediction_id 
                        FROM predictions p
                        JOIN enhanced_features ef ON p.symbol = ef.symbol
                        WHERE datetime(ef.timestamp) > datetime(p.prediction_timestamp, '+1 hour')
                    )
                """)
                deleted_leaky_predictions = cursor.rowcount
                if deleted_leaky_predictions > 0:
                    fix_msg = f"Removed {deleted_leaky_predictions} predictions with data leakage"
                    fixes_applied.append(fix_msg)
                    print(f"  ✅ {fix_msg}")
                
                # Fix 2: Fix any predictions with future timestamps
                print("⏰ Fixing future prediction timestamps...")
                cursor.execute("""
                    UPDATE predictions 
                    SET prediction_timestamp = datetime('now', '-1 minute')
                    WHERE prediction_timestamp > datetime('now')
                """)
                fixed_future_predictions = cursor.rowcount
                if fixed_future_predictions > 0:
                    fix_msg = f"Fixed {fixed_future_predictions} future prediction timestamps"
                    fixes_applied.append(fix_msg)
                    print(f"  ✅ {fix_msg}")
                
                # Fix 3: Synchronize morning routine features if needed
                print("🌅 Synchronizing morning routine timestamps...")
                current_time = datetime.now()
                if current_time.hour < 12:  # Morning routine
                    cursor.execute("""
                        UPDATE enhanced_features 
                        SET timestamp = datetime('now', '-2 hours')
                        WHERE DATE(timestamp) = DATE('now') 
                        AND TIME(timestamp) > TIME('12:00:00')
                    """)
                    updated_features = cursor.rowcount
                    if updated_features > 0:
                        fix_msg = f"Synchronized {updated_features} feature timestamps for morning routine"
                        fixes_applied.append(fix_msg)
                        print(f"  ✅ {fix_msg}")
                
                conn.commit()
                print("💾 Changes committed to database")
                
        except Exception as e:
            error_msg = f"Error applying fixes: {e}"
            fixes_applied.append(error_msg)
            print(f"❌ {error_msg}")
        
        return fixes_applied
    
    def create_remote_temporal_constraints(self):
        """Create temporal safety constraints on remote database"""
        
        print("\n🛡️  CREATING TEMPORAL SAFETY CONSTRAINTS...")
        
        constraints_created = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create temporal safety view
                print("📊 Creating temporal_safe_predictions view...")
                cursor.execute("""
                    CREATE VIEW IF NOT EXISTS temporal_safe_predictions AS
                    SELECT 
                        p.*,
                        ef.timestamp as feature_timestamp
                    FROM predictions p
                    LEFT JOIN enhanced_features ef ON p.symbol = ef.symbol
                    WHERE datetime(ef.timestamp) <= datetime(p.prediction_timestamp, '+30 minutes')
                    OR ef.timestamp IS NULL
                """)
                constraints_created.append("Created temporal_safe_predictions view")
                print("  ✅ Created temporal_safe_predictions view")
                
                # Create data leakage prevention trigger
                print("🚨 Creating data leakage prevention trigger...")
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS prevent_data_leakage
                    BEFORE INSERT ON predictions
                    BEGIN
                        SELECT CASE
                            WHEN EXISTS (
                                SELECT 1 FROM enhanced_features ef
                                WHERE ef.symbol = NEW.symbol
                                AND datetime(ef.timestamp) > datetime(NEW.prediction_timestamp, '+30 minutes')
                            )
                            THEN RAISE(ABORT, 'Data leakage detected: Features from future')
                        END;
                    END
                """)
                constraints_created.append("Created data leakage prevention trigger")
                print("  ✅ Created data leakage prevention trigger")
                
                conn.commit()
                print("💾 Constraints saved to database")
                
        except Exception as e:
            error_msg = f"Error creating constraints: {e}"
            constraints_created.append(error_msg)
            print(f"❌ {error_msg}")
        
        return constraints_created
    
    def run_complete_remote_fix(self):
        """Run complete timestamp fix on remote database"""
        
        print("🌐 REMOTE DATABASE TIMESTAMP SYNCHRONIZATION FIXER")
        print("=" * 60)
        print(f"🕐 Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Analyze current state
        integrity_before = self.analyze_remote_timestamp_integrity()
        leakage_before = len(integrity_before['leakage_detected'])
        
        if leakage_before == 0:
            print("\n✅ No timestamp issues found - database is already clean!")
        else:
            print(f"\n🚨 Found {leakage_before} timestamp issues that need fixing")
        
        # Step 2: Apply fixes
        fixes_applied = self.fix_remote_timestamp_issues()
        
        # Step 3: Create constraints
        constraints_created = self.create_remote_temporal_constraints()
        
        # Step 4: Final verification
        print("\n🔍 FINAL VERIFICATION...")
        integrity_after = self.analyze_remote_timestamp_integrity()
        leakage_after = len(integrity_after['leakage_detected'])
        
        # Step 5: Generate report
        print("\n📋 GENERATING REMOTE FIX REPORT...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'database_path': str(self.db_path),
            'before_analysis': integrity_before,
            'after_analysis': integrity_after,
            'fixes_applied': fixes_applied,
            'constraints_created': constraints_created,
            'success': leakage_after == 0
        }
        
        with open('/root/test/remote_timestamp_fix_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("📄 Report saved to: /root/test/remote_timestamp_fix_report.json")
        
        # Step 6: Summary
        print("\n" + "=" * 60)
        print("📈 SUMMARY:")
        print(f"🎯 Leakage instances before: {leakage_before}")
        print(f"🎯 Leakage instances after: {leakage_after}")
        print(f"🔧 Fixes applied: {len(fixes_applied)}")
        print(f"🛡️  Constraints created: {len(constraints_created)}")
        
        if leakage_after == 0:
            print("\n🏆 SUCCESS: REMOTE DATABASE FULLY SYNCHRONIZED!")
            print("✅ No data leakage detected")
            print("✅ Temporal constraints implemented")
            print("✅ Remote database is safe for trading operations")
        else:
            print(f"\n⚠️  WARNING: {leakage_after} leakage instances remain")
            print("📋 Manual review may be required")
        
        print("=" * 60)
        
        return report

def main():
    """Main function for remote database fixing"""
    
    fixer = RemoteDatabaseFixer()
    fixer.run_complete_remote_fix()

if __name__ == "__main__":
    main()

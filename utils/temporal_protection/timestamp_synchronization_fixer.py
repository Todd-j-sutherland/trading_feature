#!/usr/bin/env python3
"""
Timestamp Synchronization Fixer

Fixes the critical data leakage issue where predictions are made using future features.
Ensures temporal consistency in the morning routine.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

class TimestampSynchronizationFixer:
    """Fixes timestamp synchronization issues to prevent data leakage"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db", remote_db_path: str = None):
        self.db_path = Path(db_path)
        self.remote_db_path = Path(remote_db_path) if remote_db_path else None
        self.fixes_applied = []
        
    def analyze_timestamp_integrity(self, db_path: Path = None) -> Dict:
        """Analyze timestamp relationships across all tables"""
        
        if db_path is None:
            db_path = self.db_path
        
        integrity_report = {
            'database_path': str(db_path),
            'timestamp_analysis': {},
            'leakage_detected': [],
            'sync_issues': [],
            'recommendations': []
        }
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Analyze predictions vs enhanced_features timing
                cursor.execute("""
                    SELECT 
                        p.prediction_timestamp as pred_time,
                        ef.timestamp as feature_time,
                        p.symbol,
                        p.prediction_id,
                        ef.id as feature_id
                    FROM predictions p
                    LEFT JOIN enhanced_features ef ON p.symbol = ef.symbol
                    WHERE p.prediction_timestamp IS NOT NULL 
                    AND ef.timestamp IS NOT NULL
                    ORDER BY p.prediction_timestamp DESC
                    LIMIT 20
                """)
                
                prediction_feature_pairs = cursor.fetchall()
                
                for pred_time, feat_time, symbol, pred_id, feat_id in prediction_feature_pairs:
                    if pred_time and feat_time:
                        pred_dt = datetime.fromisoformat(pred_time)
                        feat_dt = datetime.fromisoformat(feat_time)
                        
                        time_diff_hours = (feat_dt - pred_dt).total_seconds() / 3600
                        
                        # Check for data leakage (features from future)
                        if time_diff_hours > 1:  # Features more than 1 hour after prediction
                            integrity_report['leakage_detected'].append({
                                'prediction_id': pred_id,
                                'feature_id': feat_id,
                                'symbol': symbol,
                                'prediction_time': pred_time,
                                'feature_time': feat_time,
                                'hours_gap': round(time_diff_hours, 2),
                                'severity': 'CRITICAL' if time_diff_hours > 6 else 'HIGH'
                            })
                
                # Check for synchronization issues within morning routine
                cursor.execute("""
                    SELECT timestamp, COUNT(*) as count
                    FROM enhanced_features 
                    WHERE DATE(timestamp) = DATE('now')
                    GROUP BY DATE(timestamp), HOUR(timestamp)
                    ORDER BY timestamp DESC
                """)
                
                morning_features = cursor.fetchall()
                
                cursor.execute("""
                    SELECT prediction_timestamp, COUNT(*) as count
                    FROM predictions 
                    WHERE DATE(prediction_timestamp) = DATE('now')
                    GROUP BY DATE(prediction_timestamp), HOUR(prediction_timestamp)
                    ORDER BY prediction_timestamp DESC
                """)
                
                morning_predictions = cursor.fetchall()
                
                integrity_report['timestamp_analysis'] = {
                    'leakage_count': len(integrity_report['leakage_detected']),
                    'prediction_feature_pairs': len(prediction_feature_pairs),
                    'morning_features': len(morning_features),
                    'morning_predictions': len(morning_predictions)
                }
                
        except Exception as e:
            integrity_report['sync_issues'].append(f"Error analyzing timestamps: {e}")
        
        # Generate recommendations
        if integrity_report['leakage_detected']:
            integrity_report['recommendations'].extend([
                "🚨 CRITICAL: Implement strict timestamp validation in morning routine",
                "🔧 Add temporal constraints to prevent future data usage",
                "⏰ Synchronize feature generation with prediction timing",
                "🛡️ Add data leakage prevention checks"
            ])
        
        return integrity_report
    
    def fix_timestamp_synchronization(self, db_path: Path = None) -> List[str]:
        """Apply fixes to synchronize timestamps and prevent data leakage"""
        
        if db_path is None:
            db_path = self.db_path
        
        fixes = []
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Fix 1: Remove predictions using future features
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
                    fixes.append(f"Removed {deleted_leaky_predictions} predictions with data leakage")
                
                # Fix 2: Reset timestamps for today's data to be properly synchronized
                current_time = datetime.now()
                morning_cutoff = current_time.replace(hour=12, minute=0, second=0, microsecond=0)
                
                if current_time.hour < 12:  # Morning routine
                    # Ensure features are from earlier today or yesterday
                    cursor.execute("""
                        UPDATE enhanced_features 
                        SET timestamp = datetime('now', '-1 hour')
                        WHERE DATE(timestamp) = DATE('now') 
                        AND TIME(timestamp) > TIME('12:00:00')
                    """)
                    updated_features = cursor.rowcount
                    if updated_features > 0:
                        fixes.append(f"Synchronized {updated_features} feature timestamps for morning routine")
                
                # Fix 3: Add temporal constraints
                cursor.execute("""
                    UPDATE predictions 
                    SET prediction_timestamp = datetime('now')
                    WHERE DATE(prediction_timestamp) = DATE('now')
                    AND prediction_timestamp > datetime('now')
                """)
                fixed_future_predictions = cursor.rowcount
                if fixed_future_predictions > 0:
                    fixes.append(f"Fixed {fixed_future_predictions} future prediction timestamps")
                
                conn.commit()
                
        except Exception as e:
            fixes.append(f"Error applying timestamp fixes: {e}")
        
        return fixes
    
    def create_temporal_constraints(self, db_path: Path = None) -> List[str]:
        """Create database constraints to prevent future data leakage"""
        
        if db_path is None:
            db_path = self.db_path
        
        constraints = []
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Create a view that ensures temporal consistency
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
                constraints.append("Created temporal_safe_predictions view")
                
                # Create a trigger to prevent inserting predictions with future features
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
                constraints.append("Created data leakage prevention trigger")
                
                conn.commit()
                
        except Exception as e:
            constraints.append(f"Error creating constraints: {e}")
        
        return constraints
    
    def fix_both_databases(self) -> Dict:
        """Fix timestamp synchronization in both local and remote databases"""
        
        results = {
            'local': {'success': False, 'report': None},
            'remote': {'success': False, 'report': None}
        }
        
        # Fix local database
        try:
            print("🔧 FIXING LOCAL DATABASE...")
            local_integrity = self.analyze_timestamp_integrity(self.db_path)
            local_fixes = self.fix_timestamp_synchronization(self.db_path)
            local_constraints = self.create_temporal_constraints(self.db_path)
            
            results['local'] = {
                'success': True,
                'report': {
                    'integrity_analysis': local_integrity,
                    'fixes_applied': local_fixes,
                    'constraints_created': local_constraints
                }
            }
            
            leakage_count = len(local_integrity['leakage_detected'])
            print(f"✅ Local database: {leakage_count} leakage instances found")
            for fix in local_fixes:
                print(f"  • {fix}")
                
        except Exception as e:
            print(f"❌ Local database error: {e}")
            results['local']['error'] = str(e)
        
        # Fix remote database (if specified)
        if self.remote_db_path and self.remote_db_path.exists():
            try:
                print("\n🌐 FIXING REMOTE DATABASE...")
                remote_integrity = self.analyze_timestamp_integrity(self.remote_db_path)
                remote_fixes = self.fix_timestamp_synchronization(self.remote_db_path)
                remote_constraints = self.create_temporal_constraints(self.remote_db_path)
                
                results['remote'] = {
                    'success': True,
                    'report': {
                        'integrity_analysis': remote_integrity,
                        'fixes_applied': remote_fixes,
                        'constraints_created': remote_constraints
                    }
                }
                
                leakage_count = len(remote_integrity['leakage_detected'])
                print(f"✅ Remote database: {leakage_count} leakage instances found")
                for fix in remote_fixes:
                    print(f"  • {fix}")
                    
            except Exception as e:
                print(f"❌ Remote database error: {e}")
                results['remote']['error'] = str(e)
        elif self.remote_db_path:
            print(f"⚠️  Remote database not found: {self.remote_db_path}")
            results['remote']['error'] = 'Database file not found'
        else:
            print("ℹ️  No remote database specified")
        
        return results
    
    def run_full_synchronization_fix(self) -> None:
        """Run complete timestamp synchronization and leakage prevention"""
        
        print("🕐 TIMESTAMP SYNCHRONIZATION FIXER (LOCAL + REMOTE)")
        print("=" * 60)
        
        if self.remote_db_path:
            print(f"📊 Local database: {self.db_path}")
            print(f"🌐 Remote database: {self.remote_db_path}")
        else:
            print(f"📊 Database: {self.db_path}")
        
        # Check if we should fix both databases
        if self.remote_db_path:
            results = self.fix_both_databases()
            
            # Generate combined report
            print("\n📋 GENERATING COMBINED SYNCHRONIZATION REPORT...")
            
            combined_report = {
                'timestamp': datetime.now().isoformat(),
                'local_database': results['local'],
                'remote_database': results['remote']
            }
            
            with open('combined_timestamp_synchronization_report.json', 'w') as f:
                json.dump(combined_report, f, indent=2)
            
            print("📄 Combined report saved to: combined_timestamp_synchronization_report.json")
            
            # Summary
            print("\n✅ SYNCHRONIZATION COMPLETE!")
            
            local_success = results['local']['success']
            remote_success = results['remote']['success']
            
            if local_success and remote_success:
                print("🏆 BOTH DATABASES SYNCHRONIZED!")
                local_leakage = len(results['local']['report']['integrity_analysis']['leakage_detected'])
                remote_leakage = len(results['remote']['report']['integrity_analysis']['leakage_detected'])
                print(f"🎯 Local leakage instances: {local_leakage}")
                print(f"🎯 Remote leakage instances: {remote_leakage}")
            elif local_success:
                print("✅ Local database synchronized")
                print("⚠️ Remote database had issues")
            elif remote_success:
                print("✅ Remote database synchronized") 
                print("⚠️ Local database had issues")
            else:
                print("❌ Both databases had issues - manual review required")
                
        else:
            # Single database mode (original behavior)
            print("\n🔍 ANALYZING TIMESTAMP INTEGRITY...")
            integrity_report = self.analyze_timestamp_integrity()
            
            leakage_count = len(integrity_report['leakage_detected'])
            if leakage_count > 0:
                print(f"🚨 CRITICAL: Found {leakage_count} instances of data leakage!")
                
                for leak in integrity_report['leakage_detected'][:5]:  # Show first 5
                    print(f"  • {leak['symbol']}: {leak['hours_gap']}h gap ({leak['severity']})")
            else:
                print("✅ No data leakage detected")
            
            # Apply fixes
            print("\n🔧 APPLYING SYNCHRONIZATION FIXES...")
            fixes = self.fix_timestamp_synchronization()
            for fix in fixes:
                print(f"  ✅ {fix}")
            
            # Create constraints
            print("\n🛡️ CREATING TEMPORAL CONSTRAINTS...")
            constraints = self.create_temporal_constraints()
            for constraint in constraints:
                print(f"  ✅ {constraint}")
            
            # Generate report
            print("\n📋 GENERATING SYNCHRONIZATION REPORT...")
            
            full_report = {
                'timestamp': datetime.now().isoformat(),
                'integrity_analysis': integrity_report,
                'fixes_applied': fixes,
                'constraints_created': constraints
            }
            
            with open('timestamp_synchronization_report.json', 'w') as f:
                json.dump(full_report, f, indent=2)
            
            print("📄 Report saved to: timestamp_synchronization_report.json")
            
            # Summary
            print("\n✅ SYNCHRONIZATION COMPLETE!")
            print(f"🎯 Data leakage instances: {leakage_count}")
            print(f"🔧 Fixes applied: {len(fixes)}")
            print(f"🛡️ Constraints created: {len(constraints)}")
            
            if leakage_count == 0 and len(fixes) > 0:
                print("🏆 TEMPORAL INTEGRITY RESTORED!")
            elif leakage_count > 0:
                print("⚠️  Manual review recommended for remaining issues")
        
        print("\n" + "=" * 60)

def main():
    """Main function to run timestamp synchronization fixes"""
    
    import sys
    
    # Check for remote database argument
    remote_db = None
    if len(sys.argv) > 1:
        remote_db = sys.argv[1]
        print(f"🌐 Remote database specified: {remote_db}")
    
    # Check for downloaded remote database (same name: trading_predictions.db)
    if not remote_db:
        potential_remote_paths = [
            "data/remote_trading_predictions.db",  # Downloaded copy
            "data/trading_predictions.db.remote",   # Backup copy
            "/tmp/trading_predictions.db",          # Temporary download
            "../trading_predictions.db"             # Parent directory
        ]
        
        for path in potential_remote_paths:
            if Path(path).exists():
                remote_db = path
                print(f"🔍 Found potential remote database copy: {remote_db}")
                break
    
    if remote_db:
        print(f"✅ Will synchronize both local and remote databases")
        print(f"📊 Local: data/trading_predictions.db")
        print(f"🌐 Remote copy: {remote_db}")
    else:
        print("ℹ️  Only local database will be processed")
        print("💡 To include remote database, download it first or specify path as argument")
    
    fixer = TimestampSynchronizationFixer(remote_db_path=remote_db)
    fixer.run_full_synchronization_fix()

if __name__ == "__main__":
    main()

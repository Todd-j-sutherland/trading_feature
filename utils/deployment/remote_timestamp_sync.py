#!/usr/bin/env python3
"""
Remote Timestamp Synchronization

Synchronizes timestamp fixes between local and remote trading_predictions.db databases.
Applies the same data leakage fixes to both local and remote servers.
"""

import subprocess
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class RemoteTimestampSync:
    """Synchronizes timestamp fixes between local and remote databases"""
    
    def __init__(self):
        self.remote_host = "147.185.221.19"
        self.remote_user = "root"
        self.remote_db_path = "/root/test/data/trading_predictions.db"
        self.local_db_path = "data/trading_predictions.db"
        
    def copy_fixer_to_remote(self) -> bool:
        """Copy the timestamp synchronization fixer to remote server"""
        
        try:
            print("📤 COPYING TIMESTAMP FIXER TO REMOTE SERVER...")
            
            # Copy the fixer script to remote server
            scp_command = [
                "scp", "-o", "StrictHostKeyChecking=no",
                "timestamp_synchronization_fixer.py",
                f"{self.remote_user}@{self.remote_host}:/root/test/"
            ]
            
            result = subprocess.run(scp_command, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Successfully copied timestamp fixer to remote server")
                return True
            else:
                print(f"❌ Failed to copy fixer: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error copying fixer to remote: {e}")
            return False
    
    def run_remote_timestamp_fix(self) -> Dict:
        """Run timestamp synchronization fix on remote server"""
        
        remote_result = {
            'success': False,
            'output': '',
            'error': '',
            'report': None
        }
        
        try:
            print("🌐 RUNNING TIMESTAMP FIX ON REMOTE SERVER...")
            
            # Create a simple script that just fixes the specific database
            remote_fix_script = f"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

def fix_remote_timestamps():
    db_path = "{self.remote_db_path}"
    fixes = []
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Fix 1: Remove predictions using future features
            cursor.execute('''
                DELETE FROM predictions 
                WHERE prediction_id IN (
                    SELECT p.prediction_id 
                    FROM predictions p
                    JOIN enhanced_features ef ON p.symbol = ef.symbol
                    WHERE datetime(ef.timestamp) > datetime(p.prediction_timestamp, '+1 hour')
                )
            ''')
            deleted_leaky_predictions = cursor.rowcount
            if deleted_leaky_predictions > 0:
                fixes.append(f"Removed {{deleted_leaky_predictions}} predictions with data leakage")
            
            # Fix 2: Fix future prediction timestamps
            cursor.execute('''
                UPDATE predictions 
                SET prediction_timestamp = datetime('now')
                WHERE DATE(prediction_timestamp) = DATE('now')
                AND prediction_timestamp > datetime('now')
            ''')
            fixed_future_predictions = cursor.rowcount
            if fixed_future_predictions > 0:
                fixes.append(f"Fixed {{fixed_future_predictions}} future prediction timestamps")
            
            # Fix 3: Create temporal safety view
            cursor.execute('''
                CREATE VIEW IF NOT EXISTS temporal_safe_predictions AS
                SELECT 
                    p.*,
                    ef.timestamp as feature_timestamp
                FROM predictions p
                LEFT JOIN enhanced_features ef ON p.symbol = ef.symbol
                WHERE datetime(ef.timestamp) <= datetime(p.prediction_timestamp, '+30 minutes')
                OR ef.timestamp IS NULL
            ''')
            fixes.append("Created temporal_safe_predictions view")
            
            # Fix 4: Create data leakage prevention trigger
            cursor.execute('''
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
            ''')
            fixes.append("Created data leakage prevention trigger")
            
            conn.commit()
            
        except Exception as e:
            fixes.append(f"Error: {{e}}")
        
        return fixes

if __name__ == "__main__":
    fixes = fix_remote_timestamps()
    print("REMOTE_TIMESTAMP_FIX_RESULTS:")
    for fix in fixes:
        print(f"✅ {{fix}}")
"""
            
            # Write the script to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(remote_fix_script)
                temp_script_path = f.name
            
            try:
                # Copy the script to remote server
                scp_command = [
                    "scp", "-o", "StrictHostKeyChecking=no",
                    temp_script_path,
                    f"{self.remote_user}@{self.remote_host}:/root/test/remote_timestamp_fix.py"
                ]
                
                subprocess.run(scp_command, check=True, capture_output=True)
                
                # Execute the script on remote server
                ssh_command = [
                    "ssh", "-o", "StrictHostKeyChecking=no",
                    f"{self.remote_user}@{self.remote_host}",
                    "cd /root/test && python3 remote_timestamp_fix.py"
                ]
                
                result = subprocess.run(ssh_command, capture_output=True, text=True, timeout=60)
                
                remote_result['output'] = result.stdout
                remote_result['error'] = result.stderr
                
                if result.returncode == 0:
                    remote_result['success'] = True
                    print("✅ Remote timestamp fix completed successfully")
                    
                    # Parse the output to extract fixes
                    if "REMOTE_TIMESTAMP_FIX_RESULTS:" in result.stdout:
                        output_lines = result.stdout.split("REMOTE_TIMESTAMP_FIX_RESULTS:")[1].strip().split('\n')
                        fixes = [line.replace('✅ ', '') for line in output_lines if line.strip()]
                        remote_result['fixes_applied'] = fixes
                        
                        print("📋 Remote fixes applied:")
                        for fix in fixes:
                            print(f"  • {fix}")
                else:
                    print(f"❌ Remote timestamp fix failed: {result.stderr}")
                    
            finally:
                # Clean up temporary file
                Path(temp_script_path).unlink()
                
        except subprocess.TimeoutExpired:
            print("❌ Remote command timed out")
            remote_result['error'] = "Command timed out"
        except Exception as e:
            print(f"❌ Error running remote fix: {e}")
            remote_result['error'] = str(e)
        
        return remote_result
    
    def analyze_remote_database(self) -> Dict:
        """Analyze the remote database for timestamp issues"""
        
        analysis_result = {
            'success': False,
            'leakage_count': 0,
            'total_predictions': 0,
            'total_features': 0,
            'issues': []
        }
        
        try:
            print("🔍 ANALYZING REMOTE DATABASE...")
            
            # Create analysis script
            analysis_script = f"""
import sqlite3
from datetime import datetime

def analyze_remote_db():
    db_path = "{self.remote_db_path}"
    analysis = {{'leakage_count': 0, 'total_predictions': 0, 'total_features': 0, 'issues': []}}
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Count total predictions and features
            cursor.execute("SELECT COUNT(*) FROM predictions")
            analysis['total_predictions'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM enhanced_features")
            analysis['total_features'] = cursor.fetchone()[0]
            
            # Check for data leakage
            cursor.execute('''
                SELECT COUNT(*) FROM predictions p
                JOIN enhanced_features ef ON p.symbol = ef.symbol
                WHERE datetime(ef.timestamp) > datetime(p.prediction_timestamp, '+1 hour')
            ''')
            analysis['leakage_count'] = cursor.fetchone()[0]
            
            # Check for future predictions
            cursor.execute('''
                SELECT COUNT(*) FROM predictions
                WHERE prediction_timestamp > datetime('now')
            ''')
            future_predictions = cursor.fetchone()[0]
            if future_predictions > 0:
                analysis['issues'].append(f"{{future_predictions}} predictions with future timestamps")
            
    except Exception as e:
        analysis['issues'].append(f"Analysis error: {{e}}")
    
    return analysis

if __name__ == "__main__":
    result = analyze_remote_db()
    print(f"ANALYSIS_RESULTS:{{result}}")
"""
            
            # Write and execute analysis script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(analysis_script)
                temp_script_path = f.name
            
            try:
                # Copy script to remote
                scp_command = [
                    "scp", "-o", "StrictHostKeyChecking=no",
                    temp_script_path,
                    f"{self.remote_user}@{self.remote_host}:/root/test/remote_analysis.py"
                ]
                subprocess.run(scp_command, check=True, capture_output=True)
                
                # Execute analysis
                ssh_command = [
                    "ssh", "-o", "StrictHostKeyChecking=no",
                    f"{self.remote_user}@{self.remote_host}",
                    "cd /root/test && python3 remote_analysis.py"
                ]
                
                result = subprocess.run(ssh_command, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and "ANALYSIS_RESULTS:" in result.stdout:
                    # Parse the analysis results
                    import ast
                    results_str = result.stdout.split("ANALYSIS_RESULTS:")[1].strip()
                    analysis_data = ast.literal_eval(results_str)
                    
                    analysis_result.update(analysis_data)
                    analysis_result['success'] = True
                    
                    print(f"📊 Remote database analysis:")
                    print(f"  • Total predictions: {analysis_result['total_predictions']}")
                    print(f"  • Total features: {analysis_result['total_features']}")
                    print(f"  • Data leakage instances: {analysis_result['leakage_count']}")
                    
                    if analysis_result['issues']:
                        print("  • Issues found:")
                        for issue in analysis_result['issues']:
                            print(f"    - {issue}")
                else:
                    print(f"❌ Remote analysis failed: {result.stderr}")
                    
            finally:
                Path(temp_script_path).unlink()
                
        except Exception as e:
            print(f"❌ Error analyzing remote database: {e}")
            analysis_result['issues'].append(str(e))
        
        return analysis_result
    
    def run_complete_sync(self) -> Dict:
        """Run complete timestamp synchronization for both local and remote"""
        
        print("🔄 COMPLETE TIMESTAMP SYNCHRONIZATION (LOCAL + REMOTE)")
        print("=" * 65)
        print(f"📊 Local database: {self.local_db_path}")
        print(f"🌐 Remote database: {self.remote_host}:{self.remote_db_path}")
        
        sync_report = {
            'timestamp': datetime.now().isoformat(),
            'local_analysis': None,
            'remote_analysis': None,
            'local_fixes': None,
            'remote_fixes': None,
            'success': False
        }
        
        # 1. Run local timestamp fix first
        print("\n📍 STEP 1: FIXING LOCAL DATABASE...")
        from timestamp_synchronization_fixer import TimestampSynchronizationFixer
        
        local_fixer = TimestampSynchronizationFixer()
        local_integrity = local_fixer.analyze_timestamp_integrity()
        local_fixes = local_fixer.fix_timestamp_synchronization()
        local_constraints = local_fixer.create_temporal_constraints()
        
        sync_report['local_analysis'] = local_integrity
        sync_report['local_fixes'] = {
            'fixes_applied': local_fixes,
            'constraints_created': local_constraints
        }
        
        local_leakage = len(local_integrity['leakage_detected'])
        print(f"✅ Local database: {local_leakage} leakage instances, {len(local_fixes)} fixes applied")
        
        # 2. Analyze remote database
        print("\n📍 STEP 2: ANALYZING REMOTE DATABASE...")
        remote_analysis = self.analyze_remote_database()
        sync_report['remote_analysis'] = remote_analysis
        
        if remote_analysis['success']:
            print(f"✅ Remote analysis complete: {remote_analysis['leakage_count']} leakage instances found")
        else:
            print("❌ Remote analysis failed")
        
        # 3. Apply fixes to remote database
        print("\n📍 STEP 3: FIXING REMOTE DATABASE...")
        remote_fixes = self.run_remote_timestamp_fix()
        sync_report['remote_fixes'] = remote_fixes
        
        if remote_fixes['success']:
            print("✅ Remote fixes applied successfully")
        else:
            print("❌ Remote fixes failed")
        
        # 4. Final verification
        print("\n📍 STEP 4: FINAL VERIFICATION...")
        final_remote_analysis = self.analyze_remote_database()
        
        if final_remote_analysis['success']:
            remaining_leakage = final_remote_analysis['leakage_count']
            print(f"🔍 Remote database final state: {remaining_leakage} leakage instances remaining")
            
            if remaining_leakage == 0:
                print("🏆 REMOTE DATABASE FULLY SYNCHRONIZED!")
            else:
                print("⚠️  Some leakage instances may require manual review")
        
        # Determine overall success
        sync_report['success'] = (
            local_leakage == 0 and 
            remote_fixes['success'] and 
            final_remote_analysis.get('leakage_count', -1) == 0
        )
        
        # 5. Generate comprehensive report
        print("\n📋 GENERATING SYNCHRONIZATION REPORT...")
        with open('complete_timestamp_sync_report.json', 'w') as f:
            json.dump(sync_report, f, indent=2)
        
        print("📄 Complete sync report saved to: complete_timestamp_sync_report.json")
        
        # 6. Summary
        print("\n" + "=" * 65)
        if sync_report['success']:
            print("🏆 COMPLETE SYNCHRONIZATION SUCCESS!")
            print("✅ Both local and remote databases are temporally consistent")
            print("✅ Data leakage eliminated from both systems")
            print("✅ Temporal constraints implemented on both databases")
        else:
            print("⚠️  SYNCHRONIZATION COMPLETED WITH WARNINGS")
            print("📋 Review the detailed report for any remaining issues")
        
        print("=" * 65)
        
        return sync_report

def main():
    """Main function to run complete timestamp synchronization"""
    
    sync = RemoteTimestampSync()
    sync.run_complete_sync()

if __name__ == "__main__":
    main()

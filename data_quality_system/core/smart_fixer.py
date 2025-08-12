#!/usr/bin/env python3
"""
Smart Data Quality Auto-Fixer
Automatically generates and executes fixes for detected data quality issues
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import yfinance as yf
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intelligent_analyzer import IntelligentDataQualityAnalyzer

class SmartDataQualityFixer:
    def __init__(self, db_path=None):
        if db_path is None:
            # Try to find the database automatically
            possible_paths = [
                "../data/trading_unified.db",
                "../../data/trading_unified.db", 
                "/root/test/data/trading_unified.db",
                "data/trading_unified.db"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
            else:
                db_path = "../data/trading_unified.db"  # Default fallback
        self.db_path = db_path
        self.analyzer = IntelligentDataQualityAnalyzer(db_path)
        self.fixes_applied = []
        
    def auto_fix_round_number_prices(self, affected_records):
        """Automatically fix round number prices using market data"""
        fixes = []
        conn = sqlite3.connect(self.db_path)
        
        for record_id in affected_records:
            try:
                # Get record details
                record = pd.read_sql_query(
                    "SELECT * FROM enhanced_outcomes WHERE id = ?", 
                    conn, params=[record_id]
                ).iloc[0]
                
                symbol = record['symbol']
                date = pd.to_datetime(record['created_at']).date()
                
                # Get market data
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=date - timedelta(days=2), end=date + timedelta(days=2))
                
                if not hist.empty:
                    # Use closest available price
                    closest_price = hist['Close'].iloc[0]
                    
                    # Update database
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE enhanced_outcomes SET entry_price = ? WHERE id = ?",
                        [closest_price, record_id]
                    )
                    
                    # Recalculate return
                    if not pd.isna(record['exit_price_1d']):
                        new_return = ((record['exit_price_1d'] - closest_price) / closest_price) * 100
                        cursor.execute(
                            "UPDATE enhanced_outcomes SET return_pct = ? WHERE id = ?",
                            [new_return, record_id]
                        )
                    
                    fixes.append({
                        'record_id': record_id,
                        'symbol': symbol,
                        'old_price': record['entry_price'],
                        'new_price': closest_price,
                        'status': 'fixed'
                    })
                    
            except Exception as e:
                fixes.append({
                    'record_id': record_id,
                    'status': 'error',
                    'error': str(e)
                })
                
        conn.commit()
        conn.close()
        
        return fixes
    
    def auto_fix_missing_exit_prices(self, affected_records):
        """Automatically backfill missing exit prices"""
        fixes = []
        conn = sqlite3.connect(self.db_path)
        
        for record_id in affected_records:
            try:
                record = pd.read_sql_query(
                    "SELECT * FROM enhanced_outcomes WHERE id = ?", 
                    conn, params=[record_id]
                ).iloc[0]
                
                symbol = record['symbol']
                entry_date = pd.to_datetime(record['created_at']).date()
                exit_date = entry_date + timedelta(days=1)
                
                # Get exit price
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=exit_date, end=exit_date + timedelta(days=3))
                
                if not hist.empty:
                    exit_price = hist['Close'].iloc[0]
                    
                    # Update database
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE enhanced_outcomes SET exit_price_1d = ? WHERE id = ?",
                        [exit_price, record_id]
                    )
                    
                    # Calculate return
                    return_pct = ((exit_price - record['entry_price']) / record['entry_price']) * 100
                    cursor.execute(
                        "UPDATE enhanced_outcomes SET return_pct = ? WHERE id = ?",
                        [return_pct, record_id]
                    )
                    
                    fixes.append({
                        'record_id': record_id,
                        'symbol': symbol,
                        'exit_price': exit_price,
                        'return_pct': return_pct,
                        'status': 'fixed'
                    })
                    
            except Exception as e:
                fixes.append({
                    'record_id': record_id,
                    'status': 'error',
                    'error': str(e)
                })
                
        conn.commit()
        conn.close()
        
        return fixes
    
    def auto_fix_extreme_returns(self, affected_records):
        """Fix obviously incorrect return calculations"""
        fixes = []
        conn = sqlite3.connect(self.db_path)
        
        for record_id in affected_records:
            try:
                record = pd.read_sql_query(
                    "SELECT * FROM enhanced_outcomes WHERE id = ?", 
                    conn, params=[record_id]
                ).iloc[0]
                
                # Recalculate return with proper formula
                if not pd.isna(record['entry_price']) and not pd.isna(record['exit_price_1d']):
                    correct_return = ((record['exit_price_1d'] - record['entry_price']) / record['entry_price']) * 100
                    
                    # Only fix if the corrected return is reasonable (-50% to 50%)
                    if -50 <= correct_return <= 50:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE enhanced_outcomes SET return_pct = ? WHERE id = ?",
                            [correct_return, record_id]
                        )
                        
                        fixes.append({
                            'record_id': record_id,
                            'old_return': record['return_pct'],
                            'new_return': correct_return,
                            'status': 'fixed'
                        })
                    else:
                        fixes.append({
                            'record_id': record_id,
                            'status': 'needs_manual_review',
                            'reason': 'corrected_return_still_extreme'
                        })
                        
            except Exception as e:
                fixes.append({
                    'record_id': record_id,
                    'status': 'error',
                    'error': str(e)
                })
                
        conn.commit()
        conn.close()
        
        return fixes
    
    def generate_custom_fix_script(self, anomaly):
        """Generate custom Python script for complex fixes"""
        script_content = f"""#!/usr/bin/env python3
# Auto-generated fix script for: {anomaly['type']}
# Generated: {datetime.now().isoformat()}
# Affected records: {len(anomaly.get('affected_records', []))}

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def fix_{anomaly['type']}():
    \"\"\"
    {anomaly['description']}
    \"\"\"
    db_path = "../data/trading_unified.db"
    conn = sqlite3.connect(db_path)
    
    affected_records = {anomaly.get('affected_records', [])}
    
    print(f"Fixing {{len(affected_records)}} records for {anomaly['type']}")
    
    # Add specific fix logic here based on anomaly type
    fixes_applied = 0
    
    for record_id in affected_records:
        try:
            # Get record
            record = pd.read_sql_query(
                "SELECT * FROM enhanced_outcomes WHERE id = ?", 
                conn, params=[record_id]
            ).iloc[0]
            
            # Apply fix logic (customize based on anomaly type)
            print(f"Processing record {{record_id}}: {{record['symbol']}}")
            
            # Example fix - customize as needed
            # cursor = conn.cursor()
            # cursor.execute("UPDATE enhanced_outcomes SET ... WHERE id = ?", [..., record_id])
            
            fixes_applied += 1
            
        except Exception as e:
            print(f"Error fixing record {{record_id}}: {{e}}")
    
    conn.commit()
    conn.close()
    
    print(f"Successfully applied {{fixes_applied}} fixes")
    return fixes_applied

if __name__ == "__main__":
    fix_{anomaly['type']}()
"""
        
        script_filename = f"automation/auto_fix_{anomaly['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        with open(script_filename, 'w') as f:
            f.write(script_content)
            
        return script_filename
    
    def run_intelligent_auto_fix(self, dry_run=True):
        """Run automated fixes based on quality analysis"""
        print("🤖 Running Intelligent Auto-Fix System...")
        
        # First, run quality analysis
        report = self.analyzer.run_comprehensive_analysis()
        
        total_fixes = 0
        fix_results = {}
        
        # Process each type of anomaly
        for anomaly_type, anomalies in report['anomalies'].items():
            for anomaly in anomalies:
                if anomaly['severity'] == 'critical' and not dry_run:
                    
                    if anomaly['type'] == 'round_number_bias':
                        fixes = self.auto_fix_round_number_prices(anomaly['affected_records'])
                        fix_results['round_number_fixes'] = fixes
                        total_fixes += len([f for f in fixes if f['status'] == 'fixed'])
                        
                    elif anomaly['type'] == 'missing_exit_prices':
                        fixes = self.auto_fix_missing_exit_prices(anomaly['affected_records'])
                        fix_results['exit_price_fixes'] = fixes
                        total_fixes += len([f for f in fixes if f['status'] == 'fixed'])
                        
                    elif anomaly['type'] == 'extreme_returns':
                        fixes = self.auto_fix_extreme_returns(anomaly['affected_records'])
                        fix_results['return_fixes'] = fixes
                        total_fixes += len([f for f in fixes if f['status'] == 'fixed'])
                        
                    else:
                        # Generate custom fix script for complex issues
                        script_file = self.generate_custom_fix_script(anomaly)
                        fix_results[f'custom_script_{anomaly["type"]}'] = script_file
        
        # Generate summary report
        fix_report = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'dry_run' if dry_run else 'live_fix',
            'original_analysis': report,
            'fixes_applied': fix_results,
            'total_fixes': total_fixes,
            'status': 'completed'
        }
        
        # Save fix report
        fix_dir = "../data/fix_reports"
        os.makedirs(fix_dir, exist_ok=True)
        report_file = f"{fix_dir}/auto_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(fix_report, f, indent=2)
        
        print(f"\n🎯 Auto-Fix Results:")
        print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE FIXES'}")
        print(f"   Fixes Applied: {total_fixes}")
        print(f"   Report Saved: {report_file}")
        
        return fix_report

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Smart Data Quality Auto-Fixer')
    parser.add_argument('--live', action='store_true', help='Apply fixes (default is dry run)')
    parser.add_argument('--force', action='store_true', help='Force fix critical issues')
    
    args = parser.parse_args()
    
    fixer = SmartDataQualityFixer()
    
    if args.live:
        print("⚠️  LIVE MODE: Will apply actual fixes to database")
        if not args.force:
            confirm = input("Are you sure? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled.")
                return
                
        report = fixer.run_intelligent_auto_fix(dry_run=False)
    else:
        print("🔍 DRY RUN MODE: Analysis only, no fixes applied")
        report = fixer.run_intelligent_auto_fix(dry_run=True)
    
    return report

if __name__ == "__main__":
    main()

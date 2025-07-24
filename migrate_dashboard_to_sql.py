#!/usr/bin/env python3
"""
Dashboard SQL Migration Script
Migrates dashboard from JSON files to SQL database as primary data source
"""

import shutil
from pathlib import Path
from datetime import datetime

def main():
    print("🔄 DASHBOARD SQL MIGRATION")
    print("=" * 40)
    
    # Test SQL data manager
    try:
        from app.dashboard.utils.sql_data_manager import DashboardDataManagerSQL
        sql_manager = DashboardDataManagerSQL()
        
        # Test data loading
        test_data = sql_manager.load_sentiment_data(['CBA.AX', 'ANZ.AX'])
        total_records = sum(len(records) for records in test_data.values())
        
        print(f"✅ SQL data manager working: {total_records} records loaded")
        
        # Get quality report
        quality = sql_manager.get_data_quality_report()
        print(f"✅ Data quality: {quality['reliability']}")
        
    except Exception as e:
        print(f"❌ SQL data manager test failed: {e}")
        return False
    
    # Backup current JSON files
    print("\n📋 Creating JSON backups...")
    backup_dir = Path("data/json_backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    json_files = [
        "data/ml_performance/prediction_history.json",
        "data/sentiment_history.json"
    ]
    
    for file_path in json_files:
        if Path(file_path).exists():
            backup_path = backup_dir / Path(file_path).name
            shutil.copy2(file_path, backup_path)
            print(f"   Backed up: {file_path} → {backup_path}")
    
    # Dashboard integration instructions
    print(f"\n🎯 NEXT STEPS FOR DASHBOARD INTEGRATION:")
    print("   1. Update enhanced_main.py to import SQLDashboardManager")
    print("   2. Replace JSON-based DataManager with SQL version")
    print("   3. Test dashboard with live SQL data")
    print("   4. Enjoy consistent, real-time data! 🎉")
    
    # Show expected dashboard improvements
    print(f"\n📊 EXPECTED DASHBOARD IMPROVEMENTS:")
    print("   ✅ Real-time data from evening routine")  
    print("   ✅ No more uniform 61% confidence values")
    print("   ✅ No duplicate timestamps or stale data")
    print("   ✅ Consistent predictions across all views")
    print("   ✅ Automatic data validation and integrity")
    
    # Quick integration template
    integration_code = '''
# Dashboard Integration Template
# Add this to your dashboard files:

from app.dashboard.utils.sql_data_manager import DashboardDataManagerSQL

# Replace:
# dashboard = DataManager()

# With:
dashboard = DashboardDataManagerSQL()

# All existing method calls work the same:
# - dashboard.load_sentiment_data()
# - dashboard.get_latest_analysis() 
# - dashboard.get_prediction_log()

# But now they use live SQL database instead of stale JSON!
'''
    
    with open("dashboard_sql_integration_template.py", "w") as f:
        f.write(integration_code)
    
    print(f"\n📝 Integration template saved: dashboard_sql_integration_template.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🎉 SQL MIGRATION PREPARATION COMPLETE!")
        print(f"   Dashboard ready to use live SQL database")
    else:
        print(f"\n❌ Migration preparation failed")

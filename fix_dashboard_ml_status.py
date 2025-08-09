#!/usr/bin/env python3
"""
Fix Dashboard ML Status Display Issues
"""

import sqlite3
import json
from datetime import datetime

def diagnose_dashboard_data_discrepancy():
    """Diagnose why dashboard shows old data"""
    
    print("🔍 Dashboard Data Discrepancy Analysis")
    print("=" * 50)
    
    db_path = './data/trading_unified.db'
    
    try:
        conn = sqlite3.connect(db_path)
        
        print("📊 Model Performance Enhanced Table Analysis:")
        
        # Check what the dashboard query returns (ORDER BY created_at DESC)
        cursor = conn.execute("""
            SELECT 
                training_date,
                training_samples, 
                direction_accuracy_1h,
                created_at,
                id
            FROM model_performance_enhanced 
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        
        dashboard_results = cursor.fetchall()
        
        print("\n🖥️ What Dashboard Sees (ORDER BY created_at DESC):")
        for i, row in enumerate(dashboard_results):
            training_date, samples, accuracy, created_at, record_id = row
            print(f"   {i+1}. ID: {record_id}")
            print(f"      Training Date: {training_date}")
            print(f"      Created At: {created_at}")
            print(f"      Samples: {samples}")
            print(f"      Accuracy: {accuracy:.3f}")
            
            if i == 0:  # This is what dashboard shows
                created_time = datetime.fromisoformat(created_at)
                training_time = datetime.fromisoformat(training_date)
                hours_since_created = (datetime.now() - created_time).total_seconds() / 3600
                hours_since_training = (datetime.now() - training_time).total_seconds() / 3600
                
                print(f"      Hours since created_at: {hours_since_created:.1f}")
                print(f"      Hours since training_date: {hours_since_training:.1f}")
        
        # Check what should be the latest (ORDER BY training_date DESC)
        print(f"\n🧠 What Should Be Latest (ORDER BY training_date DESC):")
        cursor = conn.execute("""
            SELECT 
                training_date,
                training_samples, 
                direction_accuracy_1h,
                created_at,
                id
            FROM model_performance_enhanced 
            ORDER BY training_date DESC 
            LIMIT 3
        """)
        
        actual_latest = cursor.fetchall()
        
        for i, row in enumerate(actual_latest):
            training_date, samples, accuracy, created_at, record_id = row
            print(f"   {i+1}. ID: {record_id}")
            print(f"      Training Date: {training_date}")
            print(f"      Created At: {created_at}")
            print(f"      Samples: {samples}")
            print(f"      Accuracy: {accuracy:.3f}")
        
        # Check if there's a discrepancy
        dashboard_latest = dashboard_results[0] if dashboard_results else None
        actual_latest_record = actual_latest[0] if actual_latest else None
        
        if dashboard_latest and actual_latest_record:
            if dashboard_latest[4] != actual_latest_record[4]:  # Different IDs
                print(f"\n❌ DISCREPANCY FOUND!")
                print(f"   Dashboard shows: Record ID {dashboard_latest[4]} (training: {dashboard_latest[0]})")
                print(f"   Latest should be: Record ID {actual_latest_record[4]} (training: {actual_latest_record[0]})")
                
                return True, dashboard_latest, actual_latest_record
            else:
                print(f"\n✅ No discrepancy - dashboard shows correct latest record")
                return False, None, None
        else:
            print(f"\n❌ No training records found")
            return False, None, None
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")
        return False, None, None

def fix_dashboard_query():
    """Fix the dashboard to use training_date instead of created_at"""
    
    print(f"\n🔧 Fixing Dashboard Query Logic")
    print("=" * 35)
    
    # Read current dashboard.py
    try:
        with open('dashboard.py', 'r') as f:
            content = f.read()
        
        # Check current query in fetch_enhanced_ml_training_metrics
        if 'ORDER BY created_at DESC' in content:
            print("❌ Found problematic query: ORDER BY created_at DESC")
            
            # Replace with training_date ordering
            updated_content = content.replace(
                'ORDER BY created_at DESC',
                'ORDER BY training_date DESC'
            )
            
            # Write back the fix
            with open('dashboard.py', 'w') as f:
                f.write(updated_content)
            
            print("✅ Fixed dashboard query to use: ORDER BY training_date DESC")
            print("🔄 Dashboard will now show latest training by actual training time")
            
            return True
        else:
            print("ℹ️ Query already uses correct ordering or not found")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing dashboard: {e}")
        return False

def test_dashboard_fix():
    """Test if the dashboard fix works"""
    
    print(f"\n🧪 Testing Dashboard Fix")
    print("=" * 25)
    
    try:
        # Import and test the dashboard function
        import sys
        sys.path.append('.')
        
        # Dynamically import the fixed function
        import importlib
        import dashboard
        importlib.reload(dashboard)
        
        # Test the function
        metrics = dashboard.fetch_enhanced_ml_training_metrics()
        
        if metrics and metrics.get('last_training'):
            last_training = metrics['last_training']
            hours_ago = (datetime.now() - datetime.fromisoformat(last_training)).total_seconds() / 3600
            
            print(f"✅ Dashboard function now returns:")
            print(f"   Training samples: {metrics.get('training_samples', 'N/A')}")
            print(f"   Last training: {last_training}")
            print(f"   Hours ago: {hours_ago:.1f}")
            print(f"   Accuracy: {metrics.get('direction_accuracy_4h', 'N/A'):.3f}")
            
            return True
        else:
            print(f"❌ Dashboard function returned no data")
            return False
            
    except Exception as e:
        print(f"❌ Error testing dashboard: {e}")
        return False

def create_manual_dashboard_update():
    """Create a manual update script for the dashboard"""
    
    print(f"\n📝 Creating Manual Dashboard Update")
    print("=" * 35)
    
    try:
        # Get the latest training data
        conn = sqlite3.connect('./data/trading_unified.db')
        cursor = conn.execute("""
            SELECT 
                training_date,
                training_samples, 
                direction_accuracy_1h,
                direction_accuracy_4h,
                direction_accuracy_1d
            FROM model_performance_enhanced 
            ORDER BY training_date DESC 
            LIMIT 1
        """)
        
        latest = cursor.fetchone()
        conn.close()
        
        if latest:
            training_date, samples, acc_1h, acc_4h, acc_1d = latest
            hours_ago = (datetime.now() - datetime.fromisoformat(training_date)).total_seconds() / 3600
            
            print(f"📊 Latest Training Data for Dashboard:")
            print(f"   Training Date: {training_date}")
            print(f"   Samples: {samples}")
            print(f"   1h Accuracy: {acc_1h:.3f}")
            print(f"   4h Accuracy: {acc_4h:.3f}")
            print(f"   1d Accuracy: {acc_1d:.3f}")
            print(f"   Hours Ago: {hours_ago:.1f}")
            
            # Create update SQL for dashboard
            print(f"\n📋 Manual Dashboard Update (if needed):")
            print(f"   Refresh your dashboard page")
            print(f"   Or restart Streamlit: streamlit run dashboard.py")
            
            return True
        else:
            print(f"❌ No training data found")
            return False
            
    except Exception as e:
        print(f"❌ Error creating update: {e}")
        return False

def main():
    print("🔧 Dashboard ML Status Fix Utility")
    print("=" * 40)
    
    # Step 1: Diagnose the issue
    has_discrepancy, dashboard_latest, actual_latest = diagnose_dashboard_data_discrepancy()
    
    if has_discrepancy:
        print(f"\n🛠️ Fixing the discrepancy...")
        
        # Step 2: Fix the dashboard query
        if fix_dashboard_query():
            print(f"\n🔄 Dashboard query fixed!")
            
            # Step 3: Test the fix
            if test_dashboard_fix():
                print(f"\n✅ Dashboard fix successful!")
                print(f"\n🎯 Next Steps:")
                print(f"   1. Refresh your remote dashboard")
                print(f"   2. The 'Last Training' should now show recent time")
                print(f"   3. Training samples should be up to date")
            else:
                print(f"\n⚠️ Dashboard fix applied but needs manual restart")
                create_manual_dashboard_update()
        else:
            print(f"\n⚠️ Could not automatically fix dashboard")
            create_manual_dashboard_update()
    else:
        print(f"\n✅ No discrepancy found - dashboard should be showing correct data")
        
        # Still create manual update for verification
        create_manual_dashboard_update()

if __name__ == "__main__":
    main()

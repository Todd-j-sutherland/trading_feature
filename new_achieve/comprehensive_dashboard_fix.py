#!/usr/bin/env python3
"""
Comprehensive Dashboard Fix - Update all outdated references
"""

import sqlite3
import re
from datetime import datetime

def find_all_outdated_dashboard_queries():
    """Find all queries in dashboard.py that might show old data"""
    
    print("🔍 Comprehensive Dashboard Analysis")
    print("=" * 40)
    
    try:
        with open('dashboard.py', 'r') as f:
            content = f.read()
        
        # Find all problematic patterns
        issues_found = []
        
        # 1. ORDER BY created_at instead of training_date
        created_at_matches = re.findall(r'ORDER BY created_at.*', content)
        if created_at_matches:
            for match in created_at_matches:
                issues_found.append(f"❌ Found: {match.strip()}")
        
        # 2. References to old database tables
        old_table_patterns = [
            r'FROM model_performance[^_]',  # basic model_performance (not enhanced)
            r'FROM trading_data\.db',       # old database files
            r'FROM enhanced_training_data\.db',  # old training data
        ]
        
        for pattern in old_table_patterns:
            matches = re.findall(pattern, content)
            if matches:
                for match in matches:
                    issues_found.append(f"❌ Old table reference: {match}")
        
        # 3. Hardcoded sample counts
        sample_patterns = [
            r'171',  # Old sample count
            r'170',  # Near old sample count
        ]
        
        for pattern in sample_patterns:
            matches = re.findall(rf'\b{pattern}\b', content)
            if matches:
                issues_found.append(f"❌ Hardcoded old sample count: {pattern}")
        
        print(f"📊 Analysis Results:")
        if issues_found:
            print(f"   Found {len(issues_found)} potential issues:")
            for issue in issues_found[:10]:  # Show first 10
                print(f"   {issue}")
            if len(issues_found) > 10:
                print(f"   ... and {len(issues_found) - 10} more")
        else:
            print("   ✅ No obvious issues found")
        
        return issues_found
        
    except Exception as e:
        print(f"❌ Error analyzing dashboard: {e}")
        return []

def get_current_database_state():
    """Get current state of the database for reference"""
    
    print(f"\n📊 Current Database State")
    print("=" * 30)
    
    try:
        conn = sqlite3.connect('./data/trading_unified.db')
        
        # Get latest training info
        cursor = conn.execute("""
            SELECT 
                training_date,
                training_samples, 
                direction_accuracy_1h,
                direction_accuracy_4h,
                direction_accuracy_1d,
                id
            FROM model_performance_enhanced 
            ORDER BY training_date DESC 
            LIMIT 1
        """)
        
        latest = cursor.fetchone()
        
        if latest:
            training_date, samples, acc_1h, acc_4h, acc_1d, record_id = latest
            hours_ago = (datetime.now() - datetime.fromisoformat(training_date)).total_seconds() / 3600
            
            print(f"✅ Latest Training Record (ID: {record_id}):")
            print(f"   Date: {training_date}")
            print(f"   Samples: {samples}")
            print(f"   1h Accuracy: {acc_1h:.3f}")
            print(f"   4h Accuracy: {acc_4h:.3f}")
            print(f"   1d Accuracy: {acc_1d:.3f}")
            print(f"   Hours ago: {hours_ago:.1f}")
            
            return {
                'latest_samples': samples,
                'latest_training': training_date,
                'latest_accuracy_1h': acc_1h,
                'latest_accuracy_4h': acc_4h,
                'latest_accuracy_1d': acc_1d,
                'hours_ago': hours_ago
            }
        else:
            print("❌ No training records found")
            return None
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        return None

def fix_all_dashboard_queries():
    """Comprehensive fix for all dashboard queries"""
    
    print(f"\n🔧 Comprehensive Dashboard Fix")
    print("=" * 35)
    
    try:
        with open('dashboard.py', 'r') as f:
            content = f.read()
        
        fixes_applied = []
        
        # Fix 1: All ORDER BY created_at to ORDER BY training_date
        old_pattern = r'ORDER BY created_at DESC'
        new_pattern = 'ORDER BY training_date DESC'
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            fixes_applied.append("✅ Fixed: ORDER BY created_at → ORDER BY training_date")
        
        # Fix 2: Ensure all model performance queries use enhanced table
        old_pattern = r'FROM model_performance\s+'
        new_pattern = 'FROM model_performance_enhanced '
        
        content = re.sub(old_pattern, new_pattern, content)
        fixes_applied.append("✅ Fixed: model_performance → model_performance_enhanced")
        
        # Fix 3: Update any hardcoded 171 references to be dynamic
        # Look for specific contexts where 171 appears
        if '171' in content:
            # Be careful - only replace obvious training sample references
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '171' in line and ('sample' in line.lower() or 'training' in line.lower()):
                    print(f"⚠️ Found potential hardcoded sample count on line {i+1}: {line.strip()}")
                    fixes_applied.append(f"⚠️ Manual review needed: Line {i+1} contains '171'")
        
        # Fix 4: Ensure database path consistency
        old_patterns = [
            './data/trading_data.db',
            './data/enhanced_training_data.db'
        ]
        
        for old_path in old_patterns:
            if old_path in content:
                content = content.replace(old_path, './data/trading_unified.db')
                fixes_applied.append(f"✅ Fixed database path: {old_path} → ./data/trading_unified.db")
        
        # Fix 5: Update fetch functions to use latest data
        # Look for fetch_enhanced_ml_training_metrics function specifically
        fetch_function_pattern = r'(def fetch_enhanced_ml_training_metrics.*?ORDER BY )(created_at)( DESC)'
        if re.search(fetch_function_pattern, content, re.DOTALL):
            content = re.sub(fetch_function_pattern, r'\1training_date\3', content, flags=re.DOTALL)
            fixes_applied.append("✅ Fixed: fetch_enhanced_ml_training_metrics function")
        
        # Write the fixed content back
        with open('dashboard.py', 'w') as f:
            f.write(content)
        
        print(f"📝 Applied {len(fixes_applied)} fixes:")
        for fix in fixes_applied:
            print(f"   {fix}")
        
        return True, fixes_applied
        
    except Exception as e:
        print(f"❌ Error fixing dashboard: {e}")
        return False, []

def create_dashboard_cache_clear():
    """Create commands to clear dashboard cache"""
    
    print(f"\n🔄 Dashboard Cache Clear Commands")
    print("=" * 35)
    
    cache_clear_commands = [
        "# Clear Streamlit cache",
        "rm -rf ~/.streamlit/cache/",
        "",
        "# Clear browser cache (restart browser or hard refresh)",
        "# Ctrl+F5 or Cmd+Shift+R",
        "",
        "# Restart Streamlit completely",
        "pkill -f streamlit",
        "nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &",
    ]
    
    print("💡 Cache clearing commands:")
    for cmd in cache_clear_commands:
        print(f"   {cmd}")
    
    return cache_clear_commands

def verify_dashboard_data_sources():
    """Verify all data sources in dashboard are up to date"""
    
    print(f"\n🔍 Dashboard Data Source Verification")
    print("=" * 45)
    
    try:
        with open('dashboard.py', 'r') as f:
            content = f.read()
        
        # Find all SQL queries
        sql_patterns = [
            r'SELECT.*FROM.*model_performance.*',
            r'SELECT.*FROM.*enhanced_outcomes.*',
            r'SELECT.*FROM.*enhanced_evening_analysis.*'
        ]
        
        print("📊 Found SQL queries:")
        for pattern in sql_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for i, match in enumerate(matches[:3]):  # Show first 3 of each type
                clean_match = ' '.join(match.split())[:100] + '...'
                print(f"   {clean_match}")
        
        # Check for ORDER BY clauses
        order_by_matches = re.findall(r'ORDER BY.*', content)
        print(f"\n📋 ORDER BY clauses found: {len(order_by_matches)}")
        for match in order_by_matches[:5]:  # Show first 5
            print(f"   {match.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying data sources: {e}")
        return False

def main():
    print("🔧 Comprehensive Dashboard Fix Utility")
    print("=" * 45)
    
    # Step 1: Analyze current issues
    issues = find_all_outdated_dashboard_queries()
    
    # Step 2: Get current database state
    db_state = get_current_database_state()
    
    # Step 3: Apply comprehensive fixes
    success, fixes = fix_all_dashboard_queries()
    
    if success:
        print(f"\n✅ Dashboard fixes applied successfully!")
        
        # Step 4: Verification
        verify_dashboard_data_sources()
        
        # Step 5: Cache clearing instructions
        create_dashboard_cache_clear()
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Push updated dashboard.py to remote server")
        print(f"   2. Restart Streamlit on remote")
        print(f"   3. Clear browser cache")
        print(f"   4. Verify dashboard shows 178 samples and recent training")
        
        if db_state:
            print(f"\n📊 Expected Dashboard Values:")
            print(f"   Training Samples: {db_state['latest_samples']}")
            print(f"   Last Training: {db_state['hours_ago']:.1f}h ago")
            print(f"   Success Rate: {db_state['latest_accuracy_4h']:.1%}")
            
    else:
        print(f"\n❌ Dashboard fix failed")
    
    print(f"\n🚀 After fixes, run this to push to remote:")
    print(f"   scp -i ~/.ssh/id_rsa dashboard.py root@170.64.199.151:/root/test/")

if __name__ == "__main__":
    main()

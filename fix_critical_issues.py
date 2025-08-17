#!/usr/bin/env python3
"""
Fix Future Features Issue
Remove future features that are triggering data leakage protection
"""

import sqlite3
from datetime import datetime
from pathlib import Path

def fix_future_features():
    """Remove future features that trigger data leakage protection"""
    print("🔧 FIXING FUTURE FEATURES ISSUE")
    print("=" * 40)
    
    db_path = Path(__file__).parent / "data" / "trading_predictions.db"
    
    if not db_path.exists():
        print("❌ Database not found")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check current future features
        cursor.execute("""
        SELECT feature_id, symbol, timestamp
        FROM enhanced_features 
        WHERE datetime(timestamp) > datetime('now')
        ORDER BY timestamp
        """)
        
        future_features = cursor.fetchall()
        print(f"🔍 Found {len(future_features)} future features")
        
        if future_features:
            print("🗑️ Removing future features:")
            for feature_id, symbol, timestamp in future_features:
                print(f"   Removing: {symbol} at {timestamp}")
            
            # Remove future features
            cursor.execute("""
            DELETE FROM enhanced_features 
            WHERE datetime(timestamp) > datetime('now')
            """)
            
            deleted_count = cursor.rowcount
            print(f"✅ Deleted {deleted_count} future features")
            
            conn.commit()
        else:
            print("✅ No future features found")
        
        # Verify fix
        cursor.execute("""
        SELECT COUNT(*) FROM enhanced_features 
        WHERE datetime(timestamp) > datetime('now')
        """)
        remaining_future = cursor.fetchone()[0]
        
        if remaining_future == 0:
            print("✅ All future features removed")
            
            # Test database insertion now
            try:
                test_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                test_id = f"TEST_{datetime.now().strftime('%H%M%S')}"
                
                cursor.execute('''
                INSERT INTO predictions (
                    prediction_id, symbol, prediction_timestamp, predicted_action,
                    action_confidence, predicted_direction, predicted_magnitude,
                    model_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    'TEST.AX',
                    test_timestamp,
                    'BUY',
                    0.85,
                    1,
                    0.85,
                    'test_v1.0',
                    datetime.now().isoformat()
                ))
                
                # Clean up test data
                cursor.execute("DELETE FROM predictions WHERE prediction_id = ?", (test_id,))
                conn.commit()
                
                print("✅ Database insertion test: NOW WORKING!")
                
            except Exception as e:
                print(f"❌ Database insertion still failing: {e}")
        else:
            print(f"⚠️ {remaining_future} future features still remain")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing future features: {e}")
        return False

def update_requirements():
    """Update requirements.txt with working versions"""
    print("\n🔧 UPDATING REQUIREMENTS.TXT")
    print("=" * 40)
    
    # Add missing dependencies to requirements
    additional_deps = [
        "huggingface-hub>=0.34.0",
        "safetensors>=0.4.3",
        "tokenizers>=0.21.0"
    ]
    
    req_file = Path(__file__).parent / "requirements.txt"
    
    try:
        # Read current requirements
        with open(req_file, 'r') as f:
            content = f.read()
        
        # Add missing deps if not present
        lines = content.split('\n')
        added = []
        
        for dep in additional_deps:
            dep_name = dep.split('>=')[0].split('==')[0]
            if not any(dep_name in line for line in lines):
                lines.append(dep)
                added.append(dep)
        
        if added:
            # Write updated requirements
            with open(req_file, 'w') as f:
                f.write('\n'.join(lines))
            
            print(f"✅ Added {len(added)} dependencies to requirements.txt:")
            for dep in added:
                print(f"   + {dep}")
        else:
            print("✅ Requirements.txt already up to date")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating requirements: {e}")
        return False

def main():
    """Fix the main issues"""
    print("🎯 FIXING CRITICAL SYSTEM ISSUES")
    print("=" * 60)
    
    # Fix 1: Remove future features
    fix_future_features()
    
    # Fix 2: Update requirements
    update_requirements()
    
    print("\n🎉 CRITICAL FIXES COMPLETE")
    print("Database insertion should now work!")
    print("Run enhanced analysis again to verify...")

if __name__ == "__main__":
    main()

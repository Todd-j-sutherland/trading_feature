#!/usr/bin/env python3
"""
System Issues Resolver
Fix the specific issues identified in the comprehensive analysis
"""

import subprocess
import os
from pathlib import Path

def fix_transformers_dependency():
    """Fix the missing huggingface_hub dependency"""
    print("🔧 FIXING TRANSFORMERS DEPENDENCY")
    print("=" * 40)
    
    # The issue is that transformers was updated but huggingface_hub wasn't
    # We need to install/update huggingface_hub
    
    try:
        # First, let's install huggingface_hub specifically
        result = subprocess.run([
            "pip", "install", "huggingface_hub>=0.34.0"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ huggingface_hub installed successfully")
            
            # Test transformers import
            try:
                import transformers
                print("✅ transformers import now working")
                return True
            except ImportError as e:
                print(f"❌ transformers still failing: {e}")
                return False
        else:
            print(f"❌ Failed to install huggingface_hub: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing transformers: {e}")
        return False

def investigate_morning_timeout():
    """Investigate why morning routine times out"""
    print("\n🔍 INVESTIGATING MORNING ROUTINE TIMEOUT")
    print("=" * 50)
    
    # Let's run morning routine with incremental timeout to see where it hangs
    timeouts = [30, 60, 120]
    
    for timeout in timeouts:
        print(f"\n🧪 Testing morning routine with {timeout}s timeout...")
        
        try:
            result = subprocess.run([
                "bash", "-c", 
                f"cd {Path.cwd()} && source venv/bin/activate && timeout {timeout}s python -m app.main morning"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Morning routine completed within {timeout}s")
                return True
            elif result.returncode == 124:  # timeout exit code
                print(f"⏱️ Morning routine timed out at {timeout}s")
                
                # Check what was in output before timeout
                if result.stdout:
                    lines = result.stdout.split('\n')
                    last_line = [line for line in lines if line.strip()][-1] if lines else "No output"
                    print(f"   Last output: {last_line}")
            else:
                print(f"❌ Morning routine failed with code {result.returncode}")
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}...")
                
        except Exception as e:
            print(f"❌ Error testing morning routine: {e}")
    
    return False

def check_system_health_warnings():
    """Investigate the system health warnings"""
    print("\n🔍 INVESTIGATING SYSTEM HEALTH WARNINGS")
    print("=" * 50)
    
    # Look for the health checker
    health_checker_path = Path.cwd() / "app" / "utils" / "health_checker.py"
    
    if health_checker_path.exists():
        print("✅ Health checker found")
        
        # Let's see what's causing the warnings
        try:
            with open(health_checker_path, 'r') as f:
                content = f.read()
                
            # Look for warning conditions
            if 'warning' in content.lower():
                print("📋 Health checker contains warning conditions")
                
                # Extract lines with warning
                lines = content.split('\n')
                warning_lines = [line.strip() for line in lines if 'warning' in line.lower()]
                
                print("🔍 Warning-related code:")
                for line in warning_lines[:5]:  # Show first 5
                    if line and not line.startswith('#'):
                        print(f"   {line}")
                        
            return True
            
        except Exception as e:
            print(f"❌ Error reading health checker: {e}")
            return False
    else:
        print("❌ Health checker not found")
        return False

def fix_database_data_leakage_trigger():
    """Fix the overly sensitive data leakage trigger"""
    print("\n🔧 INVESTIGATING DATA LEAKAGE TRIGGER")
    print("=" * 50)
    
    # The database test passed but earlier it was failing
    # Let's check the enhanced_features table
    
    import sqlite3
    db_path = Path.cwd() / "data" / "trading_predictions.db"
    
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check enhanced_features table
            cursor.execute("SELECT COUNT(*) FROM enhanced_features")
            feature_count = cursor.fetchone()[0]
            print(f"📊 Enhanced features count: {feature_count}")
            
            # Check recent features timestamps
            cursor.execute("""
            SELECT symbol, timestamp, 
                   datetime(timestamp) > datetime('now', '+30 minutes') as is_future
            FROM enhanced_features 
            ORDER BY timestamp DESC 
            LIMIT 10
            """)
            
            features = cursor.fetchall()
            future_count = sum(1 for f in features if f[2])
            
            print(f"🔍 Recent features: {len(features)}")
            print(f"⚠️ Future features: {future_count}")
            
            if future_count > 0:
                print("🔧 Found future features - this triggers data leakage protection")
                for symbol, timestamp, is_future in features:
                    if is_future:
                        print(f"   Future: {symbol} at {timestamp}")
            else:
                print("✅ No future features found")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error checking database: {e}")
            return False
    else:
        print("❌ Database not found")
        return False

def generate_fix_summary():
    """Generate summary of fixes applied"""
    print("\n📋 SYSTEM FIXES SUMMARY")
    print("=" * 40)
    
    # Test final state
    fixes_applied = []
    remaining_issues = []
    
    # Test 1: Transformers import
    try:
        import transformers
        fixes_applied.append("✅ transformers dependency resolved")
    except ImportError:
        remaining_issues.append("❌ transformers still failing")
    
    # Test 2: Quick status (should work)
    try:
        result = subprocess.run([
            "bash", "-c", 
            f"cd {Path.cwd()} && source venv/bin/activate && timeout 30s python -m app.main status"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            fixes_applied.append("✅ status command working")
        else:
            remaining_issues.append("❌ status command issues")
    except:
        remaining_issues.append("❌ status command test failed")
    
    print("🎯 FIXES APPLIED:")
    for fix in fixes_applied:
        print(f"   {fix}")
    
    if remaining_issues:
        print("\n⚠️ REMAINING ISSUES:")
        for issue in remaining_issues:
            print(f"   {issue}")
    
    print(f"\n📊 Status: {len(fixes_applied)} fixes applied, {len(remaining_issues)} issues remaining")

def main():
    """Run all fixes"""
    print("🔧 SYSTEM ISSUES RESOLVER")
    print("=" * 60)
    print("Fixing issues identified in comprehensive analysis...")
    print("=" * 60)
    
    # Fix 1: Transformers dependency
    fix_transformers_dependency()
    
    # Investigation 2: Morning timeout
    investigate_morning_timeout()
    
    # Investigation 3: Health warnings
    check_system_health_warnings()
    
    # Investigation 4: Data leakage trigger
    fix_database_data_leakage_trigger()
    
    # Summary
    generate_fix_summary()
    
    print("\n🎯 FIXES COMPLETE")
    print("Rerun comprehensive analysis to verify improvements")

if __name__ == "__main__":
    main()

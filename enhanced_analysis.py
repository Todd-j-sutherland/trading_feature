#!/usr/bin/env python3
"""
Enhanced Deep System Analysis with Virtual Environment Support
"""

import subprocess
import sqlite3
import os
from pathlib import Path
from datetime import datetime

def test_local_venv_system():
    """Test the local system using venv"""
    print("🔍 TESTING LOCAL SYSTEM WITH VENV")
    print("=" * 50)
    
    issues = []
    
    # Check if local venv exists
    venv_path = Path("venv/bin/activate")
    if not venv_path.exists():
        issues.append("❌ Local venv not found at venv/bin/activate")
        print("❌ Local venv not found - creating new one...")
        
        # Create virtual environment
        try:
            result = subprocess.run(["python3", "-m", "venv", "venv"], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print("✅ Created new virtual environment")
            else:
                issues.append(f"❌ Failed to create venv: {result.stderr}")
                return issues
        except Exception as e:
            issues.append(f"❌ Error creating venv: {e}")
            return issues
    else:
        print("✅ Local venv found")
    
    # Test commands with venv
    test_commands = [
        "status",
        "morning"
    ]
    
    for command in test_commands:
        print(f"\n🧪 Testing: {command} (with venv)")
        
        try:
            # Run with venv activation
            cmd = f"source venv/bin/activate && python -m app.main {command}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"  ✅ {command}: Success")
                
                # Check for warnings in output
                output = result.stdout + result.stderr
                if "Enhanced ML components not available" in output:
                    issues.append(f"⚠️  {command}: ML components not available")
                if "System health: warning" in output:
                    issues.append(f"⚠️  {command}: System health warning")
                if "Missing package" in output:
                    issues.append(f"⚠️  {command}: Missing packages")
                    
            else:
                issues.append(f"❌ {command}: Failed with code {result.returncode}")
                print(f"  ❌ {command}: Failed with code {result.returncode}")
                if result.stderr:
                    print(f"     Error: {result.stderr[:200]}")
                    
        except subprocess.TimeoutExpired:
            issues.append(f"❌ {command}: Timeout")
            print(f"  ⏱️  {command}: Timeout")
        except Exception as e:
            issues.append(f"❌ {command}: Error - {e}")
            print(f"  💥 {command}: Error - {e}")
    
    return issues

def test_remote_venv_system():
    """Test the remote system using trading_venv"""
    print("\n🔍 TESTING REMOTE SYSTEM WITH TRADING_VENV")
    print("=" * 50)
    
    issues = []
    
    # Check remote venv
    try:
        cmd = "ssh root@170.64.199.151 'ls -la /root/trading_venv/bin/activate'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Remote trading_venv found")
        else:
            issues.append("❌ Remote trading_venv not found")
            print("❌ Remote trading_venv not found")
            return issues
            
    except Exception as e:
        issues.append(f"❌ Cannot connect to remote system: {e}")
        return issues
    
    # Test remote database
    try:
        cmd = """ssh root@170.64.199.151 'cd /root/test && source /root/trading_venv/bin/activate && sqlite3 data/trading_predictions.db "SELECT COUNT(*) as predictions FROM predictions; SELECT COUNT(*) as outcomes FROM enhanced_outcomes; SELECT COUNT(*) as features FROM enhanced_features;"'"""
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 3:
                predictions = lines[0]
                outcomes = lines[1] 
                features = lines[2]
                
                print(f"📊 Remote Database Status:")
                print(f"   Predictions: {predictions}")
                print(f"   Enhanced Outcomes: {outcomes}")
                print(f"   Enhanced Features: {features}")
                
                if int(predictions) == 0:
                    issues.append("⚠️  Remote: No predictions in database")
                if int(outcomes) == 0:
                    issues.append("⚠️  Remote: No enhanced outcomes")
            else:
                issues.append("❌ Remote: Unexpected database response")
        else:
            issues.append(f"❌ Remote database check failed: {result.stderr}")
            
    except Exception as e:
        issues.append(f"❌ Remote database error: {e}")
    
    # Test remote system commands
    test_commands = ["status"]
    
    for command in test_commands:
        print(f"\n🧪 Testing remote: {command}")
        
        try:
            cmd = f"""ssh root@170.64.199.151 'cd /root/test && source /root/trading_venv/bin/activate && python -m app.main {command}'"""
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"  ✅ Remote {command}: Success")
            else:
                issues.append(f"❌ Remote {command}: Failed with code {result.returncode}")
                print(f"  ❌ Remote {command}: Failed")
                
        except subprocess.TimeoutExpired:
            issues.append(f"❌ Remote {command}: Timeout")
            print(f"  ⏱️  Remote {command}: Timeout")
        except Exception as e:
            issues.append(f"❌ Remote {command}: Error - {e}")
            print(f"  💥 Remote {command}: Error - {e}")
    
    return issues

def analyze_database_constraints():
    """Analyze database constraints that might be causing issues"""
    print("\n🔍 ANALYZING DATABASE CONSTRAINTS")
    print("=" * 50)
    
    issues = []
    
    db_path = "data/trading_predictions.db"
    if not Path(db_path).exists():
        issues.append("❌ Local database not found")
        return issues
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check indexes on predictions table
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='predictions'")
        indexes = cursor.fetchall()
        
        print(f"📋 Found {len(indexes)} indexes on predictions table:")
        unique_indexes = []
        
        for name, sql in indexes:
            if sql and 'UNIQUE' in sql.upper():
                unique_indexes.append((name, sql))
                print(f"   🔒 UNIQUE: {name}")
            else:
                print(f"   📊 INDEX: {name}")
        
        if len(unique_indexes) > 1:
            # Check if multiple unique indexes are on the same columns
            symbol_date_indexes = [idx for idx in unique_indexes if 'symbol' in idx[1] and 'date' in idx[1]]
            if len(symbol_date_indexes) > 1:
                issues.append(f"❌ Found {len(symbol_date_indexes)} conflicting UNIQUE indexes on symbol+date")
                print(f"⚠️  CONSTRAINT CONFLICT: {len(symbol_date_indexes)} unique indexes on symbol+date")
                
                for name, sql in symbol_date_indexes:
                    print(f"     • {name}")
        
        # Check if we can insert a test record
        try:
            test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            cursor.execute("""
                INSERT INTO predictions (prediction_id, symbol, prediction_timestamp, predicted_action, action_confidence)
                VALUES (?, 'CBA.AX', datetime('now'), 'BUY', 0.75)
            """, (test_id,))
            
            # If successful, clean up
            cursor.execute("DELETE FROM predictions WHERE prediction_id = ?", (test_id,))
            conn.commit()
            print("✅ Database insertion test: PASSED")
            
        except sqlite3.IntegrityError as e:
            issues.append(f"❌ Database constraint error: {e}")
            print(f"❌ Database insertion test: FAILED - {e}")
        except Exception as e:
            issues.append(f"❌ Database test error: {e}")
            print(f"❌ Database test error: {e}")
        
        conn.close()
        
    except Exception as e:
        issues.append(f"❌ Database analysis failed: {e}")
    
    return issues

def check_package_availability():
    """Check if required packages are available in venv"""
    print("\n🔍 CHECKING PACKAGE AVAILABILITY IN VENV")
    print("=" * 50)
    
    issues = []
    required_packages = ['feedparser', 'beautifulsoup4', 'lxml', 'matplotlib', 'requests', 'pandas', 'numpy']
    
    try:
        # Check packages in venv
        cmd = "source venv/bin/activate && python -c \"import sys; print('\\n'.join(sys.path))\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Virtual environment activated successfully")
        
        # Test each package
        for package in required_packages:
            cmd = f"source venv/bin/activate && python -c \"import {package}; print('{package}: OK')\""
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ {package}: Available")
            else:
                print(f"   ❌ {package}: Missing")
                issues.append(f"❌ Missing package: {package}")
        
        # Install missing packages if needed
        if issues:
            print(f"\n📦 Installing missing packages...")
            missing = [pkg.split(': ')[1] for pkg in issues if 'Missing package:' in pkg]
            
            if missing:
                cmd = f"source venv/bin/activate && pip install {' '.join(missing)}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
                
                if result.returncode == 0:
                    print(f"✅ Successfully installed missing packages")
                    # Clear package issues since they're now installed
                    issues = [issue for issue in issues if 'Missing package:' not in issue]
                else:
                    print(f"❌ Failed to install packages: {result.stderr}")
                    
    except Exception as e:
        issues.append(f"❌ Package check failed: {e}")
    
    return issues

def main():
    """Run enhanced analysis with proper virtual environment support"""
    print("🚀 ENHANCED DEEP SYSTEM ANALYSIS")
    print("🎯 Using Proper Virtual Environments")
    print("=" * 60)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_issues = []
    
    # 1. Check package availability and install if needed
    package_issues = check_package_availability()
    all_issues.extend(package_issues)
    
    # 2. Analyze database constraints
    db_issues = analyze_database_constraints()
    all_issues.extend(db_issues)
    
    # 3. Test local system with venv
    local_issues = test_local_venv_system()
    all_issues.extend(local_issues)
    
    # 4. Test remote system with trading_venv
    remote_issues = test_remote_venv_system()
    all_issues.extend(remote_issues)
    
    # Generate summary
    print("\n" + "=" * 60)
    print("🎯 ANALYSIS SUMMARY")
    print("=" * 60)
    
    critical_issues = [issue for issue in all_issues if '❌' in issue]
    warning_issues = [issue for issue in all_issues if '⚠️' in issue]
    
    print(f"📊 Total Issues Found: {len(all_issues)}")
    print(f"🔴 Critical Issues: {len(critical_issues)}")
    print(f"🟡 Warning Issues: {len(warning_issues)}")
    
    if critical_issues:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in critical_issues:
            print(f"   {issue}")
    
    if warning_issues:
        print(f"\n⚠️  WARNING ISSUES:")
        for issue in warning_issues:
            print(f"   {issue}")
    
    if not all_issues:
        print(f"\n🎉 NO ISSUES FOUND - SYSTEM HEALTHY!")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if any("constraint" in issue.lower() for issue in critical_issues):
        print("   1. 🔧 Fix database constraint conflicts")
    if any("missing package" in issue.lower() for issue in all_issues):
        print("   2. 📦 Install missing Python packages")
    if any("remote" in issue.lower() for issue in all_issues):
        print("   3. 🌐 Check remote system connectivity")
    if any("venv" in issue.lower() for issue in all_issues):
        print("   4. 🐍 Verify virtual environment setup")
    
    print(f"\n✅ ENHANCED ANALYSIS COMPLETE")

if __name__ == "__main__":
    main()

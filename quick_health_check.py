#!/usr/bin/env python3
"""
Quick System Health Check
A fast diagnostic to understand system status without timeouts
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

def quick_health_check():
    """Run a fast system health check"""
    print("⚡ QUICK SYSTEM HEALTH CHECK")
    print("=" * 40)
    
    project_root = Path(__file__).parent
    health_score = 0
    max_score = 10
    
    # 1. Check virtual environment (2 points)
    venv_path = project_root / "venv"
    if venv_path.exists():
        print("✅ Virtual environment: Found")
        health_score += 2
    else:
        print("❌ Virtual environment: Missing")
    
    # 2. Check database (2 points)
    db_path = project_root / "data" / "trading_predictions.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions")
            pred_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
            outcome_count = cursor.fetchone()[0]
            conn.close()
            print(f"✅ Database: Connected ({pred_count} predictions, {outcome_count} outcomes)")
            health_score += 2
        except Exception as e:
            print(f"⚠️ Database: Connected but error - {e}")
            health_score += 1
    else:
        print("❌ Database: Not found")
    
    # 3. Check app.main (2 points)
    main_path = project_root / "app" / "main.py"
    if main_path.exists():
        print("✅ App main: Found")
        health_score += 2
    else:
        print("❌ App main: Missing")
    
    # 4. Check enhanced ML system (2 points)
    ml_path = project_root / "enhanced_ml_system"
    if ml_path.exists():
        analyzer_path = ml_path / "analyzers" / "enhanced_morning_analyzer_with_ml.py"
        if analyzer_path.exists():
            print("✅ Enhanced ML: Complete")
            health_score += 2
        else:
            print("⚠️ Enhanced ML: Partial")
            health_score += 1
    else:
        print("❌ Enhanced ML: Missing")
    
    # 5. Check critical packages (2 points)
    try:
        import pandas, numpy, requests, sqlite3
        print("✅ Core packages: Available")
        health_score += 2
    except ImportError as e:
        print(f"⚠️ Core packages: Some missing - {e}")
        health_score += 1
    
    # Health assessment
    health_percentage = (health_score / max_score) * 100
    
    print(f"\n📊 SYSTEM HEALTH: {health_score}/{max_score} ({health_percentage:.0f}%)")
    
    if health_percentage >= 80:
        status = "🟢 HEALTHY"
        print("🎯 System is in good condition")
    elif health_percentage >= 60:
        status = "🟡 DEGRADED"
        print("⚠️ System has some issues but functional")
    else:
        status = "🔴 CRITICAL"
        print("🚨 System needs immediate attention")
    
    print(f"Status: {status}")
    
    # Quick recommendations
    print(f"\n💡 QUICK FIXES:")
    if health_score < max_score:
        if not venv_path.exists():
            print("   • Create virtual environment: python3 -m venv venv")
        if not db_path.exists():
            print("   • Initialize database: Run data setup scripts")
        if health_percentage < 80:
            print("   • Run: source venv/bin/activate && pip install -r requirements.txt")
    
    if health_percentage >= 70:
        print("   • System ready for basic operations")
        print("   • Try: python -m app.main status")
    
    return health_score, max_score

def test_basic_commands():
    """Test basic system commands without timeout"""
    print(f"\n⚡ TESTING BASIC COMMANDS")
    print("=" * 40)
    
    project_root = Path(__file__).parent
    
    # Test importing key modules
    sys.path.insert(0, str(project_root))
    
    tests = [
        ("app.main import", "from app.main import main"),
        ("settings import", "from app.config.settings import Settings"),
        ("daily_manager import", "from app.services.daily_manager import TradingSystemManager"),
    ]
    
    passed = 0
    for test_name, test_code in tests:
        try:
            exec(test_code)
            print(f"✅ {test_name}: OK")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
    
    print(f"\n📊 Import Tests: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎯 All imports working - system structure is healthy")
        return True
    else:
        print("⚠️ Some import issues - check dependencies")
        return False

if __name__ == "__main__":
    # Quick health check
    health_score, max_score = quick_health_check()
    
    # Test imports
    imports_ok = test_basic_commands()
    
    # Final assessment
    print(f"\n" + "=" * 40)
    print(f"⚡ QUICK CHECK COMPLETE")
    print(f"=" * 40)
    
    if health_score >= 8 and imports_ok:
        print("🎉 System is ready for operation!")
        print("💡 You can run: python -m app.main status")
    elif health_score >= 6:
        print("⚠️ System is partially functional")
        print("💡 Fix critical issues then retry")
    else:
        print("🚨 System needs major repairs")
        print("💡 Start with virtual environment and dependencies")

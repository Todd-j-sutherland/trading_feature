#!/usr/bin/env python3
"""
Verify Paper Trading Database Setup
Confirms that the paper trading service can find and connect to the predictions database
"""

import os
import sys

def verify_directory_structure():
    """Verify the correct directory structure exists"""
    print("🔍 Verifying Directory Structure")
    print("=" * 40)
    
    # Check if we're in the right directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Check for data directory
    data_dir = "data"
    if os.path.exists(data_dir):
        print(f"✅ {data_dir}/ directory exists")
    else:
        print(f"❌ {data_dir}/ directory missing")
        return False
    
    # Check for predictions database in data directory
    predictions_db = "data/trading_predictions.db"
    if os.path.exists(predictions_db):
        size = os.path.getsize(predictions_db)
        print(f"✅ {predictions_db} exists ({size} bytes)")
        if size > 0:
            print(f"✅ Database has data")
        else:
            print(f"⚠️ Database is empty")
    else:
        print(f"❌ {predictions_db} missing")
        return False
    
    return True

def verify_paper_trading_config():
    """Verify paper trading service configuration"""
    print(f"\n🔧 Verifying Paper Trading Configuration")
    print("=" * 40)
    
    service_file = "paper-trading-app/enhanced_paper_trading_service.py"
    if os.path.exists(service_file):
        print(f"✅ Service file exists: {service_file}")
        
        try:
            with open(service_file, 'r') as f:
                content = f.read()
                
                # Check for correct path configuration
                if "PREDICTIONS_DB_PATH = '../data/trading_predictions.db'" in content:
                    print(f"✅ Correct predictions database path configured")
                else:
                    print(f"❌ Incorrect predictions database path")
                    return False
                    
        except Exception as e:
            print(f"❌ Error reading service file: {e}")
            return False
    else:
        print(f"❌ Service file not found: {service_file}")
        return False
    
    return True

def verify_from_paper_trading_directory():
    """Verify configuration from paper trading app perspective"""
    print(f"\n📂 Verifying from Paper Trading App Directory")
    print("=" * 40)
    
    # Check path from paper-trading-app directory
    expected_path = "../data/trading_predictions.db"
    
    # Simulate being in paper-trading-app directory
    paper_app_dir = "paper-trading-app"
    if os.path.exists(paper_app_dir):
        original_dir = os.getcwd()
        try:
            os.chdir(paper_app_dir)
            
            if os.path.exists(expected_path):
                size = os.path.getsize(expected_path)
                print(f"✅ From paper-trading-app/: {expected_path} exists ({size} bytes)")
            else:
                print(f"❌ From paper-trading-app/: {expected_path} not found")
                return False
                
        finally:
            os.chdir(original_dir)
    else:
        print(f"❌ paper-trading-app directory not found")
        return False
    
    return True

def main():
    """Run all verification checks"""
    print("🧪 Paper Trading Database Setup Verification")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Run verification checks
    checks = [
        ("Directory Structure", verify_directory_structure),
        ("Paper Trading Config", verify_paper_trading_config), 
        ("Path from Paper Trading App", verify_from_paper_trading_directory)
    ]
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            if not result:
                all_checks_passed = False
        except Exception as e:
            print(f"❌ Error in {check_name}: {e}")
            all_checks_passed = False
    
    # Summary
    print(f"\n📋 Verification Summary")
    print("=" * 50)
    
    if all_checks_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Paper trading service should be able to find predictions database")
        print("✅ Path configuration matches expected structure")
        print("✅ Database contains data")
        print("\n🚀 Ready to test paper trading service!")
    else:
        print("❌ SOME CHECKS FAILED")
        print("⚠️ Paper trading service may not work correctly")
        print("📝 Review the failed checks above and fix the issues")
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    sys.exit(main())

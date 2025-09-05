#!/usr/bin/env python3
"""
IG Markets Paper Trading Integration Validation Script
Simple validation that can be run to check integration status
"""

import os
import sys
from pathlib import Path

def validate_ig_markets_integration():
    """
    Validate IG Markets integration for paper trading
    """
    print("🔍 IG Markets Paper Trading Integration Validation")
    print("=" * 60)
    
    # Check file structure
    print("📁 Checking file structure...")
    
    required_files = [
        'enhanced_ig_markets_integration.py',
        'enhanced_paper_trading_service_with_ig.py',
        'enhanced_trading_engine_ig.py',
        'run_paper_trading_ig.py',
        'README_IG_MARKETS.md'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            missing_files.append(file)
    
    # Check for IG Markets components in parent directory
    print("\n📈 Checking IG Markets components...")
    parent_components = [
        '../app/core/data/collectors/enhanced_market_data_collector.py',
        '../app/core/data/collectors/ig_markets_symbol_mapper.py',
        '../real_time_price_fetcher.py',
        '../ig_markets_asx_mapper.py'
    ]
    
    missing_components = []
    for component in parent_components:
        if os.path.exists(component):
            print(f"  ✅ {component}")
        else:
            print(f"  ❌ {component} - MISSING")
            missing_components.append(component)
    
    # Check configuration
    print("\n⚙️ Checking configuration...")
    try:
        from config import TRADING_CONFIG, IG_MARKETS_CONFIG
        
        if 'use_ig_markets' in TRADING_CONFIG:
            print(f"  ✅ IG Markets enabled in TRADING_CONFIG: {TRADING_CONFIG['use_ig_markets']}")
        else:
            print("  ⚠️ IG Markets config not found in TRADING_CONFIG")
        
        if 'enabled' in IG_MARKETS_CONFIG:
            print(f"  ✅ IG Markets configuration found: {IG_MARKETS_CONFIG['enabled']}")
        else:
            print("  ❌ IG_MARKETS_CONFIG not properly configured")
            
    except ImportError as e:
        print(f"  ❌ Configuration import error: {e}")
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
    
    # Check environment
    print("\n🔐 Checking environment variables...")
    env_vars = ['IG_USERNAME', 'IG_PASSWORD', 'IG_API_KEY']
    env_status = {}
    
    for var in env_vars:
        if os.getenv(var):
            print(f"  ✅ {var} is set")
            env_status[var] = True
        else:
            print(f"  ⚠️ {var} not set (may use .env file)")
            env_status[var] = False
    
    # Check for .env files
    print("\n📄 Checking environment files...")
    env_files = ['.env', '.env.new', '../.env', '../.env.new']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"  ✅ {env_file} found")
        else:
            print(f"  ⚠️ {env_file} not found")
    
    # Check database files
    print("\n🗄️ Checking database files...")
    db_files = ['paper_trading.db', 'enhanced_positions.db', '../data/trading_predictions.db']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"  ✅ {db_file} exists")
        else:
            print(f"  ⚠️ {db_file} not found (will be created)")
    
    # Test basic imports
    print("\n🐍 Testing Python imports...")
    
    # Test standard imports
    try:
        import sqlite3
        print("  ✅ sqlite3 available")
    except ImportError:
        print("  ❌ sqlite3 not available")
    
    try:
        import yfinance
        print("  ✅ yfinance available")
    except ImportError:
        print("  ❌ yfinance not available - install with: pip install yfinance")
    
    try:
        import requests
        print("  ✅ requests available")
    except ImportError:
        print("  ❌ requests not available - install with: pip install requests")
    
    # Test IG Markets integration imports
    try:
        sys.path.insert(0, '..')
        from app.core.data.collectors.enhanced_market_data_collector import EnhancedMarketDataCollector
        print("  ✅ Enhanced market data collector import successful")
    except ImportError as e:
        print(f"  ❌ Enhanced market data collector import failed: {e}")
    
    try:
        from app.core.data.collectors.ig_markets_symbol_mapper import IGMarketsSymbolMapper
        print("  ✅ IG Markets symbol mapper import successful")
    except ImportError as e:
        print(f"  ❌ IG Markets symbol mapper import failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Validation Summary:")
    
    if not missing_files:
        print("  ✅ All integration files present")
    else:
        print(f"  ❌ Missing files: {', '.join(missing_files)}")
    
    if not missing_components:
        print("  ✅ All IG Markets components present")
    else:
        print(f"  ❌ Missing components: {', '.join(missing_components)}")
    
    # Overall status
    critical_missing = (missing_files or missing_components)
    
    if not critical_missing:
        print("\n🎉 IG Markets Paper Trading Integration: READY")
        print("💡 You can now run:")
        print("   python run_paper_trading_ig.py init")
        print("   python run_paper_trading_ig.py service")
    else:
        print("\n⚠️ IG Markets Paper Trading Integration: INCOMPLETE")
        print("💡 Please ensure all required files are present")
    
    return not critical_missing

def check_python_environment():
    """Check Python environment and dependencies"""
    print("\n🐍 Python Environment Check:")
    print(f"  Python version: {sys.version}")
    print(f"  Python executable: {sys.executable}")
    print(f"  Current working directory: {os.getcwd()}")
    print(f"  Python path includes: {len(sys.path)} directories")
    
    # Check key packages
    packages = ['sqlite3', 'json', 'datetime', 'logging', 'os', 'sys']
    for package in packages:
        try:
            __import__(package)
            print(f"  ✅ {package} available")
        except ImportError:
            print(f"  ❌ {package} not available")

def main():
    """Main validation function"""
    print("🚀 IG Markets Paper Trading Integration Validator")
    print(f"📅 Validation Date: {Path(__file__).stat().st_mtime}")
    
    # Check Python environment
    check_python_environment()
    
    # Validate integration
    success = validate_ig_markets_integration()
    
    # Usage instructions
    print("\n💡 Next Steps:")
    if success:
        print("1. Set up IG Markets credentials in .env file")
        print("2. Run: python run_paper_trading_ig.py init")
        print("3. Run: python run_paper_trading_ig.py test")
        print("4. Run: python run_paper_trading_ig.py service")
    else:
        print("1. Ensure all required files are present")
        print("2. Check IG Markets components in parent directory")
        print("3. Install missing Python packages")
        print("4. Re-run this validation script")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Simple test script for backtesting components
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_functionality():
    """Test basic backtesting functionality"""
    print("🧪 Testing Backtesting Components...")
    
    # Test 1: Database connectivity
    print("\n1️⃣ Testing Database Connectivity...")
    try:
        import sqlite3
        from pathlib import Path
        
        db_paths = [
            "data/trading_unified.db",
            "data/trading_data.db", 
            "data/ml_models/enhanced_training_data.db"
        ]
        
        db_found = 0
        for db_path in db_paths:
            db_file = Path(db_path)
            if db_file.exists():
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    conn.close()
                    print(f"   ✅ {db_path}: {len(tables)} tables found")
                    db_found += 1
                except Exception as e:
                    print(f"   ❌ {db_path}: {e}")
            else:
                print(f"   ⚠️  {db_path}: Not found")
        
        print(f"   📊 {db_found}/{len(db_paths)} databases accessible")
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
    
    # Test 2: Required dependencies
    print("\n2️⃣ Testing Dependencies...")
    required_modules = ['pandas', 'numpy', 'matplotlib', 'sqlite3', 'json', 'datetime']
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}: Available")
        except ImportError:
            print(f"   ❌ {module}: Missing")
    
    # Test 3: Backtesting class instantiation
    print("\n3️⃣ Testing Backtesting Class...")
    try:
        from app.core.backtesting.comprehensive_backtester import ComprehensiveBacktester
        
        backtester = ComprehensiveBacktester()
        print(f"   ✅ ComprehensiveBacktester instantiated successfully")
        print(f"   📊 Bank symbols: {backtester.bank_symbols}")
        print(f"   📁 Results directory: {backtester.results_dir}")
        
        # Test data loading
        print("\n   🔄 Testing data loading...")
        sentiment_data = backtester.load_sentiment_data()
        print(f"   📈 Sentiment data sources found: {len(sentiment_data)}")
        
        for data_type, df in sentiment_data:
            print(f"      • {data_type}: {len(df)} records")
            if not df.empty:
                signals = backtester.extract_signals_from_data(data_type, df)
                print(f"        Extracted {len(signals)} trading signals")
        
    except Exception as e:
        print(f"   ❌ Backtesting class test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Basic functionality
    print("\n4️⃣ Testing Core Functions...")
    try:
        # Test performance report generation
        report = backtester.generate_performance_report()
        print(f"   ✅ Performance report generated")
        print(f"   📊 Report keys: {list(report.keys())}")
        
        if report['summary']:
            for key, value in report['summary'].items():
                print(f"      • {key}: {value}")
        
    except Exception as e:
        print(f"   ❌ Core functions test failed: {e}")
    
    print("\n🎯 Basic testing completed!")
    print("\n💡 To run full backtesting:")
    print("   python3 -c \"from test_backtesting import run_sample_backtest; run_sample_backtest()\"")

def run_sample_backtest():
    """Run a sample backtest on one symbol"""
    print("🚀 Running Sample Backtesting Analysis...")
    
    try:
        from app.core.backtesting.comprehensive_backtester import ComprehensiveBacktester
        import pandas as pd
        
        backtester = ComprehensiveBacktester()
        
        # Test with one symbol
        test_symbol = 'CBA.AX'
        print(f"📊 Testing with symbol: {test_symbol}")
        
        # Generate performance report
        print("\n1️⃣ Generating performance report...")
        report = backtester.generate_performance_report()
        
        print("📋 Performance Report Summary:")
        if report['summary']:
            for key, value in report['summary'].items():
                print(f"   {key}: {value}")
        
        if report['strategy_metrics']:
            print("\n📈 Strategy Metrics:")
            for strategy, metrics in report['strategy_metrics'].items():
                print(f"   {strategy}:")
                for metric, value in metrics.items():
                    if isinstance(value, dict):
                        print(f"     {metric}: {dict(list(value.items())[:3])}")  # Show first 3 items
                    else:
                        print(f"     {metric}: {value}")
        
        # Test Yahoo Finance data fetch (if available)
        print(f"\n2️⃣ Testing Yahoo Finance data for {test_symbol}...")
        try:
            # This might fail without internet or yfinance installed
            price_data = backtester.fetch_historical_prices(test_symbol, period="1mo")
            if not price_data.empty:
                print(f"   ✅ Price data fetched: {len(price_data)} records")
                print(f"   📅 Date range: {price_data['Date'].min()} to {price_data['Date'].max()}")
                print(f"   💰 Price range: ${price_data['Low'].min():.2f} - ${price_data['High'].max():.2f}")
            else:
                print("   ⚠️  No price data available")
        except Exception as e:
            print(f"   ⚠️  Yahoo Finance test skipped: {e}")
        
        print("\n✅ Sample backtest completed successfully!")
        
    except Exception as e:
        print(f"❌ Sample backtest failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_functionality()
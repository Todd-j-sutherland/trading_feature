#!/usr/bin/env python3
"""
Market-Aware System Deployment Test
Comprehensive testing with detailed logging
"""

import logging
import sys
from datetime import datetime
import os

# Setup comprehensive logging
def setup_logging():
    """Setup detailed logging for market-aware testing"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create logs directory
    os.makedirs("market-aware-logs", exist_ok=True)
    
    # Setup multiple log files
    log_handlers = [
        logging.FileHandler(f"market-aware-logs/market_aware_test_{timestamp}.log"),
        logging.FileHandler(f"market-aware-logs/market_context_{timestamp}.log"),
        logging.FileHandler(f"market-aware-logs/predictions_{timestamp}.log"),
        logging.StreamHandler(sys.stdout)  # Also log to console
    ]
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=log_handlers
    )
    
    return timestamp

def test_settings_integration():
    """Test Settings configuration integration"""
    print("\n" + "="*60)
    print("🔧 TESTING SETTINGS INTEGRATION")
    print("="*60)
    
    try:
        # Test importing settings
        sys.path.append('/root/test/paper-trading-app/app/config')
        from settings import Settings
        
        print(f"✅ Settings imported successfully")
        print(f"📊 Bank symbols: {Settings.BANK_SYMBOLS}")
        print(f"📈 Extended symbols: {len(Settings.EXTENDED_SYMBOLS)} symbols")
        
        # Test bank name function
        for symbol in Settings.BANK_SYMBOLS[:3]:
            bank_name = Settings.get_bank_name(symbol)
            print(f"   {symbol} → {bank_name}")
            
        return True
        
    except Exception as e:
        print(f"❌ Settings integration failed: {e}")
        logging.error(f"Settings integration error: {e}")
        return False

def test_market_context_analysis():
    """Test market context analysis"""
    print("\n" + "="*60)
    print("🌐 TESTING MARKET CONTEXT ANALYSIS")
    print("="*60)
    
    try:
        # Import market-aware system
        sys.path.append('/root/test/paper-trading-app')
        from market_aware_prediction_system import MarketAwarePricePredictor
        
        predictor = MarketAwarePricePredictor()
        
        # Test market context
        market_context = predictor.get_cached_market_context()
        
        print(f"📊 Market Context Results:")
        print(f"   ASX 200 Level: {market_context['current_level']:.1f}")
        print(f"   5-day Trend: {market_context['trend_pct']:+.2f}%")
        print(f"   Market Context: {market_context['context']}")
        print(f"   BUY Threshold: {market_context['buy_threshold']:.1%}")
        print(f"   Confidence Multiplier: {market_context['confidence_multiplier']:.1f}x")
        
        # Log detailed market analysis
        logging.info(f"Market Context Analysis: {market_context}")
        
        return True, market_context
        
    except Exception as e:
        print(f"❌ Market context analysis failed: {e}")
        logging.error(f"Market context error: {e}")
        return False, None

def test_prediction_generation():
    """Test market-aware prediction generation"""
    print("\n" + "="*60)
    print("🎯 TESTING PREDICTION GENERATION")
    print("="*60)
    
    try:
        # Import the enhanced system
        from enhanced_efficient_system_market_aware import test_market_aware_system
        
        print("🚀 Running market-aware prediction test...")
        
        # Capture output to log
        import io
        import contextlib
        
        log_stream = io.StringIO()
        with contextlib.redirect_stdout(log_stream):
            test_market_aware_system()
        
        output = log_stream.getvalue()
        print("✅ Prediction generation completed")
        
        # Log the prediction output
        logging.info(f"Prediction Generation Output:\n{output}")
        
        # Also show key metrics
        lines = output.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['buy signal', 'strong buy', 'confidence', 'market context']):
                print(f"   📈 {line.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prediction generation failed: {e}")
        logging.error(f"Prediction generation error: {e}")
        return False

def test_paper_trading_integration():
    """Test paper trading integration"""
    print("\n" + "="*60)
    print("📋 TESTING PAPER TRADING INTEGRATION")
    print("="*60)
    
    try:
        # Import main application
        from main import PaperTradingApp
        
        app = PaperTradingApp()
        
        print("✅ Paper trading app initialized")
        
        # Test signal generation
        signals = app.generate_trading_signals()
        
        print(f"📊 Generated {len(signals)} trading signals")
        
        # Log signal details
        for symbol, signal in signals.items():
            print(f"   {symbol}: {signal['action']} (confidence: {signal['confidence']:.1%})")
            logging.info(f"Trading Signal - {symbol}: {signal}")
        
        return True
        
    except Exception as e:
        print(f"❌ Paper trading integration failed: {e}")
        logging.error(f"Paper trading integration error: {e}")
        return False

def test_database_operations():
    """Test database operations"""
    print("\n" + "="*60)
    print("🗄️ TESTING DATABASE OPERATIONS")
    print("="*60)
    
    try:
        import sqlite3
        
        # Check database connection
        conn = sqlite3.connect('/root/test/paper-trading-app/paper_trading.db')
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"✅ Database connected - {len(tables)} tables found")
        
        # Check recent predictions
        cursor.execute("SELECT COUNT(*) FROM processed_predictions WHERE processed_at >= date('now', '-1 day');")
        recent_predictions = cursor.fetchone()[0]
        
        print(f"📊 Recent predictions (24h): {recent_predictions}")
        
        # Check positions
        cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'OPEN';")
        open_positions = cursor.fetchone()[0]
        
        print(f"💼 Open positions: {open_positions}")
        
        conn.close()
        
        logging.info(f"Database check: {len(tables)} tables, {recent_predictions} recent predictions, {open_positions} open positions")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        logging.error(f"Database error: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive market-aware system test"""
    timestamp = setup_logging()
    
    print("🚀 MARKET-AWARE SYSTEM COMPREHENSIVE TEST")
    print(f"📅 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Logs will be saved to: market-aware-logs/")
    print("="*80)
    
    test_results = {}
    
    # Run all tests
    test_results['settings'] = test_settings_integration()
    test_results['market_context'], market_context = test_market_context_analysis()
    test_results['predictions'] = test_prediction_generation()
    test_results['paper_trading'] = test_paper_trading_integration()
    test_results['database'] = test_database_operations()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.upper()}: {status}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Market-aware system ready for production!")
    else:
        print("⚠️ Some tests failed - Review logs for details")
    
    # Save summary to file
    summary_file = f"market-aware-logs/test_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Market-Aware System Test Summary\n")
        f.write(f"Test Date: {datetime.now()}\n")
        f.write(f"Tests Passed: {passed}/{total}\n\n")
        
        for test_name, result in test_results.items():
            status = "PASS" if result else "FAIL"
            f.write(f"{test_name}: {status}\n")
        
        if market_context:
            f.write(f"\nMarket Context:\n")
            for key, value in market_context.items():
                f.write(f"  {key}: {value}\n")
    
    print(f"📄 Test summary saved to: {summary_file}")
    
    logging.info(f"Comprehensive test completed: {passed}/{total} passed")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)

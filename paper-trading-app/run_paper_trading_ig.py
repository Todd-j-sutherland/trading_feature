#!/usr/bin/env python3
"""
Paper Trading App with IG Markets Integration - Startup Script
Initializes all components and runs the enhanced paper trading service
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('paper_trading_ig_startup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def initialize_paper_trading_with_ig():
    """
    Initialize the complete paper trading system with IG Markets integration
    """
    logger.info("🚀 Starting Paper Trading App with IG Markets Integration...")
    logger.info("="*60)
    
    try:
        # Step 1: Initialize IG Markets integration for price sources
        logger.info("📈 Step 1: Initializing IG Markets integration...")
        try:
            from enhanced_ig_markets_integration import initialize_ig_markets_integration
            ig_success = initialize_ig_markets_integration()
            if ig_success:
                logger.info("✅ IG Markets integration initialized successfully")
            else:
                logger.warning("⚠️ IG Markets integration failed - will use yfinance")
        except Exception as e:
            logger.error(f"❌ IG Markets integration error: {e}")
            ig_success = False
        
        # Step 2: Initialize enhanced trading engine
        logger.info("🏗️ Step 2: Initializing enhanced trading engine...")
        try:
            from enhanced_trading_engine_ig import initialize_enhanced_trading_engine
            engine_success = initialize_enhanced_trading_engine()
            if engine_success:
                logger.info("✅ Enhanced trading engine initialized successfully")
            else:
                logger.warning("⚠️ Enhanced trading engine initialization failed")
        except Exception as e:
            logger.error(f"❌ Trading engine initialization error: {e}")
            engine_success = False
        
        # Step 3: Verify database connectivity
        logger.info("🗄️ Step 3: Verifying database connectivity...")
        try:
            import sqlite3
            db_paths = ['paper_trading.db', 'enhanced_positions.db', '../data/trading_predictions.db']
            
            for db_path in db_paths:
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path, timeout=5.0)
                    conn.execute("SELECT 1")
                    conn.close()
                    logger.info(f"✅ Database accessible: {db_path}")
                else:
                    logger.warning(f"⚠️ Database not found: {db_path}")
            
        except Exception as e:
            logger.error(f"❌ Database connectivity check failed: {e}")
        
        # Step 4: Display configuration summary
        logger.info("📊 Step 4: Configuration Summary:")
        logger.info(f"   IG Markets Integration: {'✅ ENABLED' if ig_success else '❌ DISABLED'}")
        logger.info(f"   Enhanced Trading Engine: {'✅ ENABLED' if engine_success else '❌ DISABLED'}")
        logger.info(f"   Data Source Priority: {'IG Markets → yfinance' if ig_success else 'yfinance only'}")
        
        # Step 5: Test basic functionality
        logger.info("🧪 Step 5: Testing basic functionality...")
        try:
            test_symbols = ['CBA.AX', 'WBC.AX']
            
            if ig_success:
                from enhanced_ig_markets_integration import get_enhanced_price_source
                price_source = get_enhanced_price_source()
                
                for symbol in test_symbols:
                    price = price_source.get_current_price(symbol)
                    if price:
                        logger.info(f"   ✅ {symbol}: ${price:.2f}")
                    else:
                        logger.warning(f"   ⚠️ {symbol}: No price data")
            else:
                import yfinance as yf
                for symbol in test_symbols:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    price = info.get('currentPrice') or info.get('regularMarketPrice')
                    if price:
                        logger.info(f"   ✅ {symbol}: ${price:.2f} (yfinance)")
                    else:
                        logger.warning(f"   ⚠️ {symbol}: No price data")
                        
        except Exception as e:
            logger.error(f"❌ Basic functionality test failed: {e}")
        
        logger.info("="*60)
        logger.info("✅ Paper Trading App with IG Markets initialization completed!")
        
        return {
            'ig_markets_enabled': ig_success,
            'enhanced_engine_enabled': engine_success,
            'initialization_success': True
        }
        
    except Exception as e:
        logger.error(f"❌ Critical initialization error: {e}")
        return {
            'ig_markets_enabled': False,
            'enhanced_engine_enabled': False,
            'initialization_success': False,
            'error': str(e)
        }

def run_paper_trading_service():
    """
    Run the main paper trading service with IG Markets integration
    """
    logger.info("🎯 Starting Paper Trading Service...")
    
    try:
        # Initialize everything first
        init_result = initialize_paper_trading_with_ig()
        
        if not init_result['initialization_success']:
            logger.error("❌ Initialization failed - cannot start service")
            return 1
        
        # Import and run the enhanced service
        logger.info("🚀 Starting Enhanced Paper Trading Service with IG Markets...")
        
        try:
            from enhanced_paper_trading_service_with_ig import main as enhanced_main
            return enhanced_main()
        except ImportError:
            logger.warning("⚠️ Enhanced service not available - using original service")
            from enhanced_paper_trading_service import main as original_main
            return original_main()
            
    except KeyboardInterrupt:
        logger.info("🛑 Service stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Service error: {e}")
        return 1

def run_dashboard_with_ig():
    """
    Run the dashboard with IG Markets integration
    """
    logger.info("📊 Starting Paper Trading Dashboard with IG Markets...")
    
    try:
        # Initialize IG Markets integration
        init_result = initialize_paper_trading_with_ig()
        
        # Import and run dashboard
        from dashboard import main as dashboard_main
        
        logger.info("🌐 Starting dashboard server...")
        return dashboard_main()
        
    except ImportError:
        logger.error("❌ Dashboard module not found")
        return 1
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        return 1

def test_complete_system():
    """
    Test the complete system with IG Markets integration
    """
    logger.info("🧪 Testing Complete Paper Trading System with IG Markets...")
    
    try:
        # Initialize system
        init_result = initialize_paper_trading_with_ig()
        
        if not init_result['initialization_success']:
            logger.error("❌ System initialization failed")
            return False
        
        # Test enhanced service
        logger.info("🧪 Testing Enhanced Paper Trading Service...")
        try:
            from enhanced_paper_trading_service_with_ig import test_enhanced_service
            service_test = test_enhanced_service()
            if service_test:
                logger.info("✅ Enhanced service test passed")
            else:
                logger.warning("⚠️ Enhanced service test failed")
        except Exception as e:
            logger.error(f"❌ Enhanced service test error: {e}")
            service_test = False
        
        # Test enhanced trading engine
        logger.info("🧪 Testing Enhanced Trading Engine...")
        try:
            from enhanced_trading_engine_ig import test_enhanced_trading_engine
            engine_test = test_enhanced_trading_engine()
            if engine_test:
                logger.info("✅ Enhanced trading engine test passed")
            else:
                logger.warning("⚠️ Enhanced trading engine test failed")
        except Exception as e:
            logger.error(f"❌ Enhanced trading engine test error: {e}")
            engine_test = False
        
        # Test IG Markets integration
        logger.info("🧪 Testing IG Markets Integration...")
        try:
            from enhanced_ig_markets_integration import test_ig_markets_integration
            ig_test = test_ig_markets_integration()
            if ig_test:
                logger.info("✅ IG Markets integration test passed")
            else:
                logger.warning("⚠️ IG Markets integration test failed")
        except Exception as e:
            logger.error(f"❌ IG Markets integration test error: {e}")
            ig_test = False
        
        # Summary
        logger.info("="*60)
        logger.info("📊 Complete System Test Results:")
        logger.info(f"   System Initialization: {'✅ PASS' if init_result['initialization_success'] else '❌ FAIL'}")
        logger.info(f"   IG Markets Integration: {'✅ PASS' if ig_test else '❌ FAIL'}")
        logger.info(f"   Enhanced Trading Engine: {'✅ PASS' if engine_test else '❌ FAIL'}")
        logger.info(f"   Enhanced Service: {'✅ PASS' if service_test else '❌ FAIL'}")
        
        overall_success = (init_result['initialization_success'] and 
                          ig_test and engine_test and service_test)
        
        if overall_success:
            logger.info("🎉 Complete system test PASSED!")
            logger.info("💡 System is ready for production use with IG Markets integration")
        else:
            logger.warning("⚠️ Some system tests failed - check logs for details")
        
        return overall_success
        
    except Exception as e:
        logger.error(f"❌ Complete system test failed: {e}")
        return False

def main():
    """
    Main entry point with command line options
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Paper Trading App with IG Markets Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_paper_trading_ig.py service      # Run paper trading service
  python run_paper_trading_ig.py dashboard    # Run dashboard
  python run_paper_trading_ig.py test         # Test complete system
  python run_paper_trading_ig.py init         # Initialize only
        """
    )
    
    parser.add_argument(
        'command',
        choices=['service', 'dashboard', 'test', 'init'],
        help='Command to execute'
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 Paper Trading App with IG Markets Integration")
    logger.info(f"📋 Command: {args.command}")
    
    try:
        if args.command == 'service':
            return run_paper_trading_service()
        
        elif args.command == 'dashboard':
            return run_dashboard_with_ig()
        
        elif args.command == 'test':
            success = test_complete_system()
            return 0 if success else 1
        
        elif args.command == 'init':
            result = initialize_paper_trading_with_ig()
            return 0 if result['initialization_success'] else 1
        
    except KeyboardInterrupt:
        logger.info("🛑 Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"❌ Command execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

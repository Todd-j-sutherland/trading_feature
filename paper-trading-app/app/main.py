#!/usr/bin/env python3
"""
Main application entry point for Trading Analysis System - Simplified Version
"""

# Stability imports
from app.utils.error_handler import ErrorHandler, robust_execution, TradingError
from app.config.config_manager import ConfigurationManager
from app.utils.health_checker import SystemHealthChecker

import sys
import argparse
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config.settings import Settings
from app.config.logging import setup_logging
from app.services.daily_manager import TradingSystemManager
from app.utils.graceful_shutdown import setup_graceful_shutdown, register_cleanup

def setup_cli():
    """Setup command line interface"""
    parser = argparse.ArgumentParser(
        description="Trading Analysis System - Simplified",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.main morning              # Run morning routine
  python -m app.main evening              # Run evening routine
  python -m app.main status               # Quick status check
  python -m app.main news                 # Run news sentiment analysis
  python -m app.main simple-backtest      # Run lightweight backtesting
  python -m app.main backtest             # Run comprehensive backtesting
  python -m app.main ig-markets-test      # Test IG Markets API integration
  python -m app.main --config custom.yml  # Use custom config
        """
    )
    
    parser.add_argument(
        'command',
        choices=['morning', 'evening', 'status', 'weekly', 'restart', 'test', 'news', 'divergence', 'economic', 'backtest', 'simple-backtest', 'ig-markets-test'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to custom configuration file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    
    parser.add_argument(
        '--symbol',
        type=str,
        help='Symbol for single-symbol analysis (e.g., CBA.AX)'
    )
    
    return parser

def run_divergence_analysis():
    """Run standalone divergence analysis"""
    print("🎯 Running Sector Divergence Analysis...")
    
    try:
        from app.core.analysis.divergence import DivergenceDetector
        from app.core.data.processors.news_processor import NewsTradingAnalyzer
        from app.config.settings import Settings
        
        settings = Settings()
        divergence_detector = DivergenceDetector()
        news_analyzer = NewsTradingAnalyzer()
        
        # Get analyses for all banks
        bank_analyses = {}
        for symbol in settings.BANK_SYMBOLS:
            try:
                analysis = news_analyzer.analyze_single_bank(symbol, detailed=False)
                if analysis and 'overall_sentiment' in analysis:
                    bank_analyses[symbol] = analysis
                    print(f"  ✅ {symbol}: Sentiment {analysis['overall_sentiment']:+.3f}")
            except Exception as e:
                print(f"  ❌ {symbol}: Analysis failed")
        
        if bank_analyses:
            # Run divergence analysis
            result = divergence_detector.analyze_sector_divergence(bank_analyses)
            
            print(f"\n📊 Divergence Analysis Results:")
            print(f"  Sector Average: {result['sector_average']:+.3f}")
            print(f"  Sector Volatility: {result['sector_volatility']:.3f}")
            print(f"  Divergent Banks: {len(result['divergent_banks'])}")
            
            # Show divergent banks
            for symbol, data in result['divergent_banks'].items():
                score = data['divergence_score']
                opportunity = data['opportunity']
                print(f"  🎯 {symbol}: {score:+.3f} ({opportunity})")
            
            # Generate trading signals
            signals = divergence_detector.generate_trading_signals(result)
            if signals:
                print(f"\n📈 Trading Signals:")
                for signal in signals:
                    print(f"  {signal['symbol']}: {signal['signal']} (Significance: {signal['significance']:.2f})")
            else:
                print(f"\n📊 No high-significance trading signals detected.")
        else:
            print("❌ No bank analysis data available.")
            
    except Exception as e:
        print(f"❌ Divergence analysis error: {e}")

def run_economic_analysis():
    """Run standalone economic analysis"""
    print("🌍 Running Economic Context Analysis...")
    
    try:
        from app.core.analysis.economic import EconomicSentimentAnalyzer
        
        analyzer = EconomicSentimentAnalyzer()
        result = analyzer.analyze_economic_sentiment()
        
        print(f"\n📊 Economic Analysis Results:")
        print(f"  Overall Sentiment: {result['overall_sentiment']:+.3f}")
        print(f"  Confidence: {result['confidence']:.1%}")
        print(f"  Market Regime: {result['market_regime']['regime']}")
        print(f"  Description: {result['market_regime']['description']}")
        
        print(f"\n📈 Economic Indicators:")
        for indicator, data in result['indicators'].items():
            name = indicator.replace('_', ' ').title()
            value = data['value']
            trend = data['trend']
            sentiment = data['sentiment']
            print(f"  {name}: {value} (trend: {trend}, sentiment: {sentiment:+.2f})")
            
    except Exception as e:
        print(f"❌ Economic analysis error: {e}")

def run_comprehensive_backtest():
    """Run comprehensive backtesting analysis"""
    print("📈 Running Comprehensive Backtesting Analysis...")
    
    try:
        from app.core.backtesting.comprehensive_backtester import ComprehensiveBacktester
        
        backtester = ComprehensiveBacktester()
        print(f"🔄 Starting analysis for {len(backtester.bank_symbols)} symbols...")
        print(f"📁 Results will be saved to: {backtester.results_dir}")
        
        # Run full backtest
        results = backtester.run_full_backtest()
        
        # Display results
        print("\n" + "="*60)
        print("📊 BACKTESTING RESULTS SUMMARY")
        print("="*60)
        
        if results['performance_report']['summary']:
            summary = results['performance_report']['summary']
            print(f"🎯 Total Signals Generated: {summary.get('total_signals_generated', 0)}")
            print(f"📊 Data Sources Used: {summary.get('data_sources', 0)}")
            print(f"🏦 Symbols Analyzed: {summary.get('symbols_covered', 0)}")
            print(f"📅 Analysis Period: {summary.get('analysis_period', 'N/A')}")
        
        print(f"\n📈 Visualization Files Created:")
        for symbol, file_path in results['visualizations'].items():
            print(f"   • {symbol}: {file_path}")
        
        if results['strategy_comparison']:
            print(f"   • Strategy Comparison: {results['strategy_comparison']}")
        
        print(f"\n💰 Individual Performance Analysis:")
        for symbol, analysis in results['individual_analyses'].items():
            print(f"   {symbol}:")
            print(f"     📈 3-month return: {analysis.get('price_change_3m', 0):+.2f}%")
            print(f"     📊 Volatility: {analysis.get('volatility', 0):.2f}%")
            print(f"     💵 Current price: ${analysis.get('current_price', 0):.2f}")
        
        print(f"\n✅ Backtesting completed successfully!")
        print(f"💡 Open the HTML files in your browser to view interactive charts")
        
    except Exception as e:
        print(f"❌ Backtesting error: {e}")
        import traceback
        traceback.print_exc()

def run_ig_markets_test():
    """Test IG Markets integration"""
    print("🔄 Testing IG Markets integration...")
    
    try:
        from app.core.data.collectors.enhanced_market_data_collector import EnhancedMarketDataCollector
        from app.core.data.collectors.ig_markets_symbol_mapper import IGMarketsSymbolMapper
        
        # Initialize components
        collector = EnhancedMarketDataCollector()
        mapper = IGMarketsSymbolMapper()
        
        # Test symbols
        test_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'BHP.AX']
        
        print("Testing symbol mapping:")
        for symbol in test_symbols:
            epic = mapper.get_ig_epic(symbol)
            print(f"  {symbol} → {epic}")
        
        print("\nTesting real-time prices:")
        for symbol in test_symbols:
            try:
                price_data = collector.get_current_price(symbol)
                if price_data:
                    print(f"  {symbol}: ${price_data.get('price', 'N/A'):.3f} (Source: {price_data.get('source', 'Unknown')})")
                else:
                    print(f"  {symbol}: No data available")
            except Exception as e:
                print(f"  {symbol}: Error - {e}")
        
        # Show data source statistics
        stats = collector.get_data_source_stats()
        print(f"\nData Source Statistics:")
        print(f"  IG Markets requests: {stats.get('ig_markets', 0)}")
        print(f"  yfinance requests: {stats.get('yfinance', 0)}")
        print(f"  Cache hits: {stats.get('cache_hits', 0)}")
        print(f"  Total requests: {stats.get('total_requests', 0)}")
        
        # Test IG Markets health
        ig_health = collector.is_ig_markets_healthy()
        print(f"\nIG Markets Health: {'✅ Healthy' if ig_health else '❌ Unhealthy'}")
        
        print("✅ IG Markets integration test completed")
        
    except Exception as e:
        print(f"❌ IG Markets test error: {e}")
        import traceback
        traceback.print_exc()

def run_simple_backtest():
    """Run the lightweight backtesting analysis"""
    print("📊 Running Simple Backtesting Analysis...")
    
    try:
        from app.core.backtesting.simple_backtester import SimpleBacktester
        
        backtester = SimpleBacktester()
        results = backtester.run_simple_backtest()
        
        if 'error' not in results:
            print(f"\n📈 Backtesting Results:")
            print(f"   📊 Total Signals: {results['total_signals']}")
            print(f"   📋 Strategies Analyzed: {results['strategies_analyzed']}")
            print(f"   📁 Results Directory: {backtester.results_dir}")
            print(f"\n📄 Generated Files:")
            print(f"   📊 CSV Report: {results['csv_report']}")
            print(f"   📝 Summary Report: {results['summary_report']}")
            print(f"   🌐 HTML Visualization: {results['html_chart']}")
            print(f"\n💡 Open the HTML file in your browser to view interactive results")
        else:
            print(f"❌ Backtesting failed: {results['error']}")
            
    except Exception as e:
        print(f"❌ Simple backtesting error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main application entry point"""
    parser = setup_cli()
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else getattr(logging, args.log_level)
    setup_logging(level=log_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Trading Analysis System - Command: {args.command}")
    
    # Setup graceful shutdown
    shutdown_handler = setup_graceful_shutdown()
    
    def cleanup_system():
        """Cleanup function for graceful shutdown"""
        logger.info("Performing system cleanup...")
        print("🧹 Cleaning up trading system...")
        
        # Basic cleanup - just log the shutdown
        logger.info("System shutdown completed")
        
    # Register cleanup function
    register_cleanup(cleanup_system)
    
    try:
        # Initialize system manager
        manager = TradingSystemManager(
            config_path=args.config,
            dry_run=True  # Always use dry run for simplified system
        )
        
        # Execute command
        if args.command == 'morning':
            manager.morning_routine()
        elif args.command == 'evening':
            manager.evening_routine()
        elif args.command == 'status':
            manager.quick_status()
        elif args.command == 'weekly':
            manager.weekly_maintenance()
        elif args.command == 'restart':
            manager.emergency_restart()
        elif args.command == 'test':
            manager.test_enhanced_features()
        elif args.command == 'news':
            manager.news_analysis()
        elif args.command == 'divergence':
            run_divergence_analysis()
        elif args.command == 'economic':
            run_economic_analysis()
        elif args.command == 'backtest':
            run_comprehensive_backtest()
        elif args.command == 'simple-backtest':
            run_simple_backtest()
        elif args.command == 'ig-markets-test':
            run_ig_markets_test()
        
        logger.info(f"Command '{args.command}' completed successfully")
        print("✅ Command completed successfully")
        print("💡 Main routines: morning, evening, status")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\n👋 Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error executing command '{args.command}': {e}")
        if args.verbose:
            logger.exception("Full traceback:")
        sys.exit(1)
    
    finally:
        # Initialize stability components for final health check
        try:
            config_manager = ConfigurationManager()
            error_handler = ErrorHandler(logger)
            health_checker = SystemHealthChecker(config_manager)
            
            # Run quick health check
            health_status = health_checker.run_comprehensive_health_check()
            if health_status and health_status.get('overall_status') in ['error', 'warning']:
                logger.warning(f"System health: {health_status['overall_status']}")
                print(f"⚠️ System health: {health_status['overall_status']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize stability components: {e}")
            print("⚠️ Running in basic mode due to initialization issues")

if __name__ == "__main__":
    main()

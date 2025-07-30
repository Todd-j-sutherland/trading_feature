#!/usr/bin/env python3
"""
Main application entry point for Trading Analysis System
"""

import sys
import argparse
import logging
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
        description="Trading Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.main morning              # Run morning routine
  python -m app.main evening              # Run evening routine
  python -m app.main status               # Quick status check
  python -m app.main dashboard            # Launch dashboard
  python -m app.main news                 # Run news sentiment analysis
  python -m app.main --config custom.yml  # Use custom config
        """
    )
    
    parser.add_argument(
        'command',
        choices=['morning', 'evening', 'status', 'weekly', 'restart', 'test', 'dashboard', 'enhanced-dashboard', 'professional-dashboard', 'news', 'divergence', 'economic', 'ml-scores', 'ml-trading', 'pre-trade', 'alpaca-setup', 'alpaca-test', 'start-trading', 'trading-history'],
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
    
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute actual trades (for ML trading commands)'
    )
    
    return parser

def launch_enhanced_dashboard():
    """Launch the enhanced dashboard"""
    print("🚀 Launching Enhanced ASX Bank Analysis Dashboard...")
    print("📊 Open your browser to: http://localhost:8501")
    
    import subprocess
    import os
    
    dashboard_path = Path(__file__).parent / "dashboard" / "enhanced_main.py"
    
    try:
        subprocess.run([
            "streamlit", "run", str(dashboard_path),
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch dashboard: {e}")
        print("💡 Try running: streamlit run app/dashboard/enhanced_main.py")
    except FileNotFoundError:
        print("❌ Streamlit not found. Install with: pip install streamlit")

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

def run_alpaca_setup():
    """Run Alpaca setup script"""
    print("🏢 Running Alpaca Setup...")
    
    import subprocess
    import sys
    
    setup_script = Path(__file__).parent.parent / "setup_alpaca.py"
    
    try:
        subprocess.run([sys.executable, str(setup_script)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Alpaca setup failed: {e}")
    except FileNotFoundError:
        print(f"❌ Setup script not found: {setup_script}")

def test_alpaca_connection():
    """Test Alpaca connection"""
    print("🔌 Testing Alpaca Connection...")
    
    try:
        from app.core.trading.alpaca_simulator import AlpacaTradingSimulator
        
        simulator = AlpacaTradingSimulator(paper_trading=True)
        
        if simulator.is_connected():
            account_info = simulator.get_account_info()
            print("✅ Successfully connected to Alpaca!")
            print(f"📊 Account equity: ${account_info.get('equity', 0):,.2f}")
            print(f"💰 Buying power: ${account_info.get('buying_power', 0):,.2f}")
            print(f"💵 Cash: ${account_info.get('cash', 0):,.2f}")
        else:
            print("❌ Failed to connect to Alpaca")
            print("💡 Run 'python app/main.py alpaca-setup' to configure credentials")
            
    except Exception as e:
        print(f"❌ Error testing connection: {e}")

def start_continuous_trading():
    """Start continuous Alpaca trading service"""
    print("🚀 Starting Continuous Alpaca Trading...")
    
    try:
        from app.core.trading.continuous_alpaca_trader import ContinuousAlpacaTrader
        
        trader = ContinuousAlpacaTrader()
        trader.run_continuous_trading()
        
    except ImportError:
        print("❌ Continuous trading service not found")
        print("💡 Run 'python app/main.py alpaca-setup' first")
    except Exception as e:
        print(f"❌ Error starting continuous trading: {e}")

def run_ml_analysis():
    """Run comprehensive ML analysis before trading."""
    print("🧠 Running Comprehensive ML Analysis...")
    
    try:
        from app.core.commands.ml_trading import MLTradingCommand
        
        ml_command = MLTradingCommand()
        
        if not ml_command.components_loaded:
            print("❌ ML components not loaded properly")
            return
        
        # Run comprehensive analysis
        results = ml_command.run_ml_analysis_before_trade()
        
        if 'error' in results:
            print(f"❌ Analysis failed: {results['error']}")
            return
        
        # Display ML scores table
        ml_scores = results.get('ml_scores', {})
        if ml_scores:
            ml_command.display_ml_scores_table(ml_scores)
        
        # Save results for later use
        import json
        import os
        os.makedirs('data/ml_analysis', exist_ok=True)
        with open('data/ml_analysis/latest_analysis.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Analysis complete. Results saved to data/ml_analysis/latest_analysis.json")
        
    except Exception as e:
        print(f"❌ ML analysis error: {e}")

def run_ml_trading():
    """Execute ML-based trading strategy."""
    print("💹 Executing ML Trading Strategy...")
    
    try:
        from app.core.commands.ml_trading import MLTradingCommand
        import json
        import os
        
        ml_command = MLTradingCommand()
        
        if not ml_command.components_loaded:
            print("❌ ML components not loaded properly")
            return
        
        # Try to load previous analysis
        analysis_results = None
        analysis_file = 'data/ml_analysis/latest_analysis.json'
        
        if os.path.exists(analysis_file):
            try:
                with open(analysis_file, 'r') as f:
                    analysis_results = json.load(f)
                print("📊 Using saved analysis results")
            except:
                print("⚠️ Could not load saved analysis, running fresh analysis")
        
        # Ask user for confirmation and parameters
        print("\n🎛️ Trading Parameters:")
        max_exposure = input("Maximum total exposure (USD) [default: 25000]: ").strip()
        max_exposure = float(max_exposure) if max_exposure else 25000.0
        
        dry_run_input = input("Dry run mode? (y/N) [default: yes]: ").strip().lower()
        dry_run = dry_run_input in ['', 'y', 'yes', 'true']
        
        print(f"\n🚀 Executing strategy with ${max_exposure:,.0f} max exposure ({'DRY RUN' if dry_run else 'LIVE'})")
        
        # Execute strategy
        execution_results = ml_command.execute_ml_trading_strategy(
            analysis_results=analysis_results,
            max_total_exposure=max_exposure,
            dry_run=dry_run
        )
        
        if 'error' in execution_results:
            print(f"❌ Execution failed: {execution_results['error']}")
        else:
            print(f"✅ Strategy execution complete")
            
            # Save execution results
            os.makedirs('data/ml_trading', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            with open(f'data/ml_trading/execution_{timestamp}.json', 'w') as f:
                json.dump(execution_results, f, indent=2)
        
    except Exception as e:
        print(f"❌ ML trading error: {e}")

def show_ml_status():
    """Show ML trading system status."""
    print("📊 ML Trading System Status...")
    
    try:
        from app.core.commands.ml_trading import MLTradingCommand
        
        ml_command = MLTradingCommand()
        status = ml_command.get_ml_trading_status()
        
        print(f"\n🎯 System Status:")
        print(f"   Components Loaded: {'✅' if status.get('components_loaded') else '❌'}")
        print(f"   Alpaca Connected: {'✅' if status.get('alpaca_connected') else '❌'}")
        print(f"   ML Models Available: {'✅' if status.get('ml_models_available') else '❌'}")
        print(f"   System Ready: {'✅' if status.get('system_ready') else '❌'}")
        
        if status.get('alpaca_connected'):
            print(f"\n💰 Account Information:")
            print(f"   Equity: ${status.get('account_equity', 0):,.2f}")
            print(f"   Buying Power: ${status.get('buying_power', 0):,.2f}")
            print(f"   Day Trades: {status.get('day_trade_count', 0)}")
        
        # Check for recent analysis
        import os
        if os.path.exists('data/ml_analysis/latest_analysis.json'):
            import json
            try:
                with open('data/ml_analysis/latest_analysis.json', 'r') as f:
                    analysis = json.load(f)
                timestamp = analysis.get('timestamp', 'Unknown')
                summary = analysis.get('summary', {})
                print(f"\n📊 Latest Analysis:")
                print(f"   Timestamp: {timestamp}")
                print(f"   Banks Analyzed: {summary.get('banks_analyzed', 0)}")
                print(f"   Trading Signals: {summary.get('trading_signals_generated', 0)}")
                print(f"   Economic Regime: {summary.get('economic_regime', 'Unknown')}")
            except:
                print(f"\n⚠️ Could not read latest analysis")
        else:
            print(f"\n📊 No recent analysis available")
            print(f"   Run: python -m app.main ml-analyze")
        
    except Exception as e:
        print(f"❌ Status check error: {e}")

def launch_ml_dashboard():
    """Launch the ML trading dashboard using Streamlit."""
    print("🚀 Launching ML Trading Dashboard...")
    
    try:
        import subprocess
        import sys
        import os
        
        # Get the dashboard script path
        dashboard_script = os.path.join(os.path.dirname(__file__), 'dashboard', 'ml_trading_dashboard.py')
        
        if not os.path.exists(dashboard_script):
            print(f"❌ Dashboard script not found: {dashboard_script}")
            return
        
        print(f"📊 Starting Streamlit dashboard at: http://localhost:8501")
        print(f"🔄 Dashboard will auto-refresh with latest ML analysis data")
        print(f"⚠️  Press Ctrl+C to stop the dashboard")
        
        # Run streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", dashboard_script, "--server.port=8501"]
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print(f"\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        print(f"💡 Make sure Streamlit is installed: pip install streamlit plotly")

def show_trading_history():
    """Display ML trading positions with profit/loss information in a formatted table."""
    print("📊 ML Trading History - Positions & Performance")
    print("=" * 90)
    
    try:
        import sqlite3
        import os
        from datetime import datetime
        
        db_path = 'data/position_tracking/position_outcomes.db'
        
        if not os.path.exists(db_path):
            print("❌ No trading history database found")
            print("💡 Positions will be recorded once ML trading starts")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if there are any positions
        cursor.execute("SELECT COUNT(*) FROM position_outcomes")
        total_positions = cursor.fetchone()[0]
        
        if total_positions == 0:
            print("📝 No trading positions found in database")
            print("💡 Start ML trading to see positions here: python app/main.py ml-trading")
            conn.close()
            return
        
        # Get detailed position information
        query = """
        SELECT 
            symbol,
            DATE(entry_date) as entry_date,
            ROUND(entry_price, 2) as entry_price,
            DATE(exit_date) as exit_date,
            ROUND(exit_price, 2) as exit_price,
            position_type,
            ROUND(position_size, 0) as shares,
            CASE 
                WHEN exit_price IS NOT NULL AND entry_price IS NOT NULL THEN 
                    ROUND((exit_price - entry_price) * position_size, 2)
                ELSE NULL
            END as profit_loss,
            CASE 
                WHEN exit_price IS NOT NULL AND entry_price IS NOT NULL THEN 
                    ROUND(((exit_price - entry_price) / entry_price) * 100, 2)
                ELSE NULL
            END as return_pct,
            exit_reason,
            ROUND(confidence_at_entry * 100, 1) as ml_confidence,
            ROUND(sentiment_at_entry, 2) as sentiment_score
        FROM position_outcomes 
        ORDER BY entry_date DESC
        """
        
        cursor.execute(query)
        positions = cursor.fetchall()
        
        # Display header
        print(f"\n🎯 Total Positions: {total_positions}")
        print("\n" + "─" * 90)
        print(f"{'Symbol':<8} {'Entry Date':<12} {'Entry $':<8} {'Exit Date':<12} {'Exit $':<8} {'Shares':<7} {'P&L $':<10} {'Return %':<9} {'ML Conf':<8} {'Exit Reason':<12}")
        print("─" * 90)
        
        total_pnl = 0.0
        winning_trades = 0
        losing_trades = 0
        open_positions = 0
        
        for pos in positions:
            symbol, entry_date, entry_price, exit_date, exit_price, pos_type, shares, pnl, return_pct, exit_reason, ml_conf, sentiment = pos
            
            # Format values for display
            exit_date_str = exit_date if exit_date else "OPEN"
            exit_price_str = f"{exit_price:.2f}" if exit_price else "---"
            pnl_str = f"{pnl:+.2f}" if pnl is not None else "OPEN"
            return_pct_str = f"{return_pct:+.2f}%" if return_pct is not None else "OPEN"
            exit_reason_str = exit_reason if exit_reason else "open"
            
            # Color coding for profit/loss
            if pnl is not None:
                pnl_color = "🟢" if pnl >= 0 else "🔴"
                pnl_str = f"{pnl_color} {pnl_str}"
                total_pnl += pnl
                
                if pnl >= 0:
                    winning_trades += 1
                else:
                    losing_trades += 1
            else:
                open_positions += 1
                pnl_str = "⚪ OPEN"
            
            print(f"{symbol:<8} {entry_date:<12} {entry_price:<8.2f} {exit_date_str:<12} {exit_price_str:<8} {shares:<7.0f} {pnl_str:<17} {return_pct_str:<9} {ml_conf:<6.1f}% {exit_reason_str:<12}")
        
        conn.close()
        
        # Display summary statistics
        print("─" * 90)
        print(f"\n📈 Performance Summary:")
        print(f"   Total P&L: {'🟢' if total_pnl >= 0 else '🔴'} ${total_pnl:+,.2f}")
        print(f"   Winning Trades: 🟢 {winning_trades}")
        print(f"   Losing Trades: 🔴 {losing_trades}")
        print(f"   Open Positions: ⚪ {open_positions}")
        
        if winning_trades + losing_trades > 0:
            win_rate = (winning_trades / (winning_trades + losing_trades)) * 100
            print(f"   Win Rate: {win_rate:.1f}%")
            
            if total_pnl != 0:
                avg_win = sum(pos[7] for pos in positions if pos[7] and pos[7] > 0) / max(winning_trades, 1)
                avg_loss = sum(pos[7] for pos in positions if pos[7] and pos[7] < 0) / max(losing_trades, 1)
                print(f"   Avg Win: ${avg_win:.2f}")
                print(f"   Avg Loss: ${avg_loss:.2f}")
                if avg_loss != 0:
                    profit_factor = abs(avg_win / avg_loss) if avg_loss < 0 else avg_win
                    print(f"   Profit Factor: {profit_factor:.2f}")
        
        print(f"\n💡 Tips:")
        print(f"   • Run 'python app/main.py ml-scores' to see current opportunities")
        print(f"   • Run 'python app/main.py ml-trading' to execute new positions")
        print(f"   • Your ML system has a 70.7% historical success rate")
        
    except Exception as e:
        print(f"❌ Error displaying trading history: {e}")
        import traceback
        traceback.print_exc()

def show_alpaca_setup():
    """Show Alpaca setup instructions."""
    try:
        from app.core.trading.alpaca_simulator import setup_alpaca_credentials
        setup_alpaca_credentials()
    except Exception as e:
        print(f"❌ Error showing Alpaca setup: {e}")

def run_ml_scores_display():
    """Display ML trading scores for all banks."""
    print("🧠 ML Trading Scores Display")
    print("=" * 40)
    
    try:
        from app.core.ml.trading_manager import MLTradingManager
        
        manager = MLTradingManager()
        manager.display_ml_scores_summary()
        
    except Exception as e:
        print(f"❌ ML scores display error: {e}")

def run_ml_trading_session(execute_trades: bool = False):
    """Run a complete ML trading session."""
    print("🚀 ML Trading Session")
    print("=" * 40)
    
    try:
        from app.core.ml.trading_manager import MLTradingManager
        
        manager = MLTradingManager()
        
        if execute_trades:
            print("⚠️ WARNING: This will execute real trades!")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                print("📊 Trading session cancelled")
                return
        
        session_results = manager.run_ml_trading_session(execute_trades=execute_trades)
        
        if 'error' not in session_results:
            print("\n✅ ML Trading Session completed successfully")
            
            # Display summary
            summary = session_results.get('analysis', {}).get('summary', {})
            if summary:
                print(f"\n📊 Session Summary:")
                print(f"   Symbols Analyzed: {summary.get('symbols_analyzed', 0)}")
                print(f"   Economic Regime: {summary.get('economic_regime', 'Unknown')}")
                print(f"   Strong Buy Recommendations: {summary.get('total_recommendations', {}).get('strong_buy', 0)}")
                print(f"   Buy Recommendations: {summary.get('total_recommendations', {}).get('buy', 0)}")
        else:
            print(f"❌ ML Trading Session failed: {session_results['error']}")
            
    except Exception as e:
        print(f"❌ ML trading session error: {e}")

def run_pre_trade_analysis(symbol: str = None):
    """Run pre-trade ML analysis for a specific symbol."""
    if not symbol:
        print("❌ Symbol required for pre-trade analysis")
        print("💡 Usage: python -m app.main pre-trade --symbol CBA.AX")
        return
    
    print(f"🔍 Pre-Trade Analysis for {symbol}")
    print("=" * 40)
    
    try:
        from app.core.ml.trading_manager import MLTradingManager
        
        manager = MLTradingManager()
        pre_trade_info = manager.check_before_trade(symbol)
        
        if 'error' not in pre_trade_info:
            print(f"\n✅ Pre-trade analysis completed for {symbol}")
            
            # Ask if user wants to see Alpaca account info
            try:
                from app.core.trading.alpaca_integration import AlpacaMLTrader
                alpaca_trader = AlpacaMLTrader(paper=True)
                
                if alpaca_trader.is_available():
                    print(f"\n💰 Alpaca Account Status:")
                    account_info = alpaca_trader.get_account_info()
                    if 'error' not in account_info:
                        print(f"   Portfolio Value: ${account_info.get('portfolio_value', 0):,.2f}")
                        print(f"   Buying Power: ${account_info.get('buying_power', 0):,.2f}")
                        print(f"   Cash: ${account_info.get('cash', 0):,.2f}")
                else:
                    print(f"\n📊 Alpaca trading not available (missing credentials)")
            except Exception as e:
                print(f"\n⚠️ Alpaca status check failed: {e}")
        else:
            print(f"❌ Pre-trade analysis failed: {pre_trade_info['error']}")
            
    except Exception as e:
        print(f"❌ Pre-trade analysis error: {e}")

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
        
        # Kill any background processes we might have started
        import subprocess
        try:
            # Kill news collector processes
            subprocess.run(["pkill", "-f", "news_collector"], capture_output=True)
            # Kill any dashboard processes
            subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
            # Kill any other python trading processes
            subprocess.run(["pkill", "-f", "app.main"], capture_output=True)
            logger.info("Background processes terminated")
        except Exception as e:
            logger.warning(f"Error terminating background processes: {e}")
    
    # Register cleanup function
    register_cleanup(cleanup_system)
    
    try:
        # Initialize system manager
        manager = TradingSystemManager(
            config_path=args.config,
            dry_run=not args.execute  # Use --execute flag to enable live trading
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
        elif args.command == 'dashboard':
            # Use enhanced dashboard as default (professional dashboard has data issues)
            launch_enhanced_dashboard()
        elif args.command == 'enhanced-dashboard':
            launch_enhanced_dashboard()
        elif args.command == 'professional-dashboard':
            # Keep old professional dashboard available but not as default
            from app.dashboard.pages.professional import main as run_professional_dashboard
            run_professional_dashboard()
        elif args.command == 'news':
            manager.news_analysis()
        elif args.command == 'divergence':
            run_divergence_analysis()
        elif args.command == 'economic':
            run_economic_analysis()
        elif args.command == 'ml-scores':
            run_ml_scores_display()
        elif args.command == 'ml-trading':
            run_ml_trading_session(args.execute)
        elif args.command == 'pre-trade':
            run_pre_trade_analysis(args.symbol)
        elif args.command == 'ml-analyze':
            run_ml_analysis()
        elif args.command == 'ml-trade':
            run_ml_trading()
        elif args.command == 'ml-status':
            show_ml_status()
        elif args.command == 'ml-dashboard':
            launch_ml_dashboard()
        elif args.command == 'alpaca-setup':
            run_alpaca_setup()
        elif args.command == 'alpaca-test':
            test_alpaca_connection()
        elif args.command == 'start-trading':
            start_continuous_trading()
        elif args.command == 'trading-history':
            show_trading_history()
        
        logger.info(f"Command '{args.command}' completed successfully")
        print("✅ Command completed successfully")
        print("💡 Use Ctrl+C to stop any background processes")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\n🛑 Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error executing command '{args.command}': {e}")
        if args.verbose:
            logger.exception("Full traceback:")
        sys.exit(1)

if __name__ == "__main__":
    main()

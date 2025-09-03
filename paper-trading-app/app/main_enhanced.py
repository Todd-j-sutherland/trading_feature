#!/usr/bin/env python3
"""
Enhanced Main Application Entry Point with Market-Aware Trading System
Integrates the market context analysis from the investigation
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
from app.services.market_aware_daily_manager import MarketAwareTradingManager, create_market_aware_manager
from app.core.ml.prediction import create_market_aware_predictor

def setup_enhanced_cli():
    """Setup enhanced command line interface"""
    parser = argparse.ArgumentParser(
        description="Enhanced Trading Analysis System with Market Context",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Enhanced Commands with Market Context:
  python -m app.main_enhanced market-morning    # Morning routine with market context
  python -m app.main_enhanced market-status     # Market context analysis
  python -m app.main_enhanced market-signals    # Generate market-aware signals
  python -m app.main_enhanced test-predictor    # Test market-aware predictor
  
Standard Commands:
  python -m app.main_enhanced morning           # Standard morning routine
  python -m app.main_enhanced evening           # Standard evening routine
  python -m app.main_enhanced status            # Quick status check
        """
    )
    
    parser.add_argument(
        'command',
        choices=[
            'morning', 'evening', 'status', 
            'market-morning', 'market-status', 'market-signals',
            'test-predictor', 'test-market-context'
        ],
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
        '--dry-run',
        action='store_true',
        default=True,
        help='Run in dry-run mode (default: True)'
    )
    
    return parser

def test_market_context():
    """Test market context analysis functionality"""
    print("🧪 TESTING MARKET CONTEXT ANALYSIS")
    print("=" * 50)
    
    try:
        # Create predictor
        predictor = create_market_aware_predictor()
        
        # Test market context
        print("🌐 Testing market context retrieval...")
        market_context = predictor.get_cached_market_context()
        
        print(f"✅ Market Context Results:")
        print(f"   ASX 200 Level: {market_context['current_level']:.1f}")
        print(f"   5-day Trend: {market_context['trend_pct']:+.2f}%")
        print(f"   Market Context: {market_context['context']}")
        print(f"   Confidence Multiplier: {market_context['confidence_multiplier']:.1f}x")
        print(f"   BUY Threshold: {market_context['buy_threshold']:.1%}")
        
        # Test context logic
        if market_context['context'] == 'BEARISH':
            print("⚠️  BEARISH market detected - stricter criteria applied")
        elif market_context['context'] == 'BULLISH':
            print("📈 BULLISH market detected - enhanced opportunities")
        else:
            print("📊 NEUTRAL market - standard criteria applied")
            
        return True
        
    except Exception as e:
        print(f"❌ Market context test failed: {e}")
        return False

def test_market_aware_predictor():
    """Test the market-aware prediction system"""
    print("🧪 TESTING MARKET-AWARE PREDICTOR")
    print("=" * 50)
    
    try:
        # Create predictor
        predictor = create_market_aware_predictor()
        
        # Test sample prediction
        print("🎯 Testing sample prediction...")
        sample_features = {
            'technical_score': 65,
            'sentiment_score': 55,
            'volume_ratio': 1.2,
            'volatility': 0.020,
            'news_confidence': 0.7,
            'rsi': 45,
            'macd_signal': 0.5,
            'volume_trend': 0.05
        }
        
        prediction = predictor.predict_price_with_market_context(
            symbol="CBA.AX",
            current_price=100.50,
            features=sample_features
        )
        
        print(f"✅ Prediction Results:")
        print(f"   Symbol: {prediction.symbol}")
        print(f"   Current Price: ${prediction.current_price:.2f}")
        print(f"   Predicted Price: ${prediction.predicted_price:.2f}")
        print(f"   Price Change: {prediction.price_change_pct:+.2f}%")
        print(f"   Confidence: {prediction.confidence:.1%}")
        print(f"   Model Used: {prediction.model_used}")
        
        # Show market context details
        details = prediction.supporting_features.get('prediction_details', {})
        print(f"\n📊 Market-Aware Details:")
        print(f"   Market Context: {details.get('market_context', 'N/A')}")
        print(f"   Market Trend: {details.get('market_trend_pct', 0):+.2f}%")
        print(f"   BUY Threshold Used: {details.get('buy_threshold_used', 0):.1%}")
        print(f"   Recommended Action: {details.get('recommended_action', 'N/A')}")
        print(f"   Technical Score: {details.get('tech_score', 0):.0f}")
        print(f"   News Sentiment: {details.get('news_sentiment', 0):+.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Predictor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_market_aware_signals():
    """Generate and display market-aware trading signals"""
    print("🎯 GENERATING MARKET-AWARE TRADING SIGNALS")
    print("=" * 50)
    
    try:
        # Create manager
        manager = create_market_aware_manager(dry_run=True)
        
        # Generate signals
        print("🔄 Analyzing market conditions and generating signals...")
        predictions = manager._generate_market_aware_signals()
        
        if predictions:
            market_context = manager.market_predictor.get_cached_market_context()
            manager._display_prediction_summary(predictions, market_context)
            
            # Additional analysis
            buy_signals = []
            for symbol, prediction in predictions.items():
                details = prediction.supporting_features.get('prediction_details', {})
                action = details.get('recommended_action', 'HOLD')
                if action in ['BUY', 'STRONG_BUY']:
                    buy_signals.append(symbol)
            
            print(f"\n📈 Trading Signal Summary:")
            print(f"   Total Symbols Analyzed: {len(predictions)}")
            print(f"   BUY Signals Generated: {len(buy_signals)}")
            if buy_signals:
                print(f"   BUY Signal Symbols: {', '.join(buy_signals)}")
            
            # Save to database
            try:
                manager.market_predictor.save_predictions_to_database(predictions)
                print(f"✅ Predictions saved to database")
            except Exception as e:
                print(f"⚠️  Database save failed: {e}")
                
        else:
            print("📊 No trading signals generated")
            
        return True
        
    except Exception as e:
        print(f"❌ Signal generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Enhanced main application entry point"""
    parser = setup_enhanced_cli()
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Enhanced Trading System - Command: {args.command}")
    
    try:
        success = True
        
        if args.command == 'market-morning':
            # Enhanced morning routine with market context
            print("🚀 Starting Market-Aware Morning Routine...")
            manager = create_market_aware_manager(config_path=args.config, dry_run=args.dry_run)
            manager.enhanced_morning_routine()
            
        elif args.command == 'market-status':
            # Market context status check
            manager = create_market_aware_manager(config_path=args.config, dry_run=args.dry_run)
            manager.quick_market_status()
            
        elif args.command == 'market-signals':
            # Generate market-aware signals
            success = generate_market_aware_signals()
            
        elif args.command == 'test-market-context':
            # Test market context analysis
            success = test_market_context()
            
        elif args.command == 'test-predictor':
            # Test market-aware predictor
            success = test_market_aware_predictor()
            
        elif args.command in ['morning', 'evening', 'status']:
            # Standard commands using enhanced manager
            manager = create_market_aware_manager(config_path=args.config, dry_run=args.dry_run)
            
            if args.command == 'morning':
                manager.morning_routine()
            elif args.command == 'evening':
                manager.evening_routine()
            elif args.command == 'status':
                manager.quick_status()
                
        else:
            print(f"❌ Unknown command: {args.command}")
            success = False
        
        if success:
            logger.info(f"Command '{args.command}' completed successfully")
            print(f"\n✅ {args.command.replace('-', ' ').title()} completed successfully")
            
            # Show available commands
            if args.command in ['market-status', 'test-market-context']:
                print("\n💡 Available market-aware commands:")
                print("   • market-morning: Full morning routine with market context")
                print("   • market-signals: Generate trading signals")
                print("   • test-predictor: Test prediction system")
        else:
            print(f"\n❌ {args.command} failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\n👋 Operation cancelled by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Error executing command '{args.command}': {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        print(f"\n❌ Command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

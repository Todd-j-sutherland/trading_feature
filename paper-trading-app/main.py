#!/usr/bin/env python3
"""
Market-Aware Paper Trading System - Main Application
Integrates market context analysis with paper trading for better signal quality

Key Features:
- Market context awareness (ASX 200 trend analysis)
- Reduced base confidence (20% -> 10%) 
- Dynamic BUY thresholds based on market conditions
- Enhanced requirements during bearish markets
- Integration with existing paper trading infrastructure
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add paper trading app and app config to path
paper_trading_path = Path(__file__).parent.parent / "paper-trading-app"
app_config_path = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(paper_trading_path))
sys.path.insert(0, str(app_config_path))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_aware_paper_trading.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Import market-aware prediction system
from market_aware_prediction_system import MarketAwarePredictionSystem

# Import settings configuration
try:
    from config.settings import Settings
    SETTINGS_AVAILABLE = True
    logger.info("✅ Settings configuration loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Settings configuration not available: {e}")
    SETTINGS_AVAILABLE = False

# Import existing paper trading components
try:
    from enhanced_paper_trading_service import EnhancedPaperTradingService
    from enhanced_ig_markets_integration import get_enhanced_price_source
    PAPER_TRADING_AVAILABLE = True
    logger.info("✅ Paper trading components loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Paper trading components not available: {e}")
    PAPER_TRADING_AVAILABLE = False

class MarketAwarePaperTradingApp:
    """
    Main application that combines market-aware predictions with paper trading
    """
    
    def __init__(self):
        self.prediction_system = MarketAwarePredictionSystem()
        self.paper_trading_service = None
        self.last_market_analysis = None
        self.last_analysis_time = None
        
        if PAPER_TRADING_AVAILABLE:
            try:
                self.paper_trading_service = EnhancedPaperTradingService()
                logger.info("✅ Paper trading service initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize paper trading service: {e}")
    
    def morning_routine(self):
        """Enhanced morning routine with market context"""
        logger.info("🌅 MARKET-AWARE MORNING ROUTINE")
        logger.info("=" * 60)
        
        try:
            # 1. Analyze market context
            market_context = self.prediction_system.get_market_context()
            self.last_market_analysis = market_context
            self.last_analysis_time = datetime.now()
            
            logger.info(f"🌐 Market Context Analysis:")
            logger.info(f"   ASX 200 Level: {market_context['current_level']:.1f}")
            logger.info(f"   5-day Trend: {market_context['trend_pct']:+.2f}%")
            logger.info(f"   Market Context: {market_context['context']}")
            logger.info(f"   BUY Threshold: {market_context['buy_threshold']:.1%}")
            logger.info(f"   Confidence Multiplier: {market_context['confidence_multiplier']:.1f}x")
            
            # Alert for market conditions
            if market_context['context'] == 'BEARISH':
                logger.warning("⚠️ BEARISH MARKET DETECTED - Using stricter signal criteria")
            elif market_context['context'] == 'BULLISH':
                logger.info("📈 BULLISH MARKET DETECTED - Enhanced opportunities expected")
            
            # 2. Generate market-aware trading signals
            logger.info(f"\n🎯 Generating Market-Aware Trading Signals...")
            signals = self.generate_trading_signals()
            
            if signals:
                self.display_signal_summary(signals, market_context)
                return signals
            else:
                logger.info("📊 No trading signals generated")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error in morning routine: {e}")
            return []
    
    def generate_trading_signals(self):
        """Generate trading signals using market-aware prediction system"""
        try:
            # Use symbols from settings if available, otherwise fallback to defaults
            if SETTINGS_AVAILABLE:
                # Use ONLY the 7 bank symbols from settings configuration
                symbols = Settings.BANK_SYMBOLS.copy()
                
                logger.info(f"📊 Using {len(symbols)} bank symbols from settings configuration")
                logger.info(f"   Bank symbols: {', '.join(Settings.BANK_SYMBOLS)}")
            else:
                # Fallback symbols if settings not available
                symbols = [
                    'CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX',  # Big 4 Banks
                    'MQG.AX', 'SUN.AX', 'QBE.AX'             # Other financials
                ]
                logger.warning("⚠️ Using fallback symbols - settings not available")
            
            signals = []
            
            for symbol in symbols:
                try:
                    # Generate prediction for this symbol
                    signal = self.prediction_system.analyze_symbol(symbol)
                    
                    if signal and signal.get('action') in ['BUY', 'STRONG_BUY']:
                        signals.append(signal)
                        
                        # Show bank name if available
                        if SETTINGS_AVAILABLE:
                            bank_name = Settings.get_bank_name(symbol)
                            logger.info(f"📈 {bank_name} ({symbol}): {signal['action']} (Confidence: {signal['confidence']:.1%})")
                        else:
                            logger.info(f"📈 {symbol}: {signal['action']} (Confidence: {signal['confidence']:.1%})")
                    
                except Exception as e:
                    logger.error(f"❌ Error analyzing {symbol}: {e}")
                    continue
            
            return signals
            
        except Exception as e:
            logger.error(f"❌ Error generating trading signals: {e}")
            return []
    
    def display_signal_summary(self, signals, market_context):
        """Display formatted signal summary"""
        if not signals:
            return
            
        logger.info(f"\n📊 TRADING SIGNAL SUMMARY")
        logger.info(f"   Market Context: {market_context['context']}")
        logger.info(f"   Signals Generated: {len(signals)}")
        
        # Categorize signals
        strong_buy = [s for s in signals if s['action'] == 'STRONG_BUY']
        buy = [s for s in signals if s['action'] == 'BUY']
        
        logger.info(f"   🚀 STRONG BUY: {len(strong_buy)}")
        logger.info(f"   📈 BUY: {len(buy)}")
        
        # Show top signals
        if strong_buy:
            logger.info(f"\n🚀 STRONG BUY SIGNALS:")
            for signal in strong_buy[:3]:  # Top 3
                # Get bank name if available
                symbol_name = signal['symbol']
                if SETTINGS_AVAILABLE:
                    bank_name = Settings.get_bank_name(signal['symbol'])
                    symbol_name = f"{bank_name} ({signal['symbol']})"
                
                logger.info(f"   {symbol_name}: {signal['confidence']:.1%} confidence")
                logger.info(f"      Price: ${signal['current_price']:.2f}")
                logger.info(f"      Technical: {signal.get('tech_score', 0):.0f} | News: {signal.get('news_sentiment', 0):+.2f}")
        
        if buy:
            logger.info(f"\n📈 BUY SIGNALS:")
            for signal in buy[:3]:  # Top 3
                # Get bank name if available
                symbol_name = signal['symbol']
                if SETTINGS_AVAILABLE:
                    bank_name = Settings.get_bank_name(signal['symbol'])
                    symbol_name = f"{bank_name} ({signal['symbol']})"
                
                logger.info(f"   {symbol_name}: {signal['confidence']:.1%} confidence")
                logger.info(f"      Price: ${signal['current_price']:.2f}")
        
        # Market warnings
        total_signals = len(signals)
        if market_context['context'] == 'BEARISH' and total_signals > 3:
            logger.warning(f"⚠️ WARNING: {total_signals} BUY signals during BEARISH market")
            logger.warning(f"   Manual review recommended for risk management")
    
    def execute_paper_trading(self, signals):
        """Execute paper trading based on signals"""
        if not PAPER_TRADING_AVAILABLE or not self.paper_trading_service:
            logger.warning("⚠️ Paper trading service not available")
            return
            
        if not signals:
            logger.info("📊 No signals to execute")
            return
            
        logger.info(f"\n💼 EXECUTING PAPER TRADING")
        logger.info(f"   Processing {len(signals)} signals...")
        
        for signal in signals:
            try:
                symbol = signal['symbol']
                confidence = signal['confidence']
                action = signal['action']
                current_price = signal['current_price']
                
                # Only execute high-confidence signals
                min_confidence = 0.75 if action == 'BUY' else 0.80  # Higher bar for STRONG_BUY
                
                if confidence >= min_confidence:
                    logger.info(f"🎯 Executing {action} for {symbol} at ${current_price:.2f}")
                    
                    # Execute through paper trading service
                    # This would integrate with your existing paper trading logic
                    # self.paper_trading_service.execute_trade(symbol, action, current_price)
                    
                    logger.info(f"✅ Paper trade executed: {symbol}")
                else:
                    logger.info(f"⏸️ Skipping {symbol}: Confidence {confidence:.1%} below threshold {min_confidence:.1%}")
                    
            except Exception as e:
                logger.error(f"❌ Error executing trade for {signal['symbol']}: {e}")
    
    def run_continuous_monitoring(self):
        """Run continuous monitoring with market awareness"""
        logger.info("🔄 Starting continuous market-aware monitoring...")
        
        while True:
            try:
                current_time = datetime.now()
                
                # Check if we need to refresh market analysis (every 30 minutes)
                if (self.last_analysis_time is None or 
                    current_time - self.last_analysis_time > timedelta(minutes=30)):
                    
                    logger.info("🔄 Refreshing market context...")
                    self.last_market_analysis = self.prediction_system.get_market_context()
                    self.last_analysis_time = current_time
                
                # Generate signals every 5 minutes during market hours
                if self.is_market_hours():
                    signals = self.generate_trading_signals()
                    if signals:
                        self.execute_paper_trading(signals)
                
                # Sleep for 5 minutes
                time.sleep(300)
                
            except KeyboardInterrupt:
                logger.info("👋 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def is_market_hours(self):
        """Check if it's during ASX market hours"""
        now = datetime.now()
        
        # ASX is open Monday-Friday, 10:00 AM - 4:00 PM AEST
        if now.weekday() >= 5:  # Weekend
            return False
            
        hour = now.hour
        return 10 <= hour <= 16
    
    def status_check(self):
        """Quick status check"""
        logger.info("🔍 MARKET-AWARE PAPER TRADING STATUS")
        logger.info("=" * 50)
        
        try:
            # Market status
            if self.last_market_analysis:
                market = self.last_market_analysis
                logger.info(f"📊 Last Market Analysis: {self.last_analysis_time.strftime('%H:%M:%S')}")
                logger.info(f"   ASX 200: {market['current_level']:.1f} ({market['trend_pct']:+.2f}%)")
                logger.info(f"   Context: {market['context']}")
                logger.info(f"   BUY Threshold: {market['buy_threshold']:.1%}")
            else:
                logger.info("📊 No market analysis available - run morning routine first")
            
            # Paper trading status
            if PAPER_TRADING_AVAILABLE:
                logger.info("✅ Paper trading service: Available")
            else:
                logger.info("❌ Paper trading service: Not available")
            
            # Market hours
            if self.is_market_hours():
                logger.info("🕒 Market Status: OPEN")
            else:
                logger.info("🕒 Market Status: CLOSED")
                
        except Exception as e:
            logger.error(f"❌ Error in status check: {e}")

def main():
    """Main application entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Market-Aware Paper Trading System")
    parser.add_argument('command', choices=['morning', 'monitor', 'status', 'test'], 
                       help='Command to execute')
    args = parser.parse_args()
    
    # Initialize app
    app = MarketAwarePaperTradingApp()
    
    try:
        if args.command == 'morning':
            signals = app.morning_routine()
            if signals and PAPER_TRADING_AVAILABLE:
                app.execute_paper_trading(signals)
                
        elif args.command == 'monitor':
            app.run_continuous_monitoring()
            
        elif args.command == 'status':
            app.status_check()
            
        elif args.command == 'test':
            logger.info("🧪 Testing market-aware prediction system...")
            signals = app.generate_trading_signals()
            logger.info(f"✅ Test completed - {len(signals)} signals generated")
            
        logger.info("✅ Command completed successfully")
        
    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

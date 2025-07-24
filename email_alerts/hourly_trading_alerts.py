#!/usr/bin/env python3
"""
Hourly Trading Alerts System
Sends ML-based trading signals via email every hour during market hours

Usage:
    python hourly_trading_alerts.py        # Run once
    python hourly_trading_alerts.py --loop # Run continuously (hourly)
    python hourly_trading_alerts.py --test # Send test alert
"""

import os
import sys
import time
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'app'))

# Import your existing components
from app.core.data.collectors.market_data import ASXDataFeed
from app.services.daily_manager import TradingSystemManager
from app.config.settings import Settings
from hybrid_email_service import HybridEmailService
from no_auth_email_service import NoAuthEmailService

logger = logging.getLogger(__name__)

class HourlyTradingAlerts:
    """
    Hourly trading alert system using your existing ML components
    """
    
    def __init__(self):
        self.settings = Settings()
        self.email_service = HybridEmailService()
        self.trading_manager = TradingSystemManager()
        self.market_data = ASXDataFeed()
        
        # Symbols to monitor
        self.symbols = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX']
        
        # Alert configuration
        self.confidence_threshold = 0.7  # Only send alerts for high confidence signals
        self.min_sentiment_change = 0.1  # Minimum sentiment change to trigger alert
        
        # Alert history to avoid spam
        self.alert_history_file = Path("../data/alert_history.json")
        self.last_alerts = self.load_alert_history()
        
        # Market hours (AEST)
        self.market_open = "09:30"
        self.market_close = "16:00"
        
    def load_alert_history(self) -> dict:
        """Load previous alert history to avoid duplicates"""
        if self.alert_history_file.exists():
            try:
                with open(self.alert_history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load alert history: {e}")
        return {}
    
    def save_alert_history(self):
        """Save alert history to avoid duplicates"""
        try:
            self.alert_history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.alert_history_file, 'w') as f:
                json.dump(self.last_alerts, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save alert history: {e}")
    
    def is_market_open(self) -> bool:
        """Check if Australian market is currently open"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
            
        # Check if within market hours
        return self.market_open <= current_time <= self.market_close
    
    def should_send_alert(self, symbol: str, signal: str, confidence: float) -> bool:
        """Determine if we should send an alert based on history and thresholds"""
        
        # Check confidence threshold
        if confidence < self.confidence_threshold:
            logger.debug(f"{symbol}: Confidence {confidence:.2f} below threshold {self.confidence_threshold}")
            return False
        
        # Check if signal is actionable (not HOLD)
        if signal == 'HOLD':
            logger.debug(f"{symbol}: Signal is HOLD, no alert needed")
            return False
        
        # Check if we've sent this signal recently (within 2 hours)
        now = datetime.now()
        last_alert_key = f"{symbol}_{signal}"
        
        if last_alert_key in self.last_alerts:
            last_alert_time = datetime.fromisoformat(self.last_alerts[last_alert_key])
            hours_since_alert = (now - last_alert_time).total_seconds() / 3600
            
            if hours_since_alert < 2:  # Don't repeat same signal within 2 hours
                logger.debug(f"{symbol}: Same signal sent {hours_since_alert:.1f} hours ago, skipping")
                return False
        
        return True
    
    def generate_trading_signals(self) -> dict:
        """Generate current trading signals using your existing ML system"""
        signals = {}
        
        print("🔍 Analyzing current market conditions...")
        
        for symbol in self.symbols:
            try:
                # Get current price data
                current_data = self.market_data.get_current_data(symbol)
                current_price = current_data.get('price', 0)
                
                if current_price <= 0:
                    logger.warning(f"{symbol}: Could not get current price")
                    continue
                
                # Use your existing sentiment analysis system
                # This leverages your ML pipeline from daily_manager
                from app.core.data.processors.news_processor import NewsTradingAnalyzer
                news_analyzer = NewsTradingAnalyzer()
                
                # Get comprehensive analysis (uses your ML models)
                analysis = news_analyzer.analyze_single_bank(symbol, detailed=False)
                
                # Extract signal components
                sentiment_score = analysis.get('sentiment_score', 0)
                confidence = analysis.get('confidence', 0)
                signal = analysis.get('signal', 'HOLD')
                ml_prediction = analysis.get('ml_prediction', {})
                
                # Use your existing signal generation logic
                if hasattr(self.trading_manager, '_generate_signal_from_score'):
                    # Use the same logic from your daily_manager
                    refined_signal = self._generate_signal_from_score(sentiment_score, confidence)
                else:
                    refined_signal = signal
                
                signals[symbol] = {
                    'symbol': symbol,
                    'signal': refined_signal,
                    'sentiment_score': sentiment_score,
                    'confidence': confidence,
                    'current_price': current_price,
                    'ml_prediction': ml_prediction,
                    'timestamp': datetime.now().isoformat(),
                    'analysis': analysis
                }
                
                print(f"📊 {symbol}: {refined_signal} (Score: {sentiment_score:.3f}, Confidence: {confidence:.3f}, Price: ${current_price:.2f})")
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue
        
        return signals
    
    def _generate_signal_from_score(self, prediction_score: float, confidence: float) -> str:
        """Generate trading signal from prediction score and confidence (same logic as daily_manager)"""
        if prediction_score >= 0.7 and confidence >= 0.8:
            return "BUY"
        elif prediction_score >= 0.6 and confidence >= 0.7:
            return "BUY"
        elif prediction_score <= 0.3 and confidence >= 0.7:
            return "SELL"
        elif prediction_score <= 0.4 and confidence >= 0.8:
            return "SELL"
        else:
            return "HOLD"
    
    def create_alert_email(self, signals: dict) -> str:
        """Create formatted email content for trading alerts"""
        now = datetime.now()
        
        # Filter for actionable signals
        actionable_signals = {
            symbol: data for symbol, data in signals.items() 
            if data['signal'] != 'HOLD' and data['confidence'] >= self.confidence_threshold
        }
        
        if not actionable_signals:
            return None  # No alerts to send
        
        # Build email content
        subject = f"🚨 Trading Alert - {len(actionable_signals)} Signal{'s' if len(actionable_signals) > 1 else ''} - {now.strftime('%H:%M AEST')}"
        
        email_body = f"""
🤖 AI Trading Alert System
Generated: {now.strftime('%Y-%m-%d %H:%M:%S AEST')}

{'='*50}
📈 TRADING SIGNALS DETECTED
{'='*50}

"""
        
        for symbol, data in actionable_signals.items():
            signal = data['signal']
            price = data['current_price']
            sentiment = data['sentiment_score']
            confidence = data['confidence']
            
            # Signal emoji
            emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "🟡"
            
            email_body += f"""
{emoji} {symbol} - {signal}
    Current Price: ${price:.2f}
    Sentiment Score: {sentiment:+.3f}
    Confidence: {confidence:.1%}
    ML Prediction: {data.get('ml_prediction', {}).get('prediction', 'N/A')}
    
"""
        
        email_body += f"""
{'='*50}
📋 TRADING INSTRUCTIONS
{'='*50}

For BUY signals:
• Consider entering a long position at current market price
• Set stop-loss at -2% below entry price
• Set take-profit at +3% above entry price
• Monitor for SELL signal to close position

For SELL signals:
• Consider entering a short position or closing long positions
• Set stop-loss at +2% above entry price
• Set take-profit at -3% below entry price
• Monitor for BUY signal to close position

⚠️  RISK DISCLAIMER:
This is an automated ML-based analysis. Always:
• Verify signals with your own analysis
• Use appropriate position sizing
• Set stop-losses before entering trades
• Never risk more than you can afford to lose

📊 Next analysis in 1 hour during market hours.

Happy Trading! 🚀
"""
        
        return subject, email_body
    
    def send_trading_alerts(self, signals: dict) -> bool:
        """Send email alerts for actionable trading signals"""
        
        # Filter for actionable signals
        actionable_signals = {
            symbol: data for symbol, data in signals.items() 
            if data['signal'] != 'HOLD' and data['confidence'] >= self.confidence_threshold
        }
        
        if not actionable_signals:
            print("📭 No actionable signals to report")
            return True
        
        # Send individual alerts for each signal
        alerts_sent = 0
        
        for symbol, data in actionable_signals.items():
            try:
                # Create email content for this signal
                subject = f"🚨 Trading Alert: {symbol} - {data['signal']} Signal"
                body = f"""
🤖 AI Trading Alert

Symbol: {symbol}
Signal: {data['signal']}
Current Price: ${data['current_price']:.2f}
Confidence: {data['confidence']:.1%}

ML Analysis Details:
• Sentiment Score: {data['sentiment_score']:+.3f}
• ML Prediction: {data.get('ml_prediction', {}).get('prediction', 'N/A')}
• Analysis Time: {data['timestamp']}

Risk Management:
• Use appropriate position sizing (max 2% risk per trade)
• Set stop-loss at {'2% below entry' if data['signal'] == 'BUY' else '2% above entry'}
• Monitor for exit signals in next hourly update

⚠️ This is automated analysis. Always verify with your own research.
"""
                
                success = self.email_service.send_email(
                    to_email="sutho100@gmail.com",
                    subject=subject,
                    body=body
                )
                
                if success:
                    alerts_sent += 1
                    
                    # Update alert history
                    now = datetime.now().isoformat()
                    alert_key = f"{symbol}_{data['signal']}"
                    self.last_alerts[alert_key] = now
                
            except Exception as e:
                logger.error(f"Error sending alert for {symbol}: {e}")
        
        if alerts_sent > 0:
            print(f"✅ {alerts_sent} trading alert(s) sent successfully!")
            self.save_alert_history()
            return True
        else:
            print("❌ No alerts sent successfully")
            return False
    
    def run_single_check(self) -> bool:
        """Run a single trading signal check"""
        print("🤖 Hourly Trading Alert System")
        print("=" * 50)
        
        # Check if market is open
        if not self.is_market_open():
            print("🏢 Market is currently closed")
            print(f"📅 Market hours: {self.market_open} - {self.market_close} AEST (weekdays only)")
            return True
        
        print(f"⏰ Market is open - Running analysis at {datetime.now().strftime('%H:%M:%S AEST')}")
        
        # Generate signals
        signals = self.generate_trading_signals()
        
        if not signals:
            print("❌ No signals generated")
            return False
        
        # Send alerts for actionable signals
        return self.send_trading_alerts(signals)
    
    def run_continuous(self):
        """Run hourly checks continuously"""
        print("🔄 Starting continuous hourly monitoring...")
        print("⏰ Will check every hour during market hours")
        print("🛑 Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_single_check()
                
                # Wait for next hour
                next_hour = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                sleep_seconds = (next_hour - datetime.now()).total_seconds()
                
                print(f"💤 Waiting until {next_hour.strftime('%H:%M')} for next check...")
                time.sleep(sleep_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    """Main entry point"""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Hourly Trading Alerts using ML Analysis")
    parser.add_argument('--loop', action='store_true', help='Run continuously (hourly checks)')
    parser.add_argument('--test', action='store_true', help='Send test alert')
    
    args = parser.parse_args()
    
    # Create alerts system
    alerts = HourlyTradingAlerts()
    
    if args.test:
        # Send test alert
        print("📧 Sending test trading alert...")
        test_signals = {
            'CBA.AX': {
                'symbol': 'CBA.AX',
                'signal': 'BUY',
                'sentiment_score': 0.75,
                'confidence': 0.85,
                'current_price': 105.50,
                'ml_prediction': {'prediction': 'PROFITABLE'},
                'timestamp': datetime.now().isoformat()
            }
        }
        success = alerts.send_trading_alerts(test_signals)
        sys.exit(0 if success else 1)
    
    elif args.loop:
        # Run continuously
        alerts.run_continuous()
    
    else:
        # Run single check
        success = alerts.run_single_check()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

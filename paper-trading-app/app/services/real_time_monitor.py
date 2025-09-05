"""
Real-Time Trading Signal Monitor with Email Notifications
Continuously monitors trading signals and sends email alerts
"""

import asyncio
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Thread
from pathlib import Path

from ..core.ml.enhanced_pipeline import EnhancedMLPipeline
from ..core.analysis.pattern_ai import AIPatternDetector
from ..core.trading.alpaca_integration import AlpacaMLTrader
from ..core.data.collectors.market_data import ASXDataFeed
from ..services.email_notifier import EmailNotificationService, TradingAlert, create_alert_from_pattern_detection
from ..config.settings import Settings

logger = logging.getLogger(__name__)

class RealTimeSignalMonitor:
    """
    Real-time monitoring service that watches for trading signals and sends email notifications
    """
    
    def __init__(self):
        self.settings = Settings()
        self.email_service = EmailNotificationService()
        self.pattern_detector = AIPatternDetector()
        self.ml_pipeline = EnhancedMLPipeline()
        self.alpaca_trader = AlpacaMLTrader()
        self.market_data = ASXDataFeed()
        
        # ASX Bank stocks to monitor
        self.symbols = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX']
        
        # Monitoring configuration
        self.monitoring_interval = 300  # 5 minutes in seconds
        self.market_hours_start = "09:30"  # AEST
        self.market_hours_end = "16:00"    # AEST
        
        # Alert throttling - avoid spam emails
        self.alert_cooldown = {}  # symbol -> last_alert_time
        self.cooldown_period = 1800  # 30 minutes between alerts for same symbol
        
        # Monitoring state
        self.is_monitoring = False
        self.last_prices = {}
        self.monitoring_thread = None
        
    def start_monitoring(self):
        """Start real-time monitoring in background thread"""
        if self.is_monitoring:
            logger.warning("Monitoring is already running")
            return
            
        logger.info("Starting real-time trading signal monitoring...")
        
        # Test email configuration first
        if not self.email_service.test_email_connection():
            logger.error("Email configuration test failed. Please check your .env file settings.")
            return False
            
        self.is_monitoring = True
        self.monitoring_thread = Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Real-time monitoring started successfully")
        return True
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        logger.info("Stopping real-time monitoring...")
        self.is_monitoring = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)
            
        logger.info("Real-time monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Real-time monitoring loop started")
        
        while self.is_monitoring:
            try:
                # Check if market is open
                if not self._is_market_open():
                    logger.debug("Market is closed, monitoring paused")
                    time.sleep(60)  # Check every minute when market is closed
                    continue
                
                # Monitor each symbol
                for symbol in self.symbols:
                    try:
                        self._check_symbol_for_signals(symbol)
                    except Exception as e:
                        logger.error(f"Error monitoring {symbol}: {e}")
                
                # Wait for next monitoring cycle
                logger.debug(f"Monitoring cycle complete, sleeping for {self.monitoring_interval} seconds")
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _is_market_open(self) -> bool:
        """Check if ASX market is currently open"""
        now = datetime.now()
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Check if it's within market hours
        current_time = now.strftime("%H:%M")
        return self.market_hours_start <= current_time <= self.market_hours_end
    
    def _check_symbol_for_signals(self, symbol: str):
        """Check a specific symbol for trading signals"""
        try:
            # Get latest price data
            current_data = self._get_current_market_data(symbol)
            if not current_data:
                logger.warning(f"No data available for {symbol}")
                return
            
            current_price = current_data['price']
            
            # Check for significant price changes
            price_change_pct = self._calculate_price_change(symbol, current_price)
            
            # Run AI pattern detection
            pattern_results = self._analyze_patterns(symbol, current_data)
            
            # Run ML predictions
            ml_predictions = self._get_ml_predictions(symbol, current_data)
            
            # Check sentiment analysis
            sentiment_results = self._analyze_sentiment(symbol)
            
            # Generate comprehensive alert if conditions are met
            alert = self._generate_comprehensive_alert(
                symbol, current_price, pattern_results, ml_predictions, 
                sentiment_results, price_change_pct
            )
            
            # Send email if alert is significant enough
            if alert and self._should_send_alert(symbol, alert):
                success = self.email_service.send_trading_alert(alert)
                if success:
                    self.alert_cooldown[symbol] = datetime.now()
                    logger.info(f"Email alert sent for {symbol}")
                    
                    # Also log to dashboard
                    self._log_alert_to_dashboard(alert)
            
        except Exception as e:
            logger.error(f"Error checking signals for {symbol}: {e}")
    
    def _get_current_market_data(self, symbol: str) -> Optional[Dict]:
        """Get current market data for a symbol"""
        try:
            # Get latest data using AlpacaMLTrader
            data = self.alpaca_trader.get_latest_quote(symbol)
            
            if data and 'price' in data:
                return {
                    'price': float(data['price']),
                    'volume': data.get('volume', 0),
                    'change': data.get('change', 0),
                    'change_percent': data.get('change_percent', 0),
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def _calculate_price_change(self, symbol: str, current_price: float) -> float:
        """Calculate price change percentage since last check"""
        if symbol in self.last_prices:
            last_price = self.last_prices[symbol]
            change_pct = ((current_price - last_price) / last_price) * 100
        else:
            change_pct = 0
        
        self.last_prices[symbol] = current_price
        return change_pct
    
    def _analyze_patterns(self, symbol: str, market_data: Dict) -> Dict:
        """Run AI pattern analysis"""
        try:
            # Get historical data for pattern analysis using market data feed
            historical_data = self.market_data.get_historical_data(symbol, days=30)
            
            if not historical_data or len(historical_data) == 0:
                return {}
            
            # Run pattern detection
            patterns = self.pattern_detector.detect_patterns(historical_data)
            
            return {
                'pattern_detected': patterns.get('pattern_type', 'None'),
                'confidence': patterns.get('confidence', 0),
                'signal': patterns.get('signal', 'HOLD'),
                'breakout_probability': patterns.get('breakout_probability', 0),
                'support_level': patterns.get('support', market_data['price'] * 0.95),
                'resistance_level': patterns.get('resistance', market_data['price'] * 1.05),
                'target_price': patterns.get('target_price', market_data['price'])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing patterns for {symbol}: {e}")
            return {}
    
    def _get_ml_predictions(self, symbol: str, market_data: Dict) -> Dict:
        """Get ML model predictions"""
        try:
            # Use ML pipeline to get predictions
            prediction = self.ml_pipeline.predict_next_day_movement(symbol)
            
            return {
                'ml_signal': prediction.get('signal', 'HOLD'),
                'ml_confidence': prediction.get('confidence', 0),
                'predicted_return': prediction.get('predicted_return', 0),
                'risk_score': prediction.get('risk_score', 0.5)
            }
            
        except Exception as e:
            logger.error(f"Error getting ML predictions for {symbol}: {e}")
            return {}
    
    def _analyze_sentiment(self, symbol: str) -> Dict:
        """Analyze news sentiment"""
        try:
            # Get sentiment from market data feed
            sentiment_data = self.market_data.get_sentiment_analysis(symbol)
            
            return {
                'sentiment_score': sentiment_data.get('sentiment_score', 0),
                'news_count': sentiment_data.get('news_count', 0),
                'sentiment_trend': sentiment_data.get('trend', 'neutral')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {symbol}: {e}")
            return {}
    
    def _generate_comprehensive_alert(self, symbol: str, current_price: float, 
                                    pattern_results: Dict, ml_predictions: Dict, 
                                    sentiment_results: Dict, price_change_pct: float) -> Optional[TradingAlert]:
        """Generate comprehensive trading alert from all analysis components"""
        
        # Combine signals from different sources
        signals = []
        confidences = []
        reasoning_parts = []
        
        # Pattern analysis signal
        if pattern_results.get('signal') and pattern_results.get('confidence', 0) > 0.6:
            signals.append(pattern_results['signal'])
            confidences.append(pattern_results['confidence'])
            reasoning_parts.append(f"Pattern Analysis detected {pattern_results.get('pattern_detected', 'pattern')} "
                                 f"with {pattern_results.get('confidence', 0):.1%} confidence")
        
        # ML prediction signal
        if ml_predictions.get('ml_signal') and ml_predictions.get('ml_confidence', 0) > 0.6:
            signals.append(ml_predictions['ml_signal'])
            confidences.append(ml_predictions['ml_confidence'])
            reasoning_parts.append(f"ML Model predicts {ml_predictions.get('ml_signal')} "
                                 f"with {ml_predictions.get('ml_confidence', 0):.1%} confidence")
        
        # Sentiment analysis
        sentiment_score = sentiment_results.get('sentiment_score', 0)
        if abs(sentiment_score) > 0.5:
            sentiment_signal = 'BUY' if sentiment_score > 0.5 else 'SELL'
            signals.append(sentiment_signal)
            confidences.append(min(abs(sentiment_score), 1.0))
            reasoning_parts.append(f"News sentiment is {'positive' if sentiment_score > 0 else 'negative'} "
                                 f"(score: {sentiment_score:+.3f})")
        
        # Price movement trigger
        if abs(price_change_pct) > 2.0:  # 2% price movement
            movement_signal = 'BUY' if price_change_pct > 0 else 'SELL'
            reasoning_parts.append(f"Significant price movement: {price_change_pct:+.1f}%")
        
        # Determine overall signal
        if not signals:
            return None
        
        # Count signal types
        buy_signals = signals.count('BUY') + signals.count('STRONG_BUY')
        sell_signals = signals.count('SELL') + signals.count('STRONG_SELL')
        
        # Determine final signal
        if buy_signals > sell_signals:
            final_signal = 'STRONG_BUY' if buy_signals >= 2 else 'BUY'
        elif sell_signals > buy_signals:
            final_signal = 'STRONG_SELL' if sell_signals >= 2 else 'SELL'
        else:
            final_signal = 'HOLD'
        
        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Only create alert for strong signals
        if final_signal == 'HOLD' or avg_confidence < 0.6:
            return None
        
        # Company name mapping
        company_names = {
            'CBA.AX': 'Commonwealth Bank',
            'ANZ.AX': 'Australia & New Zealand Banking',
            'WBC.AX': 'Westpac Banking Corporation',
            'NAB.AX': 'National Australia Bank',
            'MQG.AX': 'Macquarie Group'
        }
        
        # Create comprehensive alert
        alert = TradingAlert(
            symbol=symbol,
            company_name=company_names.get(symbol, symbol),
            signal=final_signal,
            price=current_price,
            confidence=avg_confidence,
            pattern_detected=pattern_results.get('pattern_detected', 'Multiple Indicators'),
            target_price=pattern_results.get('target_price', current_price * (1.02 if 'BUY' in final_signal else 0.98)),
            support_level=pattern_results.get('support_level', current_price * 0.97),
            resistance_level=pattern_results.get('resistance_level', current_price * 1.03),
            sentiment_score=sentiment_results.get('sentiment_score', 0),
            timestamp=datetime.now(),
            alert_type='critical' if avg_confidence > 0.8 else 'warning',
            reasoning='. '.join(reasoning_parts) if reasoning_parts else f"Multiple indicators suggest {final_signal} signal."
        )
        
        return alert
    
    def _should_send_alert(self, symbol: str, alert: TradingAlert) -> bool:
        """Check if we should send an alert (avoiding spam)"""
        
        # Check cooldown period
        if symbol in self.alert_cooldown:
            last_alert_time = self.alert_cooldown[symbol]
            time_since_last = (datetime.now() - last_alert_time).total_seconds()
            
            if time_since_last < self.cooldown_period:
                logger.debug(f"Alert for {symbol} still in cooldown period")
                return False
        
        # Always send critical alerts
        if alert.alert_type == 'critical':
            return True
        
        # Send warning alerts with high confidence
        if alert.alert_type == 'warning' and alert.confidence > 0.75:
            return True
        
        return False
    
    def _log_alert_to_dashboard(self, alert: TradingAlert):
        """Log alert to file for record keeping"""
        try:
            alert_data = {
                'timestamp': alert.timestamp.isoformat(),
                'symbol': alert.symbol,
                'signal': alert.signal,
                'price': alert.price,
                'confidence': alert.confidence,
                'alert_type': alert.alert_type,
                'reasoning': alert.reasoning
            }
            
            # Log to file in logs directory
            log_file = Path("logs/trading_alerts.json")
            log_file.parent.mkdir(exist_ok=True)
            
            # Append to log file
            if log_file.exists():
                with open(log_file, 'r') as f:
                    alerts = json.load(f)
            else:
                alerts = []
            
            alerts.append(alert_data)
            
            # Keep only last 1000 alerts
            if len(alerts) > 1000:
                alerts = alerts[-1000:]
            
            with open(log_file, 'w') as f:
                json.dump(alerts, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error logging alert to file: {e}")
    
    def send_test_alert(self, symbol: str = 'CBA.AX') -> bool:
        """Send a test alert to verify email functionality"""
        try:
            test_alert = TradingAlert(
                symbol=symbol,
                company_name='Commonwealth Bank (TEST)',
                signal='BUY',
                price=105.50,
                confidence=0.85,
                pattern_detected='Test Pattern',
                target_price=108.00,
                support_level=103.00,
                resistance_level=110.00,
                sentiment_score=0.65,
                timestamp=datetime.now(),
                alert_type='info',
                reasoning='This is a test alert to verify the email notification system is working correctly.'
            )
            
            return self.email_service.send_trading_alert(test_alert)
            
        except Exception as e:
            logger.error(f"Error sending test alert: {e}")
            return False
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            'is_monitoring': self.is_monitoring,
            'symbols_monitored': self.symbols,
            'monitoring_interval': self.monitoring_interval,
            'last_prices': self.last_prices,
            'alert_cooldowns': {
                symbol: (datetime.now() - last_alert).total_seconds() 
                for symbol, last_alert in self.alert_cooldown.items()
            },
            'market_open': self._is_market_open()
        }

# Singleton instance for easy access
_monitor_instance = None

def get_signal_monitor() -> RealTimeSignalMonitor:
    """Get singleton instance of the signal monitor"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = RealTimeSignalMonitor()
    return _monitor_instance

# Convenience functions for command-line usage
def start_monitoring():
    """Start real-time monitoring"""
    monitor = get_signal_monitor()
    return monitor.start_monitoring()

def stop_monitoring():
    """Stop real-time monitoring"""
    monitor = get_signal_monitor()
    monitor.stop_monitoring()

def send_test_email():
    """Send test email"""
    monitor = get_signal_monitor()
    return monitor.send_test_alert()

def get_status():
    """Get monitoring status"""
    monitor = get_signal_monitor()
    return monitor.get_monitoring_status()

"""
Email Alert Integration for Trading Dashboard
Connects existing trading signals with email notification system
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import asyncio

from app.services.email_notifier import EmailNotificationService, TradingAlert, create_alert_from_pattern_detection
from app.services.real_time_monitor import get_signal_monitor

logger = logging.getLogger(__name__)

class DashboardEmailIntegration:
    """
    Integration layer between dashboard alerts and email notifications
    """
    
    def __init__(self):
        self.email_service = EmailNotificationService()
        self.signal_monitor = get_signal_monitor()
        
        # Company name mapping
        self.company_names = {
            'CBA': 'Commonwealth Bank',
            'CBA.AX': 'Commonwealth Bank',
            'ANZ': 'Australia & New Zealand Banking',
            'ANZ.AX': 'Australia & New Zealand Banking',
            'WBC': 'Westpac Banking Corporation',
            'WBC.AX': 'Westpac Banking Corporation',
            'NAB': 'National Australia Bank',
            'NAB.AX': 'National Australia Bank',
            'MQG': 'Macquarie Group',
            'MQG.AX': 'Macquarie Group'
        }
    
    def process_dashboard_alerts(self, ml_scores: Dict, current_prices: Dict = None) -> bool:
        """
        Process alerts from dashboard and send emails for significant signals
        
        Args:
            ml_scores: ML scores from dashboard analysis
            current_prices: Current stock prices (optional)
            
        Returns:
            bool: True if any emails were sent
        """
        try:
            emails_sent = 0
            
            for bank, scores in ml_scores.items():
                # Create trading alert from ML scores
                alert = self._create_alert_from_ml_scores(bank, scores, current_prices)
                
                if alert and self._should_send_email_alert(alert):
                    success = self.email_service.send_trading_alert(alert)
                    if success:
                        emails_sent += 1
                        logger.info(f"Email alert sent for {bank}")
                    else:
                        logger.error(f"Failed to send email alert for {bank}")
            
            return emails_sent > 0
            
        except Exception as e:
            logger.error(f"Error processing dashboard alerts: {e}")
            return False
    
    def _create_alert_from_ml_scores(self, bank: str, scores: Dict, current_prices: Dict = None) -> Optional[TradingAlert]:
        """Create TradingAlert from ML scores"""
        try:
            confidence = scores.get('confidence', 0)
            signal = scores.get('trading_signal', 'HOLD')
            overall_score = scores.get('overall_score', 0)
            pattern_score = scores.get('pattern_score', 0)
            sentiment_score = scores.get('sentiment_score', 0)
            
            # Only create alerts for strong signals
            if signal == 'HOLD' or confidence < 0.7:
                return None
            
            # Get symbol format
            symbol = bank if '.AX' in bank else f"{bank}.AX"
            
            # Get current price (mock if not available)
            current_price = 100.0  # Default price
            if current_prices and symbol in current_prices:
                current_price = current_prices[symbol]
            elif current_prices and bank in current_prices:
                current_price = current_prices[bank]
            
            # Calculate target price based on signal
            price_multiplier = 1.03 if signal in ['BUY', 'STRONG_BUY'] else 0.97
            target_price = current_price * price_multiplier
            
            # Determine alert type
            alert_type = 'critical' if confidence > 0.85 else 'warning' if confidence > 0.75 else 'info'
            
            # Create reasoning
            reasoning_parts = [
                f"ML Trading Score: {overall_score:.2f}",
                f"Pattern Analysis: {pattern_score:.2f}",
                f"Sentiment Score: {sentiment_score:+.3f}",
                f"Signal Confidence: {confidence:.1%}"
            ]
            
            if confidence > 0.9:
                reasoning_parts.append("Extremely high confidence signal detected")
            elif confidence > 0.8:
                reasoning_parts.append("High confidence signal with strong indicators")
            
            return TradingAlert(
                symbol=symbol,
                company_name=self.company_names.get(bank, bank),
                signal=signal,
                price=current_price,
                confidence=confidence,
                pattern_detected="ML Trading Analysis",
                target_price=target_price,
                support_level=current_price * 0.97,
                resistance_level=current_price * 1.03,
                sentiment_score=sentiment_score,
                timestamp=datetime.now(),
                alert_type=alert_type,
                reasoning='. '.join(reasoning_parts)
            )
            
        except Exception as e:
            logger.error(f"Error creating alert from ML scores for {bank}: {e}")
            return None
    
    def _should_send_email_alert(self, alert: TradingAlert) -> bool:
        """Check if we should send an email alert"""
        # Use the same logic as the real-time monitor
        return self.signal_monitor._should_send_alert(alert.symbol, alert)
    
    def send_daily_summary_email(self, summary_data: Dict) -> bool:
        """Send daily trading summary email"""
        try:
            return self.email_service.send_daily_summary(summary_data)
        except Exception as e:
            logger.error(f"Error sending daily summary email: {e}")
            return False
    
    def test_integration(self) -> bool:
        """Test the email integration"""
        try:
            # Create test ML scores
            test_ml_scores = {
                'CBA': {
                    'confidence': 0.85,
                    'trading_signal': 'BUY',
                    'overall_score': 0.78,
                    'pattern_score': 0.72,
                    'sentiment_score': 0.65
                }
            }
            
            test_prices = {'CBA.AX': 105.50}
            
            return self.process_dashboard_alerts(test_ml_scores, test_prices)
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            return False

# Global instance for easy access
_integration_instance = None

def get_email_integration() -> DashboardEmailIntegration:
    """Get singleton instance of email integration"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = DashboardEmailIntegration()
    return _integration_instance

def send_dashboard_alerts(ml_scores: Dict, current_prices: Dict = None) -> bool:
    """
    Send email alerts for dashboard trading signals
    
    Args:
        ml_scores: ML scores from dashboard
        current_prices: Current stock prices
        
    Returns:
        bool: True if any emails were sent
    """
    integration = get_email_integration()
    return integration.process_dashboard_alerts(ml_scores, current_prices)

def send_daily_summary(summary_data: Dict) -> bool:
    """Send daily summary email"""
    integration = get_email_integration()
    return integration.send_daily_summary_email(summary_data)

# Add this function to the enhanced_main.py dashboard to integrate email alerts
def add_email_alerts_to_dashboard():
    """
    Add email alert functionality to the existing dashboard
    Call this function after generating ML scores in the dashboard
    """
    try:
        # This would be called from enhanced_main.py after ml_scores are calculated
        # Example integration point:
        
        # In enhanced_main.py, after line with ml_scores calculation, add:
        # from app.services.dashboard_integration import send_dashboard_alerts
        # send_dashboard_alerts(ml_scores, current_prices)
        
        pass
    except Exception as e:
        logger.error(f"Error adding email alerts to dashboard: {e}")

# Function to integrate with the existing generate_trading_alerts function
def enhanced_generate_trading_alerts(ml_scores: Dict, current_prices: Dict = None) -> List[Dict]:
    """
    Enhanced version of generate_trading_alerts that also sends emails
    
    Args:
        ml_scores: ML scores from analysis
        current_prices: Current stock prices
        
    Returns:
        List of alerts for dashboard display
    """
    # Generate original alerts for dashboard
    alerts = []
    
    for bank, scores in ml_scores.items():
        confidence = scores.get('confidence', 0)
        signal = scores.get('trading_signal', 'HOLD')
        overall_score = scores.get('overall_score', 0)
        
        # High confidence buy/sell signals
        if confidence > 0.8 and signal in ['BUY', 'SELL']:
            alerts.append({
                'type': 'critical',
                'message': f'High confidence {signal} signal detected',
                'bank': bank,
                'confidence': confidence
            })
        
        # Low confidence warnings
        elif confidence < 0.3 and signal != 'HOLD':
            alerts.append({
                'type': 'warning',
                'message': f'Low confidence {signal} signal - proceed with caution',
                'bank': bank,
                'confidence': confidence
            })
        
        # Extreme scores
        elif overall_score > 0.8 or overall_score < 0.2:
            alerts.append({
                'type': 'info',
                'message': f'Extreme score detected: {overall_score:.2f}',
                'bank': bank,
                'score': overall_score
            })
    
    # Sort by priority
    priority_order = {'critical': 0, 'warning': 1, 'info': 2}
    alerts.sort(key=lambda x: priority_order.get(x['type'], 3))
    
    # Send email alerts in background
    try:
        send_dashboard_alerts(ml_scores, current_prices)
    except Exception as e:
        logger.error(f"Error sending email alerts: {e}")
    
    return alerts

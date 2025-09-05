"""
Real-Time Email Notification System for Trading Signals
Sends instant email alerts when ML indicators detect trading opportunities
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass

from ..config.settings import Settings

logger = logging.getLogger(__name__)

@dataclass
class TradingAlert:
    """Trading alert data structure"""
    symbol: str
    company_name: str
    signal: str  # BUY, SELL, STRONG_BUY, STRONG_SELL, HOLD
    price: float
    confidence: float
    pattern_detected: str
    target_price: float
    support_level: float
    resistance_level: float
    sentiment_score: float
    timestamp: datetime
    alert_type: str  # critical, warning, info
    reasoning: str

class EmailNotificationService:
    """
    Professional email notification service for trading signals
    Sends real-time alerts to sutho100@gmail.com when ML indicators detect opportunities
    """
    
    def __init__(self):
        self.settings = Settings()
        self.recipient_email = "sutho100@gmail.com"
        
        # Email configuration - uses Gmail SMTP
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
        # You'll need to set these in your .env file
        self.sender_email = self.settings.get('EMAIL_ADDRESS', 'your_email@gmail.com')
        self.sender_password = self.settings.get('EMAIL_PASSWORD', 'your_app_password')
        
        # Alert thresholds for sending emails
        self.confidence_threshold = 0.7  # Only send emails for high confidence signals
        self.critical_signals = ['STRONG_BUY', 'STRONG_SELL']
        self.important_signals = ['BUY', 'SELL']
        
    def send_trading_alert(self, alert: TradingAlert) -> bool:
        """
        Send a trading alert email
        
        Args:
            alert: TradingAlert object with signal details
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Check if alert meets criteria for email notification
            if not self._should_send_alert(alert):
                logger.info(f"Alert for {alert.symbol} doesn't meet criteria for email notification")
                return False
            
            # Create email content
            subject = self._create_subject(alert)
            html_body = self._create_html_body(alert)
            text_body = self._create_text_body(alert)
            
            # Send email
            success = self._send_email(subject, html_body, text_body)
            
            if success:
                logger.info(f"Trading alert email sent successfully for {alert.symbol}")
            else:
                logger.error(f"Failed to send trading alert email for {alert.symbol}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending trading alert email: {e}")
            return False
    
    def send_daily_summary(self, summary_data: Dict) -> bool:
        """
        Send daily trading summary email
        
        Args:
            summary_data: Dictionary containing daily summary information
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = f"📊 Daily Trading Summary - {datetime.now().strftime('%Y-%m-%d')}"
            html_body = self._create_daily_summary_html(summary_data)
            text_body = self._create_daily_summary_text(summary_data)
            
            return self._send_email(subject, html_body, text_body)
            
        except Exception as e:
            logger.error(f"Error sending daily summary email: {e}")
            return False
    
    def send_portfolio_alert(self, portfolio_data: Dict) -> bool:
        """
        Send portfolio performance alert
        
        Args:
            portfolio_data: Portfolio performance data
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = f"💼 Portfolio Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            html_body = self._create_portfolio_alert_html(portfolio_data)
            text_body = self._create_portfolio_alert_text(portfolio_data)
            
            return self._send_email(subject, html_body, text_body)
            
        except Exception as e:
            logger.error(f"Error sending portfolio alert email: {e}")
            return False
    
    def _should_send_alert(self, alert: TradingAlert) -> bool:
        """Check if alert meets criteria for email notification"""
        # Send for critical signals regardless of confidence
        if alert.signal in self.critical_signals:
            return True
            
        # Send for important signals with high confidence
        if alert.signal in self.important_signals and alert.confidence >= self.confidence_threshold:
            return True
            
        # Send for critical alert types
        if alert.alert_type == 'critical':
            return True
            
        return False
    
    def _create_subject(self, alert: TradingAlert) -> str:
        """Create email subject line"""
        urgency_emoji = "🚨" if alert.signal in self.critical_signals else "📊"
        signal_emoji = {
            'STRONG_BUY': '🚀',
            'BUY': '📈',
            'STRONG_SELL': '⚠️',
            'SELL': '📉',
            'HOLD': '➡️'
        }.get(alert.signal, '📊')
        
        return f"{urgency_emoji} Trading Alert: {alert.symbol} {signal_emoji} {alert.signal} at ${alert.price:.2f}"
    
    def _create_html_body(self, alert: TradingAlert) -> str:
        """Create HTML email body"""
        signal_color = {
            'STRONG_BUY': '#00C851',
            'BUY': '#4CAF50',
            'STRONG_SELL': '#FF4444',
            'SELL': '#FF6B6B',
            'HOLD': '#FFA726'
        }.get(alert.signal, '#757575')
        
        confidence_color = '#00C851' if alert.confidence > 0.8 else '#FFA726' if alert.confidence > 0.6 else '#FF4444'
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ padding: 20px; }}
                .signal-badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; color: white; font-weight: bold; background-color: {signal_color}; }}
                .metric {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
                .metric:last-child {{ border-bottom: none; }}
                .metric-label {{ font-weight: bold; color: #333; }}
                .metric-value {{ color: #666; }}
                .confidence {{ color: {confidence_color}; font-weight: bold; }}
                .reasoning {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid {signal_color}; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; color: #666; font-size: 12px; border-radius: 0 0 10px 10px; }}
                .timestamp {{ color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 AI Trading Alert</h1>
                    <div class="timestamp">{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S AEST')}</div>
                </div>
                
                <div class="content">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <h2>{alert.company_name} ({alert.symbol})</h2>
                        <div class="signal-badge">{alert.signal}</div>
                    </div>
                    
                    <div class="metric">
                        <span class="metric-label">Current Price:</span>
                        <span class="metric-value">${alert.price:.2f}</span>
                    </div>
                    
                    <div class="metric">
                        <span class="metric-label">Confidence:</span>
                        <span class="confidence">{alert.confidence:.1%}</span>
                    </div>
                    
                    <div class="metric">
                        <span class="metric-label">Pattern Detected:</span>
                        <span class="metric-value">{alert.pattern_detected}</span>
                    </div>
                    
                    <div class="metric">
                        <span class="metric-label">Target Price:</span>
                        <span class="metric-value">${alert.target_price:.2f} ({((alert.target_price / alert.price - 1) * 100):+.1f}%)</span>
                    </div>
                    
                    <div class="metric">
                        <span class="metric-label">Support Level:</span>
                        <span class="metric-value">${alert.support_level:.2f}</span>
                    </div>
                    
                    <div class="metric">
                        <span class="metric-label">Resistance Level:</span>
                        <span class="metric-value">${alert.resistance_level:.2f}</span>
                    </div>
                    
                    <div class="metric">
                        <span class="metric-label">Sentiment Score:</span>
                        <span class="metric-value">{alert.sentiment_score:+.3f}</span>
                    </div>
                    
                    <div class="reasoning">
                        <h4>🧠 AI Analysis:</h4>
                        <p>{alert.reasoning}</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This alert was generated by your AI Trading Analysis System</p>
                    <p>⚠️ This is not financial advice. Always do your own research before making investment decisions.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def _create_text_body(self, alert: TradingAlert) -> str:
        """Create plain text email body"""
        text_body = f"""
AI TRADING ALERT
{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S AEST')}

STOCK: {alert.company_name} ({alert.symbol})
SIGNAL: {alert.signal}
CURRENT PRICE: ${alert.price:.2f}
CONFIDENCE: {alert.confidence:.1%}

PATTERN DETECTED: {alert.pattern_detected}
TARGET PRICE: ${alert.target_price:.2f} ({((alert.target_price / alert.price - 1) * 100):+.1f}%)
SUPPORT LEVEL: ${alert.support_level:.2f}
RESISTANCE LEVEL: ${alert.resistance_level:.2f}
SENTIMENT SCORE: {alert.sentiment_score:+.3f}

AI ANALYSIS:
{alert.reasoning}

---
This alert was generated by your AI Trading Analysis System.
This is not financial advice. Always do your own research before making investment decisions.
        """
        
        return text_body.strip()
    
    def _create_daily_summary_html(self, summary_data: Dict) -> str:
        """Create daily summary email HTML"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary-card {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; color: #666; font-size: 12px; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Trading Summary</h1>
                    <div>{date_str}</div>
                </div>
                
                <div class="content">
                    <div class="summary-card">
                        <h3>🎯 Today's Signals</h3>
                        <p>Total Signals: {summary_data.get('total_signals', 0)}</p>
                        <p>Buy Signals: {summary_data.get('buy_signals', 0)}</p>
                        <p>Sell Signals: {summary_data.get('sell_signals', 0)}</p>
                    </div>
                    
                    <div class="summary-card">
                        <h3>📈 Market Overview</h3>
                        <p>Average Sentiment: {summary_data.get('avg_sentiment', 0):+.3f}</p>
                        <p>Market Volatility: {summary_data.get('volatility', 0):.2%}</p>
                        <p>Patterns Detected: {summary_data.get('patterns_detected', 0)}</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Generated by your AI Trading Analysis System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def _create_daily_summary_text(self, summary_data: Dict) -> str:
        """Create daily summary plain text"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        text_body = f"""
DAILY TRADING SUMMARY - {date_str}

TODAY'S SIGNALS:
Total Signals: {summary_data.get('total_signals', 0)}
Buy Signals: {summary_data.get('buy_signals', 0)}
Sell Signals: {summary_data.get('sell_signals', 0)}

MARKET OVERVIEW:
Average Sentiment: {summary_data.get('avg_sentiment', 0):+.3f}
Market Volatility: {summary_data.get('volatility', 0):.2%}
Patterns Detected: {summary_data.get('patterns_detected', 0)}

---
Generated by your AI Trading Analysis System
        """
        
        return text_body.strip()
    
    def _create_portfolio_alert_html(self, portfolio_data: Dict) -> str:
        """Create portfolio alert HTML"""
        # Implementation for portfolio alerts
        return "<html><body><h1>Portfolio Alert</h1></body></html>"
    
    def _create_portfolio_alert_text(self, portfolio_data: Dict) -> str:
        """Create portfolio alert text"""
        return "Portfolio Alert"
    
    def _send_email(self, subject: str, html_body: str, text_body: str) -> bool:
        """
        Send email using Gmail SMTP
        
        Args:
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
            
        Returns:
            bool: True if successful
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = self.recipient_email
            
            # Create text and HTML parts
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")
            
            # Add parts to message
            message.attach(text_part)
            message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, message.as_string())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def test_email_connection(self) -> bool:
        """
        Test email connection and configuration
        
        Returns:
            bool: True if connection successful
        """
        try:
            test_alert = TradingAlert(
                symbol="TEST",
                company_name="Test Company",
                signal="BUY",
                price=100.00,
                confidence=0.85,
                pattern_detected="Test Pattern",
                target_price=105.00,
                support_level=95.00,
                resistance_level=110.00,
                sentiment_score=0.5,
                timestamp=datetime.now(),
                alert_type="info",
                reasoning="This is a test email to verify the notification system is working correctly."
            )
            
            subject = "🧪 Test Email - Trading Alert System"
            html_body = self._create_html_body(test_alert)
            text_body = self._create_text_body(test_alert)
            
            return self._send_email(subject, html_body, text_body)
            
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False

# Convenience functions for integration
def create_alert_from_pattern_detection(pattern_result: Dict, symbol: str, current_price: float) -> TradingAlert:
    """
    Create TradingAlert from AI pattern detection result
    
    Args:
        pattern_result: Result from AIPatternDetector.detect_patterns()
        symbol: Stock symbol
        current_price: Current stock price
        
    Returns:
        TradingAlert: Alert object ready for email notification
    """
    # Map company names
    company_names = {
        'CBA.AX': 'Commonwealth Bank',
        'ANZ.AX': 'Australia & New Zealand Banking',
        'WBC.AX': 'Westpac Banking Corporation',
        'NAB.AX': 'National Australia Bank',
        'MQG.AX': 'Macquarie Group'
    }
    
    alert_type = 'critical' if pattern_result.get('confidence', 0) > 0.8 else 'warning' if pattern_result.get('confidence', 0) > 0.6 else 'info'
    
    return TradingAlert(
        symbol=symbol,
        company_name=company_names.get(symbol, symbol),
        signal=pattern_result.get('signal', 'HOLD'),
        price=current_price,
        confidence=pattern_result.get('confidence', 0),
        pattern_detected=pattern_result.get('pattern_detected', 'Unknown'),
        target_price=pattern_result.get('target_price', current_price),
        support_level=pattern_result.get('support_level', current_price * 0.95),
        resistance_level=pattern_result.get('resistance_level', current_price * 1.05),
        sentiment_score=pattern_result.get('sentiment_score', 0),
        timestamp=datetime.now(),
        alert_type=alert_type,
        reasoning=f"AI detected {pattern_result.get('pattern_detected', 'pattern')} with {pattern_result.get('confidence', 0):.1%} confidence. "
                 f"Breakout probability: {pattern_result.get('breakout_probability', 0):.1%}. "
                 f"Estimated time horizon: {pattern_result.get('time_horizon_days', 'unknown')} days."
    )

def create_alert_from_sentiment_analysis(sentiment_result: Dict, symbol: str, current_price: float) -> TradingAlert:
    """
    Create TradingAlert from sentiment analysis result
    
    Args:
        sentiment_result: Result from sentiment analysis
        symbol: Stock symbol
        current_price: Current stock price
        
    Returns:
        TradingAlert: Alert object ready for email notification
    """
    company_names = {
        'CBA.AX': 'Commonwealth Bank',
        'ANZ.AX': 'Australia & New Zealand Banking',
        'WBC.AX': 'Westpac Banking Corporation',
        'NAB.AX': 'National Australia Bank',
        'MQG.AX': 'Macquarie Group'
    }
    
    signal = sentiment_result.get('signal', 'HOLD')
    confidence = sentiment_result.get('confidence', 0)
    sentiment_score = sentiment_result.get('sentiment_score', 0)
    
    alert_type = 'critical' if confidence > 0.8 else 'warning' if confidence > 0.6 else 'info'
    
    return TradingAlert(
        symbol=symbol,
        company_name=company_names.get(symbol, symbol),
        signal=signal,
        price=current_price,
        confidence=confidence,
        pattern_detected="News Sentiment Analysis",
        target_price=current_price * (1.02 if signal in ['BUY', 'STRONG_BUY'] else 0.98),
        support_level=current_price * 0.97,
        resistance_level=current_price * 1.03,
        sentiment_score=sentiment_score,
        timestamp=datetime.now(),
        alert_type=alert_type,
        reasoning=f"News sentiment analysis indicates {signal} signal with {confidence:.1%} confidence. "
                 f"Sentiment score: {sentiment_score:+.3f}. "
                 f"Based on recent news articles and market sentiment analysis."
    )

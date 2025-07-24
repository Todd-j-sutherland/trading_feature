#!/usr/bin/env python3
"""
No-Auth Email Integration for Trading Alerts
Uses system sendmail - no authentication required
"""

import subprocess
from datetime import datetime
from typing import Optional

class NoAuthEmailService:
    """Send emails using system sendmail - no authentication required"""
    
    def __init__(self, recipient: str = "sutho100@gmail.com"):
        self.recipient = recipient
    
    def send_trading_alert(self, symbol: str, signal: str, price: float, 
                          confidence: float, details: str = "") -> bool:
        """Send a trading alert email"""
        
        subject = f"🚨 Trading Alert: {symbol} - {signal} Signal"
        
        message = f"""To: {self.recipient}
Subject: {subject}

🤖 AI Trading Alert System
═══════════════════════════

📈 TRADING SIGNAL DETECTED
═══════════════════════════

Stock: {symbol}
Signal: {signal}
Current Price: ${price:.2f}
Confidence: {confidence:.1%}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S AEST')}

{details}

═══════════════════════════
⚠️  TRADING INSTRUCTIONS
═══════════════════════════

{'📈 BUY SIGNAL - Consider entering a long position' if signal == 'BUY' else '📉 SELL SIGNAL - Consider entering a short position or closing longs' if signal == 'SELL' else '🔄 HOLD - No action required'}

Risk Management:
• Use appropriate position sizing
• Set stop-loss orders
• Monitor for exit signals

Happy Trading! 🚀

---
This alert was generated automatically by your ML trading system.
"""
        
        return self._send_email(message)
    
    def send_simple_alert(self, subject: str, message: str) -> bool:
        """Send a simple alert email"""
        
        email_content = f"""To: {self.recipient}
Subject: {subject}

{message}

---
Sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self._send_email(email_content)
    
    def _send_email(self, message: str) -> bool:
        """Send email using system sendmail"""
        try:
            process = subprocess.Popen(['sendmail', self.recipient], 
                                     stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            stdout, stderr = process.communicate(message)
            
            if process.returncode == 0:
                print(f"✅ Email sent to {self.recipient}")
                return True
            else:
                print(f"❌ Email failed: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
    
    def test_email(self) -> bool:
        """Send a test email"""
        return self.send_simple_alert(
            subject=f"🧪 Trading System Test - {datetime.now().strftime('%H:%M')}",
            message="""🤖 Trading System Test Email

This is a test email from your trading alert system.

If you receive this, the no-authentication email system is working perfectly!

The system is ready to send you trading alerts.

Best regards,
Your AI Trading Assistant 🚀"""
        )

# Quick test function
def send_quick_test():
    """Send a quick test email"""
    print("📧 No-Auth Email Test")
    print("=" * 25)
    
    email_service = NoAuthEmailService()
    
    if email_service.test_email():
        print("✅ Test email sent successfully!")
        print("📧 Check sutho100@gmail.com")
        return True
    else:
        print("❌ Test email failed")
        return False

# Trading alert example
def send_sample_trading_alert():
    """Send a sample trading alert"""
    print("📈 Sample Trading Alert")
    print("=" * 25)
    
    email_service = NoAuthEmailService()
    
    success = email_service.send_trading_alert(
        symbol="CBA.AX",
        signal="BUY",
        price=105.50,
        confidence=0.85,
        details="""ML Analysis Details:
• Sentiment Score: +0.75 (Very Positive)
• News Volume: High confidence signal
• Technical Indicators: Bullish momentum
• Risk Level: Moderate

Suggested Action: Enter long position with 2% stop-loss"""
    )
    
    if success:
        print("✅ Trading alert sent!")
    else:
        print("❌ Trading alert failed")
    
    return success

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "trading":
        send_sample_trading_alert()
    else:
        send_quick_test()

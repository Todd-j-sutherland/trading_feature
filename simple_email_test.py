#!/usr/bin/env python3
"""
Simple Email Trading Alert Test
Test the email notification system without complex dependencies
"""

import sys
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    env_vars = {}
    env_file = Path('.env')
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

def send_test_email():
    """Send a test email notification"""
    print("🤖 AI Trading Email Alert System - Test")
    print("=" * 50)
    
    # Load configuration
    env_vars = load_env_file()
    
    sender_email = env_vars.get('EMAIL_ADDRESS', '')
    sender_password = env_vars.get('EMAIL_PASSWORD', '')
    recipient_email = "sutho100@gmail.com"
    
    # Check configuration
    if not sender_email or sender_email == 'your_email@gmail.com':
        print("❌ Email configuration not set up!")
        print("Please update your .env file with:")
        print("  EMAIL_ADDRESS=your_gmail@gmail.com")
        print("  EMAIL_PASSWORD=your_app_password")
        print("\n📝 For Gmail, you'll need to:")
        print("  1. Enable 2-factor authentication")
        print("  2. Generate an App Password")
        print("  3. Use the App Password (not your regular password)")
        return False
    
    if not sender_password or sender_password == 'your_app_password_here':
        print("❌ Email password not configured!")
        print("Please set EMAIL_PASSWORD in your .env file")
        return False
    
    print(f"📧 Sender: {sender_email}")
    print(f"📧 Recipient: {recipient_email}")
    print("📧 Testing email connection...")
    
    try:
        # Create test message
        subject = "🧪 Test Email - AI Trading Alert System"
        
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                .content {{ padding: 20px; }}
                .signal-badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; color: white; font-weight: bold; background-color: #00C851; }}
                .metric {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
                .metric-label {{ font-weight: bold; color: #333; }}
                .metric-value {{ color: #666; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; color: #666; font-size: 12px; border-radius: 0 0 10px 10px; }}
                .timestamp {{ color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 AI Trading Alert System</h1>
                    <div class="timestamp">{datetime.now().strftime('%Y-%m-%d %H:%M:%S AEST')}</div>
                </div>
                
                <div class="content">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <h2>✅ Test Email Successful!</h2>
                        <div class="signal-badge">SYSTEM READY</div>
                    </div>
                    
                    <div class="metric">
                        <span class="metric-label">System Status:</span>
                        <span class="metric-value">✅ Email notifications working</span>
                    </div>
                    
                    <div class="metric">
                        <span class="metric-label">Alert Recipient:</span>
                        <span class="metric-value">sutho100@gmail.com</span>
                    </div>
                    
                    <div class="metric">
                        <span class="metric-label">Monitored Stocks:</span>
                        <span class="metric-value">CBA.AX, ANZ.AX, WBC.AX, NAB.AX, MQG.AX</span>
                    </div>
                    
                    <div class="metric">
                        <span class="metric-label">Next Steps:</span>
                        <span class="metric-value">Start real-time monitoring to receive trading alerts</span>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <h4>🧠 About Your AI Trading System:</h4>
                        <p>This email confirms that your AI trading analysis system can successfully send email notifications. 
                        When real-time monitoring is active, you'll receive alerts like this whenever the AI detects 
                        high-confidence trading opportunities including stock name, current price, symbol, AI signal, 
                        and confidence level.</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This test was sent by your AI Trading Analysis System</p>
                    <p>⚠️ Trading alerts are not financial advice. Always do your own research.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text content
        text_content = f"""
AI TRADING ALERT SYSTEM - TEST EMAIL
{datetime.now().strftime('%Y-%m-%d %H:%M:%S AEST')}

✅ EMAIL NOTIFICATION TEST SUCCESSFUL!

System Status: Email notifications working
Alert Recipient: sutho100@gmail.com
Monitored Stocks: CBA.AX, ANZ.AX, WBC.AX, NAB.AX, MQG.AX

About Your AI Trading System:
This email confirms that your AI trading analysis system can successfully 
send email notifications. When real-time monitoring is active, you'll 
receive alerts whenever the AI detects high-confidence trading opportunities 
including stock name, current price, symbol, AI signal, and confidence level.

---
This test was sent by your AI Trading Analysis System.
Trading alerts are not financial advice. Always do your own research.
        """
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = recipient_email
        
        # Add parts
        text_part = MIMEText(text_content, "plain")
        html_part = MIMEText(html_content, "html")
        message.attach(text_part)
        message.attach(html_part)
        
        # Send email
        context = ssl.create_default_context()
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        
        print("✅ Test email sent successfully!")
        print("📧 Check sutho100@gmail.com for the test message")
        print("\n🚀 Your email notification system is ready!")
        print("📝 To start real-time monitoring, you'll need to install the full dependencies")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Verify your Gmail credentials in .env file")
        print("2. Make sure you're using an App Password (not regular password)")
        print("3. Check that 2-factor authentication is enabled on Gmail")
        print("4. Verify internet connection")
        return False

def show_configuration():
    """Show current configuration"""
    print("⚙️  Email Alert Configuration:")
    print("-" * 40)
    
    env_vars = load_env_file()
    email_address = env_vars.get('EMAIL_ADDRESS', 'NOT_SET')
    email_password = env_vars.get('EMAIL_PASSWORD', 'NOT_SET')
    
    email_configured = email_address not in ['NOT_SET', 'your_email@gmail.com']
    password_configured = email_password not in ['NOT_SET', 'your_app_password_here']
    
    print(f"📧 Sender Email: {email_address}")
    print(f"📧 Password Set: {'✅ Yes' if password_configured else '❌ No'}")
    print(f"📧 Configuration: {'✅ Ready' if email_configured and password_configured else '❌ Needs setup'}")
    print(f"📧 Recipient: sutho100@gmail.com")
    print(f"📡 SMTP Server: smtp.gmail.com:587")
    
    if not email_configured or not password_configured:
        print("\n🔧 Setup Instructions:")
        print("1. Create/edit .env file in your project root")
        print("2. Add these lines:")
        print("   EMAIL_ADDRESS=your_gmail@gmail.com")
        print("   EMAIL_PASSWORD=your_app_password")
        print("3. For Gmail:")
        print("   - Enable 2-factor authentication")
        print("   - Generate an App Password in Google Account settings")
        print("   - Use the App Password (not your regular password)")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python3 simple_email_test.py [test|config]")
        print("  test   - Send test email to sutho100@gmail.com")
        print("  config - Show current configuration")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'test':
        success = send_test_email()
        sys.exit(0 if success else 1)
    elif command == 'config':
        show_configuration()
    else:
        print("Unknown command. Use 'test' or 'config'")
        sys.exit(1)

if __name__ == "__main__":
    main()

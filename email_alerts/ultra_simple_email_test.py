#!/usr/bin/env python3
"""
Ultra-simple email test to sutho100@gmail.com
Just run this script and enter your email credentials when prompted
"""

import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def send_test_email():
    """Send a simple test email with minimal code"""
    
    print("📧 Ultra-Simple Email Test")
    print("=" * 30)
    print("This will send a test email to sutho100@gmail.com")
    print()
    
    # Get credentials (you only need to enter these once)
    print("Enter your Gmail credentials:")
    sender_email = input("Your Gmail address: ").strip()
    
    if not sender_email:
        print("❌ Email address required")
        return
    
    # For security, use getpass for password input
    import getpass
    sender_password = getpass.getpass("Your Gmail app password (hidden): ").strip()
    
    if not sender_password:
        print("❌ Password required")
        return
    
    # Create simple message
    message = f"""
🤖 Simple Test Email

Sent from your trading system at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you receive this, email sending is working! ✅

Time to set up those trading alerts! 🚀
"""
    
    try:
        # Create email
        msg = MIMEText(message)
        msg['Subject'] = f"🧪 Trading System Test - {datetime.now().strftime('%H:%M')}"
        msg['From'] = sender_email
        msg['To'] = "sutho100@gmail.com"
        
        # Send via Gmail
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print("✅ Test email sent successfully to sutho100@gmail.com!")
        print("📧 Check your inbox")
        
        # Save credentials to .env for future use
        save_to_env = input("\nSave credentials to .env file for future use? (y/n): ").lower().strip()
        if save_to_env == 'y':
            save_credentials(sender_email, sender_password)
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        print("\n💡 Common issues:")
        print("• Make sure you're using an App Password, not your regular Gmail password")
        print("• Enable 2-factor authentication on your Google account first")
        print("• Generate App Password at: https://myaccount.google.com/apppasswords")

def save_credentials(email, password):
    """Save email credentials to .env file"""
    try:
        with open('../.env', 'a') as f:
            f.write(f"\n# Email Configuration (added by simple test)\n")
            f.write(f"EMAIL_ADDRESS={email}\n")
            f.write(f"EMAIL_PASSWORD={password}\n")
        print("✅ Credentials saved to .env file")
        print("🔒 Keep your .env file secure and don't commit it to git")
    except Exception as e:
        print(f"⚠️ Could not save to .env: {e}")

if __name__ == "__main__":
    send_test_email()

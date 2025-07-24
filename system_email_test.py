#!/usr/bin/env python3
"""
Send email using system sendmail (if available) or create a local mail file
No Gmail authentication required
"""

import os
import subprocess
from datetime import datetime

def send_via_sendmail():
    """Try to send email using system sendmail (Linux/Mac)"""
    message = f"""To: sutho100@gmail.com
Subject: Test Email from Trading System - {datetime.now().strftime('%H:%M')}

🤖 System Test Email

This email was sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} using system sendmail.

If you receive this, the local email system is working!

Best regards,
Your Trading System 🚀
"""
    
    try:
        # Try to use sendmail
        process = subprocess.Popen(['sendmail', 'sutho100@gmail.com'], 
                                 stdin=subprocess.PIPE, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        stdout, stderr = process.communicate(message)
        
        if process.returncode == 0:
            print("✅ Email sent via system sendmail")
            return True
        else:
            print(f"❌ Sendmail failed: {stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ Sendmail not available on this system")
        return False
    except Exception as e:
        print(f"❌ Sendmail error: {e}")
        return False

def create_mail_file():
    """Create a local mail file that can be sent later"""
    message = f"""🤖 Trading System Email Draft

To: sutho100@gmail.com
Subject: Test Email - {datetime.now().strftime('%H:%M')}

This is a test email created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

You can copy this content and send it manually, or use it to test your email system.

Best regards,
Your Trading System 🚀
"""
    
    try:
        mail_file = f"email_draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(mail_file, 'w') as f:
            f.write(message)
        
        print(f"✅ Email draft created: {mail_file}")
        print("📧 You can copy the content and send manually")
        print(f"📄 File contents:\n{message}")
        return True
        
    except Exception as e:
        print(f"❌ Could not create mail file: {e}")
        return False

def simple_notification():
    """Just print a notification message"""
    print("🔔 Trading System Notification")
    print("=" * 40)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Recipient: sutho100@gmail.com")
    print("Message: Test notification from trading system")
    print("Status: ✅ System is working!")
    print()
    print("💡 To actually send emails, you'll need:")
    print("1. Gmail App Password setup")
    print("2. Or a webhook service like Zapier")
    print("3. Or system sendmail configuration")

def main():
    """Try different email methods"""
    print("📧 Simple Email Methods Test")
    print("=" * 35)
    
    # Method 1: Try sendmail
    print("🔄 Trying system sendmail...")
    if send_via_sendmail():
        return
    
    # Method 2: Create mail file
    print("🔄 Creating email draft file...")
    if create_mail_file():
        return
    
    # Method 3: Just show notification
    print("🔄 Showing notification...")
    simple_notification()

if __name__ == "__main__":
    main()

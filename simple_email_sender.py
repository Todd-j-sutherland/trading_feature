#!/usr/bin/env python3
"""
Simple email sender to sutho100@gmail.com
Uses Gmail SMTP - requires sender email and app password
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_simple_email(sender_email, sender_password, message_text, subject="Test Email"):
    """
    Send a simple email to sutho100@gmail.com
    
    Args:
        sender_email: Your Gmail address
        sender_password: Your Gmail app password (not regular password)
        message_text: The message to send
        subject: Email subject line
    """
    
    recipient = "sutho100@gmail.com"
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(message_text, 'plain'))
        
        # Gmail SMTP configuration
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Enable security
        server.login(sender_email, sender_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, recipient, text)
        server.quit()
        
        print(f"✅ Email sent successfully to {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def send_quick_test():
    """Send a quick test email with minimal setup"""
    
    print("📧 Simple Email Sender")
    print("=" * 30)
    
    # You'll need to provide these
    sender_email = input("Enter your Gmail address: ").strip()
    sender_password = input("Enter your Gmail app password: ").strip()
    
    if not sender_email or not sender_password:
        print("❌ Email and password required")
        return False
    
    message = f"""
🤖 Test Email from Trading System

This is a test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

If you receive this, the email system is working correctly!

Best regards,
Your Trading Bot 🚀
"""
    
    subject = f"🧪 Test Email - {datetime.now().strftime('%H:%M')}"
    
    return send_simple_email(sender_email, sender_password, message, subject)

if __name__ == "__main__":
    send_quick_test()

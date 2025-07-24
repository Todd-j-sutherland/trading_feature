#!/usr/bin/env python3
"""
Send email using EmailJS or similar service (no authentication required)
This approach uses HTTP requests instead of SMTP
"""

import requests
import json
from datetime import datetime

def send_email_via_emailjs(message_text, subject="Test Email"):
    """
    Send email using EmailJS service (requires setup on emailjs.com)
    This is truly "no login" - just HTTP requests
    """
    
    # You would need to set up an EmailJS account and get these values
    # This is just an example structure
    emailjs_data = {
        'service_id': 'your_service_id',  # From EmailJS dashboard
        'template_id': 'your_template_id',  # From EmailJS dashboard
        'user_id': 'your_user_id',  # From EmailJS dashboard
        'template_params': {
            'to_email': 'sutho100@gmail.com',
            'from_name': 'Trading System',
            'subject': subject,
            'message': message_text
        }
    }
    
    try:
        response = requests.post(
            'https://api.emailjs.com/api/v1.0/email/send',
            data=json.dumps(emailjs_data),
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("✅ Email sent successfully via EmailJS")
            return True
        else:
            print(f"❌ EmailJS failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending via EmailJS: {e}")
        return False

def send_email_via_webhook():
    """
    Send email using a webhook service like Zapier or Make.com
    Truly no authentication required
    """
    
    # Example webhook URL (you'd need to create this)
    webhook_url = "https://hooks.zapier.com/hooks/catch/your_webhook_id/"
    
    data = {
        'to': 'sutho100@gmail.com',
        'subject': f'Test Email - {datetime.now().strftime("%H:%M")}',
        'message': f"""
🤖 Webhook Test Email

This email was sent via webhook at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

No authentication required!

Best regards,
Your Trading System 🚀
"""
    }
    
    try:
        response = requests.post(webhook_url, json=data)
        
        if response.status_code == 200:
            print("✅ Email sent successfully via webhook")
            return True
        else:
            print(f"❌ Webhook failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending via webhook: {e}")
        return False

if __name__ == "__main__":
    print("🔗 No-Auth Email Options:")
    print("1. EmailJS (requires free account setup)")
    print("2. Webhook (requires Zapier/Make.com setup)")
    print("\nFor immediate testing, use simple_email_sender.py with Gmail app password")

#!/usr/bin/env python3
"""
SendGrid Email Service
Uses SendGrid API instead of SMTP to bypass port blocking
"""

import os
import json
from pathlib import Path

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

class SendGridEmailService:
    """Email service using SendGrid API"""
    
    def __init__(self):
        self.api_key = None
        self.from_email = None
        self.load_credentials()
        
    def load_credentials(self):
        """Load SendGrid credentials from .env file"""
        # Look for .env in parent directory first, then current
        for env_path in [Path("../.env"), Path(".env")]:
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('SENDGRID_API_KEY='):
                            self.api_key = line.split('=', 1)[1]
                        elif line.startswith('FROM_EMAIL='):
                            self.from_email = line.split('=', 1)[1]
                        elif line.startswith('EMAIL_ADDRESS=') and not self.from_email:
                            # Use EMAIL_ADDRESS as fallback for FROM_EMAIL
                            self.from_email = line.split('=', 1)[1]
                break
    
    def is_configured(self) -> bool:
        """Check if SendGrid is properly configured"""
        return (SENDGRID_AVAILABLE and 
                self.api_key is not None and 
                self.from_email is not None)
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via SendGrid API"""
        if not self.is_configured():
            print("❌ SendGrid not configured properly")
            if not SENDGRID_AVAILABLE:
                print("   Install with: pip install sendgrid")
            if not self.api_key:
                print("   Missing SENDGRID_API_KEY in .env")
            if not self.from_email:
                print("   Missing FROM_EMAIL in .env")
            return False
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=body.replace('\n', '<br>')
            )
            
            sg = SendGridAPIClient(api_key=self.api_key)
            response = sg.send(message)
            
            if response.status_code in [200, 202]:
                print(f"✅ Email sent via SendGrid to {to_email}")
                return True
            else:
                print(f"❌ SendGrid API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ SendGrid error: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test SendGrid API connection"""
        if not self.is_configured():
            return False
            
        try:
            sg = SendGridAPIClient(api_key=self.api_key)
            # Test with a simple API call
            response = sg.client.user.profile.get()
            return response.status_code == 200
        except Exception as e:
            print(f"❌ SendGrid connection test failed: {e}")
            return False

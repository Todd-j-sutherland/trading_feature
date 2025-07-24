#!/usr/bin/env python3
"""
Simple Gmail Email Service for Trading Alerts
Uses Gmail SMTP with app password from .env file
"""

import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path

class SimpleGmailService:
    """Simple Gmail email service using SMTP"""
    
    def __init__(self):
        # Load from .env file
        self.load_credentials()
    
    def load_credentials(self):
        """Load email credentials from .env file"""
        env_file = Path("../.env")
        self.email_address = None
        self.email_password = None
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('EMAIL_ADDRESS='):
                        self.email_address = line.split('=', 1)[1]
                    elif line.startswith('EMAIL_PASSWORD='):
                        self.email_password = line.split('=', 1)[1]
    
    def test_email_connection(self) -> bool:
        """Test if email can be sent"""
        if not self.email_address or not self.email_password:
            return False
        
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                return True
        except Exception:
            return False
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send an email"""
        try:
            if not self.email_address or not self.email_password:
                print("❌ Email credentials not configured")
                return False
            
            # Create email
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.email_address
            msg['To'] = to_email
            
            # Send via Gmail
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

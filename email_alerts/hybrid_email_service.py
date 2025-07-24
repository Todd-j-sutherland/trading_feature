#!/usr/bin/env python3
"""
Hybrid Email Service
Tries multiple email methods in order of preference:
1. SendGrid API (recommended for DigitalOcean)
2. Gmail SMTP (if available)
3. Local sendmail (fallback)
"""

import smtplib
import subprocess
import os
from email.mime.text import MIMEText
from pathlib import Path

try:
    from sendgrid_email_service import SendGridEmailService
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

class HybridEmailService:
    """Email service that tries multiple methods"""
    
    def __init__(self):
        self.email_address = None
        self.email_password = None
        self.sendgrid_service = None
        self.load_credentials()
        
        # Initialize SendGrid if available
        if SENDGRID_AVAILABLE:
            self.sendgrid_service = SendGridEmailService()
        
    def load_credentials(self):
        """Load email credentials from parent .env file"""
        # Look for .env in parent directory first, then current
        for env_path in [Path("../.env"), Path(".env")]:
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('EMAIL_ADDRESS='):
                            self.email_address = line.split('=', 1)[1]
                        elif line.startswith('EMAIL_PASSWORD='):
                            self.email_password = line.split('=', 1)[1]
                break
    
    def test_email_connection(self) -> bool:
        """Test if any email method is available"""
        # Try SendGrid first
        if self.sendgrid_service and self.sendgrid_service.is_configured():
            if self.sendgrid_service.test_connection():
                return True
        
        # Try Gmail SMTP
        if self.email_address and self.email_password:
            try:
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(self.email_address, self.email_password)
                    return True
            except:
                pass
        
        # Fall back to sendmail
        return os.path.exists("/usr/sbin/sendmail")
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email using the best available method"""
        
        # Method 1: Try SendGrid API (best for DigitalOcean)
        if self.sendgrid_service and self.sendgrid_service.is_configured():
            if self.sendgrid_service.send_email(to_email, subject, body):
                return True
        
        # Method 2: Try Gmail SMTP
        if self.email_address and self.email_password:
            if self._send_via_gmail(to_email, subject, body):
                return True
        
        # Method 3: Fall back to sendmail
        if self._send_via_sendmail(to_email, subject, body):
            return True
        
        # Method 4: Try alternative SMTP ports
        if self.email_address and self.email_password:
            if self._send_via_gmail_ssl(to_email, subject, body):
                return True
        
        print("❌ All email methods failed")
        return False
    
    def _send_via_gmail(self, to_email: str, subject: str, body: str) -> bool:
        """Try Gmail SMTP on port 587"""
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.email_address
            msg['To'] = to_email
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            print(f"✅ Email sent via Gmail SMTP to {to_email}")
            return True
        except Exception as e:
            print(f"⚠️ Gmail SMTP failed: {e}")
            return False
    
    def _send_via_gmail_ssl(self, to_email: str, subject: str, body: str) -> bool:
        """Try Gmail SMTP on port 465 (SSL)"""
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.email_address
            msg['To'] = to_email
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            print(f"✅ Email sent via Gmail SSL to {to_email}")
            return True
        except Exception as e:
            print(f"⚠️ Gmail SSL failed: {e}")
            return False
    
    def _send_via_sendmail(self, to_email: str, subject: str, body: str) -> bool:
        """Send via local sendmail"""
        try:
            if not os.path.exists("/usr/sbin/sendmail"):
                return False
                
            message = f"""To: {to_email}
Subject: {subject}
From: trading-system@{self._get_hostname()}

{body}
"""
            
            process = subprocess.Popen(
                ["/usr/sbin/sendmail", to_email], 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=message)
            
            if process.returncode == 0:
                print(f"✅ Email sent via sendmail to {to_email}")
                return True
            else:
                print(f"⚠️ Sendmail failed: {stderr}")
                return False
                
        except Exception as e:
            print(f"⚠️ Sendmail error: {e}")
            return False
    
    def _get_hostname(self) -> str:
        """Get system hostname"""
        try:
            result = subprocess.run(['hostname'], capture_output=True, text=True)
            return result.stdout.strip() or 'trading-server'
        except:
            return 'trading-server'

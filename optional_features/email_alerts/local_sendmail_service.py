#!/usr/bin/env python3
"""
Local Sendmail Email Service for Remote Servers
Uses the system's sendmail utility to bypass SMTP port restrictions
"""

import subprocess
import os
from datetime import datetime
from pathlib import Path

class LocalSendmailService:
    """Email service using local sendmail utility"""
    
    def __init__(self):
        self.sendmail_path = "/usr/sbin/sendmail"
        
    def test_email_connection(self) -> bool:
        """Test if sendmail is available"""
        return os.path.exists(self.sendmail_path)
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send an email using local sendmail"""
        try:
            # Create email message
            message = f"""To: {to_email}
Subject: {subject}
From: trading-system@{self._get_hostname()}

{body}
"""
            
            # Send via sendmail
            process = subprocess.Popen(
                [self.sendmail_path, to_email], 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=message)
            
            if process.returncode == 0:
                print(f"✅ Email sent to {to_email} via sendmail")
                return True
            else:
                print(f"❌ Sendmail failed: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send email via sendmail: {e}")
            return False
    
    def _get_hostname(self) -> str:
        """Get system hostname for From address"""
        try:
            result = subprocess.run(['hostname'], capture_output=True, text=True)
            return result.stdout.strip() or 'unknown-host'
        except:
            return 'trading-server'

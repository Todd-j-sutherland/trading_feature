#!/usr/bin/env python3
"""
Setup SendGrid for Email Alerts
Helps configure SendGrid API for DigitalOcean droplets
"""

import os
import sys
from pathlib import Path

def install_sendgrid():
    """Install SendGrid Python library"""
    print("📦 Installing SendGrid library...")
    os.system("pip install sendgrid")

def setup_sendgrid_credentials():
    """Guide user through SendGrid setup"""
    print("\n🔧 SendGrid Setup Guide")
    print("=" * 50)
    
    print("\n1. Create SendGrid Account:")
    print("   - Go to https://sendgrid.com/")
    print("   - Sign up for a free account (100 emails/day)")
    print("   - Or use DigitalOcean Marketplace: SendGrid Email API")
    
    print("\n2. Get API Key:")
    print("   - Login to SendGrid dashboard")
    print("   - Go to Settings > API Keys")
    print("   - Click 'Create API Key'")
    print("   - Choose 'Full Access' or create restricted key with Mail Send permissions")
    print("   - Copy the API key (you won't see it again!)")
    
    print("\n3. Domain Authentication (Recommended):")
    print("   - Go to Settings > Sender Authentication")
    print("   - Authenticate your domain or single sender")
    print("   - This improves email deliverability")
    
    # Get credentials from user
    print("\n" + "=" * 50)
    print("Enter your SendGrid credentials:")
    
    api_key = input("\nSendGrid API Key: ").strip()
    if not api_key:
        print("❌ API Key is required")
        return False
    
    from_email = input("From Email Address: ").strip()
    if not from_email:
        print("❌ From Email is required")
        return False
    
    # Save to .env file
    env_file = Path(".env")
    
    # Read existing .env
    existing_lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            existing_lines = f.readlines()
    
    # Update or add SendGrid credentials
    updated_lines = []
    api_key_added = False
    from_email_added = False
    
    for line in existing_lines:
        if line.startswith('SENDGRID_API_KEY='):
            updated_lines.append(f'SENDGRID_API_KEY={api_key}\n')
            api_key_added = True
        elif line.startswith('FROM_EMAIL='):
            updated_lines.append(f'FROM_EMAIL={from_email}\n')
            from_email_added = True
        else:
            updated_lines.append(line)
    
    # Add missing credentials
    if not api_key_added:
        updated_lines.append(f'SENDGRID_API_KEY={api_key}\n')
    if not from_email_added:
        updated_lines.append(f'FROM_EMAIL={from_email}\n')
    
    # Write updated .env
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"\n✅ Credentials saved to {env_file}")
    return True

def test_sendgrid():
    """Test SendGrid configuration"""
    print("\n🧪 Testing SendGrid configuration...")
    
    try:
        from sendgrid_email_service import SendGridEmailService
        
        service = SendGridEmailService()
        
        if not service.is_configured():
            print("❌ SendGrid not properly configured")
            return False
        
        # Test connection
        if service.test_connection():
            print("✅ SendGrid API connection successful")
        else:
            print("❌ SendGrid API connection failed")
            return False
        
        # Send test email
        test_email = input("Enter email address for test: ").strip()
        if test_email:
            success = service.send_email(
                test_email,
                "🧪 SendGrid Test Email",
                "This is a test email from your trading system.\n\nIf you receive this, SendGrid is working correctly!"
            )
            
            if success:
                print("✅ Test email sent! Check your inbox.")
                return True
            else:
                print("❌ Test email failed")
                return False
        
    except ImportError:
        print("❌ SendGrid library not installed")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    print("🚀 SendGrid Email Setup for Trading Alerts")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Install SendGrid library")
        print("2. Setup SendGrid credentials")
        print("3. Test SendGrid configuration")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            install_sendgrid()
        elif choice == '2':
            if setup_sendgrid_credentials():
                print("\n✅ Setup complete!")
            else:
                print("\n❌ Setup failed")
        elif choice == '3':
            test_sendgrid()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()

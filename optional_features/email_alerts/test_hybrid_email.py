#!/usr/bin/env python3
"""Test the hybrid email service"""

from hybrid_email_service import HybridEmailService

def main():
    print("🧪 Testing Hybrid Email Service")
    
    service = HybridEmailService()
    
    # Check credentials
    if service.email_address:
        print(f"✅ Email address loaded: {service.email_address}")
    else:
        print("❌ No email address found")
        return
    
    if service.email_password:
        print("✅ Email password loaded")
    else:
        print("❌ No email password found")
        return
    
    # Test connection
    print("\n🔍 Testing email connection...")
    if service.test_email_connection():
        print("✅ Email connection available")
    else:
        print("❌ No email connection available")
    
    # Send test email
    print("\n📧 Sending test email...")
    success = service.send_email(
        service.email_address,
        "🧪 Hybrid Email Service Test",
        "This is a test from the hybrid email service.\n\nIf you receive this, the system is working!"
    )
    
    if success:
        print("✅ Test email sent successfully!")
    else:
        print("❌ Test email failed")

if __name__ == "__main__":
    main()

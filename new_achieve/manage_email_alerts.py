#!/usr/bin/env python3
"""
Email Trading Alerts Manager
Manage real-time email notifications for trading signals

Usage:
  python manage_email_alerts.py start     # Start real-time monitoring
  python manage_email_alerts.py stop      # Stop monitoring
  python manage_email_alerts.py test      # Send test email
  python manage_email_alerts.py status    # Check monitoring status
  python manage_email_alerts.py config    # Show configuration
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.real_time_monitor import (
    get_signal_monitor, 
    start_monitoring, 
    stop_monitoring, 
    send_test_email, 
    get_status
)
from app.services.email_notifier import EmailNotificationService
from app.config.settings import Settings

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/email_alerts.log')
        ]
    )

def start_command():
    """Start real-time monitoring"""
    print("🚀 Starting real-time trading signal monitoring...")
    
    # Check email configuration first
    settings = Settings()
    email_address = settings.get('EMAIL_ADDRESS', '')
    email_password = settings.get('EMAIL_PASSWORD', '')
    
    if not email_address or email_address == 'your_email@gmail.com':
        print("❌ Email configuration not set up!")
        print("Please update your .env file with:")
        print("  EMAIL_ADDRESS=your_gmail@gmail.com")
        print("  EMAIL_PASSWORD=your_app_password")
        print("\n📝 For Gmail, you'll need to:")
        print("  1. Enable 2-factor authentication")
        print("  2. Generate an App Password")
        print("  3. Use the App Password (not your regular password)")
        return False
    
    if not email_password or email_password == 'your_app_password_here':
        print("❌ Email password not configured!")
        print("Please set EMAIL_PASSWORD in your .env file")
        return False
    
    # Start monitoring
    success = start_monitoring()
    
    if success:
        print("✅ Real-time monitoring started successfully!")
        print("📧 Email alerts will be sent to: sutho100@gmail.com")
        print("📊 Monitoring symbols: CBA.AX, ANZ.AX, WBC.AX, NAB.AX, MQG.AX")
        print("⏰ Check interval: 5 minutes during market hours")
        print("\n🛑 Press Ctrl+C to stop monitoring")
        
        try:
            # Keep the script running
            monitor = get_signal_monitor()
            while monitor.is_monitoring:
                import time
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            stop_monitoring()
            print("✅ Monitoring stopped")
    else:
        print("❌ Failed to start monitoring")
        return False
    
    return True

def stop_command():
    """Stop monitoring"""
    print("🛑 Stopping real-time monitoring...")
    stop_monitoring()
    print("✅ Monitoring stopped")

def test_command():
    """Send test email"""
    print("📧 Sending test email to sutho100@gmail.com...")
    
    # Check configuration
    settings = Settings()
    email_address = settings.get('EMAIL_ADDRESS', '')
    
    if not email_address or email_address == 'your_email@gmail.com':
        print("❌ Email not configured. Please set up .env file first.")
        return False
    
    success = send_test_email()
    
    if success:
        print("✅ Test email sent successfully!")
        print("📧 Check sutho100@gmail.com for the test alert")
    else:
        print("❌ Failed to send test email")
        print("💡 Check your .env file configuration and internet connection")
    
    return success

def status_command():
    """Show monitoring status"""
    print("📊 Real-time monitoring status:")
    print("-" * 40)
    
    status = get_status()
    
    print(f"🔄 Monitoring: {'✅ Running' if status['is_monitoring'] else '❌ Stopped'}")
    print(f"🏢 Market Open: {'✅ Yes' if status['market_open'] else '❌ No'}")
    print(f"📈 Symbols: {', '.join(status['symbols_monitored'])}")
    print(f"⏰ Interval: {status['monitoring_interval']} seconds")
    
    if status['last_prices']:
        print("\n💰 Last Known Prices:")
        for symbol, price in status['last_prices'].items():
            print(f"  {symbol}: ${price:.2f}")
    
    if status['alert_cooldowns']:
        print("\n🔕 Alert Cooldowns:")
        for symbol, seconds_ago in status['alert_cooldowns'].items():
            minutes_ago = int(seconds_ago / 60)
            print(f"  {symbol}: {minutes_ago} minutes ago")
    
    # Check email configuration
    settings = Settings()
    email_address = settings.get('EMAIL_ADDRESS', '')
    print(f"\n📧 Email Config: {'✅ Configured' if email_address and email_address != 'your_email@gmail.com' else '❌ Not configured'}")
    print(f"📧 Recipient: sutho100@gmail.com")

def config_command():
    """Show configuration"""
    print("⚙️  Email Alert Configuration:")
    print("-" * 40)
    
    settings = Settings()
    
    # Email settings
    email_address = settings.get('EMAIL_ADDRESS', 'NOT_SET')
    email_configured = email_address != 'NOT_SET' and email_address != 'your_email@gmail.com'
    
    print(f"📧 Sender Email: {email_address}")
    print(f"📧 Password Set: {'✅ Yes' if settings.get('EMAIL_PASSWORD') else '❌ No'}")
    print(f"📧 Configuration: {'✅ Ready' if email_configured else '❌ Needs setup'}")
    print(f"📧 Recipient: sutho100@gmail.com")
    print(f"📡 SMTP Server: smtp.gmail.com:587")
    
    # Monitoring settings
    monitor = get_signal_monitor()
    print(f"\n📊 Monitoring Settings:")
    print(f"📈 Symbols: {', '.join(monitor.symbols)}")
    print(f"⏰ Interval: {monitor.monitoring_interval} seconds")
    print(f"🕘 Market Hours: {monitor.market_hours_start} - {monitor.market_hours_end} AEST")
    print(f"🔕 Cooldown: {monitor.cooldown_period / 60} minutes")
    print(f"🎯 Confidence Threshold: {monitor.confidence_threshold:.1%}")
    
    if not email_configured:
        print("\n🔧 Setup Instructions:")
        print("1. Create/edit .env file in your project root")
        print("2. Add these lines:")
        print("   EMAIL_ADDRESS=your_gmail@gmail.com")
        print("   EMAIL_PASSWORD=your_app_password")
        print("3. For Gmail:")
        print("   - Enable 2-factor authentication")
        print("   - Generate an App Password in Google Account settings")
        print("   - Use the App Password (not your regular password)")

def main():
    """Main command-line interface"""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Email Trading Alerts Manager",
        epilog="Email alerts will be sent to sutho100@gmail.com when ML indicators detect trading opportunities"
    )
    
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'test', 'status', 'config'],
        help='Command to execute'
    )
    
    args = parser.parse_args()
    
    print("🤖 AI Trading Email Alert System")
    print("=" * 50)
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    try:
        if args.command == 'start':
            success = start_command()
            sys.exit(0 if success else 1)
        
        elif args.command == 'stop':
            stop_command()
        
        elif args.command == 'test':
            success = test_command()
            sys.exit(0 if success else 1)
        
        elif args.command == 'status':
            status_command()
        
        elif args.command == 'config':
            config_command()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
        stop_monitoring()
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logging.error(f"Command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

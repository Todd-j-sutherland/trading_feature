#!/usr/bin/env python3
"""
Setup script for Hourly Trading Alerts
Configures email settings and tests the system
"""

import os
import sys
from pathlib import Path

def create_env_template():
    """Create .env template if it doesn't exist"""
    env_file = Path("../.env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    env_template = """# Email Configuration for Trading Alerts
EMAIL_ADDRESS=your_gmail@gmail.com
EMAIL_PASSWORD=your_app_password_here

# Gmail App Password Instructions:
# 1. Enable 2-factor authentication on your Google account
# 2. Go to Google Account settings > Security > 2-Step Verification
# 3. At the bottom, select "App passwords"
# 4. Select "Mail" and your device
# 5. Use the generated 16-character password (not your regular password)

# Optional: Alpaca API (if you want live trading integration)
# ALPACA_API_KEY=your_alpaca_api_key
# ALPACA_SECRET_KEY=your_alpaca_secret_key
# ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Use this for paper trading
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_template)
        print("✅ Created .env template file")
        print("📝 Please edit .env with your email settings")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_system():
    """Test the hourly alert system"""
    print("\n🧪 Testing hourly alert system...")
    
    try:
        # Import and test
        from hourly_trading_alerts import HourlyTradingAlerts
        
        alerts = HourlyTradingAlerts()
        
        # Test email configuration
        if not alerts.email_service.test_email_connection():
            print("❌ Email configuration test failed")
            print("💡 Please check your .env file settings")
            return False
        
        print("✅ Email configuration test passed")
        
        # Test signal generation (dry run)
        print("🔍 Testing signal generation...")
        signals = alerts.generate_trading_signals()
        
        if signals:
            print(f"✅ Generated signals for {len(signals)} symbols")
            for symbol, data in signals.items():
                print(f"   {symbol}: {data['signal']} (confidence: {data['confidence']:.2f})")
        else:
            print("⚠️  No signals generated (this is normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def setup_cron():
    """Instructions for setting up cron job"""
    print("\n⏰ Setting up hourly cron job:")
    print("=" * 50)
    
    cron_path = os.path.abspath("hourly_trading_cron.sh")
    
    print("1. Open your crontab for editing:")
    print("   crontab -e")
    print()
    print("2. Add this line to run hourly during market hours (10AM-3PM AEST, weekdays):")
    print(f"   0 10-15 * * 1-5 {cron_path}")
    print()
    print("3. Or run every 30 minutes during market hours:")
    print(f"   0,30 10-15 * * 1-5 {cron_path}")
    print()
    print("4. Save and exit the crontab editor")
    print()
    print("📝 The cron job will:")
    print("   • Run only during ASX market hours")
    print("   • Skip weekends automatically")
    print("   • Use .venv312 Python environment")
    print("   • Log results to logs/hourly_alerts.log")
    print("   • Send emails only when high-confidence signals are detected")

def main():
    """Main setup process"""
    print("🤖 Hourly Trading Alerts Setup")
    print("=" * 50)
    
    # Create necessary directories
    Path("../logs").mkdir(exist_ok=True)
    Path("../data").mkdir(exist_ok=True)
    
    # Step 1: Create .env template
    print("📧 Step 1: Email Configuration")
    create_env_template()
    
    # Step 2: Test system
    print("\n🧪 Step 2: System Test")
    if test_system():
        print("✅ System test passed!")
    else:
        print("❌ System test failed - please fix email configuration first")
        return
    
    # Step 3: Cron setup instructions
    print("\n⏰ Step 3: Automation Setup")
    setup_cron()
    
    # Step 4: Manual test instructions
    print("\n🚀 Step 4: Manual Testing")
    print("=" * 50)
    print("Test commands you can run:")
    print()
    print("• Test email:")
    print("  cd email_alerts && source ../.venv312/bin/activate && python hourly_trading_alerts.py --test")
    print()
    print("• Run single check:")
    print("  cd email_alerts && source ../.venv312/bin/activate && python hourly_trading_alerts.py")
    print()
    print("• Run continuous (for testing):")
    print("  cd email_alerts && source ../.venv312/bin/activate && python hourly_trading_alerts.py --loop")
    print()
    print("📧 All alerts will be sent to: sutho100@gmail.com")
    print("🎯 Only high-confidence signals (>70%) will trigger emails")
    print("🔄 Same signals won't repeat within 2 hours")

if __name__ == "__main__":
    main()

# 📧 Email Trading Alerts System

This folder contains the hourly email trading alert system that sends ML-based trading signals via email.

## 🚀 Quick Start

### 1. Test Basic Email Functionality
```bash
# Activate virtual environment
source ../.venv312/bin/activate

# Test simple email sending
python ultra_simple_email_test.py
```

### 2. Set Up Hourly Trading Alerts
```bash
# Run setup and configuration
python setup_hourly_alerts.py

# Test the trading alert system
python hourly_trading_alerts.py --test

# Run single analysis (when market is open)
python hourly_trading_alerts.py

# Run continuous monitoring (for testing)
python hourly_trading_alerts.py --loop
```

### 3. Automate with Cron Job
```bash
# Edit crontab
crontab -e

# Add line for hourly alerts during market hours (10AM-3PM AEST, weekdays)
0 10-15 * * 1-5 /path/to/email_alerts/hourly_trading_cron.sh

# Or every 30 minutes during market hours
0,30 10-15 * * 1-5 /path/to/email_alerts/hourly_trading_cron.sh
```

## 📁 Files Description

- **`ultra_simple_email_test.py`** - Basic email functionality test
- **`hourly_trading_alerts.py`** - Main hourly trading alert system
- **`simple_gmail_service.py`** - Gmail SMTP service for sending emails
- **`setup_hourly_alerts.py`** - Setup and configuration script
- **`hourly_trading_cron.sh`** - Cron job script for automation

## ⚙️ Configuration

### Email Setup
1. Enable 2-factor authentication on your Gmail account
2. Generate App Password at: https://myaccount.google.com/apppasswords
3. Add credentials to `.env` file in project root:
```bash
EMAIL_ADDRESS=your_gmail@gmail.com
EMAIL_PASSWORD=your_16_character_app_password
```

### System Requirements
- Python 3.12+ (uses ../.venv312 virtual environment)
- Gmail account with App Password
- Access to existing ML trading system components

## 🎯 How It Works

1. **Market Hours Detection**: Only runs during ASX trading hours (9:30-16:00 AEST, weekdays)
2. **ML Analysis**: Uses existing sentiment analysis and ML models
3. **Signal Generation**: Generates BUY/SELL/HOLD signals with confidence scores
4. **Smart Filtering**: Only sends alerts for high-confidence signals (>70%)
5. **Spam Prevention**: Won't repeat same signal within 2 hours
6. **Email Alerts**: Sends professional trading alerts to sutho100@gmail.com

## 📊 Signal Logic

- **BUY**: Sentiment ≥ 0.6, Confidence ≥ 0.7
- **SELL**: Sentiment ≤ 0.4, Confidence ≥ 0.7  
- **HOLD**: Everything else (no email sent)

## 🔧 Troubleshooting

### Email Issues
- Ensure using App Password, not regular Gmail password
- Check 2-factor authentication is enabled
- Verify Gmail SMTP access is allowed

### Signal Generation Issues
- ML model files may need updating
- Check if market data is accessible
- Verify all dependencies are installed in .venv312

### Cron Job Issues
- Ensure script paths are absolute
- Check cron job logs: `tail -f logs/hourly_alerts.log`
- Verify cron job timezone matches AEST

## 📈 Integration

This system integrates with:
- **Morning Routine**: Pre-market analysis
- **Evening Routine**: End-of-day ML training
- **Hourly Alerts**: Real-time opportunities (this system)

Creates a complete 3-tier trading system: Strategic → Tactical → Operational

## 🚨 Risk Disclaimer

This is an automated ML-based analysis system. Always:
- Verify signals with your own analysis
- Use appropriate position sizing (max 2% risk per trade)
- Set stop-losses before entering trades
- Never risk more than you can afford to lose

---

**Target Email**: sutho100@gmail.com  
**Market Hours**: 9:30-16:00 AEST (weekdays only)  
**Alert Frequency**: Hourly (when high-confidence signals detected)

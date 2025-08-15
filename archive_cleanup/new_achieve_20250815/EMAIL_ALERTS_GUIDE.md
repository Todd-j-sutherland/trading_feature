# Email Trading Alerts Setup Guide

Your AI trading analysis system now includes real-time email notifications! Here's how to set it up and use it.

## 🚀 Quick Setup

### 1. Configure Email Settings

Edit your `.env` file and update these settings:

```bash
# Replace with your Gmail credentials
EMAIL_ADDRESS=your_gmail@gmail.com
EMAIL_PASSWORD=your_app_password_here
```

**For Gmail users (recommended):**
1. Enable 2-factor authentication on your Gmail account
2. Go to Google Account Settings → Security → App passwords
3. Generate a new App Password for "Mail"
4. Use this App Password in the `.env` file (not your regular password)

### 2. Test Email Configuration

```bash
# Test that emails work
python manage_email_alerts.py test
```

You should receive a test email at `sutho100@gmail.com`.

### 3. Start Real-Time Monitoring

```bash
# Start continuous monitoring
python manage_email_alerts.py start
```

This will:
- Monitor CBA.AX, ANZ.AX, WBC.AX, NAB.AX, MQG.AX every 5 minutes
- Send email alerts when ML indicators detect BUY/SELL signals
- Only send emails during ASX market hours (9:30 AM - 4:00 PM AEST)
- Include 30-minute cooldown between alerts for the same stock

## 📧 What You'll Receive

### Email Alert Content
Each email includes:
- **Stock Details**: Company name, symbol, current price
- **AI Signal**: BUY, SELL, STRONG_BUY, STRONG_SELL with confidence %
- **Analysis**: Pattern detected, target price, support/resistance levels
- **Sentiment**: News sentiment score
- **Reasoning**: Why the AI detected this opportunity

### Alert Triggers
Emails are sent when:
- High confidence (>70%) BUY/SELL signals detected
- Multiple AI indicators agree (pattern analysis + ML predictions + sentiment)
- Significant price movements (>2%) combined with AI signals
- Critical market conditions detected

## 🛠️ Commands

```bash
# Start real-time monitoring
python manage_email_alerts.py start

# Stop monitoring
python manage_email_alerts.py stop

# Send test email
python manage_email_alerts.py test

# Check monitoring status
python manage_email_alerts.py status

# View configuration
python manage_email_alerts.py config
```

## 📊 Integration with Dashboard

The email system automatically integrates with your existing trading dashboard:

1. **Dashboard Alerts**: When the dashboard detects high-confidence signals, emails are sent
2. **ML Scores**: Email alerts include the same ML analysis shown in the dashboard
3. **Pattern Detection**: AI pattern recognition triggers email notifications
4. **Sentiment Analysis**: News sentiment analysis contributes to email alerts

## ⚙️ Customization

### Alert Thresholds
Edit `app/services/real_time_monitor.py` to adjust:
- `confidence_threshold = 0.7` - Minimum confidence for alerts
- `cooldown_period = 1800` - Seconds between alerts (30 minutes)
- `monitoring_interval = 300` - Check frequency (5 minutes)

### Monitored Stocks
Edit the symbols list in `real_time_monitor.py`:
```python
self.symbols = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX']
```

### Email Recipients
Currently hardcoded to `sutho100@gmail.com`. To change, edit:
- `app/services/email_notifier.py` line with `self.recipient_email`

## 🔧 Troubleshooting

### Email Not Sending
1. Check `.env` configuration:
   ```bash
   python manage_email_alerts.py config
   ```
2. Verify Gmail App Password is correct
3. Check internet connection
4. Look at logs: `logs/email_alerts.log`

### No Alerts Received
1. Check if market is open:
   ```bash
   python manage_email_alerts.py status
   ```
2. Verify monitoring is running
3. Check alert cooldown periods
4. Review confidence thresholds (may be too high)

### Common Issues
- **"Authentication failed"**: Wrong App Password or 2FA not enabled
- **"No data available"**: Market data feed issues
- **"Not configured"**: `.env` file not set up correctly

## 📈 Example Email Alert

```
Subject: 🚨 Trading Alert: CBA.AX 🚀 STRONG_BUY at $105.50

Stock: Commonwealth Bank (CBA.AX)
Signal: STRONG_BUY
Current Price: $105.50
Confidence: 87%

Pattern Detected: Bullish Breakout
Target Price: $108.50 (+2.8%)
Support Level: $103.50
Resistance Level: $110.00
Sentiment Score: +0.650

AI Analysis:
Pattern Analysis detected Bullish Breakout with 85% confidence. 
ML Model predicts STRONG_BUY with 87% confidence. 
News sentiment is positive (score: +0.650).
```

## 🔄 Running in Background

### On macOS/Linux:
```bash
# Run in background
nohup python manage_email_alerts.py start > logs/monitoring.log 2>&1 &

# Check if running
ps aux | grep manage_email_alerts

# Stop background process
python manage_email_alerts.py stop
```

### Using Screen (recommended):
```bash
# Start a screen session
screen -S trading_alerts

# Run monitoring
python manage_email_alerts.py start

# Detach (Ctrl+A, then D)
# Reattach later: screen -r trading_alerts
```

## 📱 Mobile Notifications

For mobile push notifications, consider:
1. Forward emails from `sutho100@gmail.com` to your phone
2. Set up Gmail app notifications
3. Use email-to-SMS services if needed

## 🔒 Security Notes

- App Passwords are safer than regular passwords
- Keep your `.env` file private (it's in `.gitignore`)
- Email alerts don't include personal financial information
- All alerts include disclaimer about not being financial advice

## 📞 Support

If you need help:
1. Check logs in `logs/` directory
2. Run `python manage_email_alerts.py config` to verify setup
3. Test with `python manage_email_alerts.py test`

Your email notification system is now ready! You'll receive real-time alerts at `sutho100@gmail.com` whenever the AI detects trading opportunities.

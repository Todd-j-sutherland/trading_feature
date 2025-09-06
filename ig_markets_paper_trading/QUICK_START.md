# Quick Start Guide

## 1. Configure Credentials
Edit `config/ig_markets_config.json` with your IG Markets demo account details:
```json
{
  "api_key": "YOUR_API_KEY",
  "username": "YOUR_DEMO_USERNAME", 
  "password": "YOUR_DEMO_PASSWORD",
  "account_id": "YOUR_DEMO_ACCOUNT_ID"
}
```

## 2. Manual Execution
```bash
cd ig_markets_paper_trading
python3 scripts/run_paper_trader.py
```

## 3. View Performance
```bash
python3 scripts/performance_report.py
```

## 4. Enable Automation
```bash
crontab -e
# Add the lines from crontab_example.txt
```

## 5. Monitor Logs
```bash
tail -f logs/paper_trading.log
```

## 6. Status Check
Check account balance and open positions in the logs or run performance report.

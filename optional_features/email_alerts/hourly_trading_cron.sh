#!/bin/bash
# Cron job script for hourly trading alerts
# Add this to your crontab with: crontab -e
# 0 10-15 * * 1-5 /path/to/your/hourly_trading_cron.sh

# Set working directory to email_alerts folder
cd /Users/toddsutherland/Repos/trading_analysis/email_alerts

# Activate .venv312 virtual environment (from parent directory)
source ../.venv312/bin/activate

# Set environment variables (if needed)
export PYTHONPATH=$PWD:$PYTHONPATH

# Run the hourly check (single run, not continuous)
python3 hourly_trading_alerts.py >> ../logs/hourly_alerts.log 2>&1

# Log completion
echo "$(date): Hourly trading check completed" >> ../logs/hourly_alerts.log

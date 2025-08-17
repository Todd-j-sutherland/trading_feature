#!/usr/bin/env python3
"""
Market Hours Checker and Cron Job Fixer
"""

import subprocess
import sys
from datetime import datetime, time
import pytz

def check_market_hours():
    """Check if Australian market is currently open"""
    # Australian Eastern Time
    aet = pytz.timezone('Australia/Sydney')
    now_aet = datetime.now(aet)
    
    # Market hours: Monday-Friday, 10:00 AM - 4:00 PM AEST/AEDT
    market_open = time(10, 0)  # 10:00 AM
    market_close = time(16, 0)  # 4:00 PM
    
    is_weekday = now_aet.weekday() < 5  # Monday=0, Friday=4
    is_market_hours = market_open <= now_aet.time() <= market_close
    
    print(f"🕐 Current AET Time: {now_aet.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"📅 Is Weekday: {'✅' if is_weekday else '❌'}")
    print(f"⏰ Market Hours (10:00-16:00): {'✅' if is_market_hours else '❌'}")
    print(f"🏦 Market Open: {'✅ YES' if (is_weekday and is_market_hours) else '❌ NO'}")
    
    return is_weekday and is_market_hours

def check_current_cron_jobs():
    """Check current cron jobs"""
    print("\n🔍 CURRENT CRON JOBS")
    print("=" * 40)
    
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for i, line in enumerate(lines, 1):
                if line.strip() and not line.startswith('#'):
                    print(f"{i}. {line}")
                elif line.startswith('#'):
                    print(f"   {line}")
        else:
            print("❌ No cron jobs found or error accessing crontab")
    except Exception as e:
        print(f"❌ Error checking cron jobs: {e}")

def create_market_hours_aware_cron():
    """Create a market-hours-aware cron job"""
    print("\n🔧 CREATING MARKET-HOURS-AWARE CRON JOB")
    print("=" * 50)
    
    # Create a wrapper script that checks market hours
    wrapper_script = '''#!/bin/bash
# Market Hours Aware Trading Script

# Set paths
export PATH="/root/trading_venv/bin:$PATH"
export PYTHONPATH="/root/test"
cd /root/test

# Check if market is open using Python
MARKET_OPEN=$(python3 -c "
import sys
sys.path.append('/root/test')
from datetime import datetime, time
import pytz

aet = pytz.timezone('Australia/Sydney')
now_aet = datetime.now(aet)
market_open = time(10, 0)
market_close = time(16, 0)
is_weekday = now_aet.weekday() < 5
is_market_hours = market_open <= now_aet.time() <= market_close
market_is_open = is_weekday and is_market_hours
print('1' if market_is_open else '0')
")

# Log the check
echo "$(date): Market check - Open: $MARKET_OPEN" >> /root/test/logs/market_hours.log

# Only run if market is open
if [ "$MARKET_OPEN" = "1" ]; then
    echo "$(date): Market is open - running morning routine" >> /root/test/logs/market_hours.log
    source /root/trading_venv/bin/activate
    python -m app.main morning >> /root/test/logs/morning_cron.log 2>&1
else
    echo "$(date): Market is closed - skipping morning routine" >> /root/test/logs/market_hours.log
fi
'''
    
    # Write the wrapper script
    with open('/tmp/market_hours_wrapper.sh', 'w') as f:
        f.write(wrapper_script)
    
    print("✅ Created market hours wrapper script")
    
    # Suggest new cron schedule
    print("\n📋 SUGGESTED NEW CRON SCHEDULE:")
    print("Replace the current every-30-minutes job with:")
    print("# Market Hours Only - Every 30 minutes during trading hours (10-16 Mon-Fri)")
    print("*/30 10-15 * * 1-5 /root/test/market_hours_wrapper.sh")
    print("\n💡 This will only run Monday-Friday, 10:00-15:30 (market hours)")

def main():
    """Main market hours analysis"""
    print("🏦 MARKET HOURS ANALYSIS & CRON FIX")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check if market is currently open
    market_open = check_market_hours()
    
    # Check current cron jobs
    check_current_cron_jobs()
    
    # Create market-hours-aware solution
    create_market_hours_aware_cron()
    
    # Analysis summary
    print(f"\n📊 ANALYSIS SUMMARY")
    print("=" * 30)
    
    if market_open:
        print("✅ Market is currently OPEN - predictions are appropriate")
    else:
        print("❌ Market is currently CLOSED - predictions should be paused")
    
    print("\n🔧 RECOMMENDED ACTIONS:")
    print("1. Replace the every-30-minutes cron job with market-hours-only schedule")
    print("2. Use the market_hours_wrapper.sh script to check market status")
    print("3. Monitor /root/test/logs/market_hours.log for market status checks")
    
    return market_open

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

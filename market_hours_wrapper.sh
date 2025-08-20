#!/bin/bash
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

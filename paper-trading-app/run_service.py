#!/usr/bin/env python3
import os
import sys

# Set working directory and paths
os.chdir('/root/test/paper-trading-app')
sys.path.insert(0, '/root/test/paper-trading-app')

# Override config paths
os.environ['PREDICTIONS_DB_PATH'] = '/root/test/predictions.db'
os.environ['PAPER_TRADING_DB_PATH'] = '/root/test/paper-trading-app/paper_trading.db'

# Import and run the service
from paper_trading_background_service import main
if __name__ == '__main__':
    main()

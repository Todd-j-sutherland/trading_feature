#!/usr/bin/env python3
"""
Main execution script for IG Markets Paper Trading
Run this script to execute a complete trading cycle
"""

import sys
import os
import logging
from datetime import datetime

# Add the parent directory to path to import from src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.paper_trader import PaperTrader

def setup_logging():
    """Setup logging configuration"""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'paper_trading.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main execution function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🎯 IG Markets Paper Trading Service Starting")
    logger.info("=" * 60)
    
    try:
        # Initialize paper trader
        trader = PaperTrader()
        
        # Run trading cycle
        results = trader.run_trading_cycle()
        
        # Print results
        logger.info("📊 Trading Cycle Results:")
        logger.info(f"   New Trades: {results['new_trades']}")
        logger.info(f"   Closed Trades: {results['closed_trades']}")
        logger.info(f"   Open Positions: {results['open_positions']}")
        logger.info(f"   Account Balance: ${results['account_balance']:.2f}")
        logger.info(f"   Available Funds: ${results['available_funds']:.2f}")
        
        if results['errors']:
            logger.warning(f"   Errors: {len(results['errors'])}")
            for error in results['errors']:
                logger.warning(f"     - {error}")
        
        # Get status report
        status = trader.get_status_report()
        
        logger.info("🔍 System Status:")
        logger.info(f"   API Authentication: {'✅' if status['api_status']['authenticated'] else '❌'}")
        logger.info(f"   Exit Strategy: {'✅ Phase4' if status['exit_strategy']['available'] else '⚠️ Simple'}")
        logger.info(f"   Rate Limit Status: {status['api_status']['rate_limit']['requests_remaining']} requests remaining")
        
        logger.info("✅ Paper Trading Service Completed Successfully")
        
    except Exception as e:
        logger.error(f"❌ Paper Trading Service Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Automated Technical Score Updater
This script should be run periodically to keep technical scores current
"""

import schedule
import time
import logging
from datetime import datetime
from technical_analysis_engine import TechnicalAnalysisEngine

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/technical_scores.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def update_technical_scores():
    """
    Update technical scores for all banks
    """
    logger.info("🔧 Starting technical scores update...")
    
    try:
        tech_engine = TechnicalAnalysisEngine()
        success = tech_engine.update_database_technical_scores()
        
        if success:
            logger.info("✅ Technical scores updated successfully")
            
            # Get summary for logging
            summary = tech_engine.get_technical_summary()
            logger.info(f"📊 Analysis Summary: {summary['total_banks_analyzed']} banks analyzed")
            logger.info(f"📊 Signals - BUY: {summary['signals']['BUY']}, HOLD: {summary['signals']['HOLD']}, SELL: {summary['signals']['SELL']}")
            logger.info(f"📊 Average Technical Score: {summary['average_technical_score']}")
            
        else:
            logger.error("❌ Failed to update technical scores")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Error updating technical scores: {e}")
        return False

def run_scheduler():
    """
    Run the scheduler for periodic updates
    """
    # Schedule updates during ASX trading hours
    schedule.every().day.at("09:30").do(update_technical_scores)  # Market open
    schedule.every().day.at("12:00").do(update_technical_scores)  # Midday
    schedule.every().day.at("15:30").do(update_technical_scores)  # Near close
    schedule.every().day.at("17:00").do(update_technical_scores)  # After close
    
    logger.info("📅 Technical score updater scheduled:")
    logger.info("   - 09:30 (Market open)")
    logger.info("   - 12:00 (Midday)")
    logger.info("   - 15:30 (Near close)")
    logger.info("   - 17:00 (After close)")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        # Run once for testing
        print("🔧 Running technical scores update once...")
        success = update_technical_scores()
        sys.exit(0 if success else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "schedule":
        # Run scheduler
        print("📅 Starting technical scores scheduler...")
        run_scheduler()
    else:
        print("Usage:")
        print("  python automated_technical_updater.py once      # Run once")
        print("  python automated_technical_updater.py schedule  # Run scheduler")
        print("  python automated_technical_updater.py           # Show help")

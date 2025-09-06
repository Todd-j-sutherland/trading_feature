#!/usr/bin/env python3
"""
Enhanced Paper Trading Service with IG Markets Integration
Maintains all existing functionality while adding IG Markets real-time data
"""

import os
import sys
import logging

# Set up logging first
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('enhanced_paper_trading_with_ig.log'),
            logging.StreamHandler()
        ]
    )

# Import IG Markets integration
try:
    from enhanced_ig_markets_integration import initialize_ig_markets_integration, get_enhanced_price_source
    IG_INTEGRATION_AVAILABLE = True
    logger.info("✅ IG Markets integration module loaded")
except ImportError as e:
    IG_INTEGRATION_AVAILABLE = False
    logger.warning(f"⚠️ IG Markets integration not available: {e}")

# Import the original enhanced service
from enhanced_paper_trading_service import EnhancedPaperTradingService, main as original_main

class EnhancedPaperTradingServiceWithIG(EnhancedPaperTradingService):
    """
    Enhanced Paper Trading Service with IG Markets integration
    Extends the original service with IG Markets real-time data capabilities
    """
    
    def __init__(self):
        """Initialize service with IG Markets integration"""
        logger.info("🚀 Initializing Enhanced Paper Trading Service with IG Markets...")
        
        # Initialize IG Markets integration first
        self.ig_markets_enabled = False
        if IG_INTEGRATION_AVAILABLE:
            try:
                self.ig_markets_enabled = initialize_ig_markets_integration()
                if self.ig_markets_enabled:
                    logger.info("✅ IG Markets integration initialized successfully")
                    self.enhanced_price_source = get_enhanced_price_source()
                else:
                    logger.warning("⚠️ IG Markets integration failed - using yfinance only")
            except Exception as e:
                logger.error(f"❌ IG Markets initialization error: {e}")
                self.ig_markets_enabled = False
        
        # Initialize parent class
        super().__init__()
        
        # Add IG Markets specific configuration
        if self.ig_markets_enabled:
            self.config.update({
                'ig_markets_enabled': True,
                'data_source_preference': 'ig_markets_first',
                'ig_health_check_interval': 600,  # Check IG Markets health every 10 minutes
            })
        else:
            self.config.update({
                'ig_markets_enabled': False,
                'data_source_preference': 'yfinance_only',
            })
        
        logger.info(f"📊 Data Source Configuration: {self.config.get('data_source_preference')}")

    def get_current_price(self, symbol: str):
        """
        Enhanced get_current_price with IG Markets integration
        Falls back to parent method if IG Markets fails
        """
        if self.ig_markets_enabled and hasattr(self, 'enhanced_price_source'):
            try:
                price = self.enhanced_price_source.get_current_price(symbol)
                if price is not None:
                    return price
            except Exception as e:
                logger.debug(f"IG Markets price fetch failed for {symbol}: {e}")
        
        # Fallback to original method
        return super().get_current_price(symbol)
    
    def get_enhanced_portfolio_summary(self):
        """
        Enhanced portfolio summary including IG Markets statistics
        """
        # Get original summary
        summary = super().get_portfolio_summary()
        
        # Add IG Markets specific information
        if self.ig_markets_enabled and hasattr(self, 'enhanced_price_source'):
            try:
                data_stats = self.enhanced_price_source.get_data_source_stats()
                health_status = self.enhanced_price_source.get_health_status()
                
                summary.update({
                    'ig_markets_enabled': True,
                    'data_source_stats': data_stats,
                    'ig_markets_health': health_status.get('ig_markets_healthy', False),
                    'data_sources_available': {
                        'ig_markets': health_status.get('ig_markets_available', False),
                        'yfinance': health_status.get('yfinance_available', True)
                    }
                })
            except Exception as e:
                logger.error(f"Error getting IG Markets stats: {e}")
                summary.update({
                    'ig_markets_enabled': True,
                    'ig_markets_error': str(e)
                })
        else:
            summary.update({
                'ig_markets_enabled': False,
                'data_source': 'yfinance_only'
            })
        
        return summary
    
    def log_data_source_statistics(self):
        """Log data source usage statistics"""
        if self.ig_markets_enabled and hasattr(self, 'enhanced_price_source'):
            try:
                stats = self.enhanced_price_source.get_data_source_stats()
                health = self.enhanced_price_source.get_health_status()
                
                logger.info("📊 Data Source Statistics:")
                logger.info(f"   IG Markets requests: {stats.get('ig_markets_requests', 0)}")
                logger.info(f"   yfinance requests: {stats.get('yfinance_requests', 0)}")
                logger.info(f"   Cache hits: {stats.get('cache_hits', 0)}")
                logger.info(f"   Total requests: {stats.get('total_requests', 0)}")
                logger.info(f"   IG Markets health: {'✅ Healthy' if health.get('ig_markets_healthy') else '❌ Unhealthy'}")
                
                # Calculate efficiency metrics
                total = stats.get('total_requests', 0)
                if total > 0:
                    ig_percentage = (stats.get('ig_markets_requests', 0) / total) * 100
                    cache_percentage = (stats.get('cache_hits', 0) / total) * 100
                    logger.info(f"   IG Markets usage: {ig_percentage:.1f}%")
                    logger.info(f"   Cache efficiency: {cache_percentage:.1f}%")
            
            except Exception as e:
                logger.error(f"Error logging data source statistics: {e}")

    def run(self):
        """
        Enhanced run method with IG Markets monitoring
        """
        logger.info("🚀 Enhanced Paper Trading Service with IG Markets started!")
        
        if self.ig_markets_enabled:
            logger.info("📈 IG Markets real-time data: ENABLED")
            logger.info("🔄 Fallback to yfinance: ENABLED")
        else:
            logger.info("📊 Using yfinance data only")
        
        # Log initial health status
        if self.ig_markets_enabled:
            self.log_data_source_statistics()
        
        # Add IG Markets health monitoring to the main loop
        last_ig_health_check = 0
        last_stats_log = 0
        
        # Store original running state check
        original_running = self.running
        
        try:
            import time
            
            while self.running:
                current_time = time.time()
                
                # IG Markets health check (every 10 minutes)
                if (self.ig_markets_enabled and 
                    current_time - last_ig_health_check >= self.config.get('ig_health_check_interval', 600)):
                    
                    try:
                        health = self.enhanced_price_source.get_health_status()
                        if not health.get('ig_markets_healthy', False):
                            logger.warning("⚠️ IG Markets health check failed - running on yfinance fallback")
                        else:
                            logger.info("✅ IG Markets health check passed")
                        
                        last_ig_health_check = current_time
                    except Exception as e:
                        logger.error(f"IG Markets health check error: {e}")
                
                # Log statistics every 30 minutes
                if (self.ig_markets_enabled and 
                    current_time - last_stats_log >= 1800):  # 30 minutes
                    
                    self.log_data_source_statistics()
                    last_stats_log = current_time
                
                # Call parent run method logic (we'll break after this iteration)
                # We can't call super().run() directly as it has its own loop
                # Instead, we'll implement the main logic here
                try:
                    from datetime import datetime
                    import pytz
                    from enhanced_paper_trading_service import is_asx_trading_hours, is_position_opening_hours
                    
                    current_datetime = datetime.now()
                    is_market_open = is_asx_trading_hours(datetime.now(pytz.UTC))
                    
                    # Check for configuration updates every 5 minutes
                    if current_time % 300 == 0:
                        self._load_config_from_database()
                    
                    # Sync cache with database every 10 minutes
                    if current_time % 600 == 0:
                        logger.info("🔄 Syncing position cache with database...")
                        self._load_active_positions()
                    
                    # Check active positions every minute (during trading hours only)
                    if self.active_positions:
                        if is_market_open:
                            logger.info(f"🔍 Checking {len(self.active_positions)} active positions...")
                            self.check_position_exits()
                        else:
                            # Less frequent logging during market closed hours
                            if current_time % 600 == 0:  # Every 10 minutes
                                logger.info(f"💤 Market closed - {len(self.active_positions)} positions waiting for market open")
                    
                    # Check for new predictions every 5 minutes (during position opening hours only)
                    if is_position_opening_hours(datetime.now(pytz.UTC)) and current_time % self.config['prediction_check_interval_seconds'] == 0:
                        new_predictions = self.check_for_new_predictions()
                        
                        if new_predictions:
                            logger.info(f"📈 Found {len(new_predictions)} new BUY predictions")
                            for prediction in new_predictions:
                                if self.can_take_position(prediction['symbol']):
                                    self.execute_buy_order(prediction)
                                else:
                                    logger.info(f"⚠️ Skipping {prediction['symbol']} - position already exists")
                        else:
                            logger.info("😴 No new BUY predictions")
                    
                    elif not is_position_opening_hours(datetime.now(pytz.UTC)) and is_asx_trading_hours(datetime.now(pytz.UTC)):
                        # After 3:15 PM but before 4:00 PM - only log occasionally
                        if current_time % 600 == 0:  # Every 10 minutes
                            logger.info("🕐 Position opening hours ended (3:15 PM) - only closing existing positions")
                    
                    # Portfolio summary (less frequent during closed hours)
                    if is_market_open or current_time % 1800 == 0:  # Every 30 minutes when closed
                        summary = self.get_enhanced_portfolio_summary()
                        if summary:
                            logger.info(f"💼 Portfolio: {summary['active_positions']} positions, {summary['total_trades']} trades, ${summary['total_profit']:.2f} profit")
                            
                            # Log IG Markets specific info occasionally
                            if self.ig_markets_enabled and 'data_source_stats' in summary:
                                stats = summary['data_source_stats']
                                logger.info(f"📊 Data Sources: IG Markets {stats.get('ig_markets_requests', 0)}, yfinance {stats.get('yfinance_requests', 0)}")
                    
                    # Wait for next check
                    time.sleep(self.config['check_interval_seconds'])
                
                except KeyboardInterrupt:
                    logger.info("🛑 Service stopped by user")
                    self.running = False
                except Exception as e:
                    logger.error(f"❌ Unexpected error in main loop: {e}")
                    time.sleep(60)  # Wait 1 minute on error
        
        except Exception as e:
            logger.error(f"❌ Fatal error in enhanced service: {e}")
        
        finally:
            # Log final statistics
            if self.ig_markets_enabled:
                logger.info("📊 Final Data Source Statistics:")
                self.log_data_source_statistics()

def main():
    """
    Enhanced main function with IG Markets integration
    """
    # Try to import signal handling from original
    try:
        from enhanced_paper_trading_service import acquire_lock, release_lock, signal_handler
        import signal
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Try to acquire lock
        if not acquire_lock():
            print("❌ Another instance of the service is already running!")
            print("   Only one instance is allowed to prevent database conflicts.")
            return 1
        
        try:
            logger.info("🔒 Lock acquired - starting enhanced service with IG Markets")
            service = EnhancedPaperTradingServiceWithIG()
            service.run()
        except Exception as e:
            logger.error(f"❌ Failed to start enhanced service: {e}")
            return 1
        finally:
            release_lock()
            logger.info("🔓 Lock released")
        
        return 0
        
    except ImportError:
        # Fallback if signal handling not available
        logger.warning("⚠️ Signal handling not available - running without lock protection")
        try:
            service = EnhancedPaperTradingServiceWithIG()
            service.run()
            return 0
        except Exception as e:
            logger.error(f"❌ Failed to start service: {e}")
            return 1

def test_enhanced_service():
    """Test the enhanced service with IG Markets"""
    logger.info("🧪 Testing Enhanced Paper Trading Service with IG Markets...")
    
    try:
        # Create service instance
        service = EnhancedPaperTradingServiceWithIG()
        
        # Test price fetching
        test_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX']
        logger.info("📋 Testing enhanced price fetching:")
        
        for symbol in test_symbols:
            try:
                price = service.get_current_price(symbol)
                if price:
                    logger.info(f"  ✅ {symbol}: ${price:.2f}")
                else:
                    logger.warning(f"  ❌ {symbol}: No price available")
            except Exception as e:
                logger.error(f"  ❌ {symbol}: Error - {e}")
        
        # Test enhanced portfolio summary
        logger.info("📊 Testing enhanced portfolio summary:")
        summary = service.get_enhanced_portfolio_summary()
        logger.info(f"  Portfolio summary keys: {list(summary.keys())}")
        
        # Test data source statistics
        if service.ig_markets_enabled:
            service.log_data_source_statistics()
        
        logger.info("✅ Enhanced service test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced service test failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    # Check for test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_enhanced_service()
    elif len(sys.argv) > 1 and sys.argv[1] == "--test-trading-hours":
        # Import and run trading hours test from original
        from enhanced_paper_trading_service import test_trading_hours
        test_trading_hours()
    else:
        exit(main())

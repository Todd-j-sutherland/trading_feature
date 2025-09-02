#!/usr/bin/env python3
"""
Enhanced Paper Trading Engine with IG Markets Integration
Extends the original trading engine to use IG Markets real-time data
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional

# Add parent directory for IG Markets imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

# Import original trading engine
from trading.engine import PaperTradingEngine as OriginalPaperTradingEngine

# Try to import IG Markets components
try:
    from enhanced_ig_markets_integration import get_enhanced_price_source
    IG_INTEGRATION_AVAILABLE = True
except ImportError:
    IG_INTEGRATION_AVAILABLE = False

class EnhancedPaperTradingEngine(OriginalPaperTradingEngine):
    """
    Enhanced Paper Trading Engine with IG Markets integration
    Maintains full compatibility with original engine while adding IG Markets capability
    """
    
    def __init__(self, session, account_id: int = 1):
        """Initialize enhanced engine with IG Markets support"""
        super().__init__(session, account_id)
        
        # Initialize IG Markets integration
        self.ig_markets_enabled = False
        self.enhanced_price_source = None
        
        if IG_INTEGRATION_AVAILABLE:
            try:
                self.enhanced_price_source = get_enhanced_price_source()
                self.ig_markets_enabled = True
                self.logger.info("✅ IG Markets integration enabled for trading engine")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to initialize IG Markets: {e}")
                self.ig_markets_enabled = False
        else:
            self.logger.info("📊 Trading engine using yfinance only")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Enhanced get_current_price with IG Markets integration
        Falls back to original yfinance method if IG Markets fails
        """
        # Try IG Markets first if available
        if self.ig_markets_enabled and self.enhanced_price_source:
            try:
                price = self.enhanced_price_source.get_current_price(symbol)
                if price is not None:
                    self.logger.debug(f"📈 IG Markets price for {symbol}: ${price:.2f}")
                    return price
            except Exception as e:
                self.logger.debug(f"IG Markets price fetch failed for {symbol}: {e}")
        
        # Fallback to original yfinance method
        try:
            price = super().get_current_price(symbol)
            if price is not None:
                self.logger.debug(f"📊 yfinance price for {symbol}: ${price:.2f}")
            return price
        except Exception as e:
            self.logger.error(f"Both IG Markets and yfinance failed for {symbol}: {e}")
            return None
    
    def get_data_source_stats(self):
        """Get statistics about data source usage"""
        if self.ig_markets_enabled and self.enhanced_price_source:
            return self.enhanced_price_source.get_data_source_stats()
        else:
            return {
                'ig_markets_requests': 0,
                'yfinance_requests': 'unknown',
                'cache_hits': len(self.price_cache),
                'total_requests': 'unknown',
                'source': 'yfinance_only'
            }
    
    def get_price_source_health(self):
        """Get health status of all price sources"""
        if self.ig_markets_enabled and self.enhanced_price_source:
            return self.enhanced_price_source.get_health_status()
        else:
            return {
                'ig_markets_available': False,
                'ig_markets_healthy': False,
                'yfinance_available': True,
                'cache_size': len(self.price_cache),
                'integration_status': 'yfinance_only'
            }
    
    def update_portfolio_values(self):
        """
        Enhanced portfolio value update with improved price fetching
        """
        try:
            # Log data source statistics occasionally
            if hasattr(self, '_last_stats_log'):
                time_since_last = datetime.now() - self._last_stats_log
                if time_since_last.total_seconds() > 1800:  # 30 minutes
                    self._log_data_source_stats()
            else:
                self._last_stats_log = datetime.now()
            
            # Call parent method for actual portfolio update
            super().update_portfolio_values()
            
        except Exception as e:
            self.logger.error(f"Error in enhanced portfolio update: {e}")
            # Still try the parent method as fallback
            try:
                super().update_portfolio_values()
            except Exception as e2:
                self.logger.error(f"Fallback portfolio update also failed: {e2}")
    
    def _log_data_source_stats(self):
        """Log data source usage statistics"""
        try:
            stats = self.get_data_source_stats()
            health = self.get_price_source_health()
            
            self.logger.info("📊 Trading Engine Data Source Stats:")
            self.logger.info(f"   IG Markets requests: {stats.get('ig_markets_requests', 0)}")
            self.logger.info(f"   yfinance requests: {stats.get('yfinance_requests', 'unknown')}")
            self.logger.info(f"   Cache hits: {stats.get('cache_hits', 0)}")
            self.logger.info(f"   IG Markets health: {'✅' if health.get('ig_markets_healthy') else '❌'}")
            
            self._last_stats_log = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error logging data source stats: {e}")

def patch_original_engine():
    """
    Monkey patch the original PaperTradingEngine to use IG Markets
    This allows existing code to automatically use IG Markets without changes
    """
    try:
        import trading.engine as engine_module
        
        # Store the original class
        original_class = engine_module.PaperTradingEngine
        
        # Replace with enhanced version
        engine_module.PaperTradingEngine = EnhancedPaperTradingEngine
        
        logging.info("✅ Original PaperTradingEngine patched with IG Markets integration")
        return True
        
    except Exception as e:
        logging.error(f"❌ Failed to patch original trading engine: {e}")
        return False

def initialize_enhanced_trading_engine():
    """
    Initialize the enhanced trading engine with IG Markets integration
    """
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Initializing Enhanced Trading Engine with IG Markets...")
    
    try:
        # Apply the monkey patch
        success = patch_original_engine()
        
        if success:
            logger.info("✅ Enhanced Trading Engine initialization complete")
            logger.info("💡 All paper trading components will now use IG Markets data")
            return True
        else:
            logger.warning("⚠️ Enhanced Trading Engine initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize enhanced trading engine: {e}")
        return False

def test_enhanced_trading_engine():
    """
    Test the enhanced trading engine with IG Markets integration
    """
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Testing Enhanced Trading Engine...")
    
    try:
        # Initialize enhanced engine
        success = initialize_enhanced_trading_engine()
        if not success:
            logger.error("❌ Enhanced engine initialization failed")
            return False
        
        # Test with a mock session (for testing purposes)
        class MockSession:
            def query(self, *args):
                return self
            def filter_by(self, *args, **kwargs):
                return self
            def first(self):
                return None
        
        # Create enhanced engine instance
        mock_session = MockSession()
        engine = EnhancedPaperTradingEngine(mock_session)
        
        # Test price fetching
        test_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX']
        logger.info("📋 Testing enhanced price fetching:")
        
        for symbol in test_symbols:
            try:
                price = engine.get_current_price(symbol)
                if price:
                    logger.info(f"  ✅ {symbol}: ${price:.2f}")
                else:
                    logger.warning(f"  ❌ {symbol}: No price available")
            except Exception as e:
                logger.error(f"  ❌ {symbol}: Error - {e}")
        
        # Test statistics
        stats = engine.get_data_source_stats()
        health = engine.get_price_source_health()
        
        logger.info(f"📊 Data Source Stats: {stats}")
        logger.info(f"🏥 Health Status: {health}")
        
        logger.info("✅ Enhanced Trading Engine test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced Trading Engine test failed: {e}")
        return False

if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run the test
    test_enhanced_trading_engine()

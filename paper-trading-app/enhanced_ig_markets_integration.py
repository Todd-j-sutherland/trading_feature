#!/usr/bin/env python3
"""
Enhanced IG Markets Integration for Paper Trading App
Adds IG Markets real-time data support while maintaining all existing functionality
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import time

# Add the parent directory to path for IG Markets imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from app.core.data.collectors.enhanced_market_data_collector import EnhancedMarketDataCollector
    from app.core.data.collectors.ig_markets_symbol_mapper import IGMarketsSymbolMapper
    IG_MARKETS_AVAILABLE = True
except ImportError as e:
    IG_MARKETS_AVAILABLE = False
    logging.warning(f"IG Markets components not available: {e}")
    logging.info("Paper trading will use yfinance only")

class EnhancedPaperTradingPriceSource:
    """
    Enhanced price source that integrates IG Markets with existing paper trading system
    Maintains full compatibility with existing code while adding IG Markets capability
    """
    
    def __init__(self):
        """Initialize enhanced price source with IG Markets integration"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize IG Markets components if available
        self.ig_markets_collector = None
        self.symbol_mapper = None
        
        if IG_MARKETS_AVAILABLE:
            try:
                self.ig_markets_collector = EnhancedMarketDataCollector()
                self.symbol_mapper = IGMarketsSymbolMapper()
                self.logger.info("✅ IG Markets integration initialized successfully")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to initialize IG Markets: {e}")
                self.ig_markets_collector = None
                self.symbol_mapper = None
        
        # Fallback to yfinance
        self.use_yfinance_fallback = True
        
        # Cache for price data (maintain existing cache structure)
        self.price_cache = {}
        self.cache_expiry = {}
        
        # Statistics tracking
        self.stats = {
            'ig_markets_requests': 0,
            'yfinance_requests': 0,
            'cache_hits': 0,
            'total_requests': 0
        }
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price with IG Markets integration
        Maintains exact same interface as original get_current_price method
        """
        self.stats['total_requests'] += 1
        
        try:
            # Check cache first (5-minute expiry - same as original)
            now = datetime.now()
            if (symbol in self.price_cache and 
                symbol in self.cache_expiry and 
                now < self.cache_expiry[symbol]):
                self.stats['cache_hits'] += 1
                return self.price_cache[symbol]
            
            # Try IG Markets first (if available)
            if self.ig_markets_collector and self.symbol_mapper:
                try:
                    price_data = self.ig_markets_collector.get_current_price(symbol)
                    if price_data and price_data.get('price'):
                        price = float(price_data['price'])
                        if price > 0:
                            self.stats['ig_markets_requests'] += 1
                            # Cache the price (same caching logic as original)
                            self.price_cache[symbol] = price
                            self.cache_expiry[symbol] = now + timedelta(minutes=5)
                            
                            self.logger.debug(f"📈 IG Markets price for {symbol}: ${price:.2f}")
                            return price
                except Exception as e:
                    self.logger.debug(f"IG Markets price fetch failed for {symbol}: {e}")
            
            # Fallback to yfinance (original implementation)
            if self.use_yfinance_fallback:
                return self._get_yfinance_price(symbol)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def _get_yfinance_price(self, symbol: str) -> Optional[float]:
        """
        Original yfinance price fetching logic (unchanged)
        """
        try:
            import yfinance as yf
            
            self.stats['yfinance_requests'] += 1
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try different price sources (original logic)
            price = None
            if 'currentPrice' in info:
                price = info['currentPrice']
            elif 'regularMarketPrice' in info:
                price = info['regularMarketPrice']
            elif 'previousClose' in info:
                price = info['previousClose']
                self.logger.warning(f"Using previous close for {symbol}")
            
            if price and price > 0:
                # Cache the price
                now = datetime.now()
                self.price_cache[symbol] = price
                self.cache_expiry[symbol] = now + timedelta(minutes=5)
                self.logger.debug(f"📊 yfinance price for {symbol}: ${price:.2f}")
                return price
            
            # Fallback to recent data (original logic)
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                now = datetime.now()
                self.price_cache[symbol] = price
                self.cache_expiry[symbol] = now + timedelta(minutes=5)
                return price
                
        except Exception as e:
            self.logger.error(f"Error fetching yfinance price for {symbol}: {e}")
        
        return None
    
    def get_data_source_stats(self) -> Dict:
        """Get statistics about data source usage"""
        return self.stats.copy()
    
    def is_ig_markets_healthy(self) -> bool:
        """Check if IG Markets is available and healthy"""
        if not self.ig_markets_collector:
            return False
        
        try:
            return self.ig_markets_collector.is_ig_markets_healthy()
        except Exception:
            return False
    
    def get_health_status(self) -> Dict:
        """Get comprehensive health status of all data sources"""
        return {
            'ig_markets_available': IG_MARKETS_AVAILABLE,
            'ig_markets_healthy': self.is_ig_markets_healthy(),
            'yfinance_available': True,  # Always available as fallback
            'cache_size': len(self.price_cache),
            'stats': self.get_data_source_stats()
        }

# Global enhanced price source instance
_enhanced_price_source = None

def get_enhanced_price_source() -> EnhancedPaperTradingPriceSource:
    """Get singleton instance of enhanced price source"""
    global _enhanced_price_source
    if _enhanced_price_source is None:
        _enhanced_price_source = EnhancedPaperTradingPriceSource()
    return _enhanced_price_source

def patch_trading_engine():
    """
    Monkey patch the trading engine to use IG Markets integration
    This maintains full compatibility with existing code
    """
    try:
        # Import the trading engine
        from trading.engine import PaperTradingEngine
        
        # Store original method
        original_get_current_price = PaperTradingEngine.get_current_price
        
        def enhanced_get_current_price(self, symbol: str) -> Optional[float]:
            """Enhanced get_current_price method with IG Markets integration"""
            enhanced_source = get_enhanced_price_source()
            price = enhanced_source.get_current_price(symbol)
            
            # If enhanced source fails, fall back to original method
            if price is None:
                try:
                    return original_get_current_price(self, symbol)
                except Exception as e:
                    logging.error(f"Both enhanced and original price sources failed for {symbol}: {e}")
                    return None
            
            return price
        
        # Apply the patch
        PaperTradingEngine.get_current_price = enhanced_get_current_price
        
        # Add new methods to the engine
        def get_data_source_stats(self) -> Dict:
            """Get data source statistics"""
            enhanced_source = get_enhanced_price_source()
            return enhanced_source.get_data_source_stats()
        
        def get_price_source_health(self) -> Dict:
            """Get price source health status"""
            enhanced_source = get_enhanced_price_source()
            return enhanced_source.get_health_status()
        
        PaperTradingEngine.get_data_source_stats = get_data_source_stats
        PaperTradingEngine.get_price_source_health = get_price_source_health
        
        logging.info("✅ Trading engine patched with IG Markets integration")
        return True
        
    except Exception as e:
        logging.error(f"❌ Failed to patch trading engine: {e}")
        return False

def patch_enhanced_service():
    """
    Patch the enhanced paper trading service to use IG Markets
    """
    try:
        # We'll patch the service's get_current_price method too
        import enhanced_paper_trading_service
        
        # Store original method
        original_get_current_price = enhanced_paper_trading_service.EnhancedPaperTradingService.get_current_price
        
        def enhanced_get_current_price(self, symbol: str) -> Optional[float]:
            """Enhanced get_current_price method with IG Markets integration"""
            enhanced_source = get_enhanced_price_source()
            price = enhanced_source.get_current_price(symbol)
            
            # If enhanced source fails, fall back to original method
            if price is None:
                try:
                    return original_get_current_price(self, symbol)
                except Exception as e:
                    self.logger.error(f"Both enhanced and original price sources failed for {symbol}: {e}")
                    return None
            
            return price
        
        # Apply the patch
        enhanced_paper_trading_service.EnhancedPaperTradingService.get_current_price = enhanced_get_current_price
        
        # Add new methods to track data sources
        def get_data_source_stats(self) -> Dict:
            """Get data source statistics"""
            enhanced_source = get_enhanced_price_source()
            return enhanced_source.get_data_source_stats()
        
        def get_price_source_health(self) -> Dict:
            """Get price source health status"""
            enhanced_source = get_enhanced_price_source()
            return enhanced_source.get_health_status()
        
        enhanced_paper_trading_service.EnhancedPaperTradingService.get_data_source_stats = get_data_source_stats
        enhanced_paper_trading_service.EnhancedPaperTradingService.get_price_source_health = get_price_source_health
        
        logging.info("✅ Enhanced paper trading service patched with IG Markets integration")
        return True
        
    except Exception as e:
        logging.error(f"❌ Failed to patch enhanced service: {e}")
        return False

def initialize_ig_markets_integration():
    """
    Initialize IG Markets integration for paper trading
    Call this at the start of your paper trading application
    """
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Initializing IG Markets integration for Paper Trading...")
    
    if not IG_MARKETS_AVAILABLE:
        logger.warning("⚠️ IG Markets components not available - using yfinance only")
        return False
    
    try:
        # Initialize the enhanced price source
        enhanced_source = get_enhanced_price_source()
        
        # Test the integration
        health_status = enhanced_source.get_health_status()
        logger.info(f"📊 IG Markets Health: {health_status}")
        
        # Apply patches to existing components
        engine_patched = patch_trading_engine()
        service_patched = patch_enhanced_service()
        
        if engine_patched and service_patched:
            logger.info("✅ IG Markets integration fully initialized")
            logger.info("💡 Paper trading will now use IG Markets as primary data source with yfinance fallback")
            return True
        else:
            logger.warning("⚠️ Partial IG Markets integration - some components may not be patched")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize IG Markets integration: {e}")
        return False

def test_ig_markets_integration():
    """
    Test IG Markets integration with paper trading components
    """
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Testing IG Markets Paper Trading Integration...")
    
    try:
        # Initialize integration
        success = initialize_ig_markets_integration()
        if not success:
            logger.error("❌ Integration initialization failed")
            return False
        
        # Test price fetching
        test_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX']
        enhanced_source = get_enhanced_price_source()
        
        logger.info("📋 Testing price fetching:")
        for symbol in test_symbols:
            try:
                price = enhanced_source.get_current_price(symbol)
                if price:
                    logger.info(f"  ✅ {symbol}: ${price:.2f}")
                else:
                    logger.warning(f"  ❌ {symbol}: No price available")
            except Exception as e:
                logger.error(f"  ❌ {symbol}: Error - {e}")
        
        # Show statistics
        stats = enhanced_source.get_data_source_stats()
        logger.info(f"📊 Data Source Stats: {stats}")
        
        # Test health status
        health = enhanced_source.get_health_status()
        logger.info(f"🏥 Health Status: {health}")
        
        logger.info("✅ IG Markets Paper Trading integration test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run the test
    test_ig_markets_integration()

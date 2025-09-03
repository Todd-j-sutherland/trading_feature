#!/usr/bin/env python3
"""
Enhanced Market Data Collector with IG Markets Integration
Primary data source: IG Markets -> yfinance fallback
Handles ASX symbol mapping and real-time price fetching
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.config.settings import Settings
from app.core.data.collectors.ig_markets_symbol_mapper import IGMarketsSymbolMapper

# Try to import IG Markets components
try:
    from real_time_price_fetcher import RealTimePriceFetcher
    IG_MARKETS_AVAILABLE = True
except ImportError:
    IG_MARKETS_AVAILABLE = False

# Fallback to yfinance
import yfinance as yf

logger = logging.getLogger(__name__)

class EnhancedMarketDataCollector:
    """
    Enhanced market data collector with IG Markets integration
    Provides real-time ASX data with intelligent fallback
    """
    
    def __init__(self):
        self.settings = Settings()
        self.symbol_mapper = IGMarketsSymbolMapper()
        
        # Initialize IG Markets price fetcher if available
        if IG_MARKETS_AVAILABLE:
            try:
                self.ig_price_fetcher = RealTimePriceFetcher()
                self.ig_available = True
                logger.info("✅ IG Markets integration enabled")
            except Exception as e:
                self.ig_price_fetcher = None
                self.ig_available = False
                logger.warning(f"IG Markets initialization failed: {e}")
        else:
            self.ig_price_fetcher = None
            self.ig_available = False
            logger.info("IG Markets integration not available - using yfinance only")
        
        # Cache for price data
        self.price_cache = {}
        self.cache_duration = 30  # 30 seconds
        
        # Track data source usage
        self.source_stats = {
            'ig_markets': 0,
            'yfinance': 0,
            'cache_hits': 0,
            'errors': 0
        }
    
    def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price for a symbol with comprehensive data
        Returns dict with price, source info, and metadata
        """
        # Normalize symbol
        normalized_symbol = self._normalize_symbol(symbol)
        
        # Check cache first
        cached_data = self._get_cached_price(normalized_symbol)
        if cached_data:
            self.source_stats['cache_hits'] += 1
            return cached_data
        
        # Try IG Markets first for ASX symbols
        if self.ig_available and self._is_asx_symbol(normalized_symbol):
            ig_data = self._get_ig_markets_price(normalized_symbol)
            if ig_data:
                self._cache_price(normalized_symbol, ig_data)
                return ig_data
        
        # Fallback to yfinance
        yf_data = self._get_yfinance_price(normalized_symbol)
        if yf_data:
            self._cache_price(normalized_symbol, yf_data)
            return yf_data
        
        # No data available
        self.source_stats['errors'] += 1
        logger.error(f"Could not get price data for {symbol}")
        return self._create_error_response(normalized_symbol, "No data source available")
    
    def get_current_prices_batch(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get current prices for multiple symbols efficiently
        """
        results = {}
        
        for symbol in symbols:
            try:
                price_data = self.get_current_price(symbol)
                results[symbol] = price_data
            except Exception as e:
                logger.error(f"Error getting price for {symbol}: {e}")
                results[symbol] = self._create_error_response(symbol, str(e))
        
        return results
    
    def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Get historical data for a symbol
        Currently uses yfinance - could be enhanced with IG Markets historical data
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            ticker = yf.Ticker(normalized_symbol)
            data = ticker.history(period=period)
            
            if not data.empty:
                # Add symbol column for identification
                data['Symbol'] = normalized_symbol
                return data
            else:
                logger.warning(f"No historical data found for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive market information for a symbol
        """
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            
            # Get current price data
            price_data = self.get_current_price(normalized_symbol)
            
            # Get additional info from yfinance
            ticker = yf.Ticker(normalized_symbol)
            info = ticker.info
            
            # Combine data
            market_info = {
                'symbol': normalized_symbol,
                'company_name': self.symbol_mapper.get_company_name(normalized_symbol) or info.get('longName', 'Unknown'),
                'current_price': price_data.get('price', 0),
                'currency': info.get('currency', 'AUD'),
                'market_cap': info.get('marketCap', 0),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                'day_high': info.get('dayHigh', 0),
                'day_low': info.get('dayLow', 0),
                'previous_close': info.get('previousClose', 0),
                'open': info.get('open', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'data_source': price_data.get('source', 'Unknown'),
                'data_delay_minutes': price_data.get('delay_minutes', 0),
                'last_updated': datetime.now().isoformat(),
                'ig_markets_mapped': self.symbol_mapper.is_mapped(normalized_symbol)
            }
            
            return market_info
            
        except Exception as e:
            logger.error(f"Error getting market info for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def _get_ig_markets_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get price from IG Markets with error handling"""
        try:
            # Convert to base symbol for IG Markets lookup
            base_symbol = symbol.replace('.AX', '')
            
            # Get price data from IG Markets
            price_data = self.ig_price_fetcher.get_current_price(base_symbol)
            
            if price_data:
                price, source_info, delay_minutes = price_data
                
                self.source_stats['ig_markets'] += 1
                
                return {
                    'symbol': symbol,
                    'price': float(price),
                    'source': f"IG Markets - {source_info}",
                    'delay_minutes': delay_minutes,
                    'data_quality': 'real-time' if delay_minutes == 0 else 'delayed',
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }
            
            return None
            
        except Exception as e:
            logger.error(f"IG Markets error for {symbol}: {e}")
            return None
    
    def _get_yfinance_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get price from yfinance with error handling"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try multiple price fields
            price = (info.get('currentPrice') or 
                    info.get('regularMarketPrice') or 
                    info.get('previousClose'))
            
            if price and price > 0:
                self.source_stats['yfinance'] += 1
                
                # Calculate estimated delay
                market_time = info.get('regularMarketTime')
                if market_time:
                    delay_minutes = max(0, int((time.time() - market_time) / 60))
                else:
                    delay_minutes = 900  # Assume 15 hours if no timestamp
                
                return {
                    'symbol': symbol,
                    'price': float(price),
                    'source': f"yfinance ({'real-time' if delay_minutes < 60 else 'delayed'})",
                    'delay_minutes': delay_minutes,
                    'data_quality': 'real-time' if delay_minutes < 60 else 'delayed',
                    'timestamp': datetime.now().isoformat(),
                    'volume': info.get('volume', 0),
                    'day_high': info.get('dayHigh', 0),
                    'day_low': info.get('dayLow', 0),
                    'previous_close': info.get('previousClose', 0),
                    'success': True
                }
            
            return None
            
        except Exception as e:
            logger.error(f"yfinance error for {symbol}: {e}")
            return None
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for consistent processing"""
        symbol = symbol.upper().strip()
        
        # Add .AX suffix for ASX symbols if not present
        if not symbol.endswith('.AX') and self._looks_like_asx_symbol(symbol):
            return f"{symbol}.AX"
        
        return symbol
    
    def _looks_like_asx_symbol(self, symbol: str) -> bool:
        """Check if symbol looks like an ASX symbol"""
        # ASX symbols are typically 3-4 characters
        if len(symbol) >= 2 and len(symbol) <= 4 and symbol.isalpha():
            return True
        return False
    
    def _is_asx_symbol(self, symbol: str) -> bool:
        """Check if symbol is an ASX symbol"""
        return symbol.endswith('.AX') or symbol in self.settings.BANK_SYMBOLS
    
    def _get_cached_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached price data if still valid"""
        if symbol in self.price_cache:
            data, timestamp = self.price_cache[symbol]
            if time.time() - timestamp < self.cache_duration:
                return data
        return None
    
    def _cache_price(self, symbol: str, price_data: Dict[str, Any]):
        """Cache price data with timestamp"""
        self.price_cache[symbol] = (price_data, time.time())
    
    def _create_error_response(self, symbol: str, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'symbol': symbol,
            'price': 0.0,
            'source': 'error',
            'delay_minutes': 0,
            'data_quality': 'error',
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'error': error_message
        }
    
    def get_source_statistics(self) -> Dict[str, Any]:
        """Get data source usage statistics"""
        total_requests = sum(self.source_stats.values())
        
        stats = self.source_stats.copy()
        
        if total_requests > 0:
            stats['ig_markets_percentage'] = (stats['ig_markets'] / total_requests) * 100
            stats['yfinance_percentage'] = (stats['yfinance'] / total_requests) * 100
            stats['cache_hit_rate'] = (stats['cache_hits'] / total_requests) * 100
            stats['error_rate'] = (stats['errors'] / total_requests) * 100
        
        stats['total_requests'] = total_requests
        stats['ig_markets_available'] = self.ig_available
        stats['symbol_mappings'] = self.symbol_mapper.get_mapping_stats()
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on data sources"""
        health_status = {
            'overall_status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # Test IG Markets
        if self.ig_available:
            try:
                test_data = self._get_ig_markets_price('WBC.AX')
                health_status['checks']['ig_markets'] = {
                    'status': 'healthy' if test_data and test_data.get('success') else 'unhealthy',
                    'last_test': datetime.now().isoformat(),
                    'error': None if test_data and test_data.get('success') else 'No valid response'
                }
            except Exception as e:
                health_status['checks']['ig_markets'] = {
                    'status': 'unhealthy',
                    'last_test': datetime.now().isoformat(),
                    'error': str(e)
                }
        else:
            health_status['checks']['ig_markets'] = {
                'status': 'unavailable',
                'last_test': datetime.now().isoformat(),
                'error': 'IG Markets not configured'
            }
        
        # Test yfinance
        try:
            test_data = self._get_yfinance_price('WBC.AX')
            health_status['checks']['yfinance'] = {
                'status': 'healthy' if test_data and test_data.get('success') else 'unhealthy',
                'last_test': datetime.now().isoformat(),
                'error': None if test_data and test_data.get('success') else 'No valid response'
            }
        except Exception as e:
            health_status['checks']['yfinance'] = {
                'status': 'unhealthy',
                'last_test': datetime.now().isoformat(),
                'error': str(e)
            }
        
        # Determine overall status
        check_statuses = [check['status'] for check in health_status['checks'].values()]
        if any(status == 'healthy' for status in check_statuses):
            health_status['overall_status'] = 'healthy'
        elif any(status == 'unhealthy' for status in check_statuses):
            health_status['overall_status'] = 'degraded'
        else:
            health_status['overall_status'] = 'unhealthy'
        
        return health_status

# Global instance for use throughout the application
market_data_collector = EnhancedMarketDataCollector()

# Convenience functions for easy import
def get_current_price(symbol: str) -> Dict[str, Any]:
    """Get current price data for a symbol"""
    return market_data_collector.get_current_price(symbol)

def get_current_prices(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """Get current prices for multiple symbols"""
    return market_data_collector.get_current_prices_batch(symbols)

def get_market_info(symbol: str) -> Dict[str, Any]:
    """Get comprehensive market information"""
    return market_data_collector.get_market_info(symbol)

def get_data_source_stats() -> Dict[str, Any]:
    """Get data source statistics"""
    return market_data_collector.get_source_statistics()

if __name__ == "__main__":
    # Test the enhanced market data collector
    logging.basicConfig(level=logging.INFO)
    
    collector = EnhancedMarketDataCollector()
    
    print("Enhanced Market Data Collector Test")
    print("=" * 50)
    
    # Test individual symbols
    test_symbols = ['WBC.AX', 'CBA', 'ANZ.AX', 'NAB', 'BHP']
    
    for symbol in test_symbols:
        print(f"\nTesting {symbol}:")
        price_data = collector.get_current_price(symbol)
        
        if price_data.get('success'):
            print(f"  ✅ Price: ${price_data['price']:.2f}")
            print(f"  📊 Source: {price_data['source']}")
            print(f"  ⏱️ Delay: {price_data['delay_minutes']} minutes")
            print(f"  🔄 Quality: {price_data['data_quality']}")
        else:
            print(f"  ❌ Error: {price_data.get('error', 'Unknown error')}")
    
    # Test batch processing
    print(f"\n" + "=" * 50)
    print("Batch Processing Test")
    
    batch_results = collector.get_current_prices_batch(['WBC.AX', 'CBA.AX', 'ANZ.AX'])
    success_count = sum(1 for data in batch_results.values() if data.get('success'))
    print(f"  📊 Batch results: {success_count}/{len(batch_results)} successful")
    
    # Show statistics
    stats = collector.get_source_statistics()
    print(f"\n" + "=" * 50)
    print("Data Source Statistics")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  IG Markets: {stats['ig_markets']} ({stats.get('ig_markets_percentage', 0):.1f}%)")
    print(f"  yfinance: {stats['yfinance']} ({stats.get('yfinance_percentage', 0):.1f}%)")
    print(f"  Cache hits: {stats['cache_hits']} ({stats.get('cache_hit_rate', 0):.1f}%)")
    print(f"  Errors: {stats['errors']} ({stats.get('error_rate', 0):.1f}%)")
    
    # Health check
    health = collector.health_check()
    print(f"\n" + "=" * 50)
    print("Health Check")
    print(f"  Overall status: {health['overall_status']}")
    for source, check in health['checks'].items():
        status_emoji = "✅" if check['status'] == 'healthy' else "⚠️" if check['status'] == 'degraded' else "❌"
        print(f"  {status_emoji} {source}: {check['status']}")
        if check['error']:
            print(f"    Error: {check['error']}")

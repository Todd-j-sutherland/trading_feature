#!/usr/bin/env python3
"""
Enhanced Price Fetching Module
"""


import yfinance as yf
import time
import random
from typing import Optional

def get_current_price_robust(symbol: str, max_retries: int = 3, delay_between_retries: float = 1.0) -> Optional[float]:
    """
    Enhanced price fetching with multiple methods, retries, and fallbacks
    
    Args:
        symbol: Stock symbol (e.g., 'CBA.AX')
        max_retries: Maximum number of retry attempts
        delay_between_retries: Delay between retries in seconds
        
    Returns:
        Current price as float, or None if all methods fail
    """
    
    def method_history(ticker) -> Optional[float]:
        """Method 1: Historical data (fastest and most reliable)"""
        try:
            hist = ticker.history(period='1d')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
        except Exception:
            pass
        return None
    
    def method_info(ticker) -> Optional[float]:
        """Method 2: Ticker info (comprehensive but slower)"""
        try:
            info = ticker.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            if price and price > 0:
                return float(price)
        except Exception:
            pass
        return None
    
    def method_fast_info(ticker) -> Optional[float]:
        """Method 3: Fast info (alternative approach)"""
        try:
            fast_info = ticker.fast_info
            if hasattr(fast_info, 'last_price') and fast_info.last_price > 0:
                return float(fast_info.last_price)
        except Exception:
            pass
        return None
    
    # Prioritized methods (fastest first)
    methods = [method_history, method_info, method_fast_info]
    
    for attempt in range(max_retries):
        try:
            # Add small random delay to avoid rate limiting
            if attempt > 0:
                time.sleep(delay_between_retries + random.uniform(0, 0.5))
            
            ticker = yf.Ticker(symbol)
            
            # Try each method in order
            for i, method in enumerate(methods):
                try:
                    price = method(ticker)
                    if price and price > 0:
                        if attempt > 0 or i > 0:
                            print(f"💰 {symbol}: Got price ${price:.2f} (attempt {attempt+1}, method {i+1})")
                        return price
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        print(f"⚠️ {symbol}: Method {i+1} failed: {str(e)[:50]}")
                    continue
            
            # If we get here, all methods failed for this attempt
            if attempt < max_retries - 1:
                print(f"⚠️ {symbol}: All methods failed, attempt {attempt+1}/{max_retries}")
            
        except Exception as e:
            print(f"❌ {symbol}: Ticker creation failed (attempt {attempt+1}): {str(e)[:50]}")
    
    # All attempts exhausted
    print(f"🚨 {symbol}: ALL PRICE FETCHING ATTEMPTS FAILED!")
    return None

# Example usage in morning analyzer:
# entry_price = get_current_price_robust(symbol, max_retries=3, delay_between_retries=1.0) or 0.0

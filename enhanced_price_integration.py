#!/usr/bin/env python3

# Read the current file
with open('enhanced_morning_analyzer_with_ml.py', 'r') as f:
    content = f.read()

# Define the enhanced method to insert
enhanced_method = '''    def _get_current_price_robust(self, symbol):
        """
        Enhanced price fetching with multiple methods and retries
        """
        import time
        import random
        
        methods = [
            ('history', lambda t: t.history(period='1d').iloc[-1]['Close'] if len(t.history(period='1d')) > 0 else None),
            ('info', lambda t: t.info.get('currentPrice') or t.info.get('regularMarketPrice')),
            ('fast_info', lambda t: getattr(t.fast_info, 'last_price', None))
        ]
        
        for method_name, method_func in methods:
            for attempt in range(3):  # 3 attempts per method
                try:
                    ticker = yf.Ticker(symbol)
                    price = method_func(ticker)
                    
                    if price and price > 0:
                        self.logger.info(f"💰 {symbol}: Got price using {method_name} method (attempt {attempt+1}) = ${price:.2f}")
                        return float(price)
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ {symbol}: {method_name} method attempt {attempt+1} failed: {e}")
                    if attempt < 2:  # Wait before retry (except last attempt)
                        time.sleep(random.uniform(1, 3))
                    continue
                    
        self.logger.error(f"🚨 {symbol}: ALL ENHANCED PRICE METHODS FAILED")
        return None

'''

# Insert the enhanced method before _get_model_performance_summary
insertion_point = content.find('    def _get_model_performance_summary(self) -> Dict:')
if insertion_point != -1:
    new_content = content[:insertion_point] + enhanced_method + '\n' + content[insertion_point:]
    
    # Now replace the price fetching section (lines 664-703)
    old_price_logic = '''                # Get current price with improved fallback logic
                entry_price = 0.0
                
                # First attempt: Get from technical analysis
                for tech_symbol, tech_data in analysis_results.get('technical_signals', {}).items():
                    if tech_symbol == symbol:
                        entry_price = float(tech_data.get("current_price", 0.0))
                        if entry_price > 0:
                            self.logger.info(f"💰 {symbol}: Got price from technical analysis = ${entry_price:.2f}")
                        break
                
                # Second attempt: Try yfinance if technical analysis failed
                if entry_price == 0.0:
                    try:
                        import yfinance as yf
                        ticker = yf.Ticker(symbol)
                        info = ticker.info
                        entry_price = float(info.get('currentPrice', info.get('regularMarketPrice', 0.0)))
                        if entry_price > 0:
                            self.logger.info(f"💰 {symbol}: Used yfinance fallback = ${entry_price:.2f}")
                        else:
                            self.logger.warning(f"⚠️ {symbol}: yfinance returned 0 price - info keys: {list(info.keys())[:10]}")
                    except Exception as price_error:
                        self.logger.error(f"❌ {symbol}: yfinance price lookup failed: {price_error}")
                
                # Third attempt: Try alternative yfinance method
                if entry_price == 0.0:
                    try:
                        import yfinance as yf
                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(period="1d")
                        if not hist.empty:
                            entry_price = float(hist['Close'].iloc[-1])
                            self.logger.info(f"💰 {symbol}: Used yfinance history fallback = ${entry_price:.2f}")
                    except Exception as hist_error:
                        self.logger.error(f"❌ {symbol}: yfinance history lookup failed: {hist_error}")
                
                # Final fallback: Use -9999 to indicate missing price data
                if entry_price == 0.0:
                    entry_price = -9999.0
                    self.logger.error(f"🚨 {symbol}: ALL PRICE LOOKUPS FAILED - Using -9999 fallback")'''
    
    new_price_logic = '''                # Get current price using enhanced robust method
                entry_price = self._get_current_price_robust(symbol)
                
                # Final fallback: Use -9999 to indicate missing price data
                if entry_price is None or entry_price == 0.0:
                    entry_price = -9999.0
                    self.logger.error(f"🚨 {symbol}: ALL ENHANCED PRICE LOOKUPS FAILED - Using -9999 fallback")'''
    
    new_content = new_content.replace(old_price_logic, new_price_logic)
    
    # Write the updated file
    with open('enhanced_morning_analyzer_with_ml.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Enhanced price fetching successfully integrated!")
else:
    print("❌ Could not find insertion point for enhanced method")

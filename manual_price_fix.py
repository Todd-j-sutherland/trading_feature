#!/usr/bin/env python3

# Script to manually add enhanced price fetching to the morning analyzer

import_statements = '''
import yfinance as yf
import time
import random
'''

enhanced_price_method = '''
    def _get_current_price_robust(self, symbol):
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
                        return float(price)
                        
                except Exception as e:
                    if attempt < 2:  # Wait before retry (except last attempt)
                        time.sleep(random.uniform(1, 3))
                    continue
                    
        return None

    def _get_current_price(self, symbol):
        """
        Get current price using enhanced robust method
        """
        return self._get_current_price_robust(symbol)
'''

# Read the current file
with open('enhanced_morning_analyzer_with_ml.py', 'r') as f:
    content = f.read()

# Find where to insert the method (before the last method in the class)
lines = content.split('\n')
new_lines = []
method_inserted = False

for i, line in enumerate(lines):
    # Look for the _get_model_performance_summary method and insert before it
    if '_get_model_performance_summary(self):' in line and not method_inserted:
        # Insert our enhanced methods before this line
        new_lines.extend(enhanced_price_method.split('\n'))
        method_inserted = True
    
    # Replace any existing _get_current_price method
    elif 'def _get_current_price(self, symbol):' in line:
        # Skip the old method - we'll replace it with our enhanced version
        j = i + 1
        while j < len(lines) and (lines[j].startswith('        ') or lines[j].strip() == ''):
            j += 1
        # Skip to the end of the old method
        continue
    
    new_lines.append(line)

# Write the updated content
if method_inserted:
    with open('enhanced_morning_analyzer_with_ml.py', 'w') as f:
        f.write('\n'.join(new_lines))
    print("✅ Enhanced price fetching methods successfully added!")
else:
    print("❌ Could not find insertion point")

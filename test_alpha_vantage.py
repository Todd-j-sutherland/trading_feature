import sys
sys.path.append('/root/test')
from alpha_vantage_fetcher import get_current_price_alpha_vantage

# Test with a popular stock
symbol = 'WBC.AX'
print(f'Testing Alpha Vantage for {symbol}...')
price = get_current_price_alpha_vantage(symbol)

if price:
    print(f'SUCCESS: Got price  for {symbol}')
else:
    print(f'FAILED: Could not get price for {symbol}')

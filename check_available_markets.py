import os
import sys
sys.path.append('/root/test')
from ig_markets_trading_api import IGMarketsAPIClient

# Set environment
os.environ['IG_API_KEY'] = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'
os.environ['IG_USERNAME'] = 'sutho100'
os.environ['IG_PASSWORD'] = 'Helloworld987543$'
os.environ['IG_DEMO_MODE'] = 'true'

client = IGMarketsAPIClient()

if client.authenticate():
    print('✅ Authenticated successfully')
    
    # Test some common US stocks that should be available
    us_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
    print('\n🇺🇸 Testing US Stocks:')
    
    for symbol in us_stocks:
        market_info = client.get_market_info(symbol)
        if market_info:
            snapshot = market_info.get('snapshot', {})
            bid = snapshot.get('bid')
            ask = snapshot.get('offer')
            status = snapshot.get('marketStatus')
            print(f'  ✅ {symbol}: Bid , Ask , Status: {status}')
        else:
            print(f'  ❌ {symbol}: Not available')
    
    # Test some forex pairs
    forex_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY']
    print('\n💱 Testing Forex:')
    
    for pair in forex_pairs:
        market_info = client.get_market_info(pair)
        if market_info:
            snapshot = market_info.get('snapshot', {})
            bid = snapshot.get('bid')
            ask = snapshot.get('offer')
            status = snapshot.get('marketStatus')
            print(f'  ✅ {pair}: Bid {bid}, Ask {ask}, Status: {status}')
        else:
            print(f'  ❌ {pair}: Not available')
            
    print('\n❌ Conclusion: ASX stocks are NOT available in IG Markets demo account')
    print('📝 Demo accounts typically only include US stocks, UK stocks, and major forex pairs')
    
else:
    print('❌ Authentication failed')

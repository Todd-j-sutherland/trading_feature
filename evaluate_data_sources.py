import yfinance as yf
import requests
from datetime import datetime
import pytz

def test_yfinance_asx():
    print('=== Testing yfinance ASX data ===')
    aest = pytz.timezone('Australia/Sydney')
    current_time = datetime.now(aest)
    
    symbols = ['WBC.AX', 'CBA.AX', 'ANZ.AX']
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            
            # Get recent price
            info = ticker.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            # Get latest minute data
            hist = ticker.history(period='1d', interval='1m')
            if not hist.empty:
                latest_timestamp = hist.index[-1].tz_convert(aest)
                latest_price = hist['Close'].iloc[-1]
                delay_minutes = (current_time - latest_timestamp).total_seconds() / 60
                
                print(f'{symbol}:  ({delay_minutes:.1f}min delay)')
            else:
                print(f'{symbol}: No minute data available')
                
        except Exception as e:
            print(f'{symbol}: Error - {e}')

def test_free_apis():
    print('\n=== Testing Free Alternative APIs ===')
    
    # Test Yahoo Finance API directly
    try:
        symbol = 'WBC.AX'
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'chart' in data and data['chart']['result']:
            result = data['chart']['result'][0]
            current_price = result['meta']['regularMarketPrice']
            market_time = result['meta']['regularMarketTime']
            
            print(f'Yahoo API: {symbol} =  (timestamp: {market_time})')
        else:
            print('Yahoo API: No data')
            
    except Exception as e:
        print(f'Yahoo API: Error - {e}')

if __name__ == '__main__':
    test_yfinance_asx()
    test_free_apis()

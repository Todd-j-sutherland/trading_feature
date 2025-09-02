import requests
import json

api_key = 'demo'
symbols = ['WBC.AX', 'CBA.AX', 'AAPL']

for symbol in symbols:
    print(f'\nTesting Alpha Vantage for {symbol}...')
    
    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': symbol,
        'apikey': api_key
    }
    
    response = requests.get('https://www.alphavantage.co/query', params=params, timeout=10)
    data = response.json()
    
    if 'Global Quote' in data and data['Global Quote']:
        quote = data['Global Quote']
        price = quote['05. price']
        latest_day = quote['07. latest trading day']
        print(f'SUCCESS: {symbol} =  ({latest_day})')
    else:
        print(f'FAILED: {symbol}')
        print(json.dumps(data, indent=2)[:200] + '...')

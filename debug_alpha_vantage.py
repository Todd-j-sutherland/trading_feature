import requests
import json

api_key = 'demo'
symbol = 'IBM'

print(f'Testing Alpha Vantage for {symbol}...')

params = {
    'function': 'GLOBAL_QUOTE',
    'symbol': symbol,
    'apikey': api_key
}

response = requests.get('https://www.alphavantage.co/query', params=params, timeout=10)
data = response.json()

print('Response:')
print(json.dumps(data, indent=2))

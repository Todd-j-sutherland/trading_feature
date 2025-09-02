#!/usr/bin/env python3
"""
Test script for Alpha Vantage with real API key
Run with: python3 test_alpha_vantage_real_key.py YOUR_API_KEY
"""

import sys
import requests
import json
from datetime import datetime

def test_alpha_vantage_asx(api_key):
    print(f'Testing Alpha Vantage with API key: {api_key[:8]}...')
    
    # Test ASX stocks
    symbols = ['WBC.AX', 'CBA.AX', 'ANZ.AX', 'BHP.AX']
    
    for symbol in symbols:
        print(f'\nTesting {symbol}:')
        
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': api_key
        }
        
        try:
            response = requests.get('https://www.alphavantage.co/query', 
                                  params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'Global Quote' in data and data['Global Quote']:
                quote = data['Global Quote']
                if '05. price' in quote:
                    price = quote['05. price']
                    latest_day = quote['07. latest trading day']
                    change = quote['09. change']
                    change_pct = quote['10. change percent']
                    
                    print(f'  ✅ Price: ${price}')
                    print(f'    📅 Latest: {latest_day}')
                    print(f'    📈 Change: {change} ({change_pct})')
                else:
                    print(f'  ❌ No price data in response')
            else:
                print(f'  ❌ No Global Quote data')
                if 'Error Message' in data:
                    print(f'  Error: {data["Error Message"]}')
                elif 'Note' in data:
                    print(f'  Note: {data["Note"]}')
                elif 'Information' in data:
                    print(f'  Info: {data["Information"]}')
                    
        except Exception as e:
            print(f'  ❌ Error: {e}')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python3 test_alpha_vantage_real_key.py YOUR_API_KEY')
        print('\nGet a free API key at: https://www.alphavantage.co/support/#api-key')
        sys.exit(1)
    
    api_key = sys.argv[1]
    test_alpha_vantage_asx(api_key)

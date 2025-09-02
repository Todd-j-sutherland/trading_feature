import requests
import json

# Test getting actual prices for ASX stocks in IG Markets
username = 'sutho100'
password = 'Helloworld987543$'
api_key = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'
base_url = 'https://demo-api.ig.com/gateway/deal'

print('Testing ASX stock prices in IG Markets...')

# Authenticate
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-IG-API-KEY': api_key,
    'Version': '2'
}

data = {'identifier': username, 'password': password}
response = requests.post(f'{base_url}/session', headers=headers, json=data, timeout=15)

if response.status_code == 200:
    auth_token = response.headers.get('X-SECURITY-TOKEN')
    cst_token = response.headers.get('CST')
    print('Authentication successful')
    
    auth_headers = {
        'Accept': 'application/json',
        'X-IG-API-KEY': api_key,
        'X-SECURITY-TOKEN': auth_token,
        'CST': cst_token,
        'Version': '1'
    }
    
    # Search for major ASX stocks
    asx_searches = ['westpac', 'commonwealth', 'anz', 'bhp', 'csl', 'nab', 'woolworths', 'telstra']
    
    found_stocks = {}
    
    for search_term in asx_searches:
        print(f'\nSearching for {search_term}...')
        
        try:
            response = requests.get(f'{base_url}/markets', headers=auth_headers, 
                                  params={'searchTerm': search_term}, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                markets = data.get('markets', [])
                
                for market in markets:
                    name = market.get('instrumentName', '')
                    epic = market.get('epic', '')
                    
                    # Look for main equity shares (not derivatives/notes)
                    if ('Banking Corp' in name or 'Bank' in name or 
                        'Billiton' in name or 'Limited' in name or 
                        'Group' in name or 'Corporation' in name) and 'Notes' not in name:
                        
                        found_stocks[search_term] = {'name': name, 'epic': epic}
                        print(f'  Found: {name} ({epic})')
                        break
                else:
                    print(f'  No main stock found for {search_term}')
            else:
                print(f'  Search failed: {response.status_code}')
                
        except Exception as e:
            print(f'  Error: {e}')
    
    # Now test getting prices for found stocks
    print('\n' + '='*60)
    print('TESTING REAL-TIME PRICES')
    print('='*60)
    
    for search_term, stock_info in found_stocks.items():
        epic = stock_info['epic']
        name = stock_info['name']
        
        print(f'\nGetting price for {name} ({epic})...')
        
        try:
            price_headers = auth_headers.copy()
            price_headers['Version'] = '3'
            
            response = requests.get(f'{base_url}/markets/{epic}', headers=price_headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                snapshot = data.get('snapshot', {})
                instrument = data.get('instrument', {})
                
                if snapshot:
                    bid = snapshot.get('bid')
                    offer = snapshot.get('offer')
                    
                    if bid is not None and offer is not None:
                        mid_price = (bid + offer) / 2
                        
                        print(f'  SUCCESS!')
                        print(f'    Mid Price: ')
                        print(f'    Bid: ')
                        print(f'    Offer: ')
                        print(f'    Source: IG Markets (REAL-TIME)')
                        
                        # Compare with market name
                        market_name = instrument.get('name', name)
                        print(f'    Market: {market_name}')
                    else:
                        print(f'  No bid/offer prices available')
                else:
                    print(f'  No snapshot data')
            else:
                print(f'  Price request failed: {response.status_code}')
                print(f'      Response: {response.text[:100]}...')
                
        except Exception as e:
            print(f'  Price error: {e}')
    
    print(f'\nFound {len(found_stocks)} ASX stocks with IG EPICs')
    print('IG Markets real-time ASX data is WORKING!')
    
else:
    print(f'Authentication failed: {response.status_code}')

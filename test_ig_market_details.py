import requests
import json
from datetime import datetime

# Test market details and status
username = 'sutho100'
password = 'Helloworld987543$'
api_key = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'
base_url = 'https://demo-api.ig.com/gateway/deal'

print('Testing IG Markets details...')
print(f'Current time: {datetime.now()}')

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
        'Version': '3'
    }
    
    # Test with Westpac - full market details
    epic = 'AA.D.WBC.CASH.IP'
    print(f'\nTesting detailed market info for Westpac ({epic})...')
    
    try:
        response = requests.get(f'{base_url}/markets/{epic}', headers=auth_headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print('Full market data received:')
            
            # Market status
            snapshot = data.get('snapshot', {})
            instrument = data.get('instrument', {})
            
            print(f'Market Name: {instrument.get(name, N/A)}')
            print(f'Type: {instrument.get(type, N/A)}')
            print(f'Currency: {instrument.get(currencies, [{}])[0].get(name, N/A)}')
            
            # Market status
            market_status = snapshot.get('marketStatus', 'UNKNOWN')
            print(f'Market Status: {market_status}')
            
            # Times
            update_time = snapshot.get('updateTime', 'N/A')
            print(f'Last Update: {update_time}')
            
            # Prices
            bid = snapshot.get('bid')
            offer = snapshot.get('offer')
            
            if bid is not None:
                print(f'Bid: {bid}')
            else:
                print('Bid: Not available')
                
            if offer is not None:
                print(f'Offer: {offer}')
            else:
                print('Offer: Not available')
            
            # Trading times
            dealing_rules = instrument.get('dealingRules', {})
            market_orders = dealing_rules.get('marketOrderPreference', 'N/A')
            print(f'Market Orders: {market_orders}')
            
            # Check if prices are in different fields
            print('\nChecking all price fields:')
            for key, value in snapshot.items():
                if 'price' in key.lower() or key in ['high', 'low', 'open', 'close', 'last']:
                    print(f'  {key}: {value}')
            
        else:
            print(f'Request failed: {response.status_code}')
            print(f'Response: {response.text}')
            
    except Exception as e:
        print(f'Error: {e}')
    
    # Test a US market for comparison
    print('\n' + '='*50)
    print('TESTING US MARKET FOR COMPARISON')
    print('='*50)
    
    # Search for a US stock
    try:
        response = requests.get(f'{base_url}/markets', headers=auth_headers, 
                              params={'searchTerm': 'apple'}, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            markets = data.get('markets', [])
            
            for market in markets:
                name = market.get('instrumentName', '')
                epic = market.get('epic', '')
                
                if 'Apple Inc' in name and 'CFD' not in name:
                    print(f'Found US stock: {name} ({epic})')
                    
                    # Get its prices
                    response = requests.get(f'{base_url}/markets/{epic}', headers=auth_headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        snapshot = data.get('snapshot', {})
                        
                        bid = snapshot.get('bid')
                        offer = snapshot.get('offer')
                        market_status = snapshot.get('marketStatus', 'UNKNOWN')
                        
                        print(f'  Status: {market_status}')
                        print(f'  Bid: {bid}')
                        print(f'  Offer: {offer}')
                        
                        if bid is not None and offer is not None:
                            print('  US market has prices - ASX might be closed!')
                        else:
                            print('  US market also has no prices - might be weekend/demo limitation')
                    break
                    
    except Exception as e:
        print(f'US market test error: {e}')

else:
    print(f'Authentication failed: {response.status_code}')

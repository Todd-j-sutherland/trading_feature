import requests
import json
from datetime import datetime

username = 'sutho100'
password = 'Helloworld987543$'
api_key = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'
base_url = 'https://demo-api.ig.com/gateway/deal'

print('IG Markets Debug Test')
print(f'Time: {datetime.now()}')

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
    print('Auth OK')
    
    auth_headers = {
        'Accept': 'application/json',
        'X-IG-API-KEY': api_key,
        'X-SECURITY-TOKEN': auth_token,
        'CST': cst_token,
        'Version': '3'
    }
    
    # Test Westpac details
    epic = 'AA.D.WBC.CASH.IP'
    print(f'\nTesting: {epic}')
    
    try:
        response = requests.get(f'{base_url}/markets/{epic}', headers=auth_headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Print raw data structure
            print('Raw response keys:', list(data.keys()))
            
            snapshot = data.get('snapshot', {})
            instrument = data.get('instrument', {})
            
            print('\nSnapshot keys:', list(snapshot.keys()))
            print('Instrument keys:', list(instrument.keys()))
            
            # Market info
            market_name = instrument.get('name', 'Unknown')
            market_type = instrument.get('type', 'Unknown')
            
            print(f'\nMarket: {market_name}')
            print(f'Type: {market_type}')
            
            # Status and prices
            market_status = snapshot.get('marketStatus', 'Unknown')
            print(f'Status: {market_status}')
            
            # Print all snapshot values
            print('\nAll snapshot data:')
            for key, value in snapshot.items():
                print(f'  {key}: {value}')
                
        else:
            print(f'Failed: {response.status_code}')
            print(f'Error: {response.text[:200]}')
            
    except Exception as e:
        print(f'Exception: {e}')

else:
    print(f'Auth failed: {response.status_code}')

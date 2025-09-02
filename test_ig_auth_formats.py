import requests
import json

# Test different authentication formats for IG Markets
api_key = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'
password = 'October987543$'
base_url = 'https://demo-api.ig.com/gateway/deal'

# Try different username formats
test_usernames = [
    'sutho100@gmail.com',
    'SUTHO100@GMAIL.COM',
    'SUTHTO75457900',
    'sutho100',
]

print('Testing different username formats for IG Markets...')

for i, username in enumerate(test_usernames, 1):
    print(f'\n=== Test {i}: {username} ===')
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-IG-API-KEY': api_key,
        'Version': '2'
    }
    
    data = {
        'identifier': username,
        'password': password
    }
    
    try:
        response = requests.post(f'{base_url}/session', headers=headers, json=data, timeout=15)
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            print('✅ SUCCESS! Authentication worked!')
            auth_token = response.headers.get('X-SECURITY-TOKEN')
            cst_token = response.headers.get('CST')
            print(f'Auth Token: {auth_token[:20] if auth_token else "None"}...')
            print(f'CST Token: {cst_token[:20] if cst_token else "None"}...')
            
            # Try to get market data with this authentication
            print('\nTesting market data access...')
            market_headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-IG-API-KEY': api_key,
                'X-SECURITY-TOKEN': auth_token,
                'CST': cst_token,
                'Version': '3'
            }
            
            market_response = requests.get(f'{base_url}/markets?searchTerm=WBC', headers=market_headers, timeout=10)
            print(f'Market data status: {market_response.status_code}')
            
            if market_response.status_code == 200:
                data = market_response.json()
                if 'markets' in data and data['markets']:
                    market = data['markets'][0]
                    print(f'Found market: {market.get("instrumentName", "Unknown")} ({market.get("epic", "Unknown")})')
                else:
                    print('No markets found in response')
            
            break
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f'❌ Failed: {error_data}')
            
    except Exception as e:
        print(f'❌ Error: {e}')

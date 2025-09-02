import requests
import json

# Explore what markets are available in IG demo
username = 'sutho100'
password = 'Helloworld987543$'
api_key = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'
base_url = 'https://demo-api.ig.com/gateway/deal'

print('Exploring available markets in IG demo...')

# Authenticate
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

response = requests.post(f'{base_url}/session', headers=headers, json=data, timeout=10)

if response.status_code == 200:
    auth_token = response.headers.get('X-SECURITY-TOKEN')
    cst_token = response.headers.get('CST')
    print('✅ Authentication successful')
    
    # Get authenticated headers
    auth_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-IG-API-KEY': api_key,
        'X-SECURITY-TOKEN': auth_token,
        'CST': cst_token,
        'Version': '3'
    }
    
    # Try different search terms to see what is available
    search_terms = ['AUD', 'Australia', 'ASX', 'AUDUSD', 'Gold', 'Oil', 'FTSE']
    
    for term in search_terms:
        print(f'\n=== Searching for: {term} ===')
        
        try:
            response = requests.get(f'{base_url}/markets?searchTerm={term}', headers=auth_headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                markets = data.get('markets', [])
                
                print(f'Found {len(markets)} markets:')
                for i, market in enumerate(markets[:5]):  # Show first 5
                    name = market.get('instrumentName', 'Unknown')
                    epic = market.get('epic', 'Unknown')
                    print(f'  {i+1}. {name} ({epic})')
                    
                if len(markets) > 5:
                    print(f'  ... and {len(markets) - 5} more')
                    
            else:
                print(f'Error: {response.status_code} - {response.text[:100]}...')
                
        except Exception as e:
            print(f'Error searching for {term}: {e}')
    
    # Try to get market navigation to see categories
    print('\n=== Market Navigation ===')
    try:
        response = requests.get(f'{base_url}/marketnavigation', headers=auth_headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            nodes = data.get('nodes', [])
            print(f'Available market categories:')
            for node in nodes:
                name = node.get('name', 'Unknown')
                node_id = node.get('id', 'Unknown')
                print(f'  - {name} (ID: {node_id})')
        else:
            print(f'Market navigation error: {response.status_code}')
    except Exception as e:
        print(f'Market navigation error: {e}')
        
else:
    print(f'❌ Authentication failed: {response.status_code} - {response.text}')

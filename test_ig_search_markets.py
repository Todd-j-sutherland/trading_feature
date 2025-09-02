import requests
import json

# Test IG Markets search functionality properly
username = 'sutho100'
password = 'Helloworld987543$'
api_key = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'
base_url = 'https://demo-api.ig.com/gateway/deal'

print('Testing IG Markets search_markets functionality...')

# Authenticate first
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

response = requests.post(f'{base_url}/session', headers=headers, json=data, timeout=15)

if response.status_code == 200:
    auth_token = response.headers.get('X-SECURITY-TOKEN')
    cst_token = response.headers.get('CST')
    print('‚úÖ Authentication successful')
    
    # Set up authenticated headers for search
    search_headers = {
        'Accept': 'application/json',
        'X-IG-API-KEY': api_key,
        'X-SECURITY-TOKEN': auth_token,
        'CST': cst_token,
        'Version': '1'
    }
    
    # Test various search terms and methods
    search_tests = [
        # Try different search patterns
        {'term': 'westpac', 'desc': 'Full name search for Westpac'},
        {'term': 'commonwealth', 'desc': 'Full name search for CBA'},
        {'term': 'anz', 'desc': 'Simple ANZ search'},
        {'term': 'bhp', 'desc': 'Simple BHP search'},
        {'term': 'aus', 'desc': 'Australia related'},
        {'term': 'sydney', 'desc': 'Sydney related'},
        {'term': 'bank', 'desc': 'Bank related'},
        {'term': 'mining', 'desc': 'Mining related'},
        # Try some generic terms
        {'term': 'a', 'desc': 'Single letter search'},
        {'term': '', 'desc': 'Empty search (get all?)'},
    ]
    
    for test in search_tests:
        term = test['term']
        desc = test['desc']
        
        print(f'\n=== {desc}: "{term}" ===')
        
        try:
            # Try the markets search endpoint
            search_url = f'{base_url}/markets'
            params = {'searchTerm': term} if term else {}
            
            response = requests.get(search_url, headers=search_headers, params=params, timeout=15)
            print(f'Status: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                markets = data.get('markets', [])
                
                if markets:
                    print(f'‚úÖ Found {len(markets)} markets:')
                    for i, market in enumerate(markets[:5]):  # Show first 5
                        name = market.get('instrumentName', 'Unknown')
                        epic = market.get('epic', 'Unknown')
                        instrument_type = market.get('instrumentType', 'Unknown')
                        print(f'  {i+1}. {name} ({epic}) - Type: {instrument_type}')
                        
                        # Check if this looks like an ASX stock
                        if any(x in name.upper() for x in ['WESTPAC', 'COMMONWEALTH', 'ANZ', 'BHP', 'AUSTRALIA']):
                            print(f'      ÌæØ POTENTIAL ASX MATCH!')
                    
                    if len(markets) > 5:
                        print(f'  ... and {len(markets) - 5} more markets')
                        
                    # If we found results, stop searching
                    if len(markets) > 0:
                        break
                else:
                    print('No markets found')
            else:
                error_text = response.text[:200] if response.text else 'No response'
                print(f'‚ùå Error: {response.status_code} - {error_text}...')
                
        except Exception as e:
            print(f'‚ùå Exception: {e}')
    
    # If we still haven't found anything, try a different approach
    print('\n=== Trying alternative search methods ===')
    
    # Try different API versions
    for version in ['1', '2', '3']:
        print(f'\nTrying API version {version}...')
        
        alt_headers = search_headers.copy()
        alt_headers['Version'] = version
        
        try:
            response = requests.get(f'{base_url}/markets', headers=alt_headers, 
                                  params={'searchTerm': 'bank'}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                markets = data.get('markets', [])
                print(f'Version {version}: Found {len(markets)} markets')
                
                if markets:
                    for market in markets[:3]:
                        name = market.get('instrumentName', 'Unknown')
                        epic = market.get('epic', 'Unknown')
                        print(f'  - {name} ({epic})')
                    break
            else:
                print(f'Version {version}: {response.status_code} error')
                
        except Exception as e:
            print(f'Version {version}: Exception - {e}')

else:
    print(f'‚ùå Authentication failed: {response.status_code} - {response.text}')

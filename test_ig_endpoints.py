import requests
import json

# Test different IG Markets API endpoints and configurations
api_key = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'

print('Testing different IG Markets API configurations...')

# Test different base URLs (sometimes there are regional differences)
base_urls = [
    'https://demo-api.ig.com/gateway/deal',
    'https://api.ig.com/gateway/deal',  # Live API (should still work for testing auth)
]

# Test different API versions
versions = ['1', '2', '3']

# Test data
test_data = {
    'identifier': 'SUTHTO75457900',
    'password': 'October987543$'
}

for base_url in base_urls:
    print(f'\n=== Testing {base_url} ===')
    
    for version in versions:
        print(f'\n--- Version {version} ---')
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-IG-API-KEY': api_key,
            'Version': version
        }
        
        try:
            response = requests.post(f'{base_url}/session', headers=headers, json=test_data, timeout=10)
            print(f'Status: {response.status_code}')
            
            if response.status_code == 200:
                print('✅ SUCCESS!')
                print(f'Response headers: {dict(response.headers)}')
                break
            else:
                error_text = response.text[:100] if response.text else 'No response body'
                print(f'❌ Error: {error_text}...')
                
        except Exception as e:
            print(f'❌ Exception: {e}')

# Check if API key is valid by testing a simple endpoint
print('\n=== Testing API Key Validity ===')
for base_url in base_urls:
    try:
        headers = {
            'X-IG-API-KEY': api_key,
            'Version': '1'
        }
        
        # Test a simple endpoint that should respond even without auth
        response = requests.get(f'{base_url}/ping', headers=headers, timeout=5)
        print(f'{base_url}/ping: {response.status_code}')
        
        if response.status_code not in [401, 403]:
            print(f'  Response: {response.text[:50]}...')
            
    except Exception as e:
        print(f'{base_url}/ping: Error - {e}')

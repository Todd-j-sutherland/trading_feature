import requests
import json

# Test different username/password combinations
api_key = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'
base_url = 'https://demo-api.ig.com/gateway/deal'

test_cases = [
    {'username': 'SUTHTO75457900', 'password': 'October987543$'},
    {'username': 'SUTHTO75457900', 'password': 'October987543'},  # Without escape
    {'username': 'suthto75457900', 'password': 'October987543$'},  # Lowercase
    {'username': 'suthto75457900', 'password': 'October987543'},   # Lowercase + no escape
]

for i, test_case in enumerate(test_cases, 1):
    print(f'\n=== Test {i}: {test_case["username"]} / {test_case["password"][:8]}... ===')
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-IG-API-KEY': api_key,
        'Version': '2'
    }
    
    data = {
        'identifier': test_case['username'],
        'password': test_case['password']
    }
    
    try:
        response = requests.post(f'{base_url}/session', headers=headers, json=data, timeout=10)
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            print('✅ SUCCESS! Authentication worked')
            print(f'Response: {response.text[:200]}...')
            break
        else:
            print(f'❌ Failed: {response.text}')
            
    except Exception as e:
        print(f'❌ Error: {e}')

print('\n=== Testing API Key Validity ===')
# Test if API key itself is valid by trying a simple request
try:
    headers = {'X-IG-API-KEY': api_key, 'Version': '1'}
    response = requests.get(f'{base_url}/accounts', headers=headers, timeout=10)
    print(f'API Key test status: {response.status_code}')
    if response.status_code != 401:  # 401 would mean auth required but API key was accepted
        print(f'API Key appears invalid: {response.text}')
    else:
        print('API Key format appears valid (401 = auth required)')
except Exception as e:
    print(f'API Key test error: {e}')

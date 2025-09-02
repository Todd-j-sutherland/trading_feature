import requests
import json

# Test IG Markets authentication with debug info
username = 'SUTHTO75457900'
password = 'October987543$'
api_key = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'

print('Testing IG Markets API authentication...')
print(f'Username: {username}')
print(f'API Key: {api_key[:16]}...')

# Try demo API endpoint
base_url = 'https://demo-api.ig.com/gateway/deal'

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

print(f'\nTrying demo API: {base_url}/session')
print(f'Headers: {headers}')
print(f'Data: {{\identifier\: \{username}\, \password\: \[HIDDEN]\}}')

try:
    response = requests.post(f'{base_url}/session', headers=headers, json=data, timeout=15)
    
    print(f'\nResponse Status: {response.status_code}')
    print(f'Response Headers: {dict(response.headers)}')
    print(f'Response Body: {response.text}')
    
    if response.status_code == 200:
        print('\n✅ Authentication successful!')
    else:
        print(f'\n❌ Authentication failed: {response.status_code}')
        
except Exception as e:
    print(f'\n❌ Error: {e}')

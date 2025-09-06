import os
import sys
import requests
sys.path.append('/root/test')
from ig_markets_trading_api import IGMarketsAPIClient

os.environ['IG_API_KEY'] = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'
os.environ['IG_USERNAME'] = 'sutho100'
os.environ['IG_PASSWORD'] = 'Helloworld987543$'
os.environ['IG_DEMO_MODE'] = 'true'

client = IGMarketsAPIClient()

if client.authenticate():
    print('✅ Successfully authenticated with IG Markets demo account')
    
    # Check what endpoints are available
    try:
        # Try to get account summary
        url = f'{client.base_url}/accounts'
        response = client.session.get(url, timeout=30)
        print(f'📊 Accounts endpoint: {response.status_code}')
        if response.status_code == 200:
            print(f'   Response: {response.text[:200]}...')
        
        # Try to get positions
        url = f'{client.base_url}/positions'
        response = client.session.get(url, timeout=30)
        print(f'📊 Positions endpoint: {response.status_code}')
        
        # Try to list available markets (if endpoint exists)
        url = f'{client.base_url}/marketnavigation'
        response = client.session.get(url, timeout=30)
        print(f'📊 Market navigation: {response.status_code}')
        if response.status_code == 200:
            nav_data = response.json()
            print(f'   Available market nodes: {len(nav_data.get(nodes, []))}')
            for node in nav_data.get(nodes, [])[:5]:
                print(f'     - {node.get(name, Unknown)}')
        
        # Check transaction history
        url = f'{client.base_url}/history/transactions'
        response = client.session.get(url, timeout=30)
        print(f'📊 Transaction history: {response.status_code}')
        
    except Exception as e:
        print(f'❌ Error checking capabilities: {e}')
        
    print('\n🔍 SUMMARY:')
    print('✅ Authentication: Working')
    print('❌ ASX Market Access: Not available') 
    print('❓ Demo Account Type: Limited market access')
    print('\n💡 RECOMMENDATION: Consider upgrading to live IG Markets account for full ASX access')
        
else:
    print('❌ Authentication failed')

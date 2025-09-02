"""
Quick test script for IG Markets setup
Usage: python3 test_ig_setup.py username password api_key
"""

import sys
import os

def test_ig_setup(username, password, api_key):
    # Set environment variables
    os.environ['IG_USERNAME'] = username
    os.environ['IG_PASSWORD'] = password  
    os.environ['IG_API_KEY'] = api_key
    
    print('Testing IG Markets setup...')
    print(f'Username: {username}')
    print(f'API Key: {api_key[:8]}...')
    print()
    
    # Test IG Markets directly
    try:
        from ig_markets_fetcher import IGMarketsPriceFetcher
        
        fetcher = IGMarketsPriceFetcher()
        
        print('Testing authentication...')
        if fetcher.authenticate():
            print('✅ Authentication successful!')
            
            # Test a popular ASX stock
            print('\nTesting WBC.AX price fetch...')
            result = fetcher.get_current_price_with_details('WBC.AX')
            
            if result and result.get('price'):
                price = result['price']
                bid = result.get('bid', 'N/A')
                offer = result.get('offer', 'N/A')
                market_name = result.get('market_name', 'Unknown')
                
                print(f'✅ SUCCESS!')
                print(f'  Price: ')
                print(f'  Bid: ')
                print(f'  Offer: ')
                print(f'  Market: {market_name}')
                print(f'  Source: Real-time IG Markets')
            else:
                print(f'❌ Failed to get price: {result.get("error", "Unknown error")}')
        else:
            print('❌ Authentication failed')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    
    # Test integrated real-time fetcher
    print('\n' + '='*50)
    print('Testing integrated real-time price fetcher...')
    
    try:
        from real_time_price_fetcher import get_current_price_with_source_info
        
        result = get_current_price_with_source_info('WBC.AX')
        
        if result and result.get('price'):
            price = result['price']
            source = result.get('source', 'unknown')
            delay = result.get('delay_minutes', 0)
            
            print(f'✅ SUCCESS!')
            print(f'  Price: ')
            print(f'  Source: {source}')
            if delay:
                print(f'  Delay: {delay:.1f} minutes')
            else:
                print(f'  Real-time data')
        else:
            print(f'❌ Failed: {result.get("error", "Unknown error")}')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: python3 test_ig_setup.py USERNAME PASSWORD API_KEY')
        print('\nExample:')
        print('python3 test_ig_setup.py demo_user demo_pass abc123def456')
        print('\nGet your API key from IG Markets demo account settings.')
        sys.exit(1)
    
    username, password, api_key = sys.argv[1], sys.argv[2], sys.argv[3]
    test_ig_setup(username, password, api_key)

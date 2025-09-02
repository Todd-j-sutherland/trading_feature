import os
from ig_markets_fetcher import IGMarketsPriceFetcher

# Test IG Markets market search for ASX stocks
print('Searching for ASX markets in IG...')

fetcher = IGMarketsPriceFetcher(
    username='sutho100',
    password='Helloworld987543$',
    api_key='ac68e6f053799a4a36c75936c088fc4d6cfcfa6e',
    demo=True
)

# Authenticate
if fetcher.authenticate():
    print('✅ Authentication successful')
    
    # Search for popular ASX stocks
    asx_symbols = ['WBC', 'CBA', 'ANZ', 'BHP', 'CSL', 'NAB', 'WOW', 'TLS']
    
    for symbol in asx_symbols:
        print(f'\nSearching for {symbol}...')
        epic = fetcher.search_market(f'{symbol}.AX')
        if epic:
            print(f'  Found EPIC: {epic}')
            
            # Try to get price
            result = fetcher.get_current_price_by_epic(epic)
            if result:
                price = result['price']
                market_name = result.get('market_name', 'Unknown')
                print(f'  ✅ Price: ${price:.2f} - {market_name}')
            else:
                print(f'  ❌ Could not get price for {epic}')
        else:
            # Try searching without .AX
            print(f'  Trying {symbol} without .AX...')
            epic = fetcher.search_market(symbol)
            if epic:
                print(f'  Found EPIC: {epic}')
                result = fetcher.get_current_price_by_epic(epic)
                if result:
                    price = result['price']
                    market_name = result.get('market_name', 'Unknown')
                    print(f'  ✅ Price: ${price:.2f} - {market_name}')
                else:
                    print(f'  ❌ Could not get price for {epic}')
            else:
                print(f'  ❌ No market found for {symbol}')
else:
    print('❌ Authentication failed')

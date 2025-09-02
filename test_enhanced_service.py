import sys
sys.path.append('/root/test')
from enhanced_paper_trading_service import EnhancedPaperTradingService

# Test creating the service and getting prices
print('Testing Enhanced Paper Trading Service...')

try:
    service = EnhancedPaperTradingService()
    print('✅ Service initialized successfully')
    
    # Test price fetching
    test_symbols = ['WBC.AX', 'CBA.AX']
    
    for symbol in test_symbols:
        print(f'\nTesting price fetch for {symbol}:')
        price = service.get_current_price(symbol)
        if price:
            print(f'✅ Got price: ')
        else:
            print(f'❌ Failed to get price')
            
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()

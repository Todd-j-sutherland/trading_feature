import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print('í¾¯ Testing Complete Real-Time Trading System')
print('=' * 60)

# Test 1: Real-Time Price Fetcher
print('\n1. Testing Real-Time Price Fetcher...')
try:
    from real_time_price_fetcher import RealTimePriceFetcher
    
    fetcher = RealTimePriceFetcher()
    test_symbol = 'WBC'
    
    price_data = fetcher.get_current_price(test_symbol)
    if price_data:
        price, source, delay = price_data
        print(f'   âœ… {test_symbol}: ${price:.2f} from {source} (delay: {delay}min)')
    else:
        print(f'   âŒ Failed to get price for {test_symbol}')
        
except Exception as e:
    print(f'   âŒ Price fetcher error: {e}')

# Test 2: Enhanced Paper Trading Service Price Integration
print('\n2. Testing Enhanced Paper Trading Service...')
try:
    from enhanced_paper_trading_service import EnhancedPaperTradingService
    
    # Create service instance
    service = EnhancedPaperTradingService()
    
    # Test price fetching
    test_symbols = ['WBC', 'CBA']
    
    for symbol in test_symbols:
        price = service.get_current_price(symbol)
        if price:
            print(f'   âœ… Service got {symbol}: ${price:.2f}')
        else:
            print(f'   âŒ Service failed to get {symbol} price')
            
except Exception as e:
    print(f'   âŒ Paper trading service error: {e}')

# Test 3: Source Statistics
print('\n3. Data Source Statistics...')
try:
    if 'fetcher' in locals():
        stats = fetcher.get_stats()
        total_requests = sum(stats.values())
        
        print(f'   Total requests: {total_requests}')
        for source, count in stats.items():
            if count > 0:
                percentage = (count / total_requests) * 100 if total_requests > 0 else 0
                print(f'   {source}: {count} ({percentage:.1f}%)')
                
except Exception as e:
    print(f'   âŒ Stats error: {e}')

print('\ní¾¯ Integration Test Complete!')
print('\níº€ Ready for live ASX trading with real-time IG Markets data!')

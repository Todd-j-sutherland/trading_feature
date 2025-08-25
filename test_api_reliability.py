#!/usr/bin/env python3
"""
Test Yahoo Finance API reliability and response times
"""

import yfinance as yf
import time
from datetime import datetime

def test_price_methods(symbol):
    print(f'📊 Testing {symbol}:')
    results = {}
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Method 1: ticker.info
        start_time = time.time()
        try:
            info = ticker.info
            price1 = info.get('currentPrice', info.get('regularMarketPrice', 0))
            time1 = time.time() - start_time
            results['info'] = (price1, time1)
            print(f'   Method 1 (info): ${price1:.2f} ({time1:.2f}s)')
        except Exception as e:
            results['info'] = (0, 999)
            print(f'   Method 1 (info): FAILED - {str(e)[:50]}')
        
        # Method 2: history
        start_time = time.time()
        try:
            hist = ticker.history(period='1d')
            if not hist.empty:
                price2 = hist['Close'].iloc[-1]
                time2 = time.time() - start_time
                results['history'] = (price2, time2)
                print(f'   Method 2 (history): ${price2:.2f} ({time2:.2f}s)')
            else:
                results['history'] = (0, 999)
                print(f'   Method 2 (history): No data')
        except Exception as e:
            results['history'] = (0, 999)
            print(f'   Method 2 (history): FAILED - {str(e)[:50]}')
        
        # Method 3: fast_info
        start_time = time.time()
        try:
            fast_info = ticker.fast_info
            price3 = fast_info.last_price if hasattr(fast_info, 'last_price') else 0
            time3 = time.time() - start_time
            results['fast_info'] = (price3, time3)
            print(f'   Method 3 (fast_info): ${price3:.2f} ({time3:.2f}s)')
        except Exception as e:
            results['fast_info'] = (0, 999)
            print(f'   Method 3 (fast_info): FAILED - {str(e)[:50]}')
            
    except Exception as e:
        print(f'   Overall ticker creation failed: {str(e)[:50]}')
        
    return results

def test_api_reliability():
    print('🔍 TESTING YAHOO FINANCE API RELIABILITY')
    print('=' * 45)

    banks = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX']

    # Test all banks
    all_results = {}
    for bank in banks:
        all_results[bank] = test_price_methods(bank)
        print()

    print('📈 RELIABILITY SUMMARY:')
    print('-' * 25)

    methods = ['info', 'history', 'fast_info']
    for method in methods:
        successful = 0
        total_time = 0
        for bank in banks:
            if method in all_results[bank]:
                price, duration = all_results[bank][method]
                if price > 0 and duration < 10:  # Valid price within 10 seconds
                    successful += 1
                    total_time += duration
        
        success_rate = (successful / len(banks)) * 100
        avg_time = total_time / max(successful, 1)
        
        if success_rate == 100:
            status = '✅'
        elif success_rate >= 75:
            status = '🟡'
        else:
            status = '❌'
            
        print(f'   {status} {method}: {success_rate:.0f}% success, {avg_time:.2f}s avg')

    print()
    print('💡 RECOMMENDATION:')
    print('   Use the most reliable method as primary, with fallbacks')

if __name__ == '__main__':
    test_api_reliability()

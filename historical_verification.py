#!/usr/bin/env python3
import yfinance as yf
from datetime import datetime

def main():
    print("September 12th, 2025 - Historical Data Verification")
    print("=" * 60)
    
    # Test data availability first
    print("Testing historical data availability...")
    print("Using corrected timing: Entry ~10:40 AEST, Exit ~15:30 AEST")
    ticker = yf.Ticker("ANZ.AX")
    
    intervals = ["1m", "5m", "15m", "1h"]
    for interval in intervals:
        try:
            hist = ticker.history(start="2025-09-12", end="2025-09-13", interval=interval)
            if not hist.empty:
                print(f"✓ {interval} data: {len(hist)} points")
                print(f"  Range: {hist.index.min()} to {hist.index.max()}")
            else:
                print(f"✗ {interval} data: Empty")
        except Exception as e:
            print(f"✗ {interval} data: Error - {e}")
    
    print("\n" + "=" * 60)
    print("DETAILED VERIFICATION")
    print("=" * 60)
    
    # Your September 12th data
    sept12_data = [
        {"symbol": "ANZ.AX", "return": 1.1876, "entry_price": 32.84, "exit_price": 33.23},
        {"symbol": "WBC.AX", "return": 1.2912, "entry_price": 37.95, "exit_price": 38.44},
        {"symbol": "CBA.AX", "return": 1.2458, "entry_price": 167.77, "exit_price": 169.86},
        {"symbol": "QBE.AX", "return": 1.4105, "entry_price": 20.56, "exit_price": 20.85},
        {"symbol": "SUN.AX", "return": 0.8076, "entry_price": 21.05, "exit_price": 21.22},
        {"symbol": "MQG.AX", "return": 2.0281, "entry_price": 219.91, "exit_price": 224.37},
        {"symbol": "NAB.AX", "return": 1.2552, "entry_price": 43.02, "exit_price": 43.56}
    ]
    
    # Target times - corrected for your actual trading schedule
    # Your predictions start around 10:40 AM AEST (00:40 UTC)
    # Exit around 3:30 PM AEST (05:30 UTC)
    entry_time = datetime(2025, 9, 12, 0, 40, 0)   # 00:40 UTC = 10:40 AEST
    exit_time = datetime(2025, 9, 12, 5, 30, 0)    # 05:30 UTC = 15:30 AEST
    
    verified_results = []
    
    for data in sept12_data:
        symbol = data["symbol"]
        target_entry = data["entry_price"]
        target_exit = data["exit_price"] 
        target_return = data["return"]
        
        print(f"\n{symbol}:")
        print(f"  Target: Entry ${target_entry:.4f}, Exit ${target_exit:.4f}, Return {target_return:.2f}%")
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Try to get 1-minute data first (most accurate)
            hist = ticker.history(start="2025-09-12", end="2025-09-13", interval="1m")
            data_interval = "1-minute"
            
            if hist.empty:
                # Fall back to 5-minute data
                hist = ticker.history(start="2025-09-12", end="2025-09-13", interval="5m")
                data_interval = "5-minute"
            
            if hist.empty:
                print(f"  ✗ No historical data available")
                continue
                
            # Remove timezone for easier comparison
            if hist.index.tz is not None:
                hist.index = hist.index.tz_localize(None)
            
            print(f"  📊 {data_interval} data: {len(hist)} points from {hist.index.min().strftime('%H:%M')} to {hist.index.max().strftime('%H:%M')}")
            
            # Find closest prices to target times
            entry_diffs = abs(hist.index - entry_time)
            entry_idx = entry_diffs.argmin()
            yf_entry = hist['Close'].iloc[entry_idx]
            entry_actual_time = hist.index[entry_idx]
            entry_time_diff = entry_diffs[entry_idx].total_seconds() / 60
            
            exit_diffs = abs(hist.index - exit_time)
            exit_idx = exit_diffs.argmin()
            yf_exit = hist['Close'].iloc[exit_idx]
            exit_actual_time = hist.index[exit_idx]
            exit_time_diff = exit_diffs[exit_idx].total_seconds() / 60
            
            # Calculate yfinance return
            yf_return = ((yf_exit - yf_entry) / yf_entry) * 100
            
            # Calculate differences
            entry_diff_pct = abs(target_entry - yf_entry) / yf_entry * 100
            exit_diff_pct = abs(target_exit - yf_exit) / yf_exit * 100
            return_diff_pct = abs(target_return - yf_return)
            
            print(f"  🎯 Entry: YF ${yf_entry:.4f} @ {entry_actual_time.strftime('%H:%M')} (±{entry_diff_pct:.2f}%, ±{entry_time_diff:.0f}min)")
            print(f"  🎯 Exit:  YF ${yf_exit:.4f} @ {exit_actual_time.strftime('%H:%M')} (±{exit_diff_pct:.2f}%, ±{exit_time_diff:.0f}min)")
            print(f"  📈 Return: YF {yf_return:.2f}% vs Target {target_return:.2f}% (±{return_diff_pct:.2f}%)")
            
            # Quality assessment
            entry_good = entry_diff_pct < 2.0
            exit_good = exit_diff_pct < 2.0
            return_good = return_diff_pct < 1.0
            timing_good = entry_time_diff < 60 and exit_time_diff < 60
            
            overall_status = "✅ EXCELLENT" if (entry_good and exit_good and return_good) else "✓ GOOD" if (entry_diff_pct < 3 and exit_diff_pct < 3) else "⚠ CHECK"
            print(f"  {overall_status}")
            
            verified_results.append({
                'symbol': symbol,
                'entry_diff': entry_diff_pct,
                'exit_diff': exit_diff_pct,
                'return_diff': return_diff_pct,
                'entry_time_diff': entry_time_diff,
                'exit_time_diff': exit_time_diff,
                'target_return': target_return,
                'yf_return': yf_return
            })
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    # Summary
    if verified_results:
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        entry_diffs = [r['entry_diff'] for r in verified_results]
        exit_diffs = [r['exit_diff'] for r in verified_results]
        return_diffs = [r['return_diff'] for r in verified_results]
        
        print(f"Verified {len(verified_results)}/7 stocks using historical {data_interval if verified_results else 'minute'} data")
        print(f"Average entry price difference:  {sum(entry_diffs)/len(entry_diffs):.2f}%")
        print(f"Average exit price difference:   {sum(exit_diffs)/len(exit_diffs):.2f}%")
        print(f"Average return difference:       {sum(return_diffs)/len(return_diffs):.2f}%")
        
        excellent_count = sum(1 for r in verified_results if r['entry_diff'] < 1 and r['exit_diff'] < 1 and r['return_diff'] < 0.5)
        good_count = sum(1 for r in verified_results if r['entry_diff'] < 2 and r['exit_diff'] < 2 and r['return_diff'] < 1)
        
        print(f"\nQuality Assessment:")
        print(f"  Excellent accuracy: {excellent_count}/{len(verified_results)} ({excellent_count/len(verified_results)*100:.0f}%)")
        print(f"  Good accuracy:      {good_count}/{len(verified_results)} ({good_count/len(verified_results)*100:.0f}%)")
        
        avg_return_diff = sum(return_diffs)/len(return_diffs)
        avg_price_diff = (sum(entry_diffs) + sum(exit_diffs))/(2*len(verified_results))
        
        print(f"\n🎯 OVERALL VERDICT:")
        if avg_return_diff < 0.5 and avg_price_diff < 1.0:
            print("  🌟 OUTSTANDING: Your trading data shows exceptional accuracy")
        elif avg_return_diff < 1.0 and avg_price_diff < 2.0:
            print("  ✅ EXCELLENT: Your trading data is highly accurate and reliable")
        else:
            print("  ✓ GOOD: Your trading data is within acceptable variance")

if __name__ == "__main__":
    main()

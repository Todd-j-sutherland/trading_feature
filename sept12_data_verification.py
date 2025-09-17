#!/usr/bin/env python3
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def main():
    print("September 12th, 2025 - Trading Data Verification")
    print("=" * 60)
    
    # Your actual September 12th data
    sept12_data = [
        {"symbol": "ANZ.AX", "actual_return": 1.1876, "entry_price": 32.84, "exit_price": 33.23},
        {"symbol": "WBC.AX", "actual_return": 1.2912, "entry_price": 37.95, "exit_price": 38.44},
        {"symbol": "CBA.AX", "actual_return": 1.2458, "entry_price": 167.77, "exit_price": 169.86},
        {"symbol": "QBE.AX", "actual_return": 1.4105, "entry_price": 20.56, "exit_price": 20.85},
        {"symbol": "SUN.AX", "actual_return": 0.8076, "entry_price": 21.05, "exit_price": 21.22},
        {"symbol": "MQG.AX", "actual_return": 2.0281, "entry_price": 219.91, "exit_price": 224.37},
        {"symbol": "NAB.AX", "actual_return": 1.2552, "entry_price": 43.02, "exit_price": 43.56}
    ]
    
    print("Verifying {} trading outcomes for September 12th, 2025".format(len(sept12_data)))
    print("Entry times around 01:00-01:30 UTC (11:00-11:30 AEST)")
    print("Exit times around 05:33 UTC (15:33 AEST)")
    
    verified_results = []
    
    for data in sept12_data:
        symbol = data["symbol"]
        db_entry_price = data["entry_price"]
        db_exit_price = data["exit_price"]
        db_return = data["actual_return"]
        
        print("\\n{} - Verifying trading outcome:".format(symbol))
        print("  Recorded Entry: ${:.4f}".format(db_entry_price))
        print("  Recorded Exit:  ${:.4f}".format(db_exit_price))
        print("  Recorded Return: {:.2f}%".format(db_return))
        
        # Calculate expected return from prices
        calculated_return = ((db_exit_price - db_entry_price) / db_entry_price) * 100
        print("  Calculated Return: {:.2f}%".format(calculated_return))
        
        # Verify against yfinance
        try:
            ticker = yf.Ticker(symbol)
            # Get September 12th, 2025 data
            hist = ticker.history(start="2025-09-12", end="2025-09-13", interval="5m")
            
            if hist.empty:
                print("  No yfinance data available for verification")
                continue
            
            # Remove timezone for easier comparison
            if hist.index.tz is not None:
                hist.index = hist.index.tz_localize(None)
            
            # Get price ranges for the day
            day_open = hist["Open"].iloc[0]
            day_close = hist["Close"].iloc[-1]
            day_high = hist["High"].max()
            day_low = hist["Low"].min()
            
            print("  YFinance Day Range: Open ${:.4f}, High ${:.4f}, Low ${:.4f}, Close ${:.4f}".format(
                day_open, day_high, day_low, day_close))
            
            # Check if recorded prices are within the day range
            entry_in_range = day_low <= db_entry_price <= day_high
            exit_in_range = day_low <= db_exit_price <= day_high
            
            print("  Entry price in range: {} (${:.4f} vs ${:.4f}-${:.4f})".format(
                "✅" if entry_in_range else "❌", db_entry_price, day_low, day_high))
            print("  Exit price in range:  {} (${:.4f} vs ${:.4f}-${:.4f})".format(
                "✅" if exit_in_range else "❌", db_exit_price, day_low, day_high))
            
            # Find closest times to 01:00 and 05:33 UTC
            entry_target = datetime(2025, 9, 12, 1, 0)  # 01:00 UTC
            exit_target = datetime(2025, 9, 12, 5, 33)  # 05:33 UTC
            
            # Find closest prices to expected times
            if len(hist) > 0:
                entry_diffs = abs(hist.index - entry_target)
                entry_idx = entry_diffs.argmin()
                yf_entry_price = hist["Close"].iloc[entry_idx]
                entry_time_actual = hist.index[entry_idx]
                
                exit_diffs = abs(hist.index - exit_target)
                exit_idx = exit_diffs.argmin()
                yf_exit_price = hist["Close"].iloc[exit_idx]
                exit_time_actual = hist.index[exit_idx]
                
                yf_return = ((yf_exit_price - yf_entry_price) / yf_entry_price) * 100
                
                entry_price_diff = abs(db_entry_price - yf_entry_price) / yf_entry_price * 100
                exit_price_diff = abs(db_exit_price - yf_exit_price) / yf_exit_price * 100
                return_diff = abs(db_return - yf_return)
                
                print("  YF Entry @ {}: ${:.4f} (±{:.2f}%)".format(
                    entry_time_actual.strftime("%H:%M"), yf_entry_price, entry_price_diff))
                print("  YF Exit @ {}:  ${:.4f} (±{:.2f}%)".format(
                    exit_time_actual.strftime("%H:%M"), yf_exit_price, exit_price_diff))
                print("  YF Return: {:.2f}% (±{:.2f}% from recorded)".format(yf_return, return_diff))
                
                verified_results.append({
                    "symbol": symbol,
                    "entry_diff": entry_price_diff,
                    "exit_diff": exit_price_diff,
                    "return_diff": return_diff,
                    "entry_in_range": entry_in_range,
                    "exit_in_range": exit_in_range,
                    "db_return": db_return,
                    "yf_return": yf_return
                })
                
        except Exception as e:
            print("  Error fetching yfinance data: {}".format(e))
            continue
    
    # Summary
    if verified_results:
        print("\\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        
        entry_diffs = [r["entry_diff"] for r in verified_results]
        exit_diffs = [r["exit_diff"] for r in verified_results]
        return_diffs = [r["return_diff"] for r in verified_results]
        
        in_range_entry = sum(1 for r in verified_results if r["entry_in_range"])
        in_range_exit = sum(1 for r in verified_results if r["exit_in_range"])
        
        print("Verified {} outcomes".format(len(verified_results)))
        print("Average entry price difference:  {:.2f}%".format(sum(entry_diffs)/len(entry_diffs)))
        print("Average exit price difference:   {:.2f}%".format(sum(exit_diffs)/len(exit_diffs)))
        print("Average return difference:       {:.2f}%".format(sum(return_diffs)/len(return_diffs)))
        
        print("\\nPrice Range Validation:")
        print("Entry prices within day range: {}/{} ({:.0f}%)".format(
            in_range_entry, len(verified_results), in_range_entry/len(verified_results)*100))
        print("Exit prices within day range:  {}/{} ({:.0f}%)".format(
            in_range_exit, len(verified_results), in_range_exit/len(verified_results)*100))
        
        good_entry = sum(1 for d in entry_diffs if d < 2.0)
        good_exit = sum(1 for d in exit_diffs if d < 2.0)
        good_return = sum(1 for d in return_diffs if d < 1.0)
        
        print("\\nAccuracy Assessment:")
        print("Entry prices within 2%:  {}/{} ({:.0f}%)".format(good_entry, len(entry_diffs), good_entry/len(entry_diffs)*100))
        print("Exit prices within 2%:   {}/{} ({:.0f}%)".format(good_exit, len(exit_diffs), good_exit/len(exit_diffs)*100))
        print("Returns within 1%:       {}/{} ({:.0f}%)".format(good_return, len(return_diffs), good_return/len(return_diffs)*100))
        
        print("\\nIndividual Results:")
        for result in verified_results:
            status = "✅" if result["entry_in_range"] and result["exit_in_range"] else "⚠️"
            print("  {} {}: DB {:.2f}% vs YF {:.2f}% (±{:.2f}%)".format(
                status, result["symbol"], result["db_return"], result["yf_return"], result["return_diff"]))

if __name__ == "__main__":
    main()

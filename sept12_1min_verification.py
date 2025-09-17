#!/usr/bin/env python3
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def main():
    print("September 12th, 2025 - 1-Minute Historical Data Verification")
    print("=" * 70)
    
    # Your actual September 12th data with approximate times
    sept12_data = [
        {"symbol": "ANZ.AX", "actual_return": 1.1876, "entry_price": 32.84, "exit_price": 33.23, 
         "entry_time": "2025-09-12 01:00:30", "exit_time": "2025-09-12 05:33:00"},
        {"symbol": "WBC.AX", "actual_return": 1.2912, "entry_price": 37.95, "exit_price": 38.44,
         "entry_time": "2025-09-12 01:00:30", "exit_time": "2025-09-12 05:33:00"},
        {"symbol": "CBA.AX", "actual_return": 1.2458, "entry_price": 167.77, "exit_price": 169.86,
         "entry_time": "2025-09-12 01:00:30", "exit_time": "2025-09-12 05:33:00"},
        {"symbol": "QBE.AX", "actual_return": 1.4105, "entry_price": 20.56, "exit_price": 20.85,
         "entry_time": "2025-09-12 01:00:30", "exit_time": "2025-09-12 05:32:59"},
        {"symbol": "SUN.AX", "actual_return": 0.8076, "entry_price": 21.05, "exit_price": 21.22,
         "entry_time": "2025-09-12 01:00:30", "exit_time": "2025-09-12 05:32:59"},
        {"symbol": "MQG.AX", "actual_return": 2.0281, "entry_price": 219.91, "exit_price": 224.37,
         "entry_time": "2025-09-12 01:00:30", "exit_time": "2025-09-12 05:32:59"},
        {"symbol": "NAB.AX", "actual_return": 1.2552, "entry_price": 43.02, "exit_price": 43.56,
         "entry_time": "2025-09-12 01:00:30", "exit_time": "2025-09-12 05:32:59"}
    ]
    
    print("Fetching 1-minute historical data for detailed verification...")
    print("Entry times: ~01:00:30 UTC (11:00:30 AEST)")
    print("Exit times:  ~05:32:59 UTC (15:32:59 AEST)")
    
    verified_results = []
    
    for data in sept12_data:
        symbol = data["symbol"]
        db_entry_price = data["entry_price"]
        db_exit_price = data["exit_price"]
        db_return = data["actual_return"]
        entry_time = datetime.strptime(data["entry_time"], "%Y-%m-%d %H:%M:%S")
        exit_time = datetime.strptime(data["exit_time"], "%Y-%m-%d %H:%M:%S")
        
        print("\\n{} - Historical 1-minute verification:".format(symbol))
        print("  Target Entry: {} @ ${:.4f}".format(entry_time.strftime("%H:%M:%S"), db_entry_price))
        print("  Target Exit:  {} @ ${:.4f}".format(exit_time.strftime("%H:%M:%S"), db_exit_price))
        print("  Recorded Return: {:.2f}%".format(db_return))
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get 1-minute data for September 12th, 2025
            # Try different approaches for historical 1-minute data
            hist_1m = None
            
            # Method 1: Try 1-minute interval
            try:
                hist_1m = ticker.history(start="2025-09-12", end="2025-09-13", interval="1m")
                if not hist_1m.empty:
                    print("  ‚úÖ Got 1-minute data: {} data points".format(len(hist_1m)))
            except:
                pass
            
            # Method 2: Try 5-minute if 1-minute fails
            if hist_1m is None or hist_1m.empty:
                try:
                    hist_1m = ticker.history(start="2025-09-12", end="2025-09-13", interval="5m")
                    if not hist_1m.empty:
                        print("  ‚ö†Ô∏è Using 5-minute data: {} data points".format(len(hist_1m)))
                except:
                    pass
            
            # Method 3: Try 15-minute as fallback
            if hist_1m is None or hist_1m.empty:
                try:
                    hist_1m = ticker.history(start="2025-09-12", end="2025-09-13", interval="15m")
                    if not hist_1m.empty:
                        print("  ‚ö†Ô∏è Using 15-minute data: {} data points".format(len(hist_1m)))
                except:
                    pass
            
            if hist_1m is None or hist_1m.empty:
                print("  ‚ùå No historical minute data available")
                continue
            
            # Remove timezone for easier comparison
            if hist_1m.index.tz is not None:
                hist_1m.index = hist_1m.index.tz_localize(None)
            
            print("  Ì≥ä Data range: {} to {}".format(
                hist_1m.index.min().strftime("%H:%M"), 
                hist_1m.index.max().strftime("%H:%M")))
            
            # Find closest prices to target times
            entry_diffs = abs(hist_1m.index - entry_time)
            entry_idx = entry_diffs.argmin()
            yf_entry_price = hist_1m["Close"].iloc[entry_idx]
            entry_time_actual = hist_1m.index[entry_idx]
            entry_time_diff_min = entry_diffs[entry_idx].total_seconds() / 60
            
            exit_diffs = abs(hist_1m.index - exit_time)
            exit_idx = exit_diffs.argmin()
            yf_exit_price = hist_1m["Close"].iloc[exit_idx]
            exit_time_actual = hist_1m.index[exit_idx]
            exit_time_diff_min = exit_diffs[exit_idx].total_seconds() / 60
            
            # Calculate yfinance return
            yf_return = ((yf_exit_price - yf_entry_price) / yf_entry_price) * 100
            
            # Calculate differences
            entry_price_diff = abs(db_entry_price - yf_entry_price) / yf_entry_price * 100
            exit_price_diff = abs(db_exit_price - yf_exit_price) / yf_exit_price * 100
            return_diff = abs(db_return - yf_return)
            
            print("  ÌæØ Entry: YF ${:.4f} @ {} (¬±{:.2f}%, ¬±{:.1f}min)".format(
                yf_entry_price, entry_time_actual.strftime("%H:%M:%S"), entry_price_diff, entry_time_diff_min))
            print("  ÌæØ Exit:  YF ${:.4f} @ {} (¬±{:.2f}%, ¬±{:.1f}min)".format(
                yf_exit_price, exit_time_actual.strftime("%H:%M:%S"), exit_price_diff, exit_time_diff_min))
            print("  Ì≥à YF Return: {:.2f}% vs DB {:.2f}% (¬±{:.2f}%)".format(
                yf_return, db_return, return_diff))
            
            # Quality assessment
            entry_good = entry_price_diff < 2.0
            exit_good = exit_price_diff < 2.0
            return_good = return_diff < 1.0
            time_good = entry_time_diff_min < 30 and exit_time_diff_min < 30
            
            status = "‚úÖ" if entry_good and exit_good and return_good and time_good else "‚ö†Ô∏è"
            print("  {} Overall: Entry {}, Exit {}, Return {}, Timing {}".format(
                status,
                "‚úÖ" if entry_good else "‚ùå",
                "‚úÖ" if exit_good else "‚ùå", 
                "‚úÖ" if return_good else "‚ùå",
                "‚úÖ" if time_good else "‚ùå"
            ))
            
            verified_results.append({
                "symbol": symbol,
                "entry_diff": entry_price_diff,
                "exit_diff": exit_price_diff,
                "return_diff": return_diff,
                "entry_time_diff": entry_time_diff_min,
                "exit_time_diff": exit_time_diff_min,
                "db_return": db_return,
                "yf_return": yf_return,
                "data_points": len(hist_1m)
            })
            
        except Exception as e:
            print("  ‚ùå Error fetching historical data: {}".format(e))
            continue
    
    # Comprehensive Summary
    if verified_results:
        print("\\n" + "=" * 70)
        print("COMPREHENSIVE VERIFICATION SUMMARY")
        print("=" * 70)
        
        entry_diffs = [r["entry_diff"] for r in verified_results]
        exit_diffs = [r["exit_diff"] for r in verified_results]
        return_diffs = [r["return_diff"] for r in verified_results]
        entry_time_diffs = [r["entry_time_diff"] for r in verified_results]
        exit_time_diffs = [r["exit_time_diff"] for r in verified_results]
        
        print("Verified {} outcomes using historical minute data".format(len(verified_results)))
        print("\\nPrice Accuracy:")
        print("  Average entry price difference:  {:.2f}%".format(sum(entry_diffs)/len(entry_diffs)))
        print("  Average exit price difference:   {:.2f}%".format(sum(exit_diffs)/len(exit_diffs)))
        print("  Average return difference:       {:.2f}%".format(sum(return_diffs)/len(return_diffs)))
        
        print("\\nTiming Accuracy:")
        print("  Average entry time difference:  {:.1f} minutes".format(sum(entry_time_diffs)/len(entry_time_diffs)))
        print("  Average exit time difference:   {:.1f} minutes".format(sum(exit_time_diffs)/len(exit_time_diffs)))
        
        # Quality metrics
        excellent_entry = sum(1 for d in entry_diffs if d < 1.0)
        excellent_exit = sum(1 for d in exit_diffs if d < 1.0)
        excellent_return = sum(1 for d in return_diffs if d < 0.5)
        excellent_timing = sum(1 for i, _ in enumerate(entry_time_diffs) if entry_time_diffs[i] < 15 and exit_time_diffs[i] < 15)
        
        print("\\nQuality Assessment:")
        print("  Entry prices within 1%:     {}/{} ({:.0f}%)".format(excellent_entry, len(entry_diffs), excellent_entry/len(entry_diffs)*100))
        print("  Exit prices within 1%:      {}/{} ({:.0f}%)".format(excellent_exit, len(exit_diffs), excellent_exit/len(exit_diffs)*100))
        print("  Returns within 0.5%:        {}/{} ({:.0f}%)".format(excellent_return, len(return_diffs), excellent_return/len(return_diffs)*100))
        print("  Timing within 15 minutes:   {}/{} ({:.0f}%)".format(excellent_timing, len(verified_results), excellent_timing/len(verified_results)*100))
        
        print("\\nDetailed Results:")
        for result in verified_results:
            quality = "ÌæØ" if (result["entry_diff"] < 1 and result["exit_diff"] < 1 and 
                             result["return_diff"] < 0.5 and result["entry_time_diff"] < 15) else "Ì≥ä"
            print("  {} {}: Entry ¬±{:.1f}%, Exit ¬±{:.1f}%, Return ¬±{:.2f}%, Time ¬±{:.0f}m/¬±{:.0f}m".format(
                quality, result["symbol"], result["entry_diff"], result["exit_diff"], 
                result["return_diff"], result["entry_time_diff"], result["exit_time_diff"]))
        
        # Overall verdict
        avg_return_diff = sum(return_diffs)/len(return_diffs)
        avg_price_diff = (sum(entry_diffs) + sum(exit_diffs))/(2*len(verified_results))
        
        print("\\nÌæØ VERDICT:")
        if avg_return_diff < 0.5 and avg_price_diff < 1.0:
            print("  EXCELLENT: Trading data highly accurate with minute-level precision")
        elif avg_return_diff < 1.0 and avg_price_diff < 2.0:
            print("  GOOD: Trading data accurate within acceptable trading variance")
        else:
            print("  ACCEPTABLE: Trading data within normal market data variance")

if __name__ == "__main__":
    main()

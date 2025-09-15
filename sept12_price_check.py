#!/usr/bin/env python3
import sqlite3
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def main():
    print("Price Verification Tool - September 12th, 2025")
    print("=" * 55)
    
    # Get Sep 12th outcomes from database
    conn = sqlite3.connect("/root/test/trading_predictions.db")
    query = """
    SELECT 
        p.symbol,
        p.prediction_timestamp as entry_time,
        o.evaluation_timestamp as exit_time,
        o.entry_price,
        o.exit_price,
        o.actual_return
    FROM outcomes o
    JOIN predictions p ON o.prediction_id = p.prediction_id
    WHERE date(o.evaluation_timestamp) = "2025-09-12"
    ORDER BY o.evaluation_timestamp
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("Found {} outcomes for 2025-09-12".format(len(df)))
    
    # Your expected data:
    expected_returns = {
        "ANZ.AX": 1.1876,
        "WBC.AX": 1.2912,
        "CBA.AX": 1.2458,
        "QBE.AX": 1.4105,
        "SUN.AX": 0.8076,
        "MQG.AX": 2.0281,
        "NAB.AX": 1.2552
    }
    
    verified_results = []
    
    for idx, row in df.iterrows():
        symbol = row["symbol"]
        
        # Parse datetime (handle ISO format)
        entry_time_str = row["entry_time"]
        exit_time_str = row["exit_time"]
        
        if "T" in entry_time_str:
            entry_time = datetime.fromisoformat(entry_time_str.replace("T", " ").split(".")[0])
            exit_time = datetime.fromisoformat(exit_time_str.replace("T", " ").split(".")[0])
        else:
            entry_time = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
            exit_time = datetime.strptime(exit_time_str, "%Y-%m-%d %H:%M:%S")
        
        db_entry_price = float(row["entry_price"])
        db_exit_price = float(row["exit_price"])
        db_return = float(row["actual_return"])
        
        print("\\n{}: DB Return {:.2f}%".format(symbol, db_return))
        if symbol in expected_returns:
            expected = expected_returns[symbol]
            print("  Expected: {:.2f}%, Difference: {:.3f}%".format(expected, abs(db_return - expected)))
        
        # Get yfinance data for verification
        try:
            ticker = yf.Ticker(symbol)
            start_date = entry_time.date()
            end_date = start_date + timedelta(days=1)
            hist = ticker.history(start=start_date, end=end_date, interval="5m")
            
            if hist.empty:
                print("  No yfinance data available")
                continue
                
            # Remove timezone
            if hist.index.tz is not None:
                hist.index = hist.index.tz_localize(None)
            
            # Find closest prices
            entry_diffs = abs(hist.index - entry_time)
            entry_idx = entry_diffs.argmin()
            yf_entry_price = hist["Close"].iloc[entry_idx]
            entry_time_diff = entry_diffs[entry_idx].total_seconds() / 60
            
            exit_diffs = abs(hist.index - exit_time)
            exit_idx = exit_diffs.argmin()
            yf_exit_price = hist["Close"].iloc[exit_idx]
            exit_time_diff = exit_diffs[exit_idx].total_seconds() / 60
            
            # Calculate yfinance return
            yf_return = ((yf_exit_price - yf_entry_price) / yf_entry_price) * 100
            
            # Calculate differences
            entry_price_diff = abs(db_entry_price - yf_entry_price) / yf_entry_price * 100
            exit_price_diff = abs(db_exit_price - yf_exit_price) / yf_exit_price * 100
            return_diff = abs(db_return - yf_return)
            
            print("  Entry: DB ${:.4f} vs YF ${:.4f} (±{:.1f}%, ±{:.0f}min)".format(
                db_entry_price, yf_entry_price, entry_price_diff, entry_time_diff))
            print("  Exit:  DB ${:.4f} vs YF ${:.4f} (±{:.1f}%, ±{:.0f}min)".format(
                db_exit_price, yf_exit_price, exit_price_diff, exit_time_diff))
            print("  Return: DB {:.2f}% vs YF {:.2f}% (±{:.2f}%)".format(
                db_return, yf_return, return_diff))
            
            verified_results.append({
                "symbol": symbol,
                "entry_diff": entry_price_diff,
                "exit_diff": exit_price_diff,
                "return_diff": return_diff,
                "db_return": db_return,
                "yf_return": yf_return
            })
            
        except Exception as e:
            print("  Error: {}".format(e))
            continue
    
    # Summary
    if verified_results:
        print("\\n" + "=" * 55)
        print("VERIFICATION SUMMARY")
        print("=" * 55)
        
        entry_diffs = [r["entry_diff"] for r in verified_results]
        exit_diffs = [r["exit_diff"] for r in verified_results]
        return_diffs = [r["return_diff"] for r in verified_results]
        
        print("Verified {} outcomes".format(len(verified_results)))
        print("Average entry price difference:  {:.2f}%".format(sum(entry_diffs)/len(entry_diffs)))
        print("Average exit price difference:   {:.2f}%".format(sum(exit_diffs)/len(exit_diffs)))
        print("Average return difference:       {:.2f}%".format(sum(return_diffs)/len(return_diffs)))
        
        # Quality assessment
        good_entry = sum(1 for d in entry_diffs if d < 2.0)
        good_exit = sum(1 for d in exit_diffs if d < 2.0)
        good_return = sum(1 for d in return_diffs if d < 1.0)
        
        print("\\nQuality Assessment:")
        print("Entry prices within 2%:  {}/{} ({:.0f}%)".format(good_entry, len(entry_diffs), good_entry/len(entry_diffs)*100))
        print("Exit prices within 2%:   {}/{} ({:.0f}%)".format(good_exit, len(exit_diffs), good_exit/len(exit_diffs)*100))
        print("Returns within 1%:       {}/{} ({:.0f}%)".format(good_return, len(return_diffs), good_return/len(return_diffs)*100))
        
        print("\\nIndividual Return Comparison:")
        for result in verified_results:
            print("  {}: DB {:.2f}% vs YF {:.2f}% (±{:.2f}%)".format(
                result["symbol"], result["db_return"], result["yf_return"], result["return_diff"]))

if __name__ == "__main__":
    main()

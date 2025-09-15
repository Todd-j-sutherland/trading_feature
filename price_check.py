#!/usr/bin/env python3
import sqlite3
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def main():
    print("Price Verification Tool - Sep 9th Sample")
    print("=" * 50)
    
    # Get a few outcomes from Sep 9th
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
    WHERE date(o.evaluation_timestamp) = "2025-09-09"
    ORDER BY o.evaluation_timestamp
    LIMIT 5
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("Found {} sample outcomes for 2025-09-09".format(len(df)))
    
    verified_results = []
    
    for idx, row in df.iterrows():
        symbol = row["symbol"]
        entry_time = datetime.fromisoformat(row["entry_time"].replace("T", " ").split(".")[0])
        exit_time = datetime.fromisoformat(row["exit_time"].replace("T", " ").split(".")[0])
        db_entry_price = float(row["entry_price"])
        db_exit_price = float(row["exit_price"])
        db_return = float(row["actual_return"])
        
        print("\\n{}:".format(symbol))
        print("  Entry: {} @ ${:.4f}".format(entry_time.strftime("%H:%M"), db_entry_price))
        print("  Exit:  {} @ ${:.4f}".format(exit_time.strftime("%H:%M"), db_exit_price))
        print("  Return: {:.2f}%".format(db_return))
        
        # Get yfinance data
        try:
            ticker = yf.Ticker(symbol)
            start_date = entry_time.date()
            end_date = start_date + timedelta(days=1)
            hist = ticker.history(start=start_date, end=end_date, interval="5m")
            
            if hist.empty:
                print("  No yfinance data available")
                continue
                
            # Remove timezone for comparison
            if hist.index.tz is not None:
                hist.index = hist.index.tz_localize(None)
            
            # Find closest entry price
            entry_diffs = abs(hist.index - entry_time)
            entry_idx = entry_diffs.argmin()
            yf_entry_price = hist["Close"].iloc[entry_idx]
            entry_time_diff = entry_diffs[entry_idx].total_seconds() / 60
            
            # Find closest exit price
            exit_diffs = abs(hist.index - exit_time)
            exit_idx = exit_diffs.argmin()
            yf_exit_price = hist["Close"].iloc[exit_idx]
            exit_time_diff = exit_diffs[exit_idx].total_seconds() / 60
            
            # Calculate differences
            yf_return = ((yf_exit_price - yf_entry_price) / yf_entry_price) * 100
            entry_price_diff = abs(db_entry_price - yf_entry_price) / yf_entry_price * 100
            exit_price_diff = abs(db_exit_price - yf_exit_price) / yf_exit_price * 100
            return_diff = abs(db_return - yf_return)
            
            print("  YF Entry: ${:.4f} (±{:.0f}min)".format(yf_entry_price, entry_time_diff))
            print("  YF Exit:  ${:.4f} (±{:.0f}min)".format(yf_exit_price, exit_time_diff))
            print("  YF Return: {:.2f}%".format(yf_return))
            print("  Diffs: Entry ±{:.1f}%, Exit ±{:.1f}%, Return ±{:.1f}%".format(entry_price_diff, exit_price_diff, return_diff))
            
            verified_results.append({
                "symbol": symbol,
                "entry_diff": entry_price_diff,
                "exit_diff": exit_price_diff,
                "return_diff": return_diff
            })
            
        except Exception as e:
            print("  Error: {}".format(e))
            continue
    
    # Summary
    if verified_results:
        print("\\n" + "=" * 50)
        print("SUMMARY:")
        entry_diffs = [r["entry_diff"] for r in verified_results]
        exit_diffs = [r["exit_diff"] for r in verified_results]
        return_diffs = [r["return_diff"] for r in verified_results]
        
        print("Verified {} outcomes".format(len(verified_results)))
        print("Avg entry price diff: {:.2f}%".format(sum(entry_diffs)/len(entry_diffs)))
        print("Avg exit price diff:  {:.2f}%".format(sum(exit_diffs)/len(exit_diffs)))
        print("Avg return diff:      {:.2f}%".format(sum(return_diffs)/len(return_diffs)))
        
        good_entry = sum(1 for d in entry_diffs if d < 2.0)
        good_exit = sum(1 for d in exit_diffs if d < 2.0)
        good_return = sum(1 for d in return_diffs if d < 1.0)
        
        print("\\nQuality:")
        print("Entry prices within 2%: {}/{} ({:.0f}%)".format(good_entry, len(entry_diffs), good_entry/len(entry_diffs)*100))
        print("Exit prices within 2%:  {}/{} ({:.0f}%)".format(good_exit, len(exit_diffs), good_exit/len(exit_diffs)*100))
        print("Returns within 1%:      {}/{} ({:.0f}%)".format(good_return, len(return_diffs), good_return/len(return_diffs)*100))

if __name__ == "__main__":
    main()

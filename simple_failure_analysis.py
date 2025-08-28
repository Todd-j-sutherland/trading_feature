#!/usr/bin/env python3
"""
Simplified BUY Signal Failure Analysis
"""

import sqlite3

def analyze_failures():
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("BUY SIGNAL FAILURE ANALYSIS - WEEK OF AUG 25-27")
    print("="*60)
    
    # Get failed BUY signals
    cursor.execute("""
    SELECT p.symbol, p.prediction_timestamp, p.action_confidence, 
           p.entry_price, o.actual_return, o.exit_price
    FROM predictions p
    JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE DATE(p.prediction_timestamp) >= '2025-08-25'
      AND p.predicted_action = 'BUY'
      AND o.actual_return < 0
    ORDER BY p.symbol, o.actual_return ASC
    """)
    
    failures = cursor.fetchall()
    print(f"Total failed BUY signals: {len(failures)}")
    print("-" * 40)
    
    # Group by symbol
    by_symbol = {}
    for row in failures:
        symbol = row[0]
        if symbol not in by_symbol:
            by_symbol[symbol] = []
        by_symbol[symbol].append(row)
    
    # Analyze each symbol
    for symbol, symbol_failures in by_symbol.items():
        print(f"\n{symbol} - {len(symbol_failures)} failures:")
        
        total_loss = sum(row[4] for row in symbol_failures)
        avg_confidence = sum(row[2] for row in symbol_failures) / len(symbol_failures)
        
        print(f"  Average confidence: {avg_confidence:.3f}")
        print(f"  Total loss: {total_loss*100:.1f}%")
        print("  Individual losses:")
        
        for i, row in enumerate(symbol_failures, 1):
            timestamp, confidence, entry, actual_return, exit = row[1], row[2], row[3], row[4], row[5]
            loss_pct = actual_return * 100
            print(f"    {i}. {timestamp[:10]} | Conf: {confidence:.3f} | Loss: {loss_pct:.1f}%")
    
    # Summary statistics
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print("="*60)
    
    all_losses = [row[4] for row in failures]
    all_confidences = [row[2] for row in failures]
    
    print(f"Total symbols with failures: {len(by_symbol)}")
    print(f"Average failure confidence: {sum(all_confidences)/len(all_confidences):.3f}")
    print(f"Average loss per failure: {sum(all_losses)/len(all_losses)*100:.1f}%")
    print(f"Worst single loss: {min(all_losses)*100:.1f}%")
    
    # High confidence failures (concerning)
    high_conf = [row for row in failures if row[2] > 0.75]
    if high_conf:
        print(f"\nHigh confidence failures (>0.75): {len(high_conf)}")
        for row in high_conf:
            symbol, timestamp, confidence, entry, actual_return, exit = row
            print(f"  {symbol}: {confidence:.3f} confidence, {actual_return*100:.1f}% loss")
    
    conn.close()

if __name__ == "__main__":
    analyze_failures()

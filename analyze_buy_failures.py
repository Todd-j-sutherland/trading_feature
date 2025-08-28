#!/usr/bin/env python3
"""
Comprehensive BUY Signal Failure Analysis
Analyzes failed BUY predictions to identify patterns and issues
"""

import sqlite3
from datetime import datetime

def analyze_buy_failures():
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("COMPREHENSIVE BUY SIGNAL FAILURE ANALYSIS")
    print("="*60)
    
    # Get all failed BUY signals
    cursor.execute("""
    SELECT p.symbol, p.prediction_timestamp, p.action_confidence, 
           p.entry_price, p.predicted_magnitude,
           o.actual_return, o.exit_price
    FROM predictions p
    JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE DATE(p.prediction_timestamp) >= '2025-08-25'
      AND p.predicted_action = 'BUY'
      AND o.actual_return <= 0
    ORDER BY o.actual_return ASC
    """)
    
    failed_buys = cursor.fetchall()
    print(f"\nTOTAL FAILED BUY SIGNALS: {len(failed_buys)}")
    print("-" * 40)
    
    # Analyze by symbol
    symbol_failures = {}
    for row in failed_buys:
        symbol, pred_time, confidence, entry_price, pred_mag, actual_return, exit_price = row
        
        if symbol not in symbol_failures:
            symbol_failures[symbol] = []
        
        symbol_failures[symbol].append({
            'timestamp': pred_time,
            'confidence': float(confidence) if confidence else 0.0,
            'entry_price': float(entry_price) if entry_price else 0.0,
            'predicted_magnitude': float(pred_mag) if pred_mag else 0.0,
            'actual_return': float(actual_return) if actual_return else 0.0,
            'exit_price': float(exit_price) if exit_price else 0.0
        })
    
    # Detailed symbol analysis
    for symbol, failures in symbol_failures.items():
        print(f"\n{symbol} FAILURE ANALYSIS:")
        print(f"  Failed signals: {len(failures)}")
        
        avg_confidence = sum(f['confidence'] for f in failures) / len(failures)
        avg_loss = sum(f['actual_return'] for f in failures) / len(failures)
        worst_loss = min(f['actual_return'] for f in failures)
        
        print(f"  Average confidence: {avg_confidence:.3f}")
        print(f"  Average loss: {avg_loss*100:.2f}%")
        print(f"  Worst loss: {worst_loss*100:.2f}%")
        
        print("  Individual failures:")
        for i, failure in enumerate(failures[:5], 1):  # Show first 5
            print(f"    {i}. {failure['timestamp']} | "
                  f"Conf: {failure['confidence']:.3f} | "
                  f"Entry: ${failure['entry_price']:.2f} | "
                  f"Loss: {failure['actual_return']*100:.2f}%")
    
    # Overall pattern analysis
    print(f"\n{'='*60}")
    print("PATTERN ANALYSIS:")
    print("="*60)
    
    all_confidences = [f['confidence'] for failures in symbol_failures.values() for f in failures]
    all_losses = [f['actual_return'] for failures in symbol_failures.values() for f in failures]
    
    print(f"Average failure confidence: {sum(all_confidences)/len(all_confidences):.3f}")
    print(f"Average failure loss: {sum(all_losses)/len(all_losses)*100:.2f}%")
    print(f"Confidence range: {min(all_confidences):.3f} - {max(all_confidences):.3f}")
    
    # High confidence failures (most concerning)
    high_conf_failures = [f for failures in symbol_failures.values() for f in failures if f['confidence'] > 0.8]
    if high_conf_failures:
        print(f"\nHIGH CONFIDENCE FAILURES (>0.8): {len(high_conf_failures)}")
        for failure in high_conf_failures:
            print(f"  Confidence: {failure['confidence']:.3f}, Loss: {failure['actual_return']*100:.2f}%")
    
    conn.close()

if __name__ == "__main__":
    analyze_buy_failures()

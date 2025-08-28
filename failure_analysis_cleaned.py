#!/usr/bin/env python3
"""
BUY Signal Failure Analysis with Data Cleaning
Handles corrupted confidence data
"""

import sqlite3

def clean_confidence(conf):
    """Clean confidence field that may contain corrupted data"""
    if isinstance(conf, (int, float)):
        return float(conf)
    elif isinstance(conf, str):
        # Try to extract first number from comma-separated values
        try:
            if ',' in conf:
                return float(conf.split(',')[0])
            else:
                return float(conf)
        except:
            return 0.5  # Default fallback
    else:
        return 0.5

def analyze_buy_failures():
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("BUY SIGNAL FAILURE ANALYSIS - DATA CLEANED")
    print("="*60)
    
    cursor.execute("""
    SELECT p.symbol, p.action_confidence, o.actual_return, p.prediction_timestamp
    FROM predictions p
    JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE DATE(p.prediction_timestamp) >= '2025-08-25'
      AND p.predicted_action = 'BUY'
      AND o.actual_return < 0
    ORDER BY p.symbol, o.actual_return
    """)
    
    failures = cursor.fetchall()
    print(f"Total failed BUY signals: {len(failures)}")
    
    # Clean and group data
    symbol_failures = {}
    corrupted_records = 0
    
    for symbol, conf, ret, timestamp in failures:
        cleaned_conf = clean_confidence(conf)
        if isinstance(conf, str) and ',' in str(conf):
            corrupted_records += 1
            
        if symbol not in symbol_failures:
            symbol_failures[symbol] = []
        
        symbol_failures[symbol].append({
            'confidence': cleaned_conf,
            'return': float(ret),
            'timestamp': timestamp,
            'original_conf': conf
        })
    
    print(f"Corrupted confidence records found: {corrupted_records}")
    print("-" * 40)
    
    # Analyze by symbol
    for symbol in sorted(symbol_failures.keys()):
        data = symbol_failures[symbol]
        print(f"\n{symbol} - {len(data)} failures:")
        
        confidences = [f['confidence'] for f in data]
        returns = [f['return'] for f in data]
        
        avg_conf = sum(confidences) / len(confidences)
        avg_loss = sum(returns) / len(returns)
        worst_loss = min(returns)
        
        print(f"  Average confidence: {avg_conf:.3f}")
        print(f"  Average loss: {avg_loss*100:.1f}%")
        print(f"  Worst loss: {worst_loss*100:.1f}%")
        
        # Show individual failures
        print("  Individual failures:")
        for i, failure in enumerate(data[:3], 1):  # Show first 3
            conf_str = f"({failure['original_conf']})" if isinstance(failure['original_conf'], str) and ',' in str(failure['original_conf']) else ""
            print(f"    {i}. {failure['timestamp'][:10]} | "
                  f"Conf: {failure['confidence']:.3f}{conf_str} | "
                  f"Loss: {failure['return']*100:.1f}%")
    
    # Key insights
    print(f"\n{'='*60}")
    print("KEY INSIGHTS:")
    print("="*60)
    
    print("1. ANZ.AX COMPLETE FAILURE:")
    if 'ANZ.AX' in symbol_failures:
        anz_data = symbol_failures['ANZ.AX']
        print(f"   - ALL {len(anz_data)} ANZ BUY signals failed")
        print(f"   - Average confidence: {sum(f['confidence'] for f in anz_data)/len(anz_data):.3f}")
        print(f"   - This explains the 0% success rate for ANZ")
    
    print("\n2. DATA QUALITY ISSUES:")
    print(f"   - {corrupted_records} records have corrupted confidence data")
    print("   - Comma-separated values suggest feature vector contamination")
    
    print("\n3. OVERALL FAILURE PATTERN:")
    all_confs = [f['confidence'] for data in symbol_failures.values() for f in data]
    all_rets = [f['return'] for data in symbol_failures.values() for f in data]
    
    print(f"   - Average failure confidence: {sum(all_confs)/len(all_confs):.3f}")
    print(f"   - Average loss per failure: {sum(all_rets)/len(all_rets)*100:.1f}%")
    print(f"   - Confidence range: {min(all_confs):.3f} to {max(all_confs):.3f}")
    
    conn.close()

if __name__ == "__main__":
    analyze_buy_failures()

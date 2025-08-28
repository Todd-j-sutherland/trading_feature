#!/usr/bin/env python3
"""
Simple Prediction to Paper Trading Integration
Usage: python send_signal.py SYMBOL PREDICTION CONFIDENCE [REASONING]
Example: python send_signal.py CBA.AX BUY 0.85 "Strong ML signal"
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integration.prediction_signal_handler import send_prediction_signal

def main():
    if len(sys.argv) < 4:
        print("Usage: python send_signal.py SYMBOL PREDICTION CONFIDENCE [REASONING]")
        print("Example: python send_signal.py CBA.AX BUY 0.85 'Strong ML signal'")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    prediction = sys.argv[2].upper()
    
    try:
        confidence = float(sys.argv[3])
    except ValueError:
        print("Error: Confidence must be a number between 0 and 1")
        sys.exit(1)
    
    reasoning = sys.argv[4] if len(sys.argv) > 4 else "ML Prediction Signal"
    
    # Validate inputs
    if prediction not in ['BUY', 'SELL', 'HOLD']:
        print("Error: Prediction must be BUY, SELL, or HOLD")
        sys.exit(1)
    
    if not 0 <= confidence <= 1:
        print("Error: Confidence must be between 0 and 1")
        sys.exit(1)
    
    # Send the signal
    print(f"📡 Sending signal: {symbol} {prediction} (confidence: {confidence:.2f})")
    print(f"🧠 Reasoning: {reasoning}")
    print("=" * 50)
    
    result = send_prediction_signal(symbol, prediction, confidence, reasoning)
    
    if result.success:
        print(f"✅ SUCCESS: {result.message}")
        if result.executed_price:
            print(f"💰 Executed at: ${result.executed_price:.2f}")
        if result.executed_quantity:
            print(f"📊 Quantity: {result.executed_quantity} shares")
        if result.commission:
            print(f"💸 Commission: ${result.commission:.2f}")
    else:
        print(f"❌ FAILED: {result.message}")

if __name__ == "__main__":
    main()

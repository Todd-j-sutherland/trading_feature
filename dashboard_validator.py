#!/usr/bin/env python3
"""
Real-time Dashboard Validator
Run this alongside the Streamlit dashboard to confirm expected values
"""

import time
import sys
sys.path.append('.')

from datetime import datetime
from dashboard import compute_overview_metrics
from enhanced_confidence_metrics import compute_enhanced_confidence_metrics

def validate_dashboard_continuously():
    """Continuously validate what the dashboard should be showing"""
    
    print("=" * 60)
    print("🔍 REAL-TIME DASHBOARD VALIDATOR")
    print("=" * 60)
    print("Run this while viewing the dashboard to confirm expected values")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Get current data
            overview = compute_overview_metrics()
            confidence = compute_enhanced_confidence_metrics()
            
            ml_data = overview['ml']
            
            print(f"[{timestamp}] EXPECTED DASHBOARD VALUES:")
            print(f"  🎯 Win Rate: {ml_data['win_rate']:.1%}")
            print(f"  💰 Avg Return: {ml_data['avg_return']*100:.1f}%")
            print(f"  📊 Completed Trades: {ml_data['outcomes_completed']}")
            print(f"  🔢 Total Features: {ml_data['predictions']}")
            print(f"  🤖 ML Status: {ml_data['status']}")
            print(f"  ✅ Overall Confidence: {confidence['overall_integration']['confidence']:.1%} ({confidence['overall_integration']['status']})")
            print()
            
            # If dashboard shows different values, indicate the problem
            if ml_data['avg_return'] > 0.4:  # Should be ~44.7%
                print("  ✅ Data looks correct - if dashboard differs, it's a cache issue")
            else:
                print("  ❌ Data issue detected!")
            
            print("-" * 50)
            time.sleep(10)  # Update every 10 seconds
            
    except KeyboardInterrupt:
        print("\n👋 Validator stopped")

if __name__ == "__main__":
    validate_dashboard_continuously()

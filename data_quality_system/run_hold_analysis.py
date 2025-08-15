#!/usr/bin/env python3
"""
Quick HOLD Analysis Runner
Test the HOLD position analyzer with local or remote data
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from hold_analyzer import HOLDPositionAnalyzer

def main():
    print("🔒 HOLD Position Analysis Tool")
    print("="*50)
    
    # Try to find database
    db_paths = [
        "data/trading_predictions.db",
        "../data/trading_predictions.db", 
        "/root/test/data/trading_predictions.db"
    ]
    
    db_found = None
    for path in db_paths:
        if os.path.exists(path):
            db_found = path
            break
    
    if db_found:
        print(f"📁 Found database: {db_found}")
        analyzer = HOLDPositionAnalyzer(db_found)
    else:
        print("⚠️  No local database found, will try default paths...")
        analyzer = HOLDPositionAnalyzer()
    
    try:
        report = analyzer.generate_hold_analysis_report()
        
        if 'error' not in report:
            analyzer.print_summary(report)
            print("\n✅ HOLD analysis completed successfully!")
        else:
            print(f"❌ Analysis failed: {report['error']}")
            
    except Exception as e:
        print(f"❌ Error running analysis: {str(e)}")
        print("\n💡 Make sure you have the required dependencies:")
        print("   pip install pandas numpy yfinance")

if __name__ == "__main__":
    main()

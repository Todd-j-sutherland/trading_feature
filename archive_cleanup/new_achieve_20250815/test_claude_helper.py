#!/usr/bin/env python3
"""
Test Claude Analysis Helper with Real Morning Routine Data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from claude_analysis_helper import format_for_claude, save_claude_prompt

def test_with_real_morning_data():
    """Test with data that matches your actual morning routine output"""
    
    # This matches the format from your actual morning routine
    real_morning_results = {
        "CBA.AX": {"action": "HOLD", "confidence": 0.592, "direction": "DOWN -0.16%"},
        "WBC.AX": {"action": "HOLD", "confidence": 0.599, "direction": "DOWN -0.17%"},
        "ANZ.AX": {"action": "HOLD", "confidence": 0.595, "direction": "DOWN -0.17%"},
        "NAB.AX": {"action": "HOLD", "confidence": 0.587, "direction": "DOWN -0.17%"},
        "MQG.AX": {"action": "HOLD", "confidence": 0.594, "direction": "DOWN -0.16%"},
        "SUN.AX": {"action": "HOLD", "confidence": 0.591, "direction": "DOWN -0.16%"},
        "QBE.AX": {"action": "HOLD", "confidence": 0.596, "direction": "DOWN -0.16%"},
        "market_sentiment": "-0.083",
        "agreement_rate": "71.4% (5/7)",
        "quality_score": "100.0%",
        "banks_analyzed": "7",
        "features_per_bank": "53",
        "market_regime": "NEUTRAL"
    }
    
    print("🧪 TESTING CLAUDE ANALYSIS HELPER")
    print("=" * 50)
    print("📊 Using real morning routine data format...")
    
    # Format for Claude
    formatted = format_for_claude(real_morning_results)
    
    # Save to file
    filename = save_claude_prompt(formatted, "test_claude_analysis.txt")
    
    print(f"\n✅ SUCCESS! Generated Claude analysis prompt")
    print(f"📂 File: {filename}")
    
    # Show preview
    print(f"\n📋 PREVIEW (first 300 chars):")
    print("-" * 50)
    print(formatted[:300] + "...")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"1. Open the file: {filename}")
    print(f"2. Copy all content")
    print(f"3. Paste into Claude web interface")
    print(f"4. Get professional trading analysis!")
    
    return filename

if __name__ == "__main__":
    test_with_real_morning_data()

#!/usr/bin/env python3
"""
Integration Script: Morning Routine → Claude Analysis
Run this after your morning routine to generate Claude analysis prompts
"""

import re
import sys
from datetime import datetime
from claude_analysis_helper import format_for_claude, save_claude_prompt

def parse_morning_output(output_text):
    """Parse morning routine output into structured data"""
    results = {}
    
    # Extract ML predictions
    prediction_pattern = r'(\w+\.AX):\s+(\w+)\s+\(([\d.]+)\)\s+-\s+(.*?)(?=\n|$)'
    matches = re.findall(prediction_pattern, output_text)
    
    for symbol, action, confidence, direction in matches:
        results[symbol] = {
            "action": action,
            "confidence": float(confidence),
            "direction": direction
        }
    
    # Extract market overview
    sentiment_match = re.search(r'Market Sentiment:\s*([-\d.]+)', output_text)
    if sentiment_match:
        results["market_sentiment"] = sentiment_match.group(1)
    
    agreement_match = re.search(r'Agreement Rate:\s*([\d.%\s\(\)/]+)', output_text)
    if agreement_match:
        results["agreement_rate"] = agreement_match.group(1)
    
    quality_match = re.search(r'Quality Score:\s*([\d.%]+)', output_text)
    if quality_match:
        results["quality_score"] = quality_match.group(1)
    
    return results

def main():
    print("🤖 MORNING ROUTINE → CLAUDE INTEGRATION")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Read from file
        input_file = sys.argv[1]
        print(f"📂 Reading from file: {input_file}")
        try:
            with open(input_file, 'r') as f:
                morning_output = f.read()
        except FileNotFoundError:
            print(f"❌ File not found: {input_file}")
            return
    else:
        # Read from clipboard or manual input
        print("📋 Paste your morning routine output below (Press Ctrl+D when done):")
        print("-" * 30)
        morning_output = sys.stdin.read()
    
    # Parse the output
    parsed_data = parse_morning_output(morning_output)
    
    if not parsed_data:
        print("❌ No trading data found in input")
        print("💡 Make sure you're pasting the ML PREDICTIONS SUMMARY section")
        return
    
    print(f"✅ Parsed {len([k for k in parsed_data.keys() if '.AX' in k])} bank predictions")
    
    # Format for Claude
    formatted = format_for_claude(parsed_data)
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"claude_analysis_{timestamp}.txt"
    save_claude_prompt(formatted, filename)
    
    print(f"\n🎯 READY FOR CLAUDE!")
    print(f"📂 File: {filename}")
    print(f"📋 Next steps:")
    print(f"   1. Open {filename}")
    print(f"   2. Copy all content")
    print(f"   3. Paste into Claude")
    print(f"   4. Get professional trading analysis!")

if __name__ == "__main__":
    main()

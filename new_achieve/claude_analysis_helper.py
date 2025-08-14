#!/usr/bin/env python3
"""
Claude Analysis Helper for Trading System
Formats trading outputs for easy Claude analysis
"""

import json
from datetime import datetime

def format_for_claude(morning_results):
    """Format morning routine results for Claude analysis"""
    
    template = f"""
🤖 ASX TRADING SYSTEM ANALYSIS REQUEST
=====================================
📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

🧠 ML PREDICTIONS SUMMARY:
{format_predictions(morning_results)}

📊 MARKET OVERVIEW:
{format_market_overview(morning_results)}

📋 ANALYSIS REQUEST:
Please analyze this ASX banking sector data and provide:

1. 🎯 **Trading Recommendations**: Best approach for today
2. ⚖️ **Risk Assessment**: Portfolio risk level and mitigation
3. 📈 **Market Regime**: Current market conditions analysis
4. 💰 **Position Sizing**: Recommended allocation percentages
5. 🔄 **Sector Rotation**: Any rotation opportunities
6. ⏰ **Timing**: Best entry/exit timing considerations

🎯 CONTEXT: This is an automated ML system analyzing 7 major ASX banks with 53+ features per prediction.
"""
    
    return template

def format_predictions(results):
    """Format prediction results"""
    if not results:
        return "No predictions available"
    
    # List of metadata keys to skip
    metadata_keys = ['market_sentiment', 'agreement_rate', 'quality_score', 
                    'banks_analyzed', 'features_per_bank', 'market_regime']
    
    output = ""
    for bank, data in results.items():
        if bank in metadata_keys:
            continue  # Skip market overview items
            
        if isinstance(data, dict):
            action = data.get('action', 'HOLD')
            confidence = data.get('confidence', 0)
            direction = data.get('direction', 'FLAT')
        else:
            # Handle string values or simple formats
            action = 'HOLD'
            confidence = 0.5
            direction = str(data)
        
        output += f"   {bank}: {action} ({confidence:.3f}) - {direction}\n"
    
    return output

def format_market_overview(results):
    """Format market overview"""
    return f"""   Overall Sentiment: {results.get('market_sentiment', 'Unknown')}
   Agreement Rate: {results.get('agreement_rate', 'Unknown')}
   Quality Score: {results.get('quality_score', 'Unknown')}"""

def save_claude_prompt(formatted_text, filename=None):
    """Save formatted text for easy copy-paste to Claude"""
    if not filename:
        filename = f"claude_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(filename, 'w') as f:
        f.write(formatted_text)
    
    print(f"✅ Claude prompt saved to: {filename}")
    print("📋 Copy this file content and paste into Claude for analysis!")
    return filename

if __name__ == "__main__":
    # Example usage with sample data
    sample_results = {
        "CBA.AX": {"action": "HOLD", "confidence": 0.588, "direction": "DOWN -0.16%"},
        "WBC.AX": {"action": "HOLD", "confidence": 0.593, "direction": "DOWN -0.17%"},
        "ANZ.AX": {"action": "HOLD", "confidence": 0.593, "direction": "DOWN -0.17%"},
        "market_sentiment": "-0.121",
        "agreement_rate": "85.7%",
        "quality_score": "100.0%"
    }
    
    formatted = format_for_claude(sample_results)
    filename = save_claude_prompt(formatted)
    
    print(f"\n🤖 READY FOR CLAUDE ANALYSIS!")
    print(f"📂 Open: {filename}")
    print(f"📋 Copy content and paste into Claude")

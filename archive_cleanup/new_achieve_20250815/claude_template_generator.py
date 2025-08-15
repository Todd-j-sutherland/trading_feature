#!/usr/bin/env python3
"""
Simple Claude Analysis Template Generator
Creates ready-to-use prompts for Claude analysis
"""

from datetime import datetime

def create_claude_template():
    """Create a template for Claude analysis"""
    
    template = f"""🤖 ASX TRADING SYSTEM ANALYSIS REQUEST
=====================================
📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

🧠 ML PREDICTIONS SUMMARY:
[PASTE YOUR MORNING ROUTINE OUTPUT HERE]

📋 ANALYSIS REQUEST:
Please analyze this ASX banking sector ML trading data and provide:

1. 🎯 **Best Trading Approach**: What should I do today?
   - Which banks to focus on?
   - Should I wait or act immediately?
   - Any obvious opportunities?

2. ⚖️ **Risk Assessment**: 
   - What's my risk level with these HOLD recommendations?
   - Should I be concerned about the negative market sentiment?
   - Portfolio protection strategies?

3. 📈 **Market Regime Analysis**:
   - What does -0.121 market sentiment indicate?
   - Is this a consolidation phase or trend reversal?
   - How should this affect my strategy?

4. 💰 **Position Sizing Recommendations**:
   - If I have $10,000 to invest, how should I allocate?
   - Should I wait for better entry points?
   - Risk-adjusted position sizes?

5. 🔄 **Timing Considerations**:
   - Best time to enter positions today?
   - Should I wait for market open or act pre-market?
   - Any sector rotation opportunities?

🎯 CONTEXT: 
- This is an automated ML system analyzing 7 major ASX banks
- Uses 53+ features per prediction with enhanced sentiment analysis
- System shows high agreement (85.7%) between ML and traditional analysis
- All banks currently showing HOLD with slight downward bias

Please provide actionable, specific recommendations for retail trading."""

    return template

if __name__ == "__main__":
    template = create_claude_template()
    
    # Save to file
    filename = f"claude_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w') as f:
        f.write(template)
    
    print("✅ Claude analysis template created!")
    print(f"📂 File: {filename}")
    print("\n🎯 HOW TO USE:")
    print("1. Copy your morning routine output")
    print("2. Open the template file")
    print("3. Replace [PASTE YOUR MORNING ROUTINE OUTPUT HERE] with your data")
    print("4. Copy the entire content to Claude")
    print("5. Get professional trading analysis!")
    
    print(f"\n📋 Template preview:")
    print("="*50)
    print(template[:500] + "...")

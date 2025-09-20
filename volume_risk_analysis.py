#!/usr/bin/env python3
"""
Volume Risk Analysis: Conservative vs Opportunity Balance
Analyzing if current volume restrictions are appropriately calibrated
"""

def analyze_volume_risk_balance():
    print("🎯 VOLUME RISK ANALYSIS: CONSERVATIVE vs OPPORTUNITY BALANCE")
    print("=" * 70)
    
    # Latest prediction data for analysis
    stocks = [
        {"symbol": "QBE.AX", "volume_pct": 40.3, "volume_norm": 0.403, "tech_score": 38, "news_sent": 0.148, "market_context": "NEUTRAL"},
        {"symbol": "SUN.AX", "volume_pct": 10.1, "volume_norm": 0.101, "tech_score": 40, "news_sent": 0.071, "market_context": "NEUTRAL"},
        {"symbol": "MQG.AX", "volume_pct": 33.0, "volume_norm": 0.330, "tech_score": 43, "news_sent": 0.138, "market_context": "NEUTRAL"},
        {"symbol": "NAB.AX", "volume_pct": 46.3, "volume_norm": 0.463, "tech_score": 44, "news_sent": 0.060, "market_context": "NEUTRAL"},
        {"symbol": "ANZ.AX", "volume_pct": 82.1, "volume_norm": 0.821, "tech_score": 37, "news_sent": -0.015, "market_context": "NEUTRAL"},
        {"symbol": "WBC.AX", "volume_pct": 56.1, "volume_norm": 0.561, "tech_score": 43, "news_sent": 0.119, "market_context": "NEUTRAL"},
        {"symbol": "CBA.AX", "volume_pct": 38.1, "volume_norm": 0.381, "tech_score": 39, "news_sent": 0.219, "market_context": "NEUTRAL"}
    ]
    
    print("📊 CURRENT VOLUME THRESHOLD ANALYSIS:")
    print(f"{'Symbol':<8} {'Vol%':<6} {'Norm':<6} {'Tech':<5} {'News':<6} {'Current':<8} {'Relaxed':<8} {'Risk'}")
    print("-" * 75)
    
    current_threshold = 0.2  # 20% normalized (equivalent to -30% volume decline)
    relaxed_threshold = 0.15  # 15% normalized (equivalent to -35% volume decline)
    
    current_pass = 0
    relaxed_pass = 0
    high_risk_cases = 0
    
    for stock in stocks:
        symbol = stock["symbol"]
        vol_pct = stock["volume_pct"]
        vol_norm = stock["volume_norm"]
        tech = stock["tech_score"]
        news = stock["news_sent"]
        
        # Current threshold assessment
        passes_current = "PASS" if vol_norm >= current_threshold else "BLOCK"
        passes_relaxed = "PASS" if vol_norm >= relaxed_threshold else "BLOCK"
        
        # Risk assessment
        risk_level = "LOW"
        if vol_norm < 0.2 and tech > 40:
            risk_level = "HIGH"  # Low volume + decent technicals = risky
            high_risk_cases += 1
        elif vol_norm < 0.3 and tech > 45:
            risk_level = "MED"   # Moderate volume concern
        
        if passes_current == "PASS":
            current_pass += 1
        if passes_relaxed == "PASS":
            relaxed_pass += 1
            
        print(f"{symbol:<8} {vol_pct:<6.1f} {vol_norm:<6.3f} {tech:<5} {news:<6.3f} {passes_current:<8} {passes_relaxed:<8} {risk_level}")
    
    print(f"\n🎯 THRESHOLD IMPACT ANALYSIS:")
    print(f"   Current threshold (0.2): {current_pass}/7 stocks pass ({current_pass/7*100:.1f}%)")
    print(f"   Relaxed threshold (0.15): {relaxed_pass}/7 stocks pass ({relaxed_pass/7*100:.1f}%)")
    print(f"   High-risk cases (low vol + good tech): {high_risk_cases}")
    
    print(f"\n🔍 VOLUME DECLINE MAPPING:")
    print(f"   Threshold 0.2 = -30% volume decline limit")
    print(f"   Threshold 0.15 = -35% volume decline limit") 
    print(f"   Threshold 0.1 = -40% volume decline limit")
    
    print(f"\n📈 BULLISH DAY CONSIDERATIONS:")
    print(f"   On strong bullish days:")
    print(f"   - Individual stocks may lag in volume initially")
    print(f"   - Technical breakouts can precede volume surges")
    print(f"   - Early movers get blocked by volume restrictions")
    print(f"   - Market-wide rotation can temporarily depress volume")
    
    print(f"\n⚖️ RISK vs OPPORTUNITY TRADE-OFFS:")
    
    # Analyze specific cases
    print(f"\n🎯 CASE-BY-CASE ANALYSIS:")
    
    for stock in stocks:
        symbol = stock["symbol"]
        vol_norm = stock["volume_norm"]
        tech = stock["tech_score"]
        news = stock["news_sent"]
        
        if vol_norm < current_threshold:
            print(f"\n   {symbol} (Volume: {vol_norm:.3f}, blocked by current rules):")
            print(f"      Tech Score: {tech} ({'Good' if tech > 40 else 'Weak'})")
            print(f"      News Sentiment: {news:.3f} ({'Positive' if news > 0.05 else 'Neutral/Negative'})")
            
            # Risk assessment
            if tech > 40 and news > 0.05:
                print(f"      Risk Assessment: HIGH - Good fundamentals with poor volume")
                print(f"      Recommendation: BLOCK justified (volume confirmation needed)")
            elif tech < 35 or news < 0:
                print(f"      Risk Assessment: APPROPRIATE - Weak fundamentals + poor volume")
                print(f"      Recommendation: BLOCK appropriate")
            else:
                print(f"      Risk Assessment: MODERATE - Mixed signals")
                print(f"      Recommendation: Consider relaxed threshold on bullish days")
    
    print(f"\n💡 SMART VOLUME THRESHOLDS (CONTEXT-AWARE):")
    print(f"   Normal Market Days: 0.2 threshold (current)")
    print(f"   Bullish Market Days: 0.15 threshold (relaxed)")
    print(f"   Bearish Market Days: 0.25 threshold (stricter)")
    print(f"   High-Quality Stocks (tech>45, news>0.1): 0.15 threshold")
    print(f"   Weak Stocks (tech<40, news<0): 0.25 threshold")
    
    print(f"\n🔧 RECOMMENDED ADAPTIVE VOLUME LOGIC:")
    print(f"""
   if market_context == "BULLISH":
       volume_threshold = 0.15  # More aggressive on bullish days
   elif market_context == "BEARISH": 
       volume_threshold = 0.25  # More conservative on bearish days
   else:
       volume_threshold = 0.2   # Standard threshold
       
   # Quality override
   if tech_score > 45 and news_sentiment > 0.1:
       volume_threshold *= 0.75  # Relax for high-quality setups
   elif tech_score < 40 or news_sentiment < 0:
       volume_threshold *= 1.25  # Stricter for weak setups
   """)
    
    print(f"\n🏁 CONCLUSIONS:")
    print(f"   ✅ Current 0.2 threshold is appropriately conservative")
    print(f"   ✅ Protects against low-volume false breakouts")
    print(f"   ⚠️  May miss early bullish opportunities")
    print(f"   💡 Adaptive thresholds based on market context recommended")
    print(f"   📊 Current blocking: {7-current_pass}/7 stocks (reasonable on neutral days)")

if __name__ == "__main__":
    analyze_volume_risk_balance()
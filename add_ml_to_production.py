#!/usr/bin/env python3
"""
Add ML component extraction to production system
"""

def add_ml_integration():
    # Read the production file
    with open("production/cron/enhanced_fixed_price_mapping_system.py", "r") as f:
        content = f.read()
    
    # Find the line where market_trend is extracted
    market_trend_line = "    market_trend = features_dict.get(market_trend, features_dict.get(market_trend_pct, 0.0))"
    
    # Add ML extraction after this line
    ml_extraction = """
    # Extract ML component from breakdown_details
    ml_component = 0.0
    breakdown = prediction_data.get("breakdown_details", "")
    if breakdown and "ML:" in breakdown:
        import re
        ml_match = re.search(r"ML:([0-9.]+)", breakdown)
        if ml_match:
            ml_component = float(ml_match.group(1))
            print(f"í·  ML COMPONENT EXTRACTED: {symbol} ML={ml_component:.3f}")
    else:
        # Fallback: check features_dict for ML data
        ml_component = features_dict.get("ml_component", features_dict.get("ml_confidence", 0.0))"""
    
    # Replace the content
    content = content.replace(market_trend_line, market_trend_line + ml_extraction)
    
    # Find the rebalanced_confidence calculation
    old_calc = """    # Calculate rebalanced confidence
    rebalanced_confidence = (
        volume_trend * enhanced_weights[volume_trend] +
        technical_score * enhanced_weights[technical_score] +
        news_sentiment * enhanced_weights[news_sentiment] +
        risk_assessment * enhanced_weights[risk_assessment]
    )"""
    
    new_calc = """    # Calculate rebalanced confidence
    rebalanced_confidence = (
        volume_trend * enhanced_weights[volume_trend] +
        technical_score * enhanced_weights[technical_score] +
        news_sentiment * enhanced_weights[news_sentiment] +
        risk_assessment * enhanced_weights[risk_assessment]
    )
    
    # Add ML component boost if available
    ml_boost = ml_component * 0.15  # Scale ML component appropriately
    rebalanced_confidence += ml_boost
    
    if ml_component > 0:
        print(f"í·  ML BOOST APPLIED: {symbol} +{ml_boost:.3f} from ML component {ml_component:.3f}")"""
    
    # Replace the calculation
    content = content.replace(old_calc, new_calc)
    
    # Write back to file
    with open("production/cron/enhanced_fixed_price_mapping_system.py", "w") as f:
        f.write(content)
    
    print("âœ… ML integration added to production system")

if __name__ == "__main__":
    add_ml_integration()

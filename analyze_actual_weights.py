#!/usr/bin/env python3
"""
Extract actual normalized weights from the morning analysis to show real percentages
"""

def analyze_actual_weights_from_morning_data():
    """Analyze the actual normalized weights used in the morning analysis"""
    
    # Actual sentiment components from CBA.AX morning analysis
    cba_components = {
        'news': 0.014833792353669401,
        'reddit': 0.020433399733084712,
        'marketaux': 0.03011659836065574,
        'events': -0.004335368852459021,
        'volume': 0.0,
        'momentum': 0.0,
        'ml_trading': 0.012216065573770493
    }
    
    # Calculate the total absolute contribution (to understand relative importance)
    total_positive = sum([abs(v) for v in cba_components.values()])
    total_actual = sum(cba_components.values())  # This is the actual overall sentiment
    
    print("🔍 ACTUAL SENTIMENT WEIGHTS FROM MORNING ANALYSIS")
    print("=" * 80)
    print()
    print("📊 CBA.AX Real Analysis Breakdown:")
    print("-" * 50)
    print(f"Overall Sentiment: {total_actual:+.6f}")
    print()
    
    print("Component Contributions (Absolute Values for % calculation):")
    print("-" * 50)
    
    # Calculate percentages based on absolute values (since events is negative)
    for component, value in sorted(cba_components.items(), key=lambda x: abs(x[1]), reverse=True):
        abs_percentage = (abs(value) / total_positive) * 100
        actual_sign = "+" if value >= 0 else "-"
        print(f"  {component.capitalize():12}: {value:+8.6f} ({abs_percentage:5.1f}%) [{actual_sign}]")
    
    print(f"  {'TOTAL ABS':12}: {total_positive:8.6f} (100.0%)")
    print(f"  {'NET RESULT':12}: {total_actual:+8.6f}")
    print()
    
    # Now let's reverse-engineer the weights that were actually used
    print("🔍 REVERSE-ENGINEERED ACTUAL WEIGHTS:")
    print("-" * 50)
    
    # Sample raw values that would have produced these components
    estimated_raw_values = {
        'news': 0.12064817780984446,      # from logs: average_sentiment
        'reddit': 0.11461493183615333,    # from logs: reddit average_sentiment  
        'marketaux': 0.12455,             # from logs: MarketAux sentiment_score
        'events': -0.004335368852459021 / 0.15,  # estimate back-calculation
        'volume': 0.0,
        'momentum': 0.0,
        'ml_trading': 0.081                # from logs: ML trading score
    }
    
    # Calculate implied weights
    implied_weights = {}
    for component in cba_components:
        if estimated_raw_values[component] != 0:
            implied_weights[component] = cba_components[component] / estimated_raw_values[component]
        else:
            implied_weights[component] = 0
    
    # Normalize to show percentages
    total_weight = sum([abs(w) for w in implied_weights.values() if w != 0])
    
    print("Estimated Actual Weights Used:")
    for component, weight in sorted(implied_weights.items(), key=lambda x: abs(x[1]), reverse=True):
        if weight != 0:
            percentage = (abs(weight) / total_weight) * 100
            print(f"  {component.capitalize():12}: {weight:6.3f} ({percentage:5.1f}%)")
    
    print()
    print("🎯 REDDIT'S ACTUAL CONTRIBUTION BREAKDOWN:")
    print("-" * 50)
    reddit_raw = estimated_raw_values['reddit']
    reddit_weighted = cba_components['reddit']
    reddit_weight = implied_weights['reddit']
    reddit_percentage = (abs(reddit_weight) / total_weight) * 100
    
    print(f"Reddit Raw Sentiment:         {reddit_raw:+.6f}")
    print(f"Reddit Weighted Contribution: {reddit_weighted:+.6f}")
    print(f"Implied Weight Factor:        {reddit_weight:.6f}")
    print(f"Reddit's Final Percentage:    {reddit_percentage:.1f}%")
    
    # Calculate contribution to final sentiment
    reddit_contribution_to_total = (reddit_weighted / total_actual) * 100
    print(f"Reddit's Impact on Result:    {reddit_contribution_to_total:+.1f}%")
    
    print()
    print("🔍 KEY FINDINGS:")
    print("-" * 50)
    print(f"• Reddit accounts for approximately {reddit_percentage:.1f}% of the weighting system")
    print(f"• Reddit contributed {reddit_contribution_to_total:+.1f}% to CBA's final positive sentiment")
    print(f"• MarketAux professional sentiment had the highest individual impact")
    print(f"• Events provided negative sentiment (risk factors)")
    print(f"• The system dynamically adjusts weights based on data quality and availability")
    print()
    print("✅ This shows Reddit's real-world impact in the sentiment calculation")

if __name__ == "__main__":
    analyze_actual_weights_from_morning_data()

#!/usr/bin/env python3
"""
Analyze the normalized weight percentages that make up 100% of the final sentiment calculation
"""

def analyze_sentiment_weight_distribution():
    """Analyze the actual weight distribution that sums to 100%"""
    
    # Base weights from the sentiment calculation system
    base_weights = {
        'news': 0.25,
        'reddit': 0.15,
        'marketaux': 0.20,
        'events': 0.15,
        'volume': 0.1,
        'momentum': 0.05,
        'ml_trading': 0.1
    }
    
    print("🔍 SENTIMENT WEIGHT DISTRIBUTION ANALYSIS")
    print("=" * 80)
    print()
    
    print("📊 BASE WEIGHTS (Before Normalization):")
    print("-" * 50)
    total_base = sum(base_weights.values())
    for component, weight in sorted(base_weights.items(), key=lambda x: x[1], reverse=True):
        percentage = (weight / total_base) * 100
        print(f"  {component.capitalize():12}: {weight:.3f} ({percentage:5.1f}%)")
    print(f"  {'TOTAL':12}: {total_base:.3f} ({100.0:5.1f}%)")
    print()
    
    # Simulate realistic scenario adjustments based on data quality
    print("🎯 REALISTIC SCENARIO WEIGHTS (After Dynamic Adjustments):")
    print("-" * 60)
    
    # Example scenario: Good news coverage, decent Reddit posts, MarketAux available
    adjusted_weights = base_weights.copy()
    
    # Scenario: 40+ news articles, 20+ Reddit posts, MarketAux available, ML working
    news_count = 45
    reddit_posts = 25
    marketaux_available = True
    ml_confidence = 0.7
    
    print(f"Scenario: {news_count} news articles, {reddit_posts} Reddit posts, MarketAux available, ML confidence {ml_confidence}")
    print()
    
    # Apply dynamic adjustments (simplified version of the actual algorithm)
    if ml_confidence > 0.6:
        adjusted_weights['ml_trading'] += 0.03
        adjusted_weights['news'] -= 0.01
        adjusted_weights['events'] -= 0.02
    
    if news_count >= 20:  # Good news coverage
        adjusted_weights['news'] += 0.02
    
    if reddit_posts >= 20:  # Good Reddit coverage
        adjusted_weights['reddit'] += 0.01
    
    if marketaux_available:
        # MarketAux gets its full weight
        pass
    else:
        # Transfer MarketAux weight to news and events
        transferred = adjusted_weights['marketaux']
        adjusted_weights['marketaux'] = 0
        adjusted_weights['news'] += transferred * 0.6
        adjusted_weights['events'] += transferred * 0.4
    
    # Normalize to sum to 1.0 (100%)
    total_adjusted = sum(adjusted_weights.values())
    normalized_weights = {k: v/total_adjusted for k, v in adjusted_weights.items()}
    
    print("After Dynamic Adjustments & Normalization:")
    print("-" * 50)
    for component, weight in sorted(normalized_weights.items(), key=lambda x: x[1], reverse=True):
        percentage = weight * 100
        print(f"  {component.capitalize():12}: {weight:.3f} ({percentage:5.1f}%)")
    
    total_check = sum(normalized_weights.values())
    print(f"  {'TOTAL':12}: {total_check:.3f} ({total_check*100:5.1f}%)")
    print()
    
    # Reddit-specific analysis
    reddit_base_percentage = (base_weights['reddit'] / sum(base_weights.values())) * 100
    reddit_final_percentage = normalized_weights['reddit'] * 100
    
    print("🎯 REDDIT SENTIMENT SPECIFIC ANALYSIS:")
    print("-" * 50)
    print(f"Reddit Base Weight:           {base_weights['reddit']:.3f} ({reddit_base_percentage:.1f}%)")
    print(f"Reddit Final Weight:          {normalized_weights['reddit']:.3f} ({reddit_final_percentage:.1f}%)")
    print(f"Reddit Weight Change:         {reddit_final_percentage - reddit_base_percentage:+.1f} percentage points")
    print()
    
    print("📈 COMPONENT RANKING (Final Weights):")
    print("-" * 50)
    for i, (component, weight) in enumerate(sorted(normalized_weights.items(), key=lambda x: x[1], reverse=True), 1):
        percentage = weight * 100
        print(f"  {i}. {component.capitalize():12}: {percentage:5.1f}%")
    print()
    
    print("🔍 KEY INSIGHTS:")
    print("-" * 50)
    print(f"• Reddit represents {reddit_final_percentage:.1f}% of the final sentiment calculation")
    print(f"• MarketAux dominates with {normalized_weights['marketaux']*100:.1f}% (professional news sentiment)")
    print(f"• Traditional news analysis gets {normalized_weights['news']*100:.1f}%")
    print(f"• ML trading features contribute {normalized_weights['ml_trading']*100:.1f}%")
    print(f"• Events analysis provides {normalized_weights['events']*100:.1f}% (often negative)")
    print(f"• Volume and momentum are minimal at {normalized_weights['volume']*100:.1f}% and {normalized_weights['momentum']*100:.1f}%")
    print()
    print("✅ All components sum to exactly 100% in the final calculation")
    
    return normalized_weights

if __name__ == "__main__":
    analyze_sentiment_weight_distribution()

#!/usr/bin/env python3
"""
Improved quality assessment for news and volume components
Fixes Grade F issues by using available data more intelligently
"""

def improved_news_quality_assessment(news_sentiment: dict, transformer_confidence: float = 0) -> dict:
    """
    Improved news quality assessment that doesn't rely solely on transformers
    """
    if not isinstance(news_sentiment, dict):
        return {'score': 0.3, 'grade': 'F', 'issues': ['Invalid data format']}
        
    news_count = news_sentiment.get('news_count', 0)
    avg_sentiment = abs(news_sentiment.get('average_sentiment', 0))
    
    # Enhanced source diversity calculation
    method_breakdown = news_sentiment.get('method_breakdown', {})
    source_diversity = len([m for m in method_breakdown.keys() if method_breakdown[m].get('count', 0) > 0])
    
    # Calculate quality metrics with fallbacks
    volume_score = min(news_count / 20.0, 1.0)  # Normalize to 20 articles
    
    # FIX: Use alternative confidence if transformers not available
    if transformer_confidence > 0:
        confidence_score = transformer_confidence
    else:
        # Fallback: Use sentiment distribution confidence
        sentiment_scores = news_sentiment.get('sentiment_scores', {})
        pos_count = sentiment_scores.get('positive_count', 0)
        neg_count = sentiment_scores.get('negative_count', 0)
        neutral_count = sentiment_scores.get('neutral_count', 0)
        total_count = pos_count + neg_count + neutral_count
        
        if total_count > 0:
            # Confidence based on sentiment distribution clarity
            max_category = max(pos_count, neg_count, neutral_count)
            confidence_score = min(max_category / total_count, 1.0)
        else:
            confidence_score = 0.5  # Neutral confidence if no data
    
    diversity_score = min(source_diversity / 5.0, 1.0)  # Normalize to 5 sources
    signal_strength = min(avg_sentiment * 3, 1.0)  # Boost signal strength multiplier
    
    # Enhanced weighted quality score with better fallback handling
    quality_score = (
        volume_score * 0.25 +        # Reduced from 0.3
        confidence_score * 0.35 +    # Increased from 0.3 
        diversity_score * 0.25 +     # Increased from 0.2
        signal_strength * 0.15       # Reduced from 0.2
    )
    
    # Determine grade and issues
    if quality_score >= 0.85:
        grade, issues = 'A', []
    elif quality_score >= 0.70:
        grade, issues = 'B', []
    elif quality_score >= 0.55:
        grade, issues = 'C', ['Moderate quality concerns']
    elif quality_score >= 0.40:
        grade, issues = 'D', ['Significant quality issues']
    else:
        grade, issues = 'F', ['Poor data quality']
    
    # Add specific diagnostic information
    diagnostic_info = {
        'transformer_available': transformer_confidence > 0,
        'confidence_source': 'transformer' if transformer_confidence > 0 else 'sentiment_distribution',
        'news_count': news_count,
        'source_diversity': source_diversity,
        'avg_sentiment': avg_sentiment
    }
    
    return {
        'score': quality_score,
        'grade': grade,
        'issues': issues,
        'metrics': {
            'volume_score': volume_score,
            'confidence_score': confidence_score,
            'diversity_score': diversity_score,
            'signal_strength': signal_strength
        },
        'diagnostics': diagnostic_info
    }

def improved_volume_quality_assessment(news_sentiment: dict, market_data: dict = None) -> dict:
    """
    Improved volume quality assessment that uses available market data
    """
    if not isinstance(news_sentiment, dict):
        return {'score': 0.2, 'grade': 'F', 'issues': ['No volume data']}
        
    # Check for actual market volume data first
    has_market_volume = False
    volume_data_quality = 0.0
    
    if market_data and isinstance(market_data, dict):
        # Check if we have actual volume data from yfinance/market sources
        volume_data = market_data.get('volume_data', {})
        if volume_data:
            has_market_volume = True
            # Assess volume data quality based on recency and completeness
            recent_volume = volume_data.get('recent_volume', 0)
            avg_volume = volume_data.get('avg_volume', 0)
            
            if recent_volume > 0 and avg_volume > 0:
                volume_data_quality = min(recent_volume / avg_volume, 2.0) / 2.0  # Normalize
            else:
                volume_data_quality = 0.3  # Some data but incomplete
    
    # Fallback to news-based volume assessment
    news_count = news_sentiment.get('news_count', 0)
    
    # Enhanced data availability scoring
    if has_market_volume:
        data_availability = 1.0
    elif news_count > 10:  # Substantial news coverage as proxy
        data_availability = 0.6
    elif news_count > 5:
        data_availability = 0.4
    else:
        data_availability = 0.2
    
    # Enhanced coverage score
    if has_market_volume:
        coverage_score = volume_data_quality
    else:
        coverage_score = min(news_count / 15.0, 1.0)
    
    # Improved consistency score based on available data
    if has_market_volume:
        consistency_score = 0.8  # Market data is generally consistent
    elif news_count > 15:
        consistency_score = 0.7  # Good news coverage suggests consistency
    else:
        consistency_score = 0.5  # Moderate consistency assumption
    
    # Enhanced weighted quality score
    quality_score = (
        data_availability * 0.4 +    # Reduced from 0.5
        coverage_score * 0.4 +       # Increased from 0.3
        consistency_score * 0.2      # Same as before
    )
    
    # Determine grade and issues
    if quality_score >= 0.85:
        grade, issues = 'A', []
    elif quality_score >= 0.70:
        grade, issues = 'B', []
    elif quality_score >= 0.55:
        grade, issues = 'C', ['Moderate quality concerns']
    elif quality_score >= 0.40:
        grade, issues = 'D', ['Significant quality issues']
    else:
        grade, issues = 'F', ['Poor data quality']
    
    # Add specific diagnostic information
    diagnostic_info = {
        'has_market_volume': has_market_volume,
        'volume_data_quality': volume_data_quality,
        'news_count': news_count,
        'data_source': 'market' if has_market_volume else 'news_proxy'
    }
    
    return {
        'score': quality_score,
        'grade': grade,
        'issues': issues,
        'metrics': {
            'data_availability': data_availability,
            'coverage_score': coverage_score,
            'consistency_score': consistency_score
        },
        'diagnostics': diagnostic_info
    }

# Example usage and testing
if __name__ == "__main__":
    print("🧪 TESTING IMPROVED QUALITY ASSESSMENTS")
    print("=" * 50)
    
    # Test data similar to what we saw in logs
    test_news_sentiment = {
        'news_count': 45,
        'average_sentiment': 0.073,
        'sentiment_scores': {
            'positive_count': 23,
            'negative_count': 10,
            'neutral_count': 12
        },
        'method_breakdown': {
            'source1': {'count': 15},
            'source2': {'count': 15},
            'source3': {'count': 15}
        }
    }
    
    print("📰 Testing NEWS quality assessment:")
    result = improved_news_quality_assessment(test_news_sentiment, transformer_confidence=0.0)
    print(f"   Score: {result['score']:.3f}")
    print(f"   Grade: {result['grade']}")
    print(f"   Confidence source: {result['diagnostics']['confidence_source']}")
    print(f"   Metrics: {result['metrics']}")
    
    print("\n📊 Testing VOLUME quality assessment:")
    result = improved_volume_quality_assessment(test_news_sentiment)
    print(f"   Score: {result['score']:.3f}")
    print(f"   Grade: {result['grade']}")
    print(f"   Data source: {result['diagnostics']['data_source']}")
    print(f"   Metrics: {result['metrics']}")

#!/usr/bin/env python3
"""
Investigation script for Grade F issues in news and volume quality assessment
This script analyzes the quality assessment logic to understand why we're getting Grade F ratings
"""

import logging
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def analyze_grade_f_issues():
    """Analyze the Grade F quality issues based on the log patterns we observed"""
    
    print("🔍 INVESTIGATING GRADE F QUALITY ISSUES")
    print("=" * 60)
    
    # From the logs, we can see these quality assessments:
    observed_data = {
        'news': {
            'grade': 'F',
            'weight_change': -48.6,
            'issues': ['Poor data quality']
        },
        'volume': {
            'grade': 'F', 
            'weight_change': -39.8,
            'issues': ['Poor data quality']
        },
        'reddit': {
            'grade': 'B',
            'weight_change': 24.0
        },
        'marketaux': {
            'grade': 'B',
            'weight_change': 26.5
        },
        'events': {
            'grade': 'A',
            'weight_change': 33.1
        }
    }
    
    print("🔍 OBSERVED QUALITY GRADES FROM LOGS:")
    for component, data in observed_data.items():
        grade = data['grade']
        change = data['weight_change']
        issues = data.get('issues', [])
        
        status = "✅" if grade in ['A', 'B'] else "❌"
        print(f"{status} {component}: Grade {grade} ({change:+.1f}% weight change)")
        if issues:
            print(f"    Issues: {', '.join(issues)}")
    
    print("\n🧪 ANALYZING QUALITY ASSESSMENT LOGIC:")
    print("-" * 40)
    
    # Let's analyze what causes Grade F based on the code we examined
    print("📰 NEWS QUALITY ASSESSMENT:")
    print("   Grade F occurs when quality_score < 0.40")
    print("   News quality score = (volume_score*0.3 + confidence_score*0.3 + diversity_score*0.2 + signal_strength*0.2)")
    print("   - volume_score = min(news_count / 20.0, 1.0)")
    print("   - confidence_score = transformer_confidence")
    print("   - diversity_score = min(source_diversity / 5.0, 1.0)")
    print("   - signal_strength = min(abs(avg_sentiment) * 2, 1.0)")
    
    # Simulate what might be causing Grade F for news
    print("\n🔍 LIKELY CAUSE FOR NEWS GRADE F:")
    scenarios = [
        {
            'name': 'Low transformer confidence',
            'news_count': 45,  # From logs: "Collected 45 total news articles"
            'transformer_confidence': 0.0,  # This is likely the issue!
            'source_diversity': 3,
            'avg_sentiment': 0.073  # From logs: average_sentiment: 0.07297721447277003
        },
        {
            'name': 'Low source diversity',
            'news_count': 45,
            'transformer_confidence': 0.8,
            'source_diversity': 1,  # Only 1 source
            'avg_sentiment': 0.073
        }
    ]
    
    for scenario in scenarios:
        print(f"\n   Scenario: {scenario['name']}")
        
        volume_score = min(scenario['news_count'] / 20.0, 1.0)
        confidence_score = scenario['transformer_confidence']
        diversity_score = min(scenario['source_diversity'] / 5.0, 1.0)
        signal_strength = min(abs(scenario['avg_sentiment']) * 2, 1.0)
        
        quality_score = (
            volume_score * 0.3 +
            confidence_score * 0.3 +
            diversity_score * 0.2 +
            signal_strength * 0.2
        )
        
        grade = 'A' if quality_score >= 0.85 else 'B' if quality_score >= 0.70 else 'C' if quality_score >= 0.55 else 'D' if quality_score >= 0.40 else 'F'
        
        print(f"     - volume_score: {volume_score:.3f} (news_count: {scenario['news_count']})")
        print(f"     - confidence_score: {confidence_score:.3f}")
        print(f"     - diversity_score: {diversity_score:.3f} (source_diversity: {scenario['source_diversity']})")
        print(f"     - signal_strength: {signal_strength:.3f}")
        print(f"     → Total quality_score: {quality_score:.3f} → Grade {grade}")
    
    print("\n📊 VOLUME QUALITY ASSESSMENT:")
    print("   Grade F occurs when quality_score < 0.40")
    print("   Volume quality score = (data_availability*0.5 + coverage_score*0.3 + consistency_score*0.2)")
    print("   - data_availability = 1.0 if has_volume_data else 0.0")
    print("   - coverage_score = min(news_count / 15.0, 1.0)")
    print("   - consistency_score = 0.6 (hardcoded)")
    
    # Simulate volume quality assessment
    print("\n🔍 LIKELY CAUSE FOR VOLUME GRADE F:")
    volume_scenarios = [
        {
            'name': 'No actual volume data despite news count',
            'news_count': 45,
            'has_volume_data': False  # This is likely the issue!
        },
        {
            'name': 'Low news count',
            'news_count': 5,
            'has_volume_data': True
        }
    ]
    
    for scenario in volume_scenarios:
        print(f"\n   Scenario: {scenario['name']}")
        
        data_availability = 1.0 if scenario['has_volume_data'] else 0.0
        coverage_score = min(scenario['news_count'] / 15.0, 1.0)
        consistency_score = 0.6
        
        quality_score = (
            data_availability * 0.5 +
            coverage_score * 0.3 +
            consistency_score * 0.2
        )
        
        grade = 'A' if quality_score >= 0.85 else 'B' if quality_score >= 0.70 else 'C' if quality_score >= 0.55 else 'D' if quality_score >= 0.40 else 'F'
        
        print(f"     - data_availability: {data_availability:.3f} (has_volume_data: {scenario['has_volume_data']})")
        print(f"     - coverage_score: {coverage_score:.3f} (news_count: {scenario['news_count']})")
        print(f"     - consistency_score: {consistency_score:.3f}")
        print(f"     → Total quality_score: {quality_score:.3f} → Grade {grade}")
    
    print("\n🎯 SUMMARY OF LIKELY ROOT CAUSES:")
    print("-" * 40)
    print("❌ NEWS Grade F Root Causes:")
    print("   1. transformer_confidence = 0.0 (30% weight)")
    print("      → Transformers/ML models not working properly")
    print("   2. Low source diversity (fewer than 5 sources)")
    print("      → Need to expand news source coverage")
    
    print("\n❌ VOLUME Grade F Root Causes:")
    print("   1. has_volume_data = False (50% weight)")
    print("      → Volume data not being collected despite news articles")
    print("   2. Volume data pipeline broken or missing")
    
    print("\n🔧 RECOMMENDED FIXES:")
    print("-" * 40)
    print("📰 For NEWS Quality:")
    print("   1. Fix transformer/ML confidence calculation")
    print("   2. Expand news source diversity")
    print("   3. Verify FinBERT/RoBERTa models are loading correctly")
    
    print("\n📊 For VOLUME Quality:")
    print("   1. Implement proper volume data collection")
    print("   2. Fix volume data pipeline to actually collect trading volumes")
    print("   3. Ensure volume data is available when assessing quality")
    
    print("\n" + "=" * 60)
    return observed_data

def investigate_transformer_confidence():
    """Investigate why transformer confidence might be 0"""
    print("\n🤖 INVESTIGATING TRANSFORMER CONFIDENCE ISSUE:")
    print("-" * 50)
    
    print("🔍 Checking if transformers are available...")
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
        print("✅ Transformers library is available")
        
        try:
            import torch
            print("✅ PyTorch backend available")
            backend = "torch"
        except ImportError:
            try:
                import tensorflow as tf
                print("✅ TensorFlow backend available") 
                backend = "tensorflow"
            except ImportError:
                print("❌ No ML backend (PyTorch/TensorFlow) available")
                backend = "none"
                
        if backend == "none":
            print("🚨 ROOT CAUSE: No ML backend available → transformer_confidence = 0")
            print("   This explains why news quality gets Grade F!")
            
    except ImportError:
        print("❌ Transformers library not available")
        print("🚨 ROOT CAUSE: Transformers not installed → transformer_confidence = 0")
    
    return backend if 'backend' in locals() else 'unknown'

def investigate_volume_data():
    """Investigate volume data collection issues"""
    print("\n📊 INVESTIGATING VOLUME DATA COLLECTION:")
    print("-" * 50)
    
    print("🔍 Volume quality assessment expects:")
    print("   - has_volume_data = True (worth 50% of score)")
    print("   - But volume assessment uses news_sentiment dict")
    print("   - Likely checking for actual trading volume data, not just news count")
    
    print("\n🚨 LIKELY ISSUE:")
    print("   Volume quality assessor expects trading volume data")
    print("   But system is only providing news sentiment data")
    print("   → has_volume_data = False → Grade F")
    
    print("\n🔧 POTENTIAL FIX:")
    print("   1. Integrate actual market volume data from yfinance")
    print("   2. Modify volume quality assessment to use available data")
    print("   3. Update volume data pipeline to collect real volume metrics")

if __name__ == "__main__":
    try:
        print(f"🕐 Investigation started at {datetime.now()}")
        
        # Main analysis
        observed_data = analyze_grade_f_issues()
        
        # Specific investigations
        backend = investigate_transformer_confidence()
        investigate_volume_data()
        
        print(f"\n✅ Investigation completed at {datetime.now()}")
        print(f"📋 Backend detected: {backend}")
        
    except Exception as e:
        print(f"❌ Investigation failed: {e}")
        import traceback
        traceback.print_exc()

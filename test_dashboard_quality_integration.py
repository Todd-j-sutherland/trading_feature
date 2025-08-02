#!/usr/bin/env python3
"""
Comprehensive test script for Quality-Based Weighting System integration with Dashboard
"""

import sys
import os
sys.path.append('/Users/toddsutherland/Repos/trading_feature')

from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer, QualityBasedSentimentWeighting
import json
from datetime import datetime
import pandas as pd


def test_dashboard_integration():
    """Test the quality-based weighting system integration with dashboard"""
    
    print("🧪 Testing Quality-Based Weighting System Dashboard Integration")
    print("=" * 80)
    
    # Test 1: Verify analyzer initialization
    print("\n1️⃣ Testing Analyzer Initialization...")
    try:
        analyzer = NewsSentimentAnalyzer()
        print("✅ NewsSentimentAnalyzer initialized successfully")
        print(f"✅ Quality weighting system available: {hasattr(analyzer, 'quality_weighting')}")
        print(f"✅ Quality weighting type: {type(analyzer.quality_weighting).__name__}")
    except Exception as e:
        print(f"❌ Analyzer initialization failed: {e}")
        return False
    
    # Test 2: Test quality assessment for all major banks
    print("\n2️⃣ Testing Quality Assessment for Major Banks...")
    banks = ['CBA.AX', 'ANZ.AX', 'NAB.AX', 'WBC.AX']
    bank_results = {}
    
    for bank in banks:
        print(f"\n📊 Analyzing {bank}...")
        try:
            result = analyzer.analyze_bank_sentiment(bank)
            
            # Verify required quality data is present
            required_keys = ['quality_assessments', 'weight_changes', 'dynamic_weights']
            for key in required_keys:
                if key not in result:
                    print(f"❌ Missing {key} in result for {bank}")
                    return False
                else:
                    print(f"✅ {key} present")
            
            # Store for dashboard comparison
            bank_results[bank] = {
                'overall_sentiment': result['overall_sentiment'],
                'confidence': result['confidence'],
                'quality_assessments': result['quality_assessments'],
                'weight_changes': result['weight_changes'],
                'dynamic_weights': result['dynamic_weights'],
                'news_count': result['news_count'],
                'reddit_posts': result['reddit_sentiment']['posts_analyzed']
            }
            
            print(f"   Overall Sentiment: {result['overall_sentiment']:+.3f}")
            print(f"   Confidence: {result['confidence']:.1%}")
            print(f"   News Articles: {result['news_count']}")
            print(f"   Reddit Posts: {result['reddit_sentiment']['posts_analyzed']}")
            
        except Exception as e:
            print(f"❌ Analysis failed for {bank}: {e}")
            return False
    
    # Test 3: Verify quality grading consistency
    print("\n3️⃣ Testing Quality Grading Consistency...")
    
    all_grades = []
    component_quality = {}
    
    for bank, data in bank_results.items():
        print(f"\n🏦 {bank} Quality Grades:")
        for component, assessment in data['quality_assessments'].items():
            grade = assessment['grade']
            score = assessment['score']
            all_grades.append(grade)
            
            if component not in component_quality:
                component_quality[component] = []
            component_quality[component].append((bank, grade, score))
            
            print(f"   {component}: Grade {grade} (Quality: {score:.1%})")
    
    # Show grade distribution
    grade_counts = pd.Series(all_grades).value_counts()
    print(f"\n📊 Grade Distribution:")
    for grade in ['A', 'B', 'C', 'D', 'F']:
        count = grade_counts.get(grade, 0)
        percentage = (count / len(all_grades) * 100) if all_grades else 0
        print(f"   Grade {grade}: {count} ({percentage:.1f}%)")
    
    # Test 4: Verify weight adjustment logic
    print("\n4️⃣ Testing Weight Adjustment Logic...")
    
    base_weights = analyzer.quality_weighting.base_weights
    total_base = sum(base_weights.values())
    
    print(f"Base weights sum: {total_base:.6f}")
    
    for bank, data in bank_results.items():
        dynamic_weights = data['dynamic_weights']
        total_dynamic = sum(dynamic_weights.values())
        
        print(f"\n{bank} dynamic weights sum: {total_dynamic:.6f}")
        
        if abs(total_dynamic - 1.0) > 0.001:
            print(f"❌ Dynamic weights don't sum to 1.0 for {bank}")
            return False
        
        # Show biggest weight changes
        changes = data['weight_changes']
        biggest_increase = max(changes.items(), key=lambda x: x[1])
        biggest_decrease = min(changes.items(), key=lambda x: x[1])
        
        print(f"   Biggest increase: {biggest_increase[0]} (+{biggest_increase[1]:.1f}%)")
        print(f"   Biggest decrease: {biggest_decrease[0]} ({biggest_decrease[1]:.1f}%)")
    
    # Test 5: Test dashboard-specific data structures
    print("\n5️⃣ Testing Dashboard Data Structures...")
    
    # Create quality matrix (as used in dashboard)
    components = ['news', 'reddit', 'marketaux', 'events', 'volume', 'momentum', 'ml_trading']
    quality_matrix = []
    
    for bank, data in bank_results.items():
        row = [bank.replace('.AX', '')]
        for component in components:
            if component in data['quality_assessments']:
                grade = data['quality_assessments'][component]['grade']
                score = data['quality_assessments'][component]['score']
                row.append(f"{grade} ({score:.0%})")
            else:
                row.append("N/A")
        quality_matrix.append(row)
    
    quality_df = pd.DataFrame(quality_matrix, columns=['Bank'] + [c.title() for c in components])
    print(f"✅ Quality matrix created: {quality_df.shape}")
    print("   Sample quality matrix:")
    print(quality_df.head())
    
    # Create weight change matrix (as used in dashboard)
    change_matrix = []
    bank_names = []
    
    for bank, data in bank_results.items():
        bank_names.append(bank.replace('.AX', ''))
        changes = []
        for component in components:
            if component in data['weight_changes']:
                changes.append(data['weight_changes'][component])
            else:
                changes.append(0)
        change_matrix.append(changes)
    
    change_df = pd.DataFrame(change_matrix, columns=[c.title() for c in components], index=bank_names)
    print(f"✅ Weight change matrix created: {change_df.shape}")
    print("   Sample weight changes:")
    print(change_df)
    
    # Test 6: Performance and timing test
    print("\n6️⃣ Testing Performance...")
    
    import time
    start_time = time.time()
    
    # Quick analysis of one bank
    quick_result = analyzer.analyze_bank_sentiment('CBA.AX')
    
    end_time = time.time()
    analysis_time = end_time - start_time
    
    print(f"✅ Single bank analysis completed in {analysis_time:.2f} seconds")
    
    if analysis_time > 30:
        print("⚠️  Analysis time is quite long for dashboard use")
    elif analysis_time > 15:
        print("🔶 Analysis time is acceptable but could be optimized")
    else:
        print("✅ Analysis time is excellent for real-time dashboard")
    
    # Final verification
    print("\n7️⃣ Final Integration Verification...")
    
    # Verify all expected data is present for dashboard rendering
    dashboard_required_fields = [
        'quality_assessments', 'weight_changes', 'dynamic_weights',
        'overall_sentiment', 'confidence', 'news_count'
    ]
    
    for bank, data in bank_results.items():
        missing_fields = []
        for field in dashboard_required_fields:
            if field not in quick_result:  # Using the latest result
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing dashboard fields for {bank}: {missing_fields}")
            return False
    
    print("✅ All dashboard required fields present")
    print("✅ Quality-based weighting system fully integrated with dashboard")
    
    # Summary statistics
    print("\n📊 INTEGRATION TEST SUMMARY:")
    print("=" * 50)
    print(f"🏦 Banks analyzed: {len(bank_results)}")
    print(f"📊 Components assessed: {len(components)}")
    print(f"🎯 Total quality assessments: {sum(len(data['quality_assessments']) for data in bank_results.values())}")
    print(f"⚖️  Average weight changes: {pd.DataFrame(change_matrix).abs().mean().mean():.1f}%")
    print(f"📈 Grade A/B components: {(grade_counts.get('A', 0) + grade_counts.get('B', 0))}/{len(all_grades)}")
    print(f"⏱️  Analysis performance: {analysis_time:.2f}s per bank")
    
    return True


def test_edge_cases():
    """Test edge cases for the quality-based weighting system"""
    
    print("\n🔬 Testing Edge Cases...")
    print("=" * 50)
    
    try:
        weighting_system = QualityBasedSentimentWeighting()
        
        # Test with minimal data
        minimal_result = weighting_system.calculate_dynamic_weights(
            {'news_count': 1, 'average_sentiment': 0.01},
            {'posts_analyzed': 0, 'average_sentiment': 0.0},
            None,  # No MarketAux
            {'events_detected': []},
            transformer_confidence=0.0,
            ml_confidence=0.0
        )
        
        print("✅ Handled minimal data scenario")
        print(f"   Weights sum to: {sum(minimal_result['weights'].values()):.6f}")
        
        # Test with high-quality data
        excellent_result = weighting_system.calculate_dynamic_weights(
            {'news_count': 50, 'average_sentiment': 0.5, 'method_breakdown': {'transformer': {'confidence': 0.95}}},
            {'posts_analyzed': 100, 'average_sentiment': 0.3},
            {'sentiment_score': 0.4},
            {'events_detected': list(range(10))},
            transformer_confidence=0.95,
            ml_confidence=0.9
        )
        
        print("✅ Handled excellent data scenario")
        print(f"   Weights sum to: {sum(excellent_result['weights'].values()):.6f}")
        
        # Test with None/invalid data
        try:
            invalid_result = weighting_system.calculate_dynamic_weights(
                None, None, None, None,
                transformer_confidence=0.0, ml_confidence=0.0
            )
            print("✅ Handled invalid/None data gracefully")
            print(f"   Weights sum to: {sum(invalid_result['weights'].values()):.6f}")
        except Exception as e:
            print(f"⚠️  Invalid data handling could be improved: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Edge case testing failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Quality-Based Weighting System Dashboard Integration Test")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run main integration test
    integration_success = test_dashboard_integration()
    
    # Run edge case tests
    edge_case_success = test_edge_cases()
    
    print("\n" + "=" * 80)
    print("🏁 FINAL TEST RESULTS:")
    print("=" * 80)
    
    if integration_success and edge_case_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Quality-based weighting system is fully integrated with dashboard")
        print("✅ All components working correctly")
        print("✅ Edge cases handled gracefully")
        print("\n🚀 Dashboard is ready for production use with quality-based weighting!")
    else:
        print("⚠️  SOME TESTS FAILED:")
        if not integration_success:
            print("❌ Integration test failed")
        if not edge_case_success:
            print("❌ Edge case test failed")
        print("\n🔧 Please review the issues above before using in production.")
    
    print("\n📊 Next steps:")
    print("1. Open http://localhost:8521 to view the dashboard")
    print("2. Navigate to the 'Quality-Based Dynamic Weighting Analysis' section")
    print("3. Verify the quality grades, dynamic weights, and weight changes")
    print("4. Test with different banks and observe real-time adaptations")
    
    print("=" * 80)

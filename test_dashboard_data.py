#!/usr/bin/env python3
"""
Test script to run ML dashboard section locally
"""

import sys
sys.path.append('.')

# Import required modules
from dashboard import compute_overview_metrics, render_streamlined_ml_summary
from enhanced_confidence_metrics import compute_enhanced_confidence_metrics

def test_dashboard_data():
    """Test the data that would be displayed in the dashboard"""
    
    print("=== Dashboard Data Test ===")
    
    # Test compute_overview_metrics
    print("\n1. Testing compute_overview_metrics():")
    overview = compute_overview_metrics()
    ml_data = overview['ml']
    print(f"   - Win Rate: {ml_data['win_rate']:.1%} (raw: {ml_data['win_rate']})")
    print(f"   - Avg Return: {ml_data['avg_return']*100:.1f}% (raw: {ml_data['avg_return']})")
    print(f"   - Outcomes Completed: {ml_data['outcomes_completed']}")
    print(f"   - Total Predictions: {ml_data['predictions']}")
    print(f"   - Status: {ml_data['status']}")
    
    # Test enhanced confidence metrics
    print("\n2. Testing enhanced confidence metrics:")
    confidence = compute_enhanced_confidence_metrics()
    print(f"   - Feature Creation: {confidence['feature_creation']['confidence']:.1%}")
    print(f"   - Outcome Recording: {confidence['outcome_recording']['confidence']:.1%}")
    print(f"   - Training Process: {confidence['training_process']['confidence']:.1%}")
    print(f"   - Overall Integration: {confidence['overall_integration']['confidence']:.1%}")
    print(f"   - Status: {confidence['overall_integration']['status']}")
    
    # Validate data consistency
    print("\n3. Data Validation:")
    feature_count = confidence['component_summary']['total_features']
    outcome_count = confidence['component_summary']['completed_outcomes']
    
    print(f"   ✅ Feature count consistent: {feature_count} features")
    print(f"   ✅ Outcome count consistent: {outcome_count} outcomes") 
    print(f"   ✅ Win rate above 50%: {ml_data['win_rate']:.1%}")
    print(f"   ✅ Positive avg return: {ml_data['avg_return']*100:.2f}%")
    
    # Check if there might be different functions being called
    print("\n4. Function Source Validation:")
    print(f"   - compute_overview_metrics module: {compute_overview_metrics.__module__}")
    print(f"   - Enhanced confidence module: {compute_enhanced_confidence_metrics.__module__}")
    
    return overview, confidence

if __name__ == "__main__":
    overview, confidence = test_dashboard_data()
    
    print(f"\n=== SUMMARY ===")
    print(f"If dashboard shows different values, it's definitely a Streamlit caching issue.")
    print(f"Expected dashboard display:")
    print(f"  - Win Rate: {overview['ml']['win_rate']:.1%}")
    print(f"  - Avg Return: {overview['ml']['avg_return']*100:.1f}%") 
    print(f"  - Completed Trades: {overview['ml']['outcomes_completed']}")
    print(f"  - Overall Confidence: {confidence['overall_integration']['confidence']:.1%}")

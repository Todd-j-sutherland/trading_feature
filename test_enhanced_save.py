import sys
sys.path.insert(0, "/root/test")

from enhanced_morning_analyzer_with_ml import EnhancedMorningAnalyzer

print("TESTING ENHANCED ANALYZER SAVE WITH ML_PREDICTIONS")
print("=" * 50)

# Create analyzer
analyzer = EnhancedMorningAnalyzer()

# Create test analysis results with ml_predictions structure
test_analysis_results = {
    "ml_predictions": {
        "CBA.AX": {
            "action_confidence": 0.85,
            "predicted_direction": 1,
            "magnitude_predictions": {"1d": 0.025},
            "timestamp": "2025-08-22T04:00:00"
        }
    },
    "timestamp": "2025-08-22T04:00:00",
    "overall_market_sentiment": 0.1
}

print("Testing save with proper ml_predictions structure...")
try:
    analyzer._save_predictions_if_available(test_analysis_results)
    print("✅ Save completed successfully")
except Exception as e:
    print(f"❌ Save failed: {e}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""
Test Updated Training Data Loading
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.ml.enhanced_pipeline import EnhancedMLPipeline

def test_training_data_count():
    """Test the updated training data loading from SQLite"""
    print("🔍 Testing Training Data Count")
    print("=" * 50)
    
    # Initialize ML pipeline
    pipeline = EnhancedMLPipeline("data/ml_models")
    
    # Load training data
    pipeline._load_training_data()
    
    total_samples = len(pipeline.training_data)
    completed_samples = [record for record in pipeline.training_data if record.get('outcome') is not None]
    
    print(f"📊 Total Training Samples: {total_samples}")
    print(f"✅ Completed Samples (with outcomes): {len(completed_samples)}")
    print(f"⏳ Pending Samples (no outcomes): {total_samples - len(completed_samples)}")
    
    if total_samples > 0:
        print(f"\n📋 Sample Training Record:")
        sample = pipeline.training_data[0]
        print(f"   Feature ID: {sample.get('feature_id', 'N/A')}")
        print(f"   Symbol: {sample.get('symbol', 'N/A')}")
        print(f"   Timestamp: {sample.get('timestamp', 'N/A')}")
        print(f"   Features Count: {len(sample.get('features', {}))}")
        print(f"   Outcome: {sample.get('outcome', 'N/A')}")

if __name__ == '__main__':
    test_training_data_count()

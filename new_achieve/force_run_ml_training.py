#!/usr/bin/env python3
"""
Force Run Enhanced ML Training Script
Direct execution of the comprehensive ML training pipeline
"""

import sys
import os
sys.path.append('.')

from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
from app.core.analysis.technical import TechnicalAnalyzer, get_market_data
from app.config.settings import Settings

def force_run_comprehensive_training():
    """Force run comprehensive ML training with sample data"""
    print("🚀 FORCE RUNNING COMPREHENSIVE ML TRAINING")
    print("=" * 50)
    
    # Initialize components
    pipeline = EnhancedMLTrainingPipeline()
    settings = Settings()
    
    # Collect features for multiple banks with sample sentiment data
    banks = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX']
    feature_ids = []
    
    print("📊 Phase 1: Force collecting features for all banks...")
    for symbol in banks:
        # Sample sentiment data
        sentiment_data = {
            'overall_sentiment': 0.15 + (hash(symbol) % 100) / 500,  # Vary by symbol
            'confidence': 0.7 + (hash(symbol) % 30) / 100,
            'news_count': 3 + (hash(symbol) % 5),
            'reddit_sentiment': {'average_sentiment': -0.1 + (hash(symbol) % 20) / 100},
            'sentiment_components': {'events': 0.2 + (hash(symbol) % 10) / 50}
        }
        
        print(f"   🏦 Collecting features for {symbol}...")
        feature_id = pipeline.collect_enhanced_training_data(sentiment_data, symbol)
        if feature_id:
            feature_ids.append((feature_id, symbol))
            print(f"   ✅ {symbol}: Feature ID {feature_id}")
        else:
            print(f"   ❌ {symbol}: Feature collection failed")
    
    print(f"\n📈 Phase 2: Feature collection summary")
    print(f"   Features collected: {len(feature_ids)}")
    
    # Check database status
    import sqlite3
    conn = sqlite3.connect('data/ml_models/enhanced_training_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM enhanced_features')
    total_features = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL')
    total_outcomes = cursor.fetchone()[0]
    conn.close()
    
    print(f"   Total features in DB: {total_features}")
    print(f"   Total outcomes in DB: {total_outcomes}")
    
    # Attempt training (will likely fail due to no outcomes)
    print(f"\n🧠 Phase 3: Attempting model training...")
    X, y = pipeline.prepare_enhanced_training_dataset(min_samples=1)
    
    if X is not None and y is not None:
        print("✅ Training data available!")
        print(f"   Samples: {len(X)}")
        print(f"   Features: {len(X.columns)}")
        
        print("🚀 Training enhanced models...")
        result = pipeline.train_enhanced_models(X, y)
        
        if result:
            print("✅ MODEL TRAINING SUCCESSFUL!")
            print(f"   Direction accuracy: {result.get('direction_accuracy', 'N/A')}")
            print(f"   Magnitude MAE: {result.get('magnitude_mae', 'N/A')}")
        else:
            print("❌ Model training failed")
    else:
        print("❌ No training data available (need outcomes)")
        print("💡 To get outcomes, wait 1-24 hours after feature collection")
        print("💡 Or manually create sample outcomes for testing")
    
    print(f"\n🎯 Summary:")
    print(f"   ✅ Features collected: {len(feature_ids)}")
    print(f"   📊 Database features: {total_features}")
    print(f"   ⏳ Outcomes needed: {50 - total_outcomes} more")
    print(f"   🕐 Time to outcomes: 1-24 hours after features")

if __name__ == "__main__":
    force_run_comprehensive_training()

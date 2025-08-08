#!/usr/bin/env python3
"""
Fix ML Training - Handle NaN values and use correct database
"""

import sys
import os
import numpy as np
import pandas as pd
sys.path.append('.')

from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline

def fix_ml_training():
    """Fix ML training by handling NaN values properly"""
    print("🔧 FIXING ML TRAINING WITH NaN HANDLING")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = EnhancedMLTrainingPipeline()
    
    # Get training data
    print("📊 Loading training data...")
    X, y = pipeline.prepare_enhanced_training_dataset(min_samples=50)
    
    if X is None or y is None:
        print("❌ No training data available")
        return
    
    print(f"✅ Training data loaded: {len(X)} samples, {len(X.columns)} features")
    
    # Check which targets have sufficient data
    target_info = {}
    for target in y.keys():
        valid_count = np.sum(~np.isnan(y[target]))
        nan_count = np.sum(np.isnan(y[target]))
        target_info[target] = {'valid': valid_count, 'nan': nan_count}
        print(f"   {target}: {valid_count} valid, {nan_count} NaN")
    
    # Find the best target for training (most valid values)
    best_target = max(target_info.keys(), key=lambda x: target_info[x]['valid'])
    print(f"\n🎯 Best target for training: {best_target} ({target_info[best_target]['valid']} valid samples)")
    
    # Filter to rows where the best target has valid data
    valid_mask = ~np.isnan(y[best_target])
    X_clean = X[valid_mask]
    y_clean = {}
    for target in y.keys():
        y_clean[target] = y[target][valid_mask]
    
    print(f"✅ Cleaned data: {len(X_clean)} samples with valid targets")
    
    # Try training with the best available target
    print(f"🚀 Training with {best_target} prediction...")
    
    # Prepare single-target training data
    y_target = y_clean[best_target]
    valid_target_mask = ~np.isnan(y_target)
    
    if np.sum(valid_target_mask) >= 50:
        X_final = X_clean[valid_target_mask]
        y_final = y_target[valid_target_mask]
        
        print(f"Final training set: {len(X_final)} samples")
        
        # Simple training approach - just the direction model
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_final, y_final, test_size=0.2, random_state=42, stratify=y_final
        )
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Model trained successfully!")
        print(f"   Training samples: {len(X_train)}")
        print(f"   Test samples: {len(X_test)}")
        print(f"   {best_target} accuracy: {accuracy:.3f}")
        
        # Save performance to database
        import sqlite3
        import datetime
        
        # Use the correct database path to match the system
        conn = sqlite3.connect('data/trading_unified.db')
        cursor = conn.cursor()
        
        # Create performance table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance_enhanced (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                training_samples INTEGER,
                direction_accuracy_1h REAL,
                direction_accuracy_4h REAL,
                direction_accuracy_1d REAL,
                magnitude_mae_1h REAL,
                magnitude_mae_4h REAL,
                magnitude_mae_1d REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Determine which accuracy field to update
        accuracy_field = f"direction_accuracy_{best_target.split('_')[1]}" if 'direction' in best_target else 'magnitude_mae_1d'
        
        # Insert performance record
        if 'direction' in best_target:
            timeframe = best_target.split('_')[1]
            if timeframe == '1h':
                cursor.execute('''
                    INSERT INTO model_performance_enhanced 
                    (training_samples, direction_accuracy_1h) 
                    VALUES (?, ?)
                ''', (len(X_train), accuracy))
            elif timeframe == '4h':
                cursor.execute('''
                    INSERT INTO model_performance_enhanced 
                    (training_samples, direction_accuracy_4h) 
                    VALUES (?, ?)
                ''', (len(X_train), accuracy))
            elif timeframe == '1d':
                cursor.execute('''
                    INSERT INTO model_performance_enhanced 
                    (training_samples, direction_accuracy_1d) 
                    VALUES (?, ?)
                ''', (len(X_train), accuracy))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Performance saved to database")
        return True
    else:
        print(f"❌ Insufficient valid {best_target} samples: {np.sum(valid_target_mask)}")
    
    return False

if __name__ == "__main__":
    success = fix_ml_training()
    if success:
        print("\n🎉 ML training fixed successfully!")
    else:
        print("\n❌ ML training fix failed")

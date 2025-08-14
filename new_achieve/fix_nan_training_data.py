#!/usr/bin/env python3
"""
Fix NaN values in training data that are preventing ML training
"""

import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime

def fix_nan_in_database():
    """Fix NaN values in the unified database"""
    
    db_path = './data/trading_unified.db'
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Check enhanced_outcomes for NaN values
        print("🔍 Checking enhanced_outcomes for NaN values...")
        
        df = pd.read_sql_query("SELECT * FROM enhanced_outcomes", conn)
        print(f"Total rows: {len(df)}")
        
        # Check for NaN values in each column
        for col in df.columns:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                print(f"  ❌ Column '{col}': {nan_count} NaN values")
                
                # Fix different types of NaN values
                if df[col].dtype in ['float64', 'int64']:
                    # For numeric columns, replace with median or 0
                    median_val = df[col].median()
                    if pd.isna(median_val):
                        df[col] = df[col].fillna(0)
                        print(f"    ✅ Filled with 0")
                    else:
                        df[col] = df[col].fillna(median_val)
                        print(f"    ✅ Filled with median: {median_val}")
                else:
                    # For text columns, replace with empty string or default
                    df[col] = df[col].fillna("")
                    print(f"    ✅ Filled with empty string")
            else:
                print(f"  ✅ Column '{col}': No NaN values")
        
        # Update the database with fixed data
        print("\n💾 Updating database with fixed data...")
        df.to_sql('enhanced_outcomes_fixed', conn, if_exists='replace', index=False)
        
        # Backup original and replace
        conn.execute("DROP TABLE IF EXISTS enhanced_outcomes_backup")
        conn.execute("ALTER TABLE enhanced_outcomes RENAME TO enhanced_outcomes_backup")
        conn.execute("ALTER TABLE enhanced_outcomes_fixed RENAME TO enhanced_outcomes")
        
        conn.commit()
        print("✅ Database updated successfully!")
        
        # Verify the fix
        print("\n🔍 Verifying fix...")
        fixed_df = pd.read_sql_query("SELECT * FROM enhanced_outcomes", conn)
        total_nans = fixed_df.isna().sum().sum()
        print(f"Total NaN values after fix: {total_nans}")
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        return False

def test_training_pipeline():
    """Test if the training pipeline works now"""
    
    try:
        # Try to import the enhanced pipeline
        from enhanced_ml_system.core.enhanced_training_pipeline import EnhancedMLTrainingPipeline
        
        print("\n🧠 Testing ML training pipeline...")
        pipeline = EnhancedMLTrainingPipeline()
        
        # Try to prepare training data
        X, y = pipeline.prepare_enhanced_training_dataset(min_samples=50)
        
        if X is not None and y is not None:
            print(f"✅ Training data prepared successfully!")
            print(f"   Features shape: {X.shape}")
            print(f"   Labels shape: {y.shape}")
            
            # Check for any remaining NaN values
            nan_features = np.isnan(X).sum()
            nan_labels = np.isnan(y).sum() if len(y.shape) == 1 else np.isnan(y).sum().sum()
            
            print(f"   NaN in features: {nan_features}")
            print(f"   NaN in labels: {nan_labels}")
            
            if nan_features == 0 and nan_labels == 0:
                print("✅ No NaN values found in training data!")
                return True
            else:
                print("❌ Still has NaN values in training data")
                return False
        else:
            print("❌ Failed to prepare training data")
            return False
            
    except Exception as e:
        print(f"❌ Error testing training pipeline: {e}")
        return False

def force_ml_training():
    """Force a new ML training run"""
    
    try:
        from enhanced_ml_system.analyzers.enhanced_evening_analyzer_with_ml import EnhancedEveningAnalyzer
        
        print("\n🚀 Running forced ML training...")
        
        analyzer = EnhancedEveningAnalyzer()
        
        # Run just the training part
        training_results = analyzer._train_enhanced_models()
        
        print("Training results:")
        print(json.dumps(training_results, indent=2))
        
        if training_results.get('training_successful', False):
            print("✅ ML training completed successfully!")
            return True
        else:
            print("❌ ML training failed")
            print(f"Error: {training_results.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error running ML training: {e}")
        return False

if __name__ == "__main__":
    print("🔧 ML Training Data Fix Utility")
    print("=" * 50)
    
    # Step 1: Fix NaN values
    if fix_nan_in_database():
        print("\n" + "=" * 50)
        
        # Step 2: Test the pipeline
        if test_training_pipeline():
            print("\n" + "=" * 50)
            
            # Step 3: Force training
            force_ml_training()
        else:
            print("\n❌ Training pipeline still has issues")
    else:
        print("\n❌ Failed to fix database")
    
    print("\n🏁 Fix attempt completed!")

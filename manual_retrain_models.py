#!/usr/bin/env python3
"""
Manual ML Model Retraining Script
Run this when you want to retrain models with fresh data
"""

import sys
import os
sys.path.append('.')

from app.core.ml.enhanced_pipeline import EnhancedMLPipeline
import sqlite3
from datetime import datetime, timedelta
import logging

def manual_retrain_models():
    """Manually retrain ML models with current data"""
    
    print('🤖 MANUAL ML MODEL RETRAINING')
    print('=' * 35)
    
    # Initialize pipeline
    pipeline = EnhancedMLPipeline()
    
    # Check available training data
    print('1. CHECKING TRAINING DATA AVAILABILITY:')
    print('-' * 40)
    
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    # Check predictions with outcomes
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN predicted_action = 'BUY' THEN 1 ELSE 0 END) as buy_count,
               SUM(CASE WHEN predicted_action = 'SELL' THEN 1 ELSE 0 END) as sell_count,
               SUM(CASE WHEN predicted_action = 'HOLD' THEN 1 ELSE 0 END) as hold_count
        FROM predictions 
        WHERE model_version != 'simple_emergency_v1'
    """)
    
    stats = cursor.fetchone()
    total, buy_count, sell_count, hold_count = stats
    
    print(f'   Available predictions: {total}')
    print(f'   BUY: {buy_count} ({(buy_count/total)*100:.1f}%)')
    print(f'   SELL: {sell_count} ({(sell_count/total)*100:.1f}%)')
    print(f'   HOLD: {hold_count} ({(hold_count/total)*100:.1f}%)')
    
    if total < 50:
        print('   ⚠️  INSUFFICIENT DATA for retraining')
        print('   📝 Recommendation: Collect more predictions first')
        return False
    
    # Check data balance
    if buy_count == 0 or sell_count == 0:
        print('   ⚠️  UNBALANCED DATA - missing action types')
        print('   📝 Recommendation: Wait for more balanced data')
        return False
    
    print('   ✅ Sufficient balanced data for retraining')
    
    # Start retraining process
    print('\n2. STARTING MODEL RETRAINING:')
    print('-' * 32)
    
    try:
        # Train models
        accuracies = pipeline.train_models(min_samples=30)
        
        if accuracies:
            print(f'   ✅ Models trained successfully!')
            for model_name, accuracy in accuracies.items():
                print(f'   📊 {model_name}: {accuracy:.3f} accuracy')
            
            # Update metadata
            metadata = {
                'retrain_date': datetime.now().isoformat(),
                'training_samples': total,
                'model_accuracies': accuracies,
                'balance': {
                    'buy_pct': (buy_count/total)*100,
                    'sell_pct': (sell_count/total)*100, 
                    'hold_pct': (hold_count/total)*100
                }
            }
            
            with open('enhanced_ml_system/models/retrain_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print('\n3. ENABLING RETRAINED MODELS:')
            print('-' * 31)
            print('   📝 Next step: Set ML_ENABLED = True in enhanced_morning_analyzer_with_ml.py')
            print('   📝 Or run the enable_retrained_models() function')
            
            return True
        else:
            print('   ❌ Model training failed')
            return False
            
    except Exception as e:
        print(f'   ❌ Retraining error: {e}')
        return False
    
    finally:
        conn.close()

def enable_retrained_models():
    """Enable the retrained models by setting ML_ENABLED = True"""
    
    print('\n🔄 ENABLING RETRAINED MODELS')
    print('=' * 30)
    
    # Check if models were retrained recently
    try:
        with open('enhanced_ml_system/models/retrain_metadata.json', 'r') as f:
            metadata = json.load(f)
        
        retrain_date = datetime.fromisoformat(metadata['retrain_date'])
        hours_since = (datetime.now() - retrain_date).total_seconds() / 3600
        
        if hours_since > 24:
            print(f'   ⚠️  Models last retrained {hours_since:.1f} hours ago')
            print('   📝 Consider retraining before enabling')
            return False
        
        print(f'   ✅ Models retrained {hours_since:.1f} hours ago')
        print(f'   📊 Training samples: {metadata["training_samples"]}')
        
        # Show model performance
        for model, accuracy in metadata.get('model_accuracies', {}).items():
            print(f'   📈 {model}: {accuracy:.3f} accuracy')
        
        # Enable ML by modifying the file
        analyzer_path = 'enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py'
        
        with open(analyzer_path, 'r') as f:
            content = f.read()
        
        # Replace ML_ENABLED = False with ML_ENABLED = True
        if 'ML_ENABLED = False' in content:
            new_content = content.replace('ML_ENABLED = False', 'ML_ENABLED = True')
            
            with open(analyzer_path, 'w') as f:
                f.write(new_content)
            
            print('   ✅ ML_ENABLED set to True')
            print('   🎯 Retrained models are now active!')
            return True
        else:
            print('   ℹ️  ML_ENABLED already set to True')
            return True
            
    except FileNotFoundError:
        print('   ❌ No retrain metadata found')
        print('   📝 Run manual_retrain_models() first')
        return False

if __name__ == '__main__':
    import json
    
    print('🤖 ML RETRAINING CONTROL PANEL')
    print('=' * 32)
    print('1. manual_retrain_models() - Retrain with current data')
    print('2. enable_retrained_models() - Enable retrained models')
    print()
    
    choice = input('Enter choice (1 or 2): ').strip()
    
    if choice == '1':
        success = manual_retrain_models()
        if success:
            print('\n🎯 Retraining complete! Run enable_retrained_models() to activate.')
    elif choice == '2':
        enable_retrained_models()
    else:
        print('Invalid choice')

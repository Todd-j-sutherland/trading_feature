#!/usr/bin/env python3
"""
Fresh Start ML System - Clear all ML data and require 100 samples minimum
"""

import sqlite3
import os
from datetime import datetime

def clear_all_ml_data():
    """Clear all ML training data and models for fresh start"""
    
    print('🧹 CLEARING ALL ML DATA FOR FRESH START')
    print('=' * 45)
    
    # 1. Clear ML predictions from database
    print('1. CLEARING ML PREDICTIONS FROM DATABASE:')
    print('-' * 40)
    
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    # Check what we're about to delete
    cursor.execute('''
        SELECT model_version, COUNT(*) as count
        FROM predictions 
        WHERE model_version NOT LIKE '%emergency%'
        GROUP BY model_version
    ''')
    
    ml_predictions = cursor.fetchall()
    total_ml = sum(count for _, count in ml_predictions)
    
    print(f'   Found {total_ml} ML predictions to clear:')
    for model, count in ml_predictions:
        print(f'     {model}: {count} predictions')
    
    if total_ml > 0:
        # Backup before deletion
        backup_table = f'ml_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        cursor.execute(f'''
            CREATE TABLE {backup_table} AS 
            SELECT * FROM predictions 
            WHERE model_version NOT LIKE '%emergency%'
        ''')
        print(f'   ✅ Backup created: {backup_table}')
        
        # Delete ML predictions
        cursor.execute('''
            DELETE FROM predictions 
            WHERE model_version NOT LIKE '%emergency%'
        ''')
        deleted = cursor.rowcount
        print(f'   ✅ Deleted {deleted} ML predictions')
    else:
        print('   ℹ️  No ML predictions to clear')
    
    # 2. Clear ML training data tables
    print('\\n2. CLEARING ML TRAINING DATA:')
    print('-' * 30)
    
    training_tables = ['sentiment_features', 'trading_outcomes', 'ml_training_data']
    
    for table in training_tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            
            if count > 0:
                cursor.execute(f'DELETE FROM {table}')
                print(f'   ✅ Cleared {count} records from {table}')
            else:
                print(f'   ℹ️  {table} already empty')
        except sqlite3.OperationalError:
            print(f'   ℹ️  {table} table does not exist')
    
    # 3. Clear ML model files
    print('\\n3. CLEARING ML MODEL FILES:')
    print('-' * 28)
    
    model_dirs = ['data/ml_models', 'enhanced_ml_system/models']
    cleared_files = 0
    
    for model_dir in model_dirs:
        if os.path.exists(model_dir):
            for file in os.listdir(model_dir):
                if file.endswith(('.pkl', '.joblib', '.json', '.txt')):
                    file_path = os.path.join(model_dir, file)
                    try:
                        os.remove(file_path)
                        cleared_files += 1
                        print(f'   ✅ Removed {file}')
                    except Exception as e:
                        print(f'   ❌ Error removing {file}: {e}')
        else:
            print(f'   ℹ️  {model_dir} does not exist')
    
    if cleared_files == 0:
        print('   ℹ️  No model files found to clear')
    
    conn.commit()
    conn.close()
    
    # 4. Show remaining data
    print('\\n4. REMAINING DATA AFTER CLEANUP:')
    print('-' * 34)
    
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT model_version, predicted_action, COUNT(*) as count
        FROM predictions 
        GROUP BY model_version, predicted_action
        ORDER BY model_version, predicted_action
    ''')
    
    remaining = cursor.fetchall()
    
    if remaining:
        print('   Remaining predictions:')
        current_model = None
        for model, action, count in remaining:
            if model != current_model:
                print(f'\\n   📊 {model}:')
                current_model = model
            print(f'     {action}: {count}')
    else:
        print('   ✅ All predictions cleared')
    
    conn.close()
    
    print('\\n🎯 FRESH START COMPLETE!')
    print('✅ All ML data cleared')
    print('✅ Emergency traditional signals preserved')
    print('📝 System will collect new training data organically')

def create_100_sample_minimum_system():
    """Create system that requires 100 samples before using ML"""
    
    print('\\n🎯 CREATING 100-SAMPLE MINIMUM SYSTEM')
    print('=' * 38)
    
    # This will modify the enhanced pipeline to check sample count
    pipeline_patch = '''
def should_use_ml_predictions(self) -> bool:
    """
    Check if we have enough training data to use ML predictions
    Returns True only if we have 100+ balanced samples
    """
    try:
        import sqlite3
        conn = sqlite3.connect('data/trading_predictions.db')
        cursor = conn.cursor()
        
        # Count predictions with outcomes (training data)
        cursor.execute("""
            SELECT predicted_action, COUNT(*) as count
            FROM predictions 
            WHERE model_version NOT LIKE '%emergency%'
            AND entry_price > 0
            GROUP BY predicted_action
        """)
        
        action_counts = dict(cursor.fetchall())
        total_samples = sum(action_counts.values())
        
        # Require 100+ samples AND balanced distribution
        if total_samples < 100:
            self.logger.info(f"ML disabled: Only {total_samples}/100 training samples available")
            return False
        
        # Check balance - each action should have at least 10% of total
        buy_count = action_counts.get('BUY', 0) 
        sell_count = action_counts.get('SELL', 0)
        hold_count = action_counts.get('HOLD', 0)
        
        min_per_action = total_samples * 0.1  # 10% minimum per action
        
        if buy_count < min_per_action or sell_count < min_per_action or hold_count < min_per_action:
            self.logger.info(f"ML disabled: Unbalanced data (BUY:{buy_count}, SELL:{sell_count}, HOLD:{hold_count})")
            return False
        
        self.logger.info(f"ML enabled: {total_samples} balanced samples available")
        return True
        
    except Exception as e:
        self.logger.error(f"Error checking ML readiness: {e}")
        return False
    finally:
        conn.close()
'''
    
    # Create the patch file
    with open('ml_100_sample_patch.py', 'w') as f:
        f.write(f'''#!/usr/bin/env python3
"""
100-Sample Minimum ML System Patch
Add this method to EnhancedMLPipeline class
"""

{pipeline_patch}

# Usage in enhanced_morning_analyzer_with_ml.py:
# 
# Replace ML prediction logic with:
# if self.enhanced_pipeline.should_use_ml_predictions():
#     # Use ML predictions
#     ml_prediction = self.enhanced_pipeline.predict_enhanced(sentiment_data, symbol)
# else:
#     # Use traditional signals (automatic fallback)
#     ml_prediction = self._traditional_fallback_signals(symbol, current_price)
''')
    
    print('✅ Created ml_100_sample_patch.py')
    print('📝 This patch will be applied to the enhanced morning analyzer')

def create_traditional_fallback_method():
    """Create traditional fallback method for when ML isn't ready"""
    
    fallback_method = '''
def _traditional_fallback_signals(self, symbol, current_price):
    """
    Traditional signals fallback when ML has insufficient training data
    This runs automatically until 100+ balanced samples are collected
    """
    try:
        import yfinance as yf
        
        # Get technical data
        data = yf.download(symbol, period="30d", interval="1d", progress=False)
        if data.empty:
            return {
                'optimal_action': 'HOLD',
                'confidence_scores': {'average': 0.5},
                'magnitude_predictions': {'1d': 0.0},
                'reasoning': 'Fallback: No data available'
            }
        
        # Simple technical analysis
        close_prices = data['Close']
        volume = data['Volume']
        
        # RSI calculation
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
        
        # Moving averages
        sma_5 = float(close_prices.rolling(window=5).mean().iloc[-1])
        sma_20 = float(close_prices.rolling(window=20).mean().iloc[-1])
        
        # Price momentum
        price_change = ((current_price - close_prices.iloc[-6]) / close_prices.iloc[-6]) * 100 if len(close_prices) > 5 else 0
        
        # Volume analysis
        avg_volume = volume.rolling(window=10).mean().iloc[-1]
        volume_ratio = volume.iloc[-1] / avg_volume if avg_volume > 0 else 1.0
        
        # Balanced traditional signals (ensures all action types)
        confidence = 0.6
        
        # BUY conditions (encourage BUY signals)
        if (current_rsi < 35) and (sma_5 > sma_20) and (volume_ratio > 1.2):
            return {
                'optimal_action': 'BUY',
                'confidence_scores': {'average': 0.75},
                'magnitude_predictions': {'1d': max(0.02, abs(price_change)/100)},
                'reasoning': f'Traditional BUY: Oversold RSI ({current_rsi:.1f}) + momentum + volume'
            }
        elif (current_rsi < 40) and (price_change > 1.5):
            return {
                'optimal_action': 'BUY',
                'confidence_scores': {'average': 0.7},
                'magnitude_predictions': {'1d': max(0.015, abs(price_change)/100)},
                'reasoning': f'Traditional BUY: Low RSI + positive momentum ({price_change:.1f}%)'
            }
        
        # SELL conditions
        elif (current_rsi > 70) and (sma_5 < sma_20):
            return {
                'optimal_action': 'SELL',
                'confidence_scores': {'average': 0.75},
                'magnitude_predictions': {'1d': max(0.02, abs(price_change)/100)},
                'reasoning': f'Traditional SELL: Overbought RSI ({current_rsi:.1f}) + downward trend'
            }
        elif (current_rsi > 75):
            return {
                'optimal_action': 'SELL',
                'confidence_scores': {'average': 0.7},
                'magnitude_predictions': {'1d': max(0.015, abs(price_change)/100)},
                'reasoning': f'Traditional SELL: Very overbought RSI ({current_rsi:.1f})'
            }
        
        # HOLD (default)
        else:
            return {
                'optimal_action': 'HOLD',
                'confidence_scores': {'average': confidence},
                'magnitude_predictions': {'1d': min(0.01, abs(price_change)/100)},
                'reasoning': f'Traditional HOLD: Neutral (RSI: {current_rsi:.1f}, Change: {price_change:.1f}%)'
            }
            
    except Exception as e:
        self.logger.error(f"Traditional fallback error for {symbol}: {e}")
        return {
            'optimal_action': 'HOLD',
            'confidence_scores': {'average': 0.5},
            'magnitude_predictions': {'1d': 0.0},
            'reasoning': f'Traditional ERROR: {str(e)}'
        }
'''
    
    with open('traditional_fallback_method.py', 'w') as f:
        f.write(fallback_method)
    
    print('✅ Created traditional_fallback_method.py')
    print('📝 This method will be added to the enhanced morning analyzer')

def save_fresh_start_scripts():
    """Save all fresh start scripts"""
    
    print('\\n📦 SAVING FRESH START SCRIPTS')
    print('=' * 32)
    
    create_100_sample_minimum_system()
    create_traditional_fallback_method()
    
    # Create deployment script
    deploy_script = '''#!/usr/bin/env python3
"""
Deploy Fresh Start ML System to Remote Server
"""

def deploy_fresh_start():
    """Deploy the fresh start system"""
    
    print('🚀 DEPLOYING FRESH START ML SYSTEM')
    print('=' * 35)
    
    steps = [
        '1. Clear all ML data and models',
        '2. Add 100-sample minimum check to ML pipeline', 
        '3. Add traditional fallback method to morning analyzer',
        '4. Remove ML_ENABLED flag (no longer needed)',
        '5. System automatically uses traditional signals until 100 samples'
    ]
    
    for step in steps:
        print(f'   {step}')
    
    print('\\n✅ Fresh start system ready for deployment')
    print('📝 System will organically collect training data')
    print('🎯 ML will activate automatically at 100+ balanced samples')

if __name__ == '__main__':
    deploy_fresh_start()
'''
    
    with open('deploy_fresh_start.py', 'w') as f:
        f.write(deploy_script)
    
    print('✅ Created deploy_fresh_start.py')
    print('\\n🎯 FRESH START SYSTEM READY!')
    print('\\nFiles created:')
    print('   📄 ml_100_sample_patch.py - 100-sample minimum logic')
    print('   📄 traditional_fallback_method.py - Fallback signals method')
    print('   📄 deploy_fresh_start.py - Deployment guide')

if __name__ == '__main__':
    clear_all_ml_data()
    save_fresh_start_scripts()

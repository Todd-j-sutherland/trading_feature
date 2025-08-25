#!/usr/bin/env python3
"""
Final Simple Fresh Start Implementation
Just add sample count check without changing existing structure
"""

def apply_minimal_fresh_start():
    """Apply minimal fresh start changes that won't break existing code"""
    
    print('🎯 APPLYING MINIMAL FRESH START SYSTEM')
    print('=' * 38)
    
    # Read current file
    with open('enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py', 'r') as f:
        content = f.read()
    
    # 1. Just remove the ML_ENABLED lines (clean up emergency patch)
    print('1. CLEANING UP EMERGENCY PATCH:')
    print('-' * 30)
    
    emergency_lines = [
        'ML_ENABLED = False  # Switch to traditional signals only',
        'print("🚨 EMERGENCY MODE: ML disabled due to bias, using traditional signals")',
        'n# EMERGENCY PATCH: Disable ML due to bias (87% SELL, 0% BUY)'
    ]
    
    removed_count = 0
    for line in emergency_lines:
        if line in content:
            content = content.replace(line, '')
            removed_count += 1
    
    print(f'   ✅ Removed {removed_count} emergency patch lines')
    
    # 2. Add a simple check at the very beginning of predict_enhanced method
    print('\\n2. ADDING 100-SAMPLE CHECK TO ML PIPELINE:')
    print('-' * 41)
    
    # Find the enhanced pipeline class and add sample check
    if 'class EnhancedMLPipeline:' in content:
        # Add method to pipeline class
        sample_check_method = '''
    def has_sufficient_training_data(self, min_samples=100):
        """Check if we have sufficient training data for ML predictions"""
        try:
            import sqlite3
            conn = sqlite3.connect("data/trading_predictions.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions WHERE entry_price > 0")
            sample_count = cursor.fetchone()[0]
            conn.close()
            
            return sample_count >= min_samples
        except Exception as e:
            logger.warning(f"Error checking training data: {e}")
            return False
'''
        
        # Find where to insert (after __init__ method of EnhancedMLPipeline)
        pipeline_init_end = content.find('logger.info("Enhanced ML Pipeline initialized")')
        if pipeline_init_end > 0:
            next_method = content.find('def ', pipeline_init_end)
            if next_method > 0:
                content = content[:next_method] + sample_check_method + '\\n    ' + content[next_method:]
                print('   ✅ Added has_sufficient_training_data method to pipeline')
    
    # 3. Update predict_enhanced to check sample count
    if 'def predict_enhanced(self, sentiment_data: Dict, symbol: str)' in content:
        # Add check at beginning of predict_enhanced method
        predict_start = content.find('def predict_enhanced(self, sentiment_data: Dict, symbol: str)')
        method_body_start = content.find('"""', predict_start)
        method_body_start = content.find('"""', method_body_start + 1) + 3
        
        sample_check = '''
        
        # Fresh Start: Check if we have sufficient training data
        if not self.has_sufficient_training_data():
            return {
                "error": "insufficient_training_data",
                "message": "Less than 100 training samples available",
                "fallback_needed": True
            }
'''
        
        content = content[:method_body_start] + sample_check + content[method_body_start:]
        print('   ✅ Added sample check to predict_enhanced method')
    
    # Save the updated file
    with open('enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py', 'w') as f:
        f.write(content)
    
    print('\\n✅ MINIMAL FRESH START COMPLETE!')
    print('\\n🎯 SYSTEM BEHAVIOR:')
    print('   • ML pipeline checks sample count automatically')
    print('   • Returns error if < 100 samples')
    print('   • Morning analyzer will handle error gracefully')
    print('   • No structural changes to existing code')
    print('   • Seamless transition when 100+ samples collected')

if __name__ == '__main__':
    apply_minimal_fresh_start()

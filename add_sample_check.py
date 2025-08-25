#!/usr/bin/env python3
"""
Add sample check method to enhanced pipeline
"""

def add_sample_check_to_pipeline():
    """Add the sample check method to enhanced pipeline"""
    
    print('📝 ADDING SAMPLE CHECK TO ENHANCED PIPELINE')
    print('=' * 43)
    
    # Read the current pipeline file
    with open('app/core/ml/enhanced_pipeline.py', 'r') as f:
        content = f.read()
    
    # Check if method already exists
    if 'has_sufficient_training_data' in content:
        print('   ✅ Sample check method already exists')
        return
    
    # Create the method to add
    method_code = '''
    def has_sufficient_training_data(self, min_samples=100):
        """
        Check if we have sufficient training data for ML predictions
        
        Args:
            min_samples: Minimum number of samples required (default: 100)
            
        Returns:
            bool: True if sufficient training data available
        """
        try:
            import sqlite3
            conn = sqlite3.connect("data/trading_predictions.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions WHERE entry_price > 0")
            sample_count = cursor.fetchone()[0]
            conn.close()
            
            logger.info(f"Fresh Start: {sample_count}/{min_samples} training samples available")
            return sample_count >= min_samples
        except Exception as e:
            logger.warning(f"Error checking training data count: {e}")
            return False
'''
    
    # Find where to insert the method (after __init__)
    init_marker = 'logger.info("Enhanced ML Pipeline initialized")'
    init_pos = content.find(init_marker)
    
    if init_pos > 0:
        # Find the next method definition
        next_def = content.find('def ', init_pos)
        
        if next_def > 0:
            # Insert the new method before the next method
            new_content = content[:next_def] + method_code + '\n    ' + content[next_def:]
            
            # Save the updated file
            with open('app/core/ml/enhanced_pipeline.py', 'w') as f:
                f.write(new_content)
            
            print('   ✅ Added has_sufficient_training_data method')
            print('   📍 Location: app/core/ml/enhanced_pipeline.py')
        else:
            print('   ❌ Could not find next method to insert before')
    else:
        print('   ❌ Could not find __init__ method end marker')

if __name__ == '__main__':
    add_sample_check_to_pipeline()

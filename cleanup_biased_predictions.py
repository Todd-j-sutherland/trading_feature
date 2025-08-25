#!/usr/bin/env python3
"""
Clean up biased ML predictions and prepare for model retraining
"""

import sqlite3
from datetime import datetime, timedelta

def cleanup_biased_predictions():
    """Remove ML predictions that show severe bias"""
    
    print('🧹 CLEANING UP BIASED ML PREDICTIONS')
    print('=' * 40)
    
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    # 1. Identify the biased period (when no BUY signals appeared)
    print('1. IDENTIFYING BIASED PERIOD:')
    print('-' * 30)
    
    # Find the last BUY prediction
    cursor.execute('''
        SELECT prediction_timestamp, symbol, predicted_action
        FROM predictions 
        WHERE predicted_action = 'BUY'
        ORDER BY prediction_timestamp DESC
        LIMIT 1
    ''')
    
    last_buy = cursor.fetchone()
    if last_buy:
        print(f'   Last BUY prediction: {last_buy[0]} ({last_buy[1]} - {last_buy[2]})')
        bias_start = last_buy[0]
    else:
        print('   No BUY predictions found in database')
        # If no BUY predictions, let's be conservative and clean last 7 days
        bias_start = (datetime.now() - timedelta(days=7)).isoformat()
    
    # 2. Count predictions in biased period
    cursor.execute('''
        SELECT predicted_action, COUNT(*) as count
        FROM predictions 
        WHERE prediction_timestamp > ?
        GROUP BY predicted_action
        ORDER BY count DESC
    ''', (bias_start,))
    
    biased_actions = cursor.fetchall()
    total_biased = sum(count for _, count in biased_actions)
    
    print(f'\\n2. BIASED PREDICTIONS SINCE {bias_start}:')
    print('-' * 50)
    for action, count in biased_actions:
        percentage = (count / total_biased) * 100 if total_biased > 0 else 0
        print(f'   {action}: {count} predictions ({percentage:.1f}%)')
    print(f'   Total biased predictions: {total_biased}')
    
    # 3. Check if we should proceed with cleanup
    buy_count = next((count for action, count in biased_actions if action == 'BUY'), 0)
    sell_count = next((count for action, count in biased_actions if action == 'SELL'), 0)
    
    bias_confirmed = False
    if buy_count == 0 and sell_count > 20:
        bias_confirmed = True
        print('\\n   ✅ BIAS CONFIRMED: Zero BUY signals with significant SELL bias')
    elif total_biased > 0:
        sell_percentage = (sell_count / total_biased) * 100
        if sell_percentage > 85:
            bias_confirmed = True
            print(f'\\n   ✅ BIAS CONFIRMED: {sell_percentage:.1f}% SELL predictions')
    
    if not bias_confirmed:
        print('\\n   ❌ NO SEVERE BIAS DETECTED - Cleanup not recommended')
        conn.close()
        return
    
    # 4. Backup before deletion
    print('\\n3. CREATING BACKUP:')
    print('-' * 18)
    
    backup_table = f'biased_predictions_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    cursor.execute(f'''
        CREATE TABLE {backup_table} AS 
        SELECT * FROM predictions 
        WHERE prediction_timestamp > ?
    ''', (bias_start,))
    
    backup_count = cursor.rowcount
    print(f'   ✅ Backup created: {backup_table} ({backup_count} records)')
    
    # 5. Delete biased predictions
    print('\\n4. DELETING BIASED PREDICTIONS:')
    print('-' * 32)
    
    cursor.execute('''
        DELETE FROM predictions 
        WHERE prediction_timestamp > ?
    ''', (bias_start,))
    
    deleted_count = cursor.rowcount
    print(f'   ✅ Deleted {deleted_count} biased predictions')
    
    # 6. Verify cleanup
    cursor.execute('''
        SELECT predicted_action, COUNT(*) as count
        FROM predictions 
        GROUP BY predicted_action
        ORDER BY count DESC
    ''')
    
    remaining_actions = cursor.fetchall()
    remaining_total = sum(count for _, count in remaining_actions)
    
    print('\\n5. REMAINING PREDICTIONS AFTER CLEANUP:')
    print('-' * 40)
    for action, count in remaining_actions:
        percentage = (count / remaining_total) * 100 if remaining_total > 0 else 0
        print(f'   {action}: {count} predictions ({percentage:.1f}%)')
    print(f'   Total remaining: {remaining_total}')
    
    # 7. Check if we have balanced data for retraining
    if remaining_total > 0:
        buy_remaining = next((count for action, count in remaining_actions if action == 'BUY'), 0)
        sell_remaining = next((count for action, count in remaining_actions if action == 'SELL'), 0)
        hold_remaining = next((count for action, count in remaining_actions if action == 'HOLD'), 0)
        
        print('\\n6. RETRAINING DATA ASSESSMENT:')
        print('-' * 30)
        
        if buy_remaining > 0 and sell_remaining > 0 and hold_remaining > 0:
            print('   ✅ BALANCED DATA: All action types present')
            print('   ✅ READY FOR RETRAINING')
        else:
            print('   ⚠️  UNBALANCED DATA: Some action types missing')
            print('   ⚠️  May need additional historical data for retraining')
    else:
        print('\\n6. NO REMAINING DATA - NEED FRESH START')
        print('-' * 40)
        print('   ⚠️  All predictions deleted - need to collect new training data')
    
    conn.commit()
    conn.close()
    
    print('\\n✅ CLEANUP COMPLETE!')
    print('\\nNEXT STEPS:')
    print('1. Verify traditional signals are working')
    print('2. Collect new balanced training data')
    print('3. Retrain ML model with proper BUY/SELL/HOLD distribution')
    print('4. Add bias monitoring to prevent future issues')

if __name__ == '__main__':
    cleanup_biased_predictions()

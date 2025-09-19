import sqlite3
import json
from datetime import datetime

def comprehensive_risk_analysis():
    print('COMPREHENSIVE RISK CALCULATION ANALYSIS')
    print('=' * 60)
    print()
    
    conn = sqlite3.connect('data/trading_predictions.db')
    cursor = conn.cursor()
    
    # Get all stocks for both dates
    symbols = ['ANZ.AX', 'CBA.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'QBE.AX', 'SUN.AX']
    
    print('1. CONFIDENCE DROP ANALYSIS (Sept 12 vs Sept 19)')
    print('-' * 50)
    
    for symbol in symbols:
        # Sept 12 data
        cursor.execute('''
            SELECT action_confidence, confidence_components, tech_score, 
                   news_sentiment, volume_trend, risk_level
            FROM predictions 
            WHERE symbol = ? AND DATE(prediction_timestamp) = '2025-09-12'
            LIMIT 1
        ''', (symbol,))
        sept12 = cursor.fetchone()
        
        # Sept 19 data  
        cursor.execute('''
            SELECT action_confidence, confidence_components, tech_score,
                   news_sentiment, volume_trend, risk_level
            FROM predictions
            WHERE symbol = ? AND DATE(prediction_timestamp) = '2025-09-19'
            LIMIT 1
        ''', (symbol,))
        sept19 = cursor.fetchone()
        
        if sept12 and sept19:
            conf12 = sept12[0]
            conf19 = sept19[0]
            conf_change = conf19 - conf12
            
            # Extract risk components
            try:
                components12 = json.loads(sept12[1]) if sept12[1] else {}
                components19 = json.loads(sept19[1]) if sept19[1] else {}
                risk12 = components12.get('risk_component', 0)
                risk19 = components19.get('risk_component', 0)
                risk_change = risk19 - risk12
            except:
                risk12 = risk19 = risk_change = 0
            
            print(f'{symbol:7} | Conf: {conf12:.3f}→{conf19:.3f} ({conf_change:+.3f}) | '
                  f'Risk: {risk12:.4f}→{risk19:.4f} ({risk_change:+.4f})')
    
    print()
    print('2. RISK COMPONENT DETAILED ANALYSIS')
    print('-' * 40)
    
    # Analyze risk distribution
    cursor.execute('''
        SELECT symbol, confidence_components, action_confidence, risk_level,
               DATE(prediction_timestamp) as date
        FROM predictions 
        WHERE DATE(prediction_timestamp) IN ('2025-09-12', '2025-09-19')
        AND confidence_components IS NOT NULL
        ORDER BY symbol, date
    ''')
    
    risk_stats = {'2025-09-12': [], '2025-09-19': []}
    
    for row in cursor.fetchall():
        symbol, components_json, confidence, risk_level, date = row
        try:
            components = json.loads(components_json)
            risk_component = components.get('risk_component', 0)
            risk_stats[date].append({
                'symbol': symbol,
                'risk_component': risk_component,
                'confidence': confidence,
                'risk_level': risk_level
            })
        except:
            continue
    
    # Calculate statistics
    for date in ['2025-09-12', '2025-09-19']:
        risks = [item['risk_component'] for item in risk_stats[date]]
        confidences = [item['confidence'] for item in risk_stats[date]]
        
        if risks:
            avg_risk = sum(risks) / len(risks)
            max_risk = max(risks)
            min_risk = min(risks)
            avg_conf = sum(confidences) / len(confidences)
            
            print(f'{date}:')
            print(f'  Average Risk Component: {avg_risk:.4f}')
            print(f'  Risk Range: {min_risk:.4f} - {max_risk:.4f}')
            print(f'  Average Confidence: {avg_conf:.3f} ({avg_conf*100:.1f}%)')
            print()
    
    print('3. THRESHOLD ANALYSIS')
    print('-' * 20)
    
    # Check how many would qualify for BUY at different thresholds
    thresholds = [0.50, 0.55, 0.60, 0.65, 0.70]
    
    for threshold in thresholds:
        count_sept12 = len([item for item in risk_stats['2025-09-12'] if item['confidence'] >= threshold])
        count_sept19 = len([item for item in risk_stats['2025-09-19'] if item['confidence'] >= threshold])
        
        print(f'Threshold {threshold*100:2.0f}%: Sept12={count_sept12}/7 stocks, Sept19={count_sept19}/7 stocks')
    
    print()
    print('4. RISK IMPACT QUANTIFICATION')
    print('-' * 30)
    
    total_confidence_loss = 0
    total_risk_penalty = 0
    
    for date in ['2025-09-12', '2025-09-19']:
        risk_penalty = sum(item['risk_component'] * 0.20 for item in risk_stats[date])
        print(f'{date}: Total Risk Penalty = {risk_penalty:.4f} ({risk_penalty*100:.1f}%)')
        
        if date == '2025-09-19':
            total_risk_penalty = risk_penalty
        elif date == '2025-09-12':
            baseline_penalty = risk_penalty
    
    added_penalty = total_risk_penalty - baseline_penalty if 'baseline_penalty' in locals() else 0
    
    print(f'Additional Risk Penalty Added: {added_penalty:.4f} ({added_penalty*100:.1f}%)')
    print()
    
    print('5. RECOMMENDATIONS')
    print('-' * 15)
    print('Based on this analysis:')
    
    # Calculate what confidence would be with different risk weights
    current_avg_conf_sept19 = sum(item['confidence'] for item in risk_stats['2025-09-19']) / len(risk_stats['2025-09-19'])
    avg_risk_sept19 = sum(item['risk_component'] for item in risk_stats['2025-09-19']) / len(risk_stats['2025-09-19'])
    
    print(f'Current Avg Confidence (Sept 19): {current_avg_conf_sept19*100:.1f}%')
    print(f'Current Avg Risk Component: {avg_risk_sept19:.4f}')
    print()
    
    # Simulate different risk weights
    for new_weight in [0.10, 0.15, 0.20]:
        # Remove current risk impact and apply new weight
        confidence_without_risk = current_avg_conf_sept19 + (avg_risk_sept19 * 0.20)
        new_confidence = confidence_without_risk - (avg_risk_sept19 * new_weight)
        
        buy_qualified = len([item for item in risk_stats['2025-09-19'] 
                           if (item['confidence'] + (item['risk_component'] * 0.20) - (item['risk_component'] * new_weight)) >= 0.65])
        
        print(f'Risk Weight {new_weight*100:2.0f}%: Avg Confidence → {new_confidence*100:.1f}%, BUY Qualified: {buy_qualified}/7')
    
    conn.close()

if __name__ == "__main__":
    comprehensive_risk_analysis()

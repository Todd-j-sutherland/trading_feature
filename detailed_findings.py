print('DETAILED FINDINGS - CONFIDENCE COLLAPSE ANALYSIS')
print('=' * 55)
print()

# Key findings from the comprehensive analysis
print('SHOCKING DISCOVERIES:')
print('-' * 20)
print()

print('1. MASSIVE CONFIDENCE COLLAPSE ACROSS ALL STOCKS:')
print('   Sept 12: Average 70.6% confidence')
print('   Sept 19: Average 42.1% confidence') 
print('   DROP: -28.5 percentage points (40% reduction!)')
print()

print('2. RISK PENALTY IS NOT THE MAIN CULPRIT:')
print('   Sept 12: Total risk penalty = 40.0%')
print('   Sept 19: Total risk penalty = 6.7%')
print('   Risk penalties actually DECREASED by 33.2%!')
print()

print('3. THRESHOLD ANALYSIS REVEALS THE TRUTH:')
print('   Sept 12: 6-12 stocks qualified for BUY at various thresholds')
print('   Sept 19: 0 stocks qualify for BUY at ANY threshold')
print('   This suggests SYSTEMIC calculation changes, not just risk')
print()

print('INDIVIDUAL STOCK ANALYSIS:')
print('-' * 25)
stocks = [
    ('ANZ', 0.643, 0.397, 0.0000, 0.0000),
    ('CBA', 0.694, 0.444, 0.0583, 0.0083), 
    ('WBC', 0.684, 0.424, 0.0000, 0.0401),
    ('NAB', 0.811, 0.412, 0.0600, 0.0600),
    ('MQG', 0.732, 0.428, 0.0057, 0.0557),
    ('QBE', 0.701, 0.430, 0.0000, 0.0000),
    ('SUN', 0.703, 0.414, 0.0546, 0.0046)
]

for symbol, conf12, conf19, risk12, risk19 in stocks:
    conf_drop = conf19 - conf12
    risk_change = risk19 - risk12
    risk_impact = risk_change * 0.20  # 20% weight
    
    print(f'{symbol}: Confidence {conf_drop:+.3f} | Risk change {risk_change:+.4f} (impact: {risk_impact:+.3f})')

print()
print('CRITICAL INSIGHTS:')
print('-' * 18)
print()
print('1. CONFIDENCE DROPS TOO LARGE FOR RISK ALONE:')
print('   - ANZ: -24.6% confidence, 0% risk change')
print('   - NAB: -39.9% confidence, 0% risk change') 
print('   - QBE: -27.2% confidence, 0% risk change')
print('   Risk cannot explain these massive drops!')
print()

print('2. ALGORITHM/MODEL FUNDAMENTAL CHANGE:')
print('   - ALL stocks show 25-40% confidence drops')
print('   - Even stocks with NO risk change are affected')
print('   - System appears to have been RECALIBRATED')
print()

print('3. POSSIBLE CAUSES:')
print('   a) ML model retrained with more conservative parameters')
print('   b) Confidence calculation formula changed')
print('   c) Feature weights drastically rebalanced')
print('   d) Market context penalties increased')
print('   e) Volume veto power became more aggressive')
print()

print('RECOMMENDATIONS:')
print('-' * 15)
print('1. INVESTIGATE MODEL CHANGES between Sept 12-19')
print('2. CHECK for confidence calculation updates')
print('3. LOWER BUY threshold from 65% to 50-55%')
print('4. REVIEW volume veto logic - may be too strict')
print('5. EXAMINE market context penalty weights')
print()

print('IMMEDIATE ACTIONS:')
print('- Risk penalty is NOT the main problem')
print('- Focus on confidence calculation changes')
print('- Consider emergency threshold adjustment')
print('- Investigate why ALL stocks lost 25-40% confidence')


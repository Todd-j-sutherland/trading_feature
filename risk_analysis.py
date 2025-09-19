print('WBC CONFIDENCE CALCULATION - With vs Without Risk Penalty')
print('=' * 60)

# WBC Sept 19th actual components from the database
technical_component = 0.4124041748046875
news_component = 0.22456176757812502  
volume_component = 0.121668701171875
risk_component = 0.04010589599609375

# System weights
weights = {
    'technical': 0.25,
    'news': 0.20,
    'volume': 0.35,
    'risk': 0.20
}

print('SEPTEMBER 19th ACTUAL COMPONENTS:')
print(f'  Technical: {technical_component:.4f}')
print(f'  News: {news_component:.4f}')
print(f'  Volume: {volume_component:.4f}')
print(f'  Risk: {risk_component:.4f}')
print()

# Calculate WITH risk penalty (current system)
confidence_with_risk = (
    technical_component * weights['technical'] +
    news_component * weights['news'] +
    volume_component * weights['volume'] +
    risk_component * weights['risk']
)

# Calculate WITHOUT risk penalty (risk = 0)
confidence_without_risk = (
    technical_component * weights['technical'] +
    news_component * weights['news'] +
    volume_component * weights['volume'] +
    0.0 * weights['risk']  # No risk penalty
)

print('CONFIDENCE CALCULATIONS:')
print(f'  WITH Risk Penalty: {confidence_with_risk:.4f} ({confidence_with_risk*100:.1f}%)')
print(f'  WITHOUT Risk Penalty: {confidence_without_risk:.4f} ({confidence_without_risk*100:.1f}%)')
print()

difference = confidence_without_risk - confidence_with_risk
print(f'IMPACT OF RISK PENALTY:')
print(f'  Confidence Loss: {difference:.4f} ({difference*100:.1f} percentage points)')
print(f'  Relative Impact: {(difference/confidence_with_risk)*100:.1f}% reduction')
print()

# Check against BUY threshold
buy_threshold = 0.65
print(f'BUY THRESHOLD ANALYSIS (65%):')
print(f'  Current (with risk): {confidence_with_risk:.3f} < {buy_threshold} -> HOLD')
print(f'  Without risk: {confidence_without_risk:.3f} < {buy_threshold} -> Still HOLD')
print()

if confidence_without_risk >= buy_threshold:
    print('  ✅ WITHOUT risk penalty, WBC would qualify for BUY!')
else:
    print(f'  ❌ Even without risk, WBC needs {buy_threshold - confidence_without_risk:.3f} more confidence')

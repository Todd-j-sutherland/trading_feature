print('MQG CONFIDENCE ANALYSIS - Why HOLD Despite +1.1% Gain')
print('=' * 55)
print()

print('MQG SEPTEMBER 12th vs 19th COMPARISON:')
print('-' * 40)

# September 12th data
sept12_confidence = 0.731569152832031
sept12_tech = 36
sept12_news = 0.133
sept12_volume = -30.0
sept12_risk = 0.0057275390625

# September 19th data  
sept19_confidence = 0.4276
sept19_tech = 41
sept19_news = 0.138
sept19_volume = -17.0
sept19_risk = 0.055727539062500005

print('SEPTEMBER 12th:')
print(f'  Confidence: {sept12_confidence:.3f} ({sept12_confidence*100:.1f}%)')
print(f'  Technical: {sept12_tech}/100')
print(f'  News: {sept12_news:.3f} ({sept12_news*100:.1f}%)')
print(f'  Volume: {sept12_volume}%')
print(f'  Risk Component: {sept12_risk:.4f}')
print()

print('SEPTEMBER 19th:')
print(f'  Confidence: {sept19_confidence:.3f} ({sept19_confidence*100:.1f}%)')
print(f'  Technical: {sept19_tech}/100')
print(f'  News: {sept19_news:.3f} ({sept19_news*100:.1f}%)')
print(f'  Volume: {sept19_volume}%')
print(f'  Risk Component: {sept19_risk:.4f}')
print()

print('CHANGES (Sept 12 -> Sept 19):')
print('-' * 30)
conf_change = sept19_confidence - sept12_confidence
tech_change = sept19_tech - sept12_tech
news_change = sept19_news - sept12_news
volume_change = sept19_volume - sept12_volume
risk_change = sept19_risk - sept12_risk

print(f'Confidence: {conf_change:+.3f} ({conf_change*100:+.1f}%)')
print(f'Technical: {tech_change:+d} points')
print(f'News: {news_change:+.3f} ({news_change*100:+.1f}%)')
print(f'Volume: {volume_change:+.1f}% (less negative)')
print(f'Risk: {risk_change:+.4f} (PENALTY INCREASED 10x!)')
print()

print('RISK PENALTY ANALYSIS:')
print('-' * 20)
risk_weight = 0.20
risk_impact_sept12 = sept12_risk * risk_weight
risk_impact_sept19 = sept19_risk * risk_weight
risk_penalty_increase = risk_impact_sept19 - risk_impact_sept12

print(f'  Sept 12 Risk Impact: {risk_impact_sept12:.4f}')
print(f'  Sept 19 Risk Impact: {risk_impact_sept19:.4f}')
print(f'  Additional Penalty: {risk_penalty_increase:.4f} ({risk_penalty_increase*100:.1f}%)')
print()

confidence_without_extra_risk = sept19_confidence + risk_penalty_increase

print('WHAT IF RISK PENALTY STAYED THE SAME:')
print(f'  Current Confidence: {sept19_confidence*100:.1f}%')
print(f'  Without Extra Risk: {confidence_without_extra_risk*100:.1f}%')
print(f'  Recovery: +{risk_penalty_increase*100:.1f}%')
print()

buy_threshold = 0.65
print('BUY THRESHOLD ANALYSIS (65%):')
print(f'  Current: {sept19_confidence*100:.1f}% < 65% -> HOLD')
print(f'  Gap to BUY: {(buy_threshold - sept19_confidence)*100:.1f}%')
print()

print('WHY MQG IS PENALIZED DESPITE +1.1% GAIN:')
print('1. MASSIVE Risk penalty increase (10x higher)')
print('2. Volume still negative (-17%) despite improvement')
print('3. 65% BUY threshold too high for current market')
print('4. Risk calculation appears to be overreacting')

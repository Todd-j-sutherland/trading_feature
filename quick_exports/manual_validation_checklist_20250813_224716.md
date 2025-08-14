
# 📋 MANUAL DATA VALIDATION CHECKLIST

## 🎯 PREDICTIONS TABLE VALIDATION

### Action Distribution Check
- [ ] BUY signals: Should be 20-40% of total
- [ ] SELL signals: Should be 10-30% of total  
- [ ] HOLD signals: Should be 30-70% of total
- [ ] No unknown/invalid actions

### Confidence Distribution Check
- [ ] Average confidence: Should be 0.4-0.7
- [ ] Not all values exactly 0.5
- [ ] Reasonable spread (std > 0.05)
- [ ] No values outside 0.0-1.0 range

### Feature Vector Validation
- [ ] Sentiment scores: Range -1.0 to 1.0, not all 0.0
- [ ] RSI values: Range 0-100, NOT mostly 50.0
- [ ] MACD values: Realistic range, NOT mostly 0.0
- [ ] Current prices: $15-$150 for ASX stocks, NOT 0.0
- [ ] No completely identical feature vectors

### Symbol Validation
- [ ] Only valid ASX symbols (*.AX format)
- [ ] Focus on: ANZ.AX, CBA.AX, WBC.AX, NAB.AX
- [ ] No invalid/test symbols

### Timestamp Validation
- [ ] Recent predictions (within last 7 days)
- [ ] No future timestamps
- [ ] Logical sequence

## 📈 OUTCOMES TABLE VALIDATION (if exists)

### Return Values
- [ ] Realistic returns: -10% to +10% typical
- [ ] Not all 0.0% returns
- [ ] Entry/exit prices make sense

### Reference Integrity
- [ ] All outcome prediction_ids exist in predictions table
- [ ] No orphaned outcomes

## 🚨 RED FLAGS TO WATCH FOR

### Data Quality Issues
- [ ] More than 50% of RSI values = 50.0 (static default)
- [ ] More than 50% of MACD values = 0.0 (static default)
- [ ] More than 80% of one action type
- [ ] All confidence values clustered around 0.5
- [ ] Many 0.0 prices
- [ ] Identical feature vectors

### System Issues
- [ ] No new predictions in 24+ hours
- [ ] Error patterns in feature vectors
- [ ] Missing data for major symbols

## ✅ VALIDATION STEPS

1. **Export Data**: Run data_export_validator.py
2. **Review CSVs**: Check exported CSV files manually
3. **Spot Check**: Verify 10-20 random predictions
4. **Cross Reference**: Compare with expected value ranges
5. **Flag Issues**: Document any concerning patterns

## 📊 EXPECTED VALUE RANGES

### Technical Indicators
- RSI: 20-80 (30-70 typical), NOT consistently 50
- MACD: -2.0 to +2.0 typical, NOT consistently 0
- Prices: $15-$150 for major banks
- Sentiment: -0.5 to +0.5 typical

### Prediction Patterns
- Confidence: 0.3-0.8 typical
- Actions: Mixed distribution, not >90% one type
- Timestamps: Recent and sequential

---
Generated: {datetime.now().isoformat()}

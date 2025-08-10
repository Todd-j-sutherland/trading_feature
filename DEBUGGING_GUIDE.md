# 🔍 Return Calculation Debugging Guide

## Step-by-Step Investigation Process

### Step 1: Find the Calculation Code

Search for files that calculate return percentages:

```bash
# Find return calculation logic
cd /Users/toddsutherland/Repos/trading_feature
grep -r "return_pct" --include="*.py" . | head -20
grep -r "exit_price.*entry_price" --include="*.py" .
grep -r "((.*exit.*entry.*)/.*entry.*)" --include="*.py" .
```

Look for patterns like:
```python
# Common calculation patterns to find:
return_pct = ((exit_price - entry_price) / entry_price) * 100
return_percentage = (exit_price - entry_price) / entry_price
pct_return = ((exit - entry) / entry) * 100
```

### Step 2: Examine the Evening Analysis Workflow

The issue likely occurs in evening analysis where outcomes are recorded:

```bash
# Look for evening-related files
find . -name "*evening*" -type f
find . -name "*outcome*" -type f
ls -la *evening* *outcome* 2>/dev/null
```

Common file names to check:
- `evening_analyzer.py`
- `enhanced_evening_analyzer.py`
- `outcome_processor.py`
- `trading_analyzer.py`

### Step 3: Database Insert/Update Analysis

Search for database operations on enhanced_outcomes:

```bash
# Find database operations
grep -r "INSERT INTO enhanced_outcomes" --include="*.py" .
grep -r "UPDATE enhanced_outcomes" --include="*.py" .
grep -r "enhanced_outcomes.*SET" --include="*.py" .
```

### Step 4: Variable Name Investigation

Look for potential variable mix-ups:

```bash
# Check for confusing variable names
grep -r "entry_price\|exit_price\|current_price\|close_price" --include="*.py" . | grep -v ".pyc"
```

## 🐛 Common Bug Patterns

### Pattern 1: Variable Mix-up
```python
# BUG: Using wrong variables
return_pct = ((entry_price - exit_price) / exit_price) * 100  # ❌ WRONG ORDER

# CORRECT:
return_pct = ((exit_price - entry_price) / entry_price) * 100  # ✅ CORRECT
```

### Pattern 2: Data Source Confusion
```python
# BUG: Using different price sources
entry_price = feature_data['current_price']  # From features table
exit_price = yahoo_data['Close']             # From Yahoo API
# These might be different timeframes/sources

# CORRECT: Ensure consistent data sources
entry_price = feature_data['current_price']
exit_price = get_exit_price_same_source(symbol, exit_time)
```

### Pattern 3: Timing Issues
```python
# BUG: Wrong time calculation
exit_time = prediction_time + timedelta(hours=24)  # Might hit weekend
exit_price = get_price_at_time(symbol, exit_time)  # No trading data

# CORRECT: Business day calculation
exit_time = get_next_trading_day(prediction_time)
exit_price = get_price_at_time(symbol, exit_time)
```

### Pattern 4: Update Logic Error
```python
# BUG: Partial updates overwriting correct data
cursor.execute("""
    UPDATE enhanced_outcomes 
    SET return_pct = ? 
    WHERE symbol = ?
""", (new_return, symbol))  # ❌ Updates ALL records for symbol

# CORRECT: Specific record updates
cursor.execute("""
    UPDATE enhanced_outcomes 
    SET return_pct = ? 
    WHERE id = ?
""", (new_return, outcome_id))  # ✅ Updates specific record
```

## 🔬 Debugging Techniques

### Technique 1: Add Debug Logging
```python
# Add this to the calculation function:
def calculate_return_pct(entry_price, exit_price, symbol=None):
    if entry_price is None or exit_price is None:
        print(f"DEBUG: Missing prices for {symbol}: entry={entry_price}, exit={exit_price}")
        return None
    
    return_pct = ((exit_price - entry_price) / entry_price) * 100
    
    print(f"DEBUG: {symbol} calculation:")
    print(f"  Entry: ${entry_price:.4f}")
    print(f"  Exit:  ${exit_price:.4f}")
    print(f"  Return: {return_pct:.4f}%")
    
    return return_pct
```

### Technique 2: Data Validation
```python
# Add validation before storing
def validate_return_calculation(entry_price, exit_price, stored_return):
    calculated = ((exit_price - entry_price) / entry_price) * 100
    difference = abs(stored_return - calculated)
    
    if difference > 0.01:
        print(f"WARNING: Return calculation mismatch!")
        print(f"  Calculated: {calculated:.4f}%")
        print(f"  Stored: {stored_return:.4f}%")
        print(f"  Difference: {difference:.4f}%")
        return False
    return True
```

### Technique 3: Mock Data Testing
```python
# Test with known values
def test_calculation_function():
    test_cases = [
        (100.0, 105.0, 5.0),    # 5% gain
        (100.0, 95.0, -5.0),    # 5% loss
        (100.0, 100.0, 0.0),    # No change
    ]
    
    for entry, exit, expected in test_cases:
        result = calculate_return_pct(entry, exit)
        assert abs(result - expected) < 0.01, f"Expected {expected}, got {result}"
    
    print("✅ All calculation tests passed")
```

## 🎯 Specific Investigation Areas

### 1. Price Data Consistency
Check if entry_price and exit_price come from the same data source:
```sql
-- Look for price inconsistencies
SELECT symbol, entry_price, exit_price_1d, 
       ABS(entry_price - exit_price_1d) as price_diff
FROM enhanced_outcomes 
WHERE ABS(entry_price - exit_price_1d) > 50  -- Large price differences
ORDER BY price_diff DESC;
```

### 2. Timestamp Analysis
Check if calculations happen at correct times:
```sql
-- Look for timing patterns
SELECT symbol, prediction_timestamp, created_at,
       JULIANDAY(created_at) - JULIANDAY(prediction_timestamp) as days_diff
FROM enhanced_outcomes 
WHERE return_pct IS NOT NULL
ORDER BY days_diff DESC;
```

### 3. Symbol-Specific Patterns
Check if certain symbols are more affected:
```sql
-- Check error patterns by symbol
SELECT symbol, 
       COUNT(*) as total_records,
       SUM(CASE WHEN ABS(return_pct - ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4)) > 0.01 THEN 1 ELSE 0 END) as error_count
FROM enhanced_outcomes 
WHERE return_pct IS NOT NULL AND exit_price_1d IS NOT NULL
GROUP BY symbol
ORDER BY error_count DESC;
```

## 🔧 Quick Fix Template

Once you find the buggy calculation, here's a template for the fix:

```python
def fix_return_calculation():
    """Fix return_pct calculation for all existing records"""
    
    conn = sqlite3.connect('data/trading_unified.db')
    cursor = conn.cursor()
    
    # Get all records that need fixing
    cursor.execute("""
        SELECT id, entry_price, exit_price_1d, return_pct
        FROM enhanced_outcomes 
        WHERE exit_price_1d IS NOT NULL 
        AND return_pct IS NOT NULL
    """)
    
    records = cursor.fetchall()
    fixed_count = 0
    
    for record_id, entry, exit, stored_return in records:
        # Calculate correct return
        correct_return = ((exit - entry) / entry) * 100
        
        # Check if fix is needed
        if abs(stored_return - correct_return) > 0.01:
            cursor.execute("""
                UPDATE enhanced_outcomes 
                SET return_pct = ? 
                WHERE id = ?
            """, (correct_return, record_id))
            fixed_count += 1
            
            print(f"Fixed record {record_id}: {stored_return:.4f}% → {correct_return:.4f}%")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Fixed {fixed_count} records")
    return fixed_count
```

## 📊 Verification After Fix

After implementing the fix, run these verification steps:

```bash
# 1. Run verification summary
python verification_summary.py

# 2. Check calculation accuracy
python test_return_calculations.py

# 3. Validate trading patterns
python simple_return_test.py

# 4. Check for remaining issues
sqlite3 data/trading_unified.db "
SELECT COUNT(*) as error_count
FROM enhanced_outcomes 
WHERE exit_price_1d IS NOT NULL 
  AND return_pct IS NOT NULL
  AND ABS(return_pct - ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4)) > 0.01;
"
```

Expected results after fix:
- ✅ Error count should be 0
- ✅ Calculation accuracy should be >99%
- ✅ BUY/SELL win rates should be realistic (not 100%/0%)

---
*Debug Guide Created: August 10, 2025*  
*Use this guide to systematically find and fix the return calculation bug*

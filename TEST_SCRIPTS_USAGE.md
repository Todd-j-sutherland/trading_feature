# 🧪 ASX Trading System - Test Scripts with Log Analysis

## Overview
Two test scripts have been created to run your core features and automatically analyze logs for errors and warnings.

## Scripts Available

### 1. `simple_test_with_logs.sh` (Recommended)
**Runs your exact command sequence with log analysis**

```bash
# Run the script
./simple_test_with_logs.sh
```

**What it does:**
- Runs your exact commands in sequence:
  - `python -m app.main morning`
  - `python enhanced_ml_system/multi_bank_data_collector.py` 
  - `python export_and_validate_metrics.py`
  - `python enhanced_ml_system/html_dashboard_generator.py`
- Captures all output to temp log files
- Automatically searches for errors, warnings, and critical issues
- Provides summary of issues found
- Shows quick commands to view logs

### 2. `comprehensive_test_with_logs.sh` (Advanced)
**Comprehensive testing with individual test tracking**

```bash
# Basic comprehensive test
./comprehensive_test_with_logs.sh

# Include evening analysis (takes 5-10 minutes)
./comprehensive_test_with_logs.sh --include-evening
```

**What it does:**
- Runs each test individually and tracks pass/fail status
- Creates separate log files for each test
- Analyzes each log file individually
- Provides detailed error analysis per test
- Creates a comprehensive summary report

## Log Files Created

Both scripts create temporary directories with logs:
- Location: `/tmp/asx_test_YYYYMMDD_HHMMSS/` or `/tmp/asx_trading_test_YYYYMMDD_HHMMSS/`
- Files include complete output and error analysis

## Sample Output

### Error Analysis Example:
```
🚨 ERRORS FOUND:
================
ERROR: Could not load model file
ModuleNotFoundError: No module named 'some_module'

⚠️  WARNINGS FOUND:
==================
WARNING: Using fallback data source
UserWarning: Low confidence prediction

📊 ISSUE SUMMARY
================
Errors: 2
Warnings: 2
Critical: 0
```

## Quick Commands After Running

After running either script, you'll get commands like:
```bash
# View complete output
cat /tmp/asx_test_20250727_143022/combined_output.log

# View only errors/warnings  
cat /tmp/asx_test_20250727_143022/errors_and_warnings.log

# Search for specific issues
grep -i 'connection' /tmp/asx_test_20250727_143022/combined_output.log
```

## Remote Testing Usage

For remote testing on `ssh root@170.64.199.151`:

```bash
# 1. SSH to remote server
ssh root@170.64.199.151

# 2. Navigate to project directory
cd /path/to/trading_feature

# 3. Activate environment
source ../trading_venv/bin/activate

# 4. Run test script
./simple_test_with_logs.sh

# 5. Check results
# The script will show you the exact commands to view logs
```

## Benefits

✅ **Automatic Error Detection**: No need to manually scan output
✅ **Log Preservation**: All output saved for later analysis  
✅ **Issue Categorization**: Errors, warnings, and critical issues separated
✅ **Quick Analysis**: Summary shows issue counts immediately
✅ **Reusable**: Can be run multiple times to compare results
✅ **Remote Friendly**: Works perfectly on SSH connections

## Troubleshooting

If scripts fail to run:
```bash
# Make executable (if needed)
chmod +x simple_test_with_logs.sh
chmod +x comprehensive_test_with_logs.sh

# Check if Python is available
python --version

# Run commands manually if needed
python -m app.main morning 2>&1 | tee /tmp/manual_test.log
```

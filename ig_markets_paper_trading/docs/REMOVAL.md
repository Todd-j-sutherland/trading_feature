# IG Markets Paper Trading System Removal Guide

## Quick Removal

To completely remove the IG Markets Paper Trading System from your workspace:

### 1. Stop Any Running Processes
```bash
# Kill any running paper trading processes
pkill -f "paper_trader"
pkill -f "ig_markets"

# Remove from crontab
crontab -l | grep -v "ig_markets_paper_trading" | crontab -
```

### 2. Remove the System
```bash
# Remove the entire system directory
rm -rf ig_markets_paper_trading/
```

### 3. Clean Up References (Optional)

If you've integrated any calls to the paper trading system in other scripts:

```bash
# Search for references in your workspace
grep -r "ig_markets_paper_trading" . --exclude-dir=ig_markets_paper_trading

# Common files that might reference the system:
# - Cron jobs: check crontab -l
# - Shell scripts: *.sh files
# - Python scripts: *.py files
# - Configuration files: *.json, *.yaml files
```

## Detailed Removal Steps

### Step 1: Backup Data (Optional)
If you want to preserve trading data before removal:

```bash
# Backup the database
cp ig_markets_paper_trading/data/paper_trading.db ~/paper_trading_backup.db

# Backup logs
cp -r ig_markets_paper_trading/logs ~/paper_trading_logs_backup/

# Backup configuration
cp -r ig_markets_paper_trading/config ~/paper_trading_config_backup/
```

### Step 2: Stop Automated Execution
```bash
# Check for cron jobs
crontab -l | grep ig_markets_paper_trading

# Remove cron jobs
crontab -e
# Delete lines containing "ig_markets_paper_trading"

# Check for systemd services (if any)
systemctl --user list-units | grep paper_trading
```

### Step 3: Remove Integration Points

Check these common integration points:

1. **Main prediction scripts**: Look for imports or calls to paper trading modules
2. **Cron job files**: Remove any scheduled paper trading executions
3. **Shell scripts**: Remove any wrapper scripts that call the paper trader
4. **Configuration files**: Remove any external configs that reference the system

### Step 4: Verify Removal
```bash
# Ensure no processes are running
ps aux | grep paper_trader

# Ensure no cron jobs remain
crontab -l | grep ig_markets

# Check for any remaining files
find . -name "*ig_markets*" -o -name "*paper_trad*" 2>/dev/null
```

## File Inventory

The paper trading system consists of these components that will be removed:

```
ig_markets_paper_trading/
├── config/
│   ├── ig_markets_config.json
│   └── trading_parameters.json
├── src/
│   ├── position_manager.py
│   ├── ig_markets_client.py
│   └── paper_trader.py
├── scripts/
│   ├── run_paper_trader.py
│   ├── performance_report.py
│   ├── deploy.sh
│   └── setup_config.py
├── tests/
│   └── test_system.py
├── data/
│   └── paper_trading.db
├── logs/
│   └── *.log files
├── docs/
│   └── REMOVAL.md
├── README.md
├── QUICK_START.md
└── crontab_example.txt
```

## Dependencies

The paper trading system does not modify or install any system-wide dependencies. It only uses:
- Standard Python libraries
- `requests` (if already installed)
- `sqlite3` (built into Python)

No additional cleanup of dependencies is required.

## Reverting Integration Changes

If you made changes to existing files to integrate with the paper trading system:

### 1. Exit Strategy Integration
If you modified any exit strategy files, check for:
```python
# Look for these imports in your files
from ig_markets_paper_trading.src.paper_trader import PaperTrader

# Or calls like this
paper_trader.evaluate_exit_strategy(...)
```

### 2. Prediction Processing
Check prediction processing scripts for:
```python
# Integration calls
paper_trader.process_prediction(...)

# Database references
ig_markets_paper_trading/data/paper_trading.db
```

### 3. Configuration Files
Remove any references in configuration files:
```json
{
  "paper_trading": {
    "enabled": true,
    "config_path": "ig_markets_paper_trading/config/"
  }
}
```

## Verification Commands

Run these commands to verify complete removal:

```bash
# 1. No files remaining
ls -la | grep ig_markets

# 2. No processes running
ps aux | grep -i paper_trad

# 3. No cron jobs
crontab -l | grep -i ig_markets

# 4. No references in code (run from workspace root)
find . -name "*.py" -exec grep -l "ig_markets_paper_trading" {} \; 2>/dev/null

# 5. No database connections
lsof | grep paper_trading.db
```

## Clean Removal Confirmation

After removal, you should see:
- ✅ No `ig_markets_paper_trading/` directory
- ✅ No cron jobs mentioning paper trading
- ✅ No running paper trading processes
- ✅ No references in your existing code
- ✅ Original system unchanged and working

The removal is complete and your workspace is restored to its original state.

## Re-installation

If you need to reinstall later, the system is completely self-contained. Simply:
1. Recreate the system using the same setup process
2. Restore any backed-up data to the new installation
3. Reconfigure as needed

The system design ensures clean installation and removal without affecting your existing trading infrastructure.

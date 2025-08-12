# 🤖 Intelligent Data Quality Management System

## Overview
This system uses machine learning and statistical analysis to automatically detect, analyze, and fix data quality issues in your trading system.

## 🎯 **Key Features**

### 1. **Intelligent Detection**
- **Statistical Anomaly Detection**: Finds outliers, dummy data, impossible values
- **ML-Powered Pattern Recognition**: Learns normal data patterns and detects deviations
- **Real-time Market Validation**: Validates prices against actual market data
- **Prediction Bias Detection**: Identifies model bias and training issues

### 2. **Automated Fixes**
- **Smart Price Correction**: Fixes dummy/round number prices using Yahoo Finance
- **Missing Data Backfill**: Automatically fills missing exit prices
- **Return Recalculation**: Corrects calculation errors
- **Custom Fix Generation**: Creates custom scripts for complex issues

### 3. **Continuous Monitoring**
- **ML Models**: Trains on your data to learn normal patterns
- **Drift Detection**: Alerts when data distribution changes
- **Automated Reports**: Daily/weekly quality assessments
- **Executive Dashboards**: High-level status summaries

## 🚀 **Quick Start**

### Initial Setup
```bash
cd data_quality_system

# Set up automated monitoring
python3 data_quality_manager.py --setup

# Run first comprehensive analysis
python3 data_quality_manager.py --mode full
```

### Daily Usage
```bash
# Quick daily check
python3 data_quality_manager.py --mode standard

# Apply automatic fixes
python3 data_quality_manager.py --mode fix
```

## 📊 **Analysis Modes**

### **Standard Mode** (Recommended for daily use)
```bash
python3 data_quality_manager.py --mode standard
```
- Quick statistical analysis
- ML-powered anomaly detection
- Dry-run fix recommendations
- ~30 seconds execution time

### **Full Mode** (Recommended for weekly deep analysis)
```bash
python3 data_quality_manager.py --mode full
```
- Comprehensive analysis
- ML model retraining
- Advanced pattern detection
- ~2-3 minutes execution time

### **Fix Mode** (Apply automatic corrections)
```bash
python3 data_quality_manager.py --mode fix
```
- Runs analysis
- Applies safe automated fixes
- Generates fix reports
- Validates corrections

## 🔧 **Individual Tools**

### 1. Intelligent Data Quality Analyzer
```bash
cd core
python3 intelligent_analyzer.py
```
**What it detects:**
- Round number bias (dummy data like 100.0, 50.0)
- Price outliers using Isolation Forest
- Impossible returns (>1000% or <-100%)
- Missing data patterns
- Prediction bias in ML models

### 2. Smart Data Quality Fixer
```bash
cd core
# Dry run (safe)
python3 smart_fixer.py

# Apply fixes
python3 smart_fixer.py --live --force
```
**What it fixes:**
- Replaces dummy prices with real market data
- Backfills missing exit prices
- Recalculates incorrect returns
- Generates custom fix scripts

### 3. ML Data Quality Monitor
```bash
cd core
# Train new models
python3 ml_monitor.py --train

# Run monitoring
python3 ml_monitor.py --days 7
```
**What it monitors:**
- Price pattern anomalies
- Return distribution changes
- Confidence score patterns
- Statistical drift detection

## 📁 **Folder Structure**

```
data_quality_system/
├── core/                        # Core analysis engines
│   ├── intelligent_analyzer.py  # Statistical anomaly detection
│   ├── smart_fixer.py           # Automated fix system
│   └── ml_monitor.py            # ML-powered monitoring
├── automation/                  # Automated scripts
│   ├── daily_quality_monitor.sh # Daily monitoring
│   └── weekly_deep_analysis.sh  # Weekly deep analysis
├── docs/                        # Documentation
└── data_quality_manager.py      # Main orchestrator
```

## 📁 **Output Structure**

```
../data/
├── quality_reports/          # Comprehensive analysis reports
├── fix_reports/             # Applied fix summaries
├── ml_monitoring/           # ML monitoring results
├── quality_models/          # Trained ML models
└── ml_performance_history/  # Historical tracking (existing)
```

## 🔔 **Alert Levels**

### **Critical** 🚨
- Extreme returns (>1000%)
- Missing return calculations
- Systematic data corruption
- **Action**: Immediate investigation required

### **High** ⚠️
- Round number bias >10%
- Missing exit prices >5%
- Statistical drift >3σ
- **Action**: Review and consider fixes

### **Medium** 📊
- Price outliers detected
- Confidence score anomalies
- Minor prediction bias
- **Action**: Monitor and investigate if pattern continues

## 🎛️ **Automation Setup**

The system creates automated monitoring scripts:

### Daily Monitor
```bash
./automation/daily_quality_monitor.sh
```
- Runs standard analysis
- Checks for critical issues
- Saves results to reports

### Weekly Deep Analysis
```bash
./automation/weekly_deep_analysis.sh
```
- Full ML training and analysis
- Comprehensive pattern detection
- Model performance updates

## 💡 **Smart Recommendations**

The system provides intelligent recommendations:

1. **Data Source Issues**: "Review data collection - round numbers suggest dummy data"
2. **Model Bias**: "SELL bias detected - consider rebalancing training data"
3. **Missing Data**: "Backfill missing exit prices using market data"
4. **Calculation Errors**: "Return formulas appear incorrect - review logic"

## 🏥 **Health Scoring**

**Data Quality Score = 100 - (anomalies × 5) - (critical_issues × 15)**

- **90-100**: Excellent data quality
- **70-89**: Good with minor issues
- **50-69**: Fair, needs attention
- **<50**: Poor, immediate action required

## 📈 **Integration with Existing System**

This system works alongside your existing monitoring:
- Complements `evening_ml_check_with_history.py`
- Enhances `daily_ml_monitor.sh`
- Integrates with JSON performance tracking
- Provides additional validation layers

## 🔍 **Example Detection Scenarios**

### Scenario 1: Dummy Data Detection
```
🔍 Detected: 8 records with entry_price = 100.0
💡 Recommendation: Run price validation against Yahoo Finance
🔧 Auto-fix: python3 ../fix_entry_prices_with_yahoo.py
```

### Scenario 2: Missing Exit Prices
```
🔍 Detected: 25 records missing exit_price_1d
💡 Recommendation: Backfill using historical market data
🔧 Auto-fix: python3 ../fix_exit_prices_with_yahoo.py
```

### Scenario 3: Model Bias
```
🔍 Detected: SELL predictions only 3.2% win rate
💡 Recommendation: Investigate training data balance
🔧 Auto-fix: Retrain with balanced sampling
```

## 🎯 **Best Practices**

1. **Run daily standard checks** - catches issues early
2. **Weekly full analysis** - maintains ML model accuracy
3. **Review critical alerts immediately** - prevents data corruption
4. **Apply fixes during market close** - avoids trading disruption
5. **Validate fixes** - rerun analysis after applying corrections

## 🚀 **Advanced Usage**

### Custom Thresholds
Modify detection sensitivity in the scripts:
- Isolation Forest contamination (default: 0.1 = 10%)
- Statistical drift threshold (default: 2σ)
- Round number threshold (default: 10%)

### Integration with Alerts
Add email/Slack notifications:
```bash
# In daily_quality_monitor.sh
if [ critical_issues > 0 ]; then
    python3 send_alert.py "Critical data quality issues detected"
fi
```

### Remote Server Integration
```bash
# Copy system to remote server
scp -r data_quality_system/ root@170.64.199.151:/root/test/

# Run on remote server
ssh root@170.64.199.151 "cd /root/test/data_quality_system && python3 data_quality_manager.py --mode standard"
```

This system transforms your data quality from reactive (fixing after problems) to proactive (preventing problems through intelligent monitoring). 🎯

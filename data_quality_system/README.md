# 🤖 Data Quality Management System

An intelligent, ML-powered system for automated data quality monitoring, analysis, and fixing in trading systems.

## 🚀 Quick Start

```bash
cd data_quality_system

# Set up automated monitoring
python3 data_quality_manager.py --setup

# Run comprehensive analysis
python3 data_quality_manager.py --mode standard
```

## 📁 System Structure

```
data_quality_system/
├── 📁 core/                     # Core analysis engines
│   ├── intelligent_analyzer.py  # Statistical anomaly detection
│   ├── smart_fixer.py           # Automated fix system
│   └── ml_monitor.py            # ML-powered monitoring
├── 📁 automation/               # Automated scripts
│   ├── daily_quality_monitor.sh # Daily monitoring script
│   └── weekly_deep_analysis.sh  # Weekly deep analysis
├── 📁 docs/                     # Documentation
│   └── USER_GUIDE.md           # Comprehensive user guide
├── data_quality_manager.py      # Main orchestrator
└── README.md                   # This file
```

## 🎯 Main Features

### **Intelligent Detection**
- Statistical anomaly detection using Isolation Forest
- ML pattern recognition for data quality issues
- Real-time market data validation
- Model bias and overfitting detection

### **Automated Fixes**
- Smart price correction using Yahoo Finance
- Missing data backfill
- Return calculation fixes
- Custom script generation for complex issues

### **Continuous Monitoring**
- ML models that learn your data patterns
- Statistical drift detection
- Automated daily/weekly reports
- Executive summary dashboards

## 📊 Usage Examples

### Daily Monitoring
```bash
# Quick health check (30 seconds)
python3 data_quality_manager.py --mode standard

# Results example:
# 📊 EXECUTIVE SUMMARY
#    System Status: GOOD
#    Data Quality Score: 85.0/100
#    Critical Issues: 0
#    Total Anomalies: 3
```

### Weekly Deep Analysis
```bash
# Full analysis with ML training (2-3 minutes)
python3 data_quality_manager.py --mode full
```

### Apply Fixes
```bash
# Automatically fix detected issues
python3 data_quality_manager.py --mode fix
```

## 🔧 Individual Tools

Each core component can be run independently:

```bash
cd core

# Statistical analysis only
python3 intelligent_analyzer.py

# ML monitoring only
python3 ml_monitor.py --train

# Automated fixes only (dry run)
python3 smart_fixer.py
```

## 📈 Integration

This system integrates with your existing monitoring:
- Works alongside `evening_ml_check_with_history.py`
- Enhances `daily_ml_monitor.sh`
- Saves reports to `../data/quality_reports/`
- Compatible with JSON performance tracking

## ⚡ Automation

Set up automated monitoring:

```bash
# Daily monitoring (add to cron)
./automation/daily_quality_monitor.sh

# Weekly deep analysis (add to cron)
./automation/weekly_deep_analysis.sh
```

## 📋 What Gets Detected

### **Critical Issues** 🚨
- Extreme returns (>1000% or <-100%)
- Missing return calculations
- Systematic data corruption

### **High Priority** ⚠️
- Round number bias (dummy data)
- Missing exit prices >5%
- Statistical drift >3σ

### **Medium Priority** 📊
- Price outliers
- Confidence score anomalies
- Minor prediction bias

## 💡 Smart Recommendations

The system provides actionable intelligence:
- "Review data collection - round numbers suggest dummy data"
- "Model showing HOLD bias - consider rebalancing training data"
- "Backfill missing exit prices using market data"

## 🏥 Health Scoring

**Score = 100 - (anomalies × 5) - (critical_issues × 15)**
- **90-100**: Excellent
- **70-89**: Good
- **50-69**: Needs attention
- **<50**: Immediate action required

## 🔍 Example Output

```
🔍 Running Quick Data Quality Analysis...
📊 Loaded 193 outcome records

============================================================
 🤖 INTELLIGENT DATA QUALITY ANALYSIS COMPLETE
============================================================

📊 SUMMARY:
   Records Analyzed: 193
   Anomalies Found: 4
   Critical Issues: 0
   Quality Score: 80/100

💡 TOP RECOMMENDATIONS:
   1. Model showing HOLD bias - consider rebalancing training data
      Command: python3 ../enhanced_training_pipeline.py --rebalance
```

## 📖 Documentation

See `docs/USER_GUIDE.md` for comprehensive documentation including:
- Detailed feature explanations
- Advanced configuration options
- Integration examples
- Best practices
- Troubleshooting

## 🚀 Getting Started

1. **Install dependencies**: `pip install pandas numpy scikit-learn yfinance`
2. **Run initial analysis**: `python3 data_quality_manager.py --mode full`
3. **Set up automation**: `python3 data_quality_manager.py --setup`
4. **Review results**: Check `../data/quality_reports/` for detailed reports

This system transforms reactive data quality management into proactive, intelligent monitoring! 🎯

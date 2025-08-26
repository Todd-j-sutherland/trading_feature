# ASX Trading System - Quick Reference Card

**🚀 Daily Operations Cheat Sheet**

---

## 📱 Quick Status Check
```bash
ssh root@170.64.199.151
cd /root/test
echo "=== System Status ===" && date
sqlite3 data/trading_predictions.db "SELECT COUNT(*) as predictions_today FROM predictions WHERE DATE(prediction_timestamp) = DATE('now');"
tail -5 cron_prediction.log
```

## 🔍 Essential Commands

### Check Recent Predictions
```bash
sqlite3 data/trading_predictions.db "SELECT symbol, prediction_direction, confidence_score, prediction_timestamp FROM predictions ORDER BY prediction_timestamp DESC LIMIT 5;"
```

### View System Health
```bash
crontab -l | grep -v "^#"  # Active cron jobs
df -h /root/test          # Disk usage
uptime                    # System load
```

### Manual Prediction Generation
```bash
export PYTHONPATH=/root/test
/root/trading_venv/bin/python3 enhanced_efficient_system.py
```

### Check ML Training Status
```bash
tail -20 /root/test/logs/evening_ml_training.log
sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM enhanced_outcomes;"
```

### Emergency Restart
```bash
systemctl restart cron
killall python3  # If processes are stuck
```

---

## 📊 Performance Metrics

| Metric | Command | Target |
|--------|---------|--------|
| **Daily Predictions** | `sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM predictions WHERE DATE(prediction_timestamp) = DATE('now');"` | >12 |
| **System Accuracy** | `sqlite3 data/trading_predictions.db "SELECT AVG(CASE WHEN prediction_direction = actual_direction THEN 1.0 ELSE 0.0 END) FROM predictions p JOIN outcomes o ON p.prediction_id = o.prediction_id WHERE prediction_timestamp >= date('now', '-7 days');"` | >0.70 |
| **ML Training Data** | `sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM enhanced_outcomes;"` | >20 |

---

## 🚨 Emergency Procedures

### If No Predictions Today
1. Check cron: `systemctl status cron`
2. Test manual: `/root/trading_venv/bin/python3 enhanced_efficient_system.py`
3. Check logs: `tail -50 cron_prediction.log`

### If Evening Training Failed
1. Check log: `tail -50 /root/test/logs/evening_ml_training.log`
2. Test pipeline: `export PYTHONPATH=/root/test && /root/trading_venv/bin/python3 -c "from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline; p=EnhancedMLTrainingPipeline(); print('Training data:', p.has_sufficient_training_data())"`
3. Repopulate if needed: `/root/trading_venv/bin/python3 populate_enhanced_outcomes_fixed.py`

### Database Issues
1. Check integrity: `sqlite3 data/trading_predictions.db "PRAGMA integrity_check;"`
2. Backup: `cp data/trading_predictions.db data/backup_$(date +%Y%m%d).db`
3. Vacuum: `sqlite3 data/trading_predictions.db "VACUUM;"`

---

## 📅 Schedule Overview (UTC Times)

| Time | Task | Frequency |
|------|------|-----------|
| **00:00-06:00** | Market Predictions | Every 30 min |
| **08:00** | Evening ML Training | Daily |
| **Every Hour** | Outcome Evaluation | Hourly |

---

## 🎯 Success Indicators

✅ **All Good**: New predictions every 30 min during market hours  
✅ **All Good**: Evening training log shows "FULLY OPERATIONAL"  
✅ **All Good**: >70% accuracy on weekly performance  
✅ **All Good**: Disk usage <80%, system load <2.0  

⚠️ **Check Needed**: No predictions for >2 hours during market  
⚠️ **Check Needed**: Evening training errors for >2 days  
⚠️ **Check Needed**: Accuracy drops below 60%  

🚨 **Action Required**: System down, database corruption, critical errors  

---

**Contact**: Check main user guide for detailed troubleshooting  
**Version**: 5.0 - Post-Fix Implementation  
**Last Updated**: August 25, 2025

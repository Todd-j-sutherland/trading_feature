# TRADING SYSTEM TODO LIST
## High Priority Issues to Address

### 🔴 **CRITICAL ISSUES**

#### 1. **Local vs Remote Repository Sync**
- [ ] **Repository divergence detected** - Local on `final/working` branch, not `main`
- [ ] **Dashboard files missing on remote** - `comprehensive_table_dashboard.py` exists locally but not remotely
- [ ] Create strategy for syncing without losing current working system
- [ ] **Current branches:** Local has `final/working`, `main`, `emergency_backup_*` branches
- [ ] **Remote working system** is stable - backup before any merges
- [ ] Document which changes were reverted and why

#### 2. **Prediction Accuracy Issues**
- [ ] **Current accuracy: 23.3%** - Below optimal (target: 40-60%)
- [ ] **BUY predictions underperforming** (20.6% accuracy, -13.43% avg return)
- [ ] HOLD predictions performing better (33.3% accuracy) - investigate why
- [ ] Zero SELL predictions evaluated - need to analyze SELL logic
- [ ] Review ML model features and thresholds

### 🟡 **MAJOR FEATURES TO REVIVE**

#### 3. **Comprehensive Table Dashboard Revival**
- [ ] **`comprehensive_table_dashboard.py` exists locally** (978 lines) but missing on remote
- [ ] **Dependencies available on remote:** ✅ Streamlit, Plotly, Pandas installed
- [ ] Transfer dashboard file to remote server
- [ ] Test dashboard functionality with current data structure
- [ ] Update dashboard to work with new prediction schema
- [ ] **Missing performance_analytics_module** - needs to be created or dependency removed
- [ ] Integrate with current database structure (predictions, outcomes, enhanced_features tables)

#### 4. **ASX Market Aware Improvements**
- [ ] **ASX market awareness needs enhancement**
- [ ] Review current market hours logic (currently 00:00-05:30 UTC)
- [ ] Implement proper ASX trading calendar (holidays, half-days)
- [ ] Add market volatility awareness during different trading sessions
- [ ] Improve market context integration in predictions
- [ ] Add ASX sector-specific analysis

### 🟢 **SYSTEM IMPROVEMENTS**

#### 5. **Complexity Reversion Analysis**
- [ ] **Document work that was reverted due to complexity**
- [ ] Create list of features that were too complex and caused issues
- [ ] Identify simpler alternatives for complex features
- [ ] Plan phased approach for re-implementing beneficial features
- [ ] Establish complexity guidelines for future development

#### 6. **Data Quality & Evaluation System**
- [ ] **42 out of 75 predictions still need evaluation** (57.3% coverage)
- [ ] Improve real-time outcome evaluation
- [ ] Add automated accuracy monitoring and alerts
- [ ] Implement prediction quality scoring system
- [ ] Add confidence threshold adjustments based on performance

#### 7. **ML Model Optimization**
- [ ] Address sklearn version warnings (1.4.2 vs 1.7.1)
- [ ] Review feature engineering (currently 53 features)
- [ ] Optimize model training pipeline
- [ ] Add model versioning and rollback capability
- [ ] Implement A/B testing for model improvements

### 🔵 **INFRASTRUCTURE & MAINTENANCE**

#### 8. **Cron Job Management**
- [x] ✅ **Simple runner script created** (`run_trading_system.sh`) - Interactive menu
- [x] ✅ **Quick command script created** (`quick_trade.sh`) - Command line interface
  - Usage: `./quick_trade.sh predictions` or `./quick_trade.sh all`
- [ ] Test manual execution of all trading processes
- [ ] Add logging and monitoring for cron job failures
- [ ] Create backup/restore procedures for cron configurations
- [ ] Add health check automation

#### 9. **Database & Schema Management**
- [ ] Review database schema consistency across tables
- [ ] Optimize database performance for large datasets
- [ ] Add automated backup procedures
- [ ] Implement data retention policies
- [ ] Add database integrity checks

#### 10. **Frontend Integration**
- [ ] Check status of frontend development server
- [ ] Integrate dashboard with current backend data
- [ ] Test real-time data updates
- [ ] Add mobile-responsive design
- [ ] Implement user authentication if needed

---

## **IMMEDIATE NEXT STEPS** (This Week)

1. **✅ Test the new trading scripts:**
   - `./run_trading_system.sh` (interactive menu)
   - `./quick_trade.sh all` (run everything)
   - `./quick_trade.sh status` (check status)

2. **Transfer dashboard to remote:**
   ```bash
   scp dashboards/comprehensive_table_dashboard.py root@170.64.199.151:/root/test/
   ```

3. **Analyze repository differences** between `final/working` and `main` branches
4. **Create performance_analytics_module** or remove dependency from dashboard
5. **Document complexity reversions** - identify what was too complex and removed

## **SUCCESS METRICS**

- [ ] Prediction accuracy > 40%
- [ ] All predictions evaluated within 4 hours
- [ ] Dashboard fully functional and responsive
- [ ] Repository sync completed without system breakage
- [ ] ASX market awareness demonstrably improved

---

*Created: September 8, 2025*
*Status: Initial assessment after system restoration*

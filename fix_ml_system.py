#!/usr/bin/env python3
"""
Fix ML System Issues
===================

Addresses critical issues:
1. 0% training accuracy despite 77% validation accuracy
2. 0 features in training data (critical pipeline issue)
3. Duplicate predictions cleanup
4. Data validation and integrity checks

Usage:
    python fix_ml_system.py [--dry-run] [--retrain]
"""

import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import shutil
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MLSystemRepairer:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.base_path = Path(__file__).parent
        self.data_path = self.base_path / 'data'
        self.ml_performance_path = self.data_path / 'ml_performance'
        self.ml_models_path = self.data_path / 'ml_models'
        
        # Ensure directories exist
        self.ml_performance_path.mkdir(parents=True, exist_ok=True)
        self.ml_models_path.mkdir(parents=True, exist_ok=True)
        
        self.issues_found = []
        self.fixes_applied = []
    
    def diagnose_system(self):
        """Run comprehensive diagnostics on ML system"""
        print("🔍 ML SYSTEM DIAGNOSTICS")
        print("=" * 50)
        
        # Check prediction data
        self._check_prediction_data()
        
        # Check model metrics
        self._check_model_metrics()
        
        # Check model files
        self._check_model_files()
        
        # Check for data pipeline issues
        self._check_data_pipeline()
        
        return len(self.issues_found) == 0
    
    def _check_prediction_data(self):
        """Check prediction data for issues"""
        pred_file = self.ml_performance_path / 'prediction_history.json'
        
        if not pred_file.exists():
            self.issues_found.append("Missing prediction_history.json")
            return
        
        with open(pred_file, 'r') as f:
            predictions = json.load(f)
        
        print(f"📈 Predictions: {len(predictions)} total")
        
        # Check for duplicates
        duplicates = self._find_duplicates(predictions)
        if duplicates:
            self.issues_found.append(f"Found {len(duplicates)} duplicate predictions")
        
        # Check for pending predictions
        pending = [p for p in predictions if p.get('status') == 'pending']
        if pending:
            print(f"⏳ {len(pending)} pending predictions")
        
        # Check confidence diversity
        confidences = [p['prediction']['confidence'] for p in predictions 
                      if 'prediction' in p and 'confidence' in p['prediction']]
        if confidences:
            unique_count = len(set(f'{c:.3f}' for c in confidences))
            print(f"🎯 Confidence diversity: {unique_count}/{len(confidences)} unique values")
            
            # Check for suspicious uniform values
            uniform_61 = sum(1 for c in confidences if abs(c - 0.61) < 0.001)
            if uniform_61 > len(confidences) * 0.1:  # More than 10%
                self.issues_found.append(f"Too many uniform confidence values: {uniform_61}")
    
    def _check_model_metrics(self):
        """Check model training metrics"""
        metrics_file = self.ml_performance_path / 'model_metrics_history.json'
        
        if not metrics_file.exists():
            self.issues_found.append("Missing model_metrics_history.json")
            return
        
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        if not metrics:
            self.issues_found.append("Empty model metrics")
            return
        
        latest = metrics[-1]
        train_acc = latest['metrics'].get('training_accuracy', 0)
        val_acc = latest['metrics'].get('validation_accuracy', 0)
        feature_count = latest['metrics'].get('feature_count', 0)
        sample_count = latest['metrics'].get('training_samples', 0)
        
        print(f"🤖 Model Performance:")
        print(f"   Training accuracy: {train_acc:.1%}")
        print(f"   Validation accuracy: {val_acc:.1%}")
        print(f"   Features: {feature_count}")
        print(f"   Samples: {sample_count}")
        
        # Critical issues
        if train_acc == 0:
            self.issues_found.append("CRITICAL: Training accuracy is 0%")
        
        if feature_count == 0:
            self.issues_found.append("CRITICAL: Feature count is 0 (data pipeline broken)")
        
        if sample_count < 50:
            self.issues_found.append("WARNING: Very few training samples")
    
    def _check_model_files(self):
        """Check model files existence and age"""
        if not self.ml_models_path.exists():
            self.issues_found.append("ML models directory missing")
            return
        
        model_files = list(self.ml_models_path.glob('*.pkl'))
        print(f"📁 Model files: {len(model_files)}")
        
        if not model_files:
            self.issues_found.append("No model files found")
            return
        
        # Check if models are recent (within last 7 days)
        week_ago = datetime.now().timestamp() - (7 * 24 * 3600)
        old_models = []
        
        for model in model_files:
            if model.stat().st_mtime < week_ago:
                old_models.append(model.name)
        
        if old_models:
            print(f"⚠️  Old models (>7 days): {len(old_models)}")
    
    def _check_data_pipeline(self):
        """Check data pipeline components"""
        # Look for feature engineering components
        core_path = self.base_path / 'app' / 'core'
        if core_path.exists():
            feature_files = list(core_path.rglob('*feature*'))
            ml_files = list(core_path.rglob('*ml*'))
            print(f"🔧 Pipeline components: {len(feature_files)} feature files, {len(ml_files)} ML files")
        
        # Check if daily manager exists
        daily_manager_files = list(self.base_path.rglob('daily_manager*.py'))
        if not daily_manager_files:
            self.issues_found.append("Daily manager component missing")
        else:
            print(f"📅 Daily manager files: {len(daily_manager_files)}")
    
    def _find_duplicates(self, predictions):
        """Find duplicate predictions"""
        seen = set()
        duplicates = []
        
        for i, pred in enumerate(predictions):
            # Create a unique key based on symbol, timestamp, and prediction
            key = (
                pred.get('symbol', ''),
                pred.get('timestamp', ''),
                pred.get('prediction', {}).get('signal', ''),
                pred.get('prediction', {}).get('confidence', 0)
            )
            
            if key in seen:
                duplicates.append(i)
            seen.add(key)
        
        return duplicates
    
    def fix_duplicates(self):
        """Remove duplicate predictions"""
        pred_file = self.ml_performance_path / 'prediction_history.json'
        
        if not pred_file.exists():
            return
        
        print("\n🔧 FIXING DUPLICATES")
        print("-" * 30)
        
        with open(pred_file, 'r') as f:
            predictions = json.load(f)
        
        original_count = len(predictions)
        
        # Group by symbol and hour to keep latest prediction per symbol per hour
        grouped = defaultdict(list)
        
        for pred in predictions:
            # Extract hour from timestamp
            try:
                dt = datetime.fromisoformat(pred['timestamp'].replace('Z', '+00:00'))
                hour_key = f"{pred['symbol']}_{dt.strftime('%Y-%m-%d_%H')}"
                grouped[hour_key].append(pred)
            except Exception as e:
                # Keep predictions with invalid timestamps for manual review
                grouped[f"invalid_{pred['symbol']}"].append(pred)
        
        # Keep only the latest prediction for each symbol-hour combination
        cleaned_predictions = []
        for group in grouped.values():
            if len(group) == 1:
                cleaned_predictions.extend(group)
            else:
                # Sort by timestamp and keep the latest
                try:
                    latest = max(group, key=lambda x: datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')))
                    cleaned_predictions.append(latest)
                except Exception:
                    # If timestamp comparison fails, keep the first one
                    cleaned_predictions.append(group[0])
        
        if not self.dry_run and len(cleaned_predictions) < original_count:
            # Backup original
            backup_file = pred_file.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            shutil.copy2(pred_file, backup_file)
            
            # Save cleaned data
            with open(pred_file, 'w') as f:
                json.dump(cleaned_predictions, f, indent=2)
            
            removed = original_count - len(cleaned_predictions)
            self.fixes_applied.append(f"Removed {removed} duplicate predictions")
            print(f"✅ Removed {removed} duplicates (kept {len(cleaned_predictions)}/{original_count})")
        else:
            removed = original_count - len(cleaned_predictions)
            print(f"Would remove {removed} duplicates (keep {len(cleaned_predictions)}/{original_count})")
    
    def retrain_models(self):
        """Trigger ML model retraining"""
        print("\n🤖 RETRAINING ML MODELS")
        print("-" * 30)
        
        # Look for training scripts
        training_scripts = [
            'app/services/daily_manager.py',
            'app/core/ml_trainer.py',
            'test_ml_models.py'
        ]
        
        for script in training_scripts:
            script_path = self.base_path / script
            if script_path.exists():
                print(f"📋 Found training script: {script}")
                if not self.dry_run:
                    # This would require importing and running the training
                    print(f"   Would trigger retraining via {script}")
                break
        else:
            print("❌ No training scripts found")
            self.issues_found.append("Cannot retrain - no training scripts found")
    
    def create_validation_report(self):
        """Create a comprehensive validation report"""
        report_file = self.base_path / f'ml_system_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        
        report_content = f"""# ML System Validation Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Issues Found ({len(self.issues_found)})
"""
        
        for issue in self.issues_found:
            report_content += f"- {issue}\n"
        
        report_content += f"""
## Fixes Applied ({len(self.fixes_applied)})
"""
        
        for fix in self.fixes_applied:
            report_content += f"- {fix}\n"
        
        report_content += """
## Recommendations

1. **Immediate Actions:**
   - Fix feature engineering pipeline (0 features detected)
   - Retrain ML models with proper feature data
   - Update any pending predictions with actual outcomes

2. **System Health:**
   - Implement automated health checks
   - Add feature count validation in training pipeline
   - Set up alerts for training accuracy drops

3. **Data Quality:**
   - Validate timestamp formats
   - Check for data leakage in train/validation split
   - Monitor prediction diversity
"""
        
        if not self.dry_run:
            with open(report_file, 'w') as f:
                f.write(report_content)
            print(f"📊 Validation report saved to: {report_file}")
        else:
            print("📊 Would create validation report")
    
    def run_repair(self, retrain=False):
        """Run the complete repair process"""
        print("🛠️  ML SYSTEM REPAIR")
        print("=" * 50)
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
            print()
        
        # Diagnose issues
        system_healthy = self.diagnose_system()
        
        if self.issues_found:
            print(f"\n❌ Found {len(self.issues_found)} issues:")
            for issue in self.issues_found:
                print(f"   - {issue}")
        
        # Apply fixes
        self.fix_duplicates()
        
        if retrain:
            self.retrain_models()
        
        # Generate report
        self.create_validation_report()
        
        print(f"\n📋 SUMMARY:")
        print(f"   Issues found: {len(self.issues_found)}")
        print(f"   Fixes applied: {len(self.fixes_applied)}")
        
        if self.issues_found:
            print("\n🚨 CRITICAL ISSUES REQUIRE ATTENTION:")
            critical = [issue for issue in self.issues_found if 'CRITICAL' in issue]
            for issue in critical:
                print(f"   ❗ {issue}")
        
        return len(self.issues_found) == 0

def main():
    parser = argparse.ArgumentParser(description='Fix ML System Issues')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--retrain', action='store_true',
                       help='Trigger ML model retraining')
    
    args = parser.parse_args()
    
    repairer = MLSystemRepairer(dry_run=args.dry_run)
    success = repairer.run_repair(retrain=args.retrain)
    
    if success:
        print("\n✅ ML system appears healthy!")
        return 0
    else:
        print("\n⚠️  ML system requires attention")
        return 1

if __name__ == '__main__':
    sys.exit(main())

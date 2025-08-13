#!/usr/bin/env python3
"""
Migration Script: Old System → New Prediction Pipeline
Safely transitions from retrospective labeling to true predictions
"""

import os
import sqlite3
import pandas as pd
import shutil
from datetime import datetime
import logging

class SystemMigration:
    """Handles migration from old retrospective system to new prediction system"""
    
    def __init__(self, old_db="data/trading_unified.db", backup_dir="data/migration_backup"):
        self.old_db = old_db
        self.backup_dir = backup_dir
        self.logger = logging.getLogger(__name__)
        
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self) -> bool:
        """Create complete backup of current system"""
        
        print("💾 Creating backup of current system...")
        
        try:
            # Backup database
            if os.path.exists(self.old_db):
                backup_db = os.path.join(self.backup_dir, f"trading_unified_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
                shutil.copy2(self.old_db, backup_db)
                print(f"✅ Database backed up to: {backup_db}")
            
            # Backup any model files
            model_dirs = ["models/", "data/ml_models/"]
            for model_dir in model_dirs:
                if os.path.exists(model_dir):
                    backup_model_dir = os.path.join(self.backup_dir, f"models_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    shutil.copytree(model_dir, backup_model_dir, dirs_exist_ok=True)
                    print(f"✅ Models backed up to: {backup_model_dir}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False
    
    def analyze_current_system(self) -> dict:
        """Analyze the current system to understand migration scope"""
        
        print("🔍 Analyzing current system...")
        
        if not os.path.exists(self.old_db):
            print("❌ No existing database found")
            return {}
        
        conn = sqlite3.connect(self.old_db)
        
        analysis = {}
        
        # Check tables
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
        analysis['tables'] = tables['name'].tolist()
        
        # Check data volume
        if 'enhanced_outcomes' in analysis['tables']:
            outcomes = pd.read_sql_query("SELECT COUNT(*) as count FROM enhanced_outcomes", conn)
            analysis['total_outcomes'] = outcomes['count'].iloc[0]
            
            # Check action distribution
            actions = pd.read_sql_query("SELECT optimal_action, COUNT(*) as count FROM enhanced_outcomes GROUP BY optimal_action", conn)
            analysis['action_distribution'] = dict(zip(actions['optimal_action'], actions['count']))
            
            # Check date range
            dates = pd.read_sql_query("SELECT MIN(prediction_timestamp) as min_date, MAX(prediction_timestamp) as max_date FROM enhanced_outcomes", conn)
            analysis['date_range'] = {
                'start': dates['min_date'].iloc[0],
                'end': dates['max_date'].iloc[0]
            }
        
        # Check features
        if 'enhanced_features' in analysis['tables']:
            features = pd.read_sql_query("SELECT COUNT(*) as count FROM enhanced_features", conn)
            analysis['total_features'] = features['count'].iloc[0]
        
        conn.close()
        
        # Display analysis
        print("\n📊 Current System Analysis:")
        print(f"   Tables: {len(analysis.get('tables', []))}")
        print(f"   Total Outcomes: {analysis.get('total_outcomes', 0)}")
        print(f"   Date Range: {analysis.get('date_range', {}).get('start', 'N/A')} to {analysis.get('date_range', {}).get('end', 'N/A')}")
        
        if 'action_distribution' in analysis:
            print("   Action Distribution:")
            for action, count in analysis['action_distribution'].items():
                print(f"     {action}: {count}")
        
        return analysis
    
    def validate_migration_readiness(self) -> bool:
        """Check if system is ready for migration"""
        
        print("✅ Validating migration readiness...")
        
        issues = []
        
        # Check database exists
        if not os.path.exists(self.old_db):
            issues.append("No existing database found")
        
        # Check required tables
        if os.path.exists(self.old_db):
            conn = sqlite3.connect(self.old_db)
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
            table_names = tables['name'].tolist()
            
            required_tables = ['enhanced_features', 'enhanced_outcomes']
            for table in required_tables:
                if table not in table_names:
                    issues.append(f"Missing required table: {table}")
            
            # Check data volume
            if 'enhanced_outcomes' in table_names:
                count = pd.read_sql_query("SELECT COUNT(*) as count FROM enhanced_outcomes", conn)
                if count['count'].iloc[0] < 10:
                    issues.append("Insufficient historical data for training")
            
            conn.close()
        
        # Check dependencies
        try:
            import sklearn
            import yfinance
        except ImportError as e:
            issues.append(f"Missing required package: {e}")
        
        if issues:
            print("❌ Migration issues found:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        else:
            print("✅ System ready for migration")
            return True
    
    def perform_migration(self) -> bool:
        """Perform the actual migration"""
        
        print("\n🚀 Starting System Migration...")
        print("="*50)
        
        # Step 1: Create backup
        if not self.create_backup():
            print("❌ Migration aborted - backup failed")
            return False
        
        # Step 2: Validate readiness
        if not self.validate_migration_readiness():
            print("❌ Migration aborted - system not ready")
            return False
        
        # Step 3: Initialize new system components
        try:
            from true_prediction_engine import TruePredictionEngine, OutcomeEvaluator
            from model_trainer import ModelTrainer
            
            print("📦 Initializing new system components...")
            
            # Initialize prediction engine (creates new database)
            predictor = TruePredictionEngine()
            print("✅ Prediction engine initialized")
            
            # Initialize evaluator
            evaluator = OutcomeEvaluator()
            print("✅ Outcome evaluator initialized")
            
            # Initialize trainer
            trainer = ModelTrainer()
            print("✅ Model trainer initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize components: {e}")
            return False
        
        # Step 4: Convert historical data
        print("\n🔄 Converting historical data...")
        if not trainer.convert_historical_data():
            print("❌ Historical data conversion failed")
            return False
        
        # Step 5: Train initial models
        print("\n🎯 Training initial models...")
        results = trainer.train_models()
        
        if not results:
            print("❌ Model training failed")
            return False
        
        print("✅ Initial models trained successfully")
        
        # Step 6: Create migration report
        self._create_migration_report(results)
        
        print("\n🎉 Migration completed successfully!")
        print("\n📋 Next Steps:")
        print("   1. Test the new prediction engine")
        print("   2. Start making real predictions")
        print("   3. Monitor prediction accuracy")
        print("   4. Gradually phase out old system")
        
        return True
    
    def _create_migration_report(self, training_results: dict):
        """Create migration completion report"""
        
        report_file = os.path.join(self.backup_dir, f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        with open(report_file, 'w') as f:
            f.write("TRADING SYSTEM MIGRATION REPORT\n")
            f.write("="*40 + "\n\n")
            f.write(f"Migration Date: {datetime.now()}\n")
            f.write(f"Old Database: {self.old_db}\n")
            f.write(f"Backup Location: {self.backup_dir}\n\n")
            
            f.write("MIGRATION STEPS COMPLETED:\n")
            f.write("✅ System backup created\n")
            f.write("✅ Migration readiness validated\n")
            f.write("✅ New components initialized\n")
            f.write("✅ Historical data converted\n")
            f.write("✅ Initial models trained\n\n")
            
            f.write("TRAINING RESULTS:\n")
            for key, value in training_results.items():
                f.write(f"   {key}: {value}\n")
            
            f.write("\nCRITICAL CHANGES:\n")
            f.write("• Predictions are now made in real-time\n")
            f.write("• No more retrospective labeling\n")
            f.write("• Separate prediction and outcome storage\n")
            f.write("• Proper temporal validation\n")
            f.write("• Model performance is now meaningful\n\n")
            
            f.write("POST-MIGRATION TASKS:\n")
            f.write("1. Test new prediction engine\n")
            f.write("2. Monitor prediction accuracy\n")
            f.write("3. Retrain models as more data accumulates\n")
            f.write("4. Implement automated evaluation pipeline\n")
        
        print(f"📄 Migration report saved: {report_file}")

def main():
    """Run the migration process"""
    
    logging.basicConfig(level=logging.INFO)
    
    migrator = SystemMigration()
    
    print("🔄 TRADING SYSTEM MIGRATION TOOL")
    print("="*40)
    
    # Analyze current system
    analysis = migrator.analyze_current_system()
    
    if analysis:
        # Ask for confirmation
        print("\n⚠️  This migration will:")
        print("   • Create backups of current system")
        print("   • Initialize new prediction architecture")  
        print("   • Convert historical data for training")
        print("   • Train new prediction models")
        print("   • Preserve all existing data")
        
        confirm = input("\nProceed with migration? (yes/no): ").lower().strip()
        
        if confirm in ['yes', 'y']:
            success = migrator.perform_migration()
            
            if success:
                print("\n🎉 Migration completed successfully!")
                print("Your trading system now uses true forward-looking predictions!")
            else:
                print("\n❌ Migration failed. Check logs and backups.")
        else:
            print("Migration cancelled.")
    else:
        print("No existing system found to migrate.")

if __name__ == "__main__":
    main()

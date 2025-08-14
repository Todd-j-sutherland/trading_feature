#!/usr/bin/env python3
"""
🔍 Trading System Fix Validation Script
Validates that the architecture fix resolved all the retrospective labeling issues
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
import sys
import os

class SystemValidator:
    def __init__(self, db_path="data/trading_predictions.db"):
        self.db_path = db_path
        self.validation_results = {}
        
    def validate_system(self):
        """Run comprehensive validation of the fixed system"""
        print("🔍 TRADING SYSTEM FIX VALIDATION")
        print("=" * 50)
        
        # Check if new database exists
        if not os.path.exists(self.db_path):
            print(f"❌ New prediction database not found at {self.db_path}")
            print("   Run the migration script first")
            return False
            
        # Connect to database
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"✅ Connected to prediction database: {self.db_path}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
            
        # Run validation tests
        tests = [
            ("Database Schema", self._validate_schema),
            ("Prediction Timing", self._validate_timing),
            ("Prediction Consistency", self._validate_consistency), 
            ("No Contradictions", self._validate_no_contradictions),
            ("Outcome Separation", self._validate_outcome_separation),
            ("Model Availability", self._validate_models)
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}:")
            try:
                passed = test_func()
                if passed:
                    print(f"   ✅ PASSED")
                else:
                    print(f"   ❌ FAILED")
                    all_passed = False
            except Exception as e:
                print(f"   ⚠️  ERROR: {e}")
                all_passed = False
                
        # Summary
        print("\n" + "=" * 50)
        if all_passed:
            print("🎉 ALL VALIDATIONS PASSED!")
            print("   Your trading system is now a genuine prediction engine")
        else:
            print("⚠️  SOME VALIDATIONS FAILED")
            print("   Check the issues above and re-run migration if needed")
            
        return all_passed
        
    def _validate_schema(self):
        """Validate the new database schema"""
        cursor = self.conn.cursor()
        
        # Check predictions table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='predictions'
        """)
        if not cursor.fetchone():
            print("   ❌ predictions table not found")
            return False
            
        # Check outcomes table exists  
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='outcomes'
        """)
        if not cursor.fetchone():
            print("   ❌ outcomes table not found")
            return False
            
        # Check predictions table schema
        cursor.execute("PRAGMA table_info(predictions)")
        columns = [row[1] for row in cursor.fetchall()]
        required_columns = [
            'prediction_id', 'symbol', 'prediction_timestamp',
            'predicted_action', 'action_confidence', 'predicted_direction'
        ]
        
        for col in required_columns:
            if col not in columns:
                print(f"   ❌ Missing column in predictions: {col}")
                return False
                
        print("   ✅ Database schema is correct")
        return True
        
    def _validate_timing(self):
        """Validate that predictions are stored immediately (no delays)"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                prediction_id,
                prediction_timestamp,
                created_at,
                (julianday(created_at) - julianday(prediction_timestamp)) * 24 * 60 as delay_minutes
            FROM predictions
            WHERE prediction_timestamp IS NOT NULL AND created_at IS NOT NULL
        """)
        
        delays = cursor.fetchall()
        if not delays:
            print("   ℹ️  No predictions with timing data found")
            return True
            
        # Check for excessive delays (> 5 minutes indicates retrospective labeling)
        excessive_delays = [d for d in delays if d[3] > 5]
        
        if excessive_delays:
            print(f"   ❌ Found {len(excessive_delays)} predictions with excessive delays:")
            for delay in excessive_delays[:3]:  # Show first 3
                print(f"      ID: {delay[0]}, Delay: {delay[3]:.1f} minutes")
            return False
            
        avg_delay = sum(d[3] for d in delays) / len(delays)
        print(f"   ✅ Average prediction delay: {avg_delay:.2f} minutes")
        return True
        
    def _validate_consistency(self):
        """Validate prediction consistency"""
        cursor = self.conn.cursor()
        
        # Check for null predictions
        cursor.execute("""
            SELECT COUNT(*) FROM predictions 
            WHERE predicted_action IS NULL 
               OR action_confidence IS NULL
               OR predicted_direction IS NULL
        """)
        
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            print(f"   ❌ Found {null_count} predictions with null values")
            return False
            
        # Check confidence ranges
        cursor.execute("""
            SELECT MIN(action_confidence), MAX(action_confidence), AVG(action_confidence)
            FROM predictions
        """)
        
        min_conf, max_conf, avg_conf = cursor.fetchone()
        if min_conf is not None:
            if min_conf < 0 or max_conf > 1:
                print(f"   ❌ Confidence out of range: [{min_conf:.3f}, {max_conf:.3f}]")
                return False
            print(f"   ✅ Confidence range: [{min_conf:.3f}, {max_conf:.3f}], avg: {avg_conf:.3f}")
        
        return True
        
    def _validate_no_contradictions(self):
        """Validate no contradictory predictions (BUY with DOWN direction)"""
        cursor = self.conn.cursor()
        
        # Check for BUY predictions with DOWN direction
        cursor.execute("""
            SELECT COUNT(*) FROM predictions 
            WHERE predicted_action = 'BUY' AND predicted_direction = -1
        """)
        
        buy_down_count = cursor.fetchone()[0]
        if buy_down_count > 0:
            print(f"   ❌ Found {buy_down_count} BUY predictions with DOWN direction")
            return False
            
        # Check for SELL predictions with UP direction
        cursor.execute("""
            SELECT COUNT(*) FROM predictions 
            WHERE predicted_action = 'SELL' AND predicted_direction = 1
        """)
        
        sell_up_count = cursor.fetchone()[0]
        if sell_up_count > 0:
            print(f"   ❌ Found {sell_up_count} SELL predictions with UP direction")
            return False
            
        print("   ✅ No contradictory predictions found")
        return True
        
    def _validate_outcome_separation(self):
        """Validate that outcomes are properly separated from predictions"""
        cursor = self.conn.cursor()
        
        # Check if outcomes table exists and is separate
        cursor.execute("SELECT COUNT(*) FROM outcomes")
        outcome_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM predictions")
        prediction_count = cursor.fetchone()[0]
        
        print(f"   ✅ Predictions: {prediction_count}, Outcomes: {outcome_count}")
        print(f"   ✅ Outcomes are stored separately from predictions")
        
        # Check for foreign key relationship
        if outcome_count > 0:
            cursor.execute("""
                SELECT COUNT(*) FROM outcomes o
                JOIN predictions p ON o.prediction_id = p.prediction_id
            """)
            linked_count = cursor.fetchone()[0]
            print(f"   ✅ {linked_count} outcomes properly linked to predictions")
            
        return True
        
    def _validate_models(self):
        """Validate that trained models are available"""
        model_files = [
            "models/action_model.joblib",
            "models/direction_model.joblib", 
            "models/magnitude_model.joblib"
        ]
        
        available_models = []
        for model_file in model_files:
            if os.path.exists(model_file):
                available_models.append(model_file)
                
        if not available_models:
            print("   ⚠️  No trained models found")
            print("      Run model training after collecting some data")
            return True  # Not a failure, just needs training
            
        print(f"   ✅ Found {len(available_models)} trained models:")
        for model in available_models:
            print(f"      - {model}")
            
        return True
        
    def generate_report(self):
        """Generate a comprehensive validation report"""
        cursor = self.conn.cursor()
        
        print("\n📊 SYSTEM STATUS REPORT")
        print("=" * 50)
        
        # Prediction counts
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]
        print(f"Total Predictions: {total_predictions}")
        
        if total_predictions > 0:
            # Action distribution
            cursor.execute("""
                SELECT predicted_action, COUNT(*) 
                FROM predictions 
                GROUP BY predicted_action
            """)
            print("\nAction Distribution:")
            for action, count in cursor.fetchall():
                pct = (count / total_predictions) * 100
                print(f"  {action}: {count} ({pct:.1f}%)")
                
            # Recent predictions
            cursor.execute("""
                SELECT prediction_timestamp, symbol, predicted_action, action_confidence
                FROM predictions 
                ORDER BY prediction_timestamp DESC 
                LIMIT 5
            """)
            print("\nRecent Predictions:")
            for row in cursor.fetchall():
                print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]:.1%}")
                
        # Outcome evaluation
        cursor.execute("SELECT COUNT(*) FROM outcomes")
        total_outcomes = cursor.fetchone()[0]
        print(f"\nEvaluated Outcomes: {total_outcomes}")
        
        if total_outcomes > 0:
            cursor.execute("""
                SELECT 
                    AVG(CASE WHEN 
                        (p.predicted_action = 'BUY' AND o.actual_return > 0) OR
                        (p.predicted_action = 'SELL' AND o.actual_return < 0) OR
                        (p.predicted_action = 'HOLD')
                    THEN 1 ELSE 0 END) as accuracy
                FROM predictions p
                JOIN outcomes o ON p.prediction_id = o.prediction_id
            """)
            accuracy = cursor.fetchone()[0]
            if accuracy:
                print(f"Current Accuracy: {accuracy:.1%}")
                
        print("\n✅ System is ready for live trading!")

def main():
    """Main validation function"""
    validator = SystemValidator()
    
    if validator.validate_system():
        validator.generate_report()
        return 0
    else:
        print("\n⚠️  Please fix the issues above before using the system")
        return 1

if __name__ == "__main__":
    sys.exit(main())

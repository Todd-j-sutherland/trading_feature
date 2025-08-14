#!/usr/bin/env python3
"""
Morning Routine Data Integrity Checker

Ensures the morning routine operates with proper temporal constraints and data integrity.
This should be run BEFORE your morning analysis to validate data quality.
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class MorningRoutineValidator:
    """Validates data integrity before running morning analysis"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = Path(db_path)
        
    def validate_temporal_integrity(self) -> Dict:
        """Check for any temporal inconsistencies that would cause data leakage"""
        
        validation_result = {
            'is_safe': True,
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check 1: No future features being used for current predictions
                current_time = datetime.now()
                cutoff_time = current_time + timedelta(minutes=30)  # Allow 30min tolerance
                
                cursor.execute("""
                    SELECT COUNT(*) FROM enhanced_features
                    WHERE timestamp > ?
                """, (cutoff_time.isoformat(),))
                
                future_features = cursor.fetchone()[0]
                if future_features > 0:
                    validation_result['is_safe'] = False
                    validation_result['issues'].append(f"Found {future_features} features with future timestamps")
                
                # Check 2: Feature-prediction timestamp alignment
                cursor.execute("""
                    SELECT 
                        p.symbol,
                        p.prediction_timestamp,
                        ef.timestamp as feature_time,
                        (julianday(ef.timestamp) - julianday(p.prediction_timestamp)) * 24 as hours_diff
                    FROM predictions p
                    JOIN enhanced_features ef ON p.symbol = ef.symbol
                    WHERE DATE(p.prediction_timestamp) = DATE('now')
                    AND (julianday(ef.timestamp) - julianday(p.prediction_timestamp)) * 24 > 1
                """)
                
                misaligned_pairs = cursor.fetchall()
                if misaligned_pairs:
                    validation_result['is_safe'] = False
                    for symbol, pred_time, feat_time, hours_diff in misaligned_pairs:
                        validation_result['issues'].append(
                            f"Data leakage: {symbol} prediction at {pred_time} uses features from {feat_time} (+{hours_diff:.1f}h)"
                        )
                
                # Check 3: Morning routine data availability
                cursor.execute("""
                    SELECT symbol, MAX(timestamp) as latest_feature
                    FROM enhanced_features
                    WHERE symbol IN ('ANZ.AX', 'CBA.AX', 'WBC.AX', 'NAB.AX')
                    GROUP BY symbol
                """)
                
                feature_availability = cursor.fetchall()
                current_date = current_time.date()
                
                for symbol, latest_feature in feature_availability:
                    if latest_feature:
                        latest_dt = datetime.fromisoformat(latest_feature)
                        if latest_dt.date() < current_date:
                            validation_result['warnings'].append(
                                f"Stale features for {symbol}: latest from {latest_dt.date()}"
                            )
                
                # Check 4: Technical indicator sanity
                cursor.execute("""
                    SELECT symbol, rsi, macd_line, current_price, bollinger_upper, bollinger_lower
                    FROM enhanced_features
                    WHERE timestamp = (SELECT MAX(timestamp) FROM enhanced_features)
                """)
                
                technical_data = cursor.fetchall()
                for symbol, rsi, macd, price, bb_upper, bb_lower in technical_data:
                    if rsi and (rsi < 0 or rsi > 100):
                        validation_result['warnings'].append(f"Invalid RSI for {symbol}: {rsi}")
                    
                    if macd and abs(macd) > 10:
                        validation_result['warnings'].append(f"Extreme MACD for {symbol}: {macd}")
                    
                    if bb_upper and bb_lower and price:
                        if price > bb_upper * 1.2 or price < bb_lower * 0.8:
                            validation_result['warnings'].append(f"Price outside reasonable Bollinger range for {symbol}")
                
        except Exception as e:
            validation_result['is_safe'] = False
            validation_result['issues'].append(f"Validation error: {e}")
        
        # Generate recommendations
        if not validation_result['is_safe']:
            validation_result['recommendations'].extend([
                "🚨 DO NOT run morning analysis until issues are resolved",
                "🔧 Run timestamp_synchronization_fixer.py to fix data leakage",
                "⏰ Ensure features are generated before predictions",
                "🛡️ Implement temporal validation in your morning routine"
            ])
        elif validation_result['warnings']:
            validation_result['recommendations'].extend([
                "⚠️ Review warnings before proceeding",
                "📊 Validate technical indicator calculations",
                "🔄 Consider refreshing stale data"
            ])
        else:
            validation_result['recommendations'].append("✅ Safe to proceed with morning analysis")
        
        return validation_result
    
    def get_safe_data_for_morning_analysis(self) -> Dict:
        """Get temporally safe data for morning analysis"""
        
        safe_data = {
            'predictions': [],
            'features': [],
            'latest_safe_timestamp': None
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get latest safe timestamp (not from future)
                current_time = datetime.now()
                safe_cutoff = current_time - timedelta(minutes=5)  # 5min safety buffer
                
                # Get safe predictions (not using future data)
                cursor.execute("""
                    SELECT DISTINCT p.*
                    FROM predictions p
                    WHERE p.prediction_timestamp <= ?
                    AND NOT EXISTS (
                        SELECT 1 FROM enhanced_features ef
                        WHERE ef.symbol = p.symbol
                        AND ef.timestamp > p.prediction_timestamp
                        AND ef.timestamp > ?
                    )
                    ORDER BY p.prediction_timestamp DESC
                    LIMIT 10
                """, (safe_cutoff.isoformat(), safe_cutoff.isoformat()))
                
                safe_data['predictions'] = [
                    dict(zip([col[0] for col in cursor.description], row))
                    for row in cursor.fetchall()
                ]
                
                # Get safe features (not from future)
                cursor.execute("""
                    SELECT *
                    FROM enhanced_features
                    WHERE timestamp <= ?
                    ORDER BY timestamp DESC
                    LIMIT 20
                """, (safe_cutoff.isoformat(),))
                
                safe_data['features'] = [
                    dict(zip([col[0] for col in cursor.description], row))
                    for row in cursor.fetchall()
                ]
                
                safe_data['latest_safe_timestamp'] = safe_cutoff.isoformat()
                
        except Exception as e:
            safe_data['error'] = str(e)
        
        return safe_data
    
    def run_morning_validation(self) -> bool:
        """Run complete morning routine validation - returns True if safe to proceed"""
        
        print("🌅 MORNING ROUTINE DATA INTEGRITY VALIDATOR")
        print("=" * 55)
        
        # 1. Validate temporal integrity
        print("\n🔍 VALIDATING TEMPORAL INTEGRITY...")
        validation_result = self.validate_temporal_integrity()
        
        if validation_result['is_safe']:
            print("✅ Temporal integrity PASSED")
        else:
            print("🚨 Temporal integrity FAILED")
            print("\n❌ CRITICAL ISSUES:")
            for issue in validation_result['issues']:
                print(f"  • {issue}")
        
        # 2. Show warnings if any
        if validation_result['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in validation_result['warnings']:
                print(f"  • {warning}")
        
        # 3. Show recommendations
        print("\n💡 RECOMMENDATIONS:")
        for rec in validation_result['recommendations']:
            print(f"  {rec}")
        
        # 4. Get safe data summary
        print("\n📊 SAFE DATA SUMMARY:")
        safe_data = self.get_safe_data_for_morning_analysis()
        
        if 'error' in safe_data:
            print(f"❌ Error retrieving safe data: {safe_data['error']}")
        else:
            print(f"✅ Safe predictions available: {len(safe_data['predictions'])}")
            print(f"✅ Safe features available: {len(safe_data['features'])}")
            print(f"🕐 Latest safe timestamp: {safe_data['latest_safe_timestamp']}")
        
        # 5. Final verdict
        print("\n" + "=" * 55)
        if validation_result['is_safe']:
            print("🏆 MORNING ROUTINE: SAFE TO PROCEED")
            print("✅ No data leakage detected")
            print("✅ Temporal constraints satisfied")
        else:
            print("🛑 MORNING ROUTINE: DO NOT PROCEED")
            print("🚨 Data leakage or temporal issues detected")
            print("🔧 Run fixes before continuing")
        print("=" * 55)
        
        return validation_result['is_safe']

def main():
    """Main function to validate morning routine data integrity"""
    
    validator = MorningRoutineValidator()
    is_safe = validator.run_morning_validation()
    
    # Exit with appropriate code
    sys.exit(0 if is_safe else 1)

if __name__ == "__main__":
    main()

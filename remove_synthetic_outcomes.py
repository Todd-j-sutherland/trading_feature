#!/usr/bin/env python3
"""
Remove Synthetic Outcomes Script
Clean removal of synthetic data from enhanced_outcomes table
"""

import sqlite3
import os
from datetime import datetime

def remove_synthetic_outcomes():
    """
    Remove synthetic outcomes from the database, keeping only real market data
    """
    print("🧹 REMOVING SYNTHETIC OUTCOMES")
    print("=" * 50)
    
    db_path = "data/ml_models/enhanced_training_data.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current state
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        total_before = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL")
        outcomes_before = cursor.fetchone()[0]
        
        print(f"📊 Before cleanup:")
        print(f"   Total outcome records: {total_before}")
        print(f"   With price data: {outcomes_before}")
        
        # Identify synthetic outcomes (where exit_timestamp = prediction_timestamp)
        cursor.execute("""
            SELECT COUNT(*) FROM enhanced_outcomes 
            WHERE exit_timestamp = prediction_timestamp
        """)
        synthetic_count = cursor.fetchone()[0]
        
        print(f"   Identified synthetic: {synthetic_count}")
        
        if synthetic_count > 0:
            # Create backup of synthetic data (just in case)
            backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            print(f"📦 Creating backup of synthetic data...")
            
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS synthetic_backup_{backup_timestamp} AS
                SELECT * FROM enhanced_outcomes 
                WHERE exit_timestamp = prediction_timestamp
            """)
            
            # Remove synthetic outcomes
            print(f"🗑️ Removing {synthetic_count} synthetic outcomes...")
            
            cursor.execute("""
                DELETE FROM enhanced_outcomes 
                WHERE exit_timestamp = prediction_timestamp
            """)
            
            removed_count = cursor.rowcount
            conn.commit()
            
            print(f"   ✅ Removed {removed_count} synthetic outcome records")
            
        else:
            print("   ℹ️ No synthetic outcomes found to remove")
        
        # Check final state
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        total_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL")
        outcomes_after = cursor.fetchone()[0]
        
        print(f"\n📊 After cleanup:")
        print(f"   Total outcome records: {total_after}")
        print(f"   With price data: {outcomes_after}")
        print(f"   Removed: {total_before - total_after} records")
        
        # Check training readiness
        cursor.execute("SELECT COUNT(*) FROM enhanced_features")
        features_count = cursor.fetchone()[0]
        
        training_ready = features_count >= 50 and outcomes_after >= 50
        print(f"\n🎯 Training Status:")
        print(f"   Features: {features_count}")
        print(f"   Real outcomes: {outcomes_after}")
        print(f"   Training ready: {'✅ YES' if training_ready else '❌ NO'}")
        
        if not training_ready:
            print(f"\n💡 Next Steps:")
            print("   • System now has ONLY real market data")
            print("   • Run 'python -m app.main morning' regularly to accumulate data")
            print("   • Wait for natural outcome accumulation over time")
            print("   • Check back in 1-2 weeks for sufficient training data")
        
        # Show data composition
        if outcomes_after > 0:
            cursor.execute("""
                SELECT symbol, COUNT(*) as count
                FROM enhanced_outcomes
                GROUP BY symbol
                ORDER BY count DESC
            """)
            symbol_outcomes = cursor.fetchall()
            
            print(f"\n📈 Real Outcomes by Symbol:")
            for symbol, count in symbol_outcomes:
                print(f"   {symbol}: {count} real outcomes")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

def verify_clean_database():
    """
    Verify that only real market data remains
    """
    print(f"\n🔍 Verifying clean database...")
    
    db_path = "data/ml_models/enhanced_training_data.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for any remaining synthetic data
        cursor.execute("""
            SELECT COUNT(*) FROM enhanced_outcomes 
            WHERE exit_timestamp = prediction_timestamp
        """)
        remaining_synthetic = cursor.fetchone()[0]
        
        if remaining_synthetic == 0:
            print("   ✅ All synthetic data successfully removed")
            print("   ✅ Database contains ONLY real market outcomes")
        else:
            print(f"   ⚠️ {remaining_synthetic} synthetic records still present")
        
        # Show data quality metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MIN(prediction_timestamp) as earliest,
                MAX(prediction_timestamp) as latest,
                COUNT(DISTINCT symbol) as symbols
            FROM enhanced_outcomes
        """)
        
        stats = cursor.fetchone()
        if stats[0] > 0:
            print(f"   📊 Real Data Summary:")
            print(f"     Total real outcomes: {stats[0]}")
            print(f"     Date range: {stats[1]} to {stats[2]}")
            print(f"     Symbols covered: {stats[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Verification error: {e}")

if __name__ == "__main__":
    print("🚀 Starting synthetic data removal...\n")
    
    success = remove_synthetic_outcomes()
    
    if success:
        verify_clean_database()
        print(f"\n✅ CLEANUP COMPLETE!")
        print("   Database now contains ONLY real market data")
        print("   System will accumulate training data naturally over time")
    else:
        print(f"\n❌ Cleanup failed. Check database permissions and path.")
    
    print(f"\n" + "=" * 50)

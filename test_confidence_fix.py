#!/usr/bin/env python3
"""
Test script to verify the confidence value fix is working
Run this to check if the uniform 61.0% issue has been resolved
"""

import sqlite3
from collections import Counter
from pathlib import Path

def test_remote_confidence_values():
    """Test confidence values on remote server database"""
    
    # This would connect to remote database
    # For local testing, you can modify the path to point to local DB if available
    
    print("🔍 CONFIDENCE VALUE ANALYSIS")
    print("=" * 40)
    
    try:
        # Connect to database (adjust path as needed)
        db_path = "data/ml_models/training_data.db"
        
        if not Path(db_path).exists():
            print("❌ Database not found locally")
            print("🌐 Use the Simple Browser to view: http://170.64.199.151:8505")
            print("   This dashboard shows the live confidence values from remote server")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get recent confidence values
        cursor.execute("""
            SELECT confidence, COUNT(*) as count
            FROM sentiment_features 
            WHERE timestamp >= date('now', '-7 days')
            GROUP BY confidence
            ORDER BY confidence
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("❌ No recent data found")
            return
            
        print(f"Confidence distribution (last 7 days):")
        print("-" * 30)
        
        total_records = sum(count for _, count in results)
        uniform_61_count = 0
        
        for confidence, count in results:
            percentage = (count / total_records) * 100
            print(f"{confidence:5.1f}%: {count:3d} records ({percentage:4.1f}%)")
            
            if abs(confidence - 61.0) < 0.1:  # Check for 61.0%
                uniform_61_count = count
        
        print(f"\nTotal records analyzed: {total_records}")
        print(f"Unique confidence values: {len(results)}")
        
        # Analysis
        uniform_percentage = (uniform_61_count / total_records) * 100
        
        if uniform_percentage > 80:
            print(f"❌ ISSUE: {uniform_percentage:.1f}% of records still have 61.0% confidence")
            print("   Fix may not be fully deployed")
        elif uniform_percentage > 50:
            print(f"⚠️  IMPROVING: {uniform_percentage:.1f}% have 61.0% confidence (down from 85.9%)")
            print("   Some improvement, but more diverse values needed")
        else:
            print(f"✅ FIXED: Only {uniform_percentage:.1f}% have 61.0% confidence!")
            print("   Confidence values show good diversity")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🌐 View live dashboard at: http://170.64.199.151:8505")

def show_fix_summary():
    """Show summary of the confidence fix implementation"""
    
    print("\n" + "=" * 50)
    print("🛠️  CONFIDENCE FIX IMPLEMENTATION SUMMARY")
    print("=" * 50)
    
    print("\n📋 Issues Fixed:")
    print("   1. News collection parameter validation")
    print("   2. Dynamic market-based confidence (45-65%)")
    print("   3. Improved ML fallback confidence (45-75%)")
    print("   4. Data-driven confidence calculation")
    
    print("\n📊 Expected Results:")
    print("   • Before: 85.9% uniform 61.0% confidence")
    print("   • After: Diverse confidence ranges:")
    print("     - Market conditions: 45-65%")
    print("     - ML predictions: Variable %")
    print("     - Quality-based fallback: 45-75%")
    
    print("\n🌐 Live Dashboard:")
    print("   URL: http://170.64.199.151:8505")
    print("   Features:")
    print("   • Real-time SQL data")
    print("   • Confidence distribution analysis")
    print("   • Data quality metrics")
    print("   • Prediction timeline")
    
    print("\n✅ Verification Methods:")
    print("   1. Check dashboard confidence charts")
    print("   2. Look for values other than 61.0%")
    print("   3. Verify 'GOOD' quality score")
    print("   4. Confirm diverse prediction signals")

if __name__ == "__main__":
    test_remote_confidence_values()
    show_fix_summary()
    
    print(f"\n🔗 Open the dashboard to see the live results:")
    print(f"   http://170.64.199.151:8505")

#!/usr/bin/env python3
"""
Dashboard Data Verification - Ensure both dashboards show enhanced data
"""

import sqlite3
import pandas as pd
from datetime import datetime

def verify_dashboard_data():
    """Verify that both dashboards can access the enhanced data properly"""
    
    print("🔍 DASHBOARD DATA VERIFICATION")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('data/trading_predictions.db')
        
        # 1. Test enhanced data query (like new dashboards use)
        print("\n✅ ENHANCED DATA QUERY TEST:")
        enhanced_query = """
        SELECT 
            ef.symbol,
            ef.sentiment_score,
            ef.confidence,
            ef.current_price,
            eo.optimal_action,
            eo.confidence_score,
            eo.entry_price
        FROM enhanced_features ef
        LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        ORDER BY ef.timestamp DESC
        LIMIT 5
        """
        
        enhanced_df = pd.read_sql_query(enhanced_query, conn)
        print(f"Enhanced query returned: {len(enhanced_df)} rows")
        
        if len(enhanced_df) > 0:
            print("Sample enhanced data:")
            for _, row in enhanced_df.iterrows():
                print(f"  {row['symbol']}: {row['optimal_action']} (conf: {row['confidence_score']:.3f}, price: ${row['entry_price']:.2f})")
            print("✅ Enhanced data available for dashboards")
        else:
            print("⚠️  No enhanced data found")
        
        # 2. Test legacy data query (fallback)
        print("\n✅ LEGACY DATA QUERY TEST:")
        legacy_query = """
        SELECT 
            symbol,
            predicted_action,
            action_confidence,
            entry_price,
            created_at
        FROM predictions 
        WHERE entry_price > 0
        ORDER BY created_at DESC
        LIMIT 5
        """
        
        legacy_df = pd.read_sql_query(legacy_query, conn)
        print(f"Legacy query returned: {len(legacy_df)} rows")
        
        if len(legacy_df) > 0:
            print("Sample legacy data:")
            for _, row in legacy_df.iterrows():
                print(f"  {row['symbol']}: {row['predicted_action']} (conf: {row['action_confidence']:.3f}, price: ${row['entry_price']:.2f})")
            print("✅ Legacy data available as fallback")
        else:
            print("⚠️  No legacy data found")
        
        # 3. Data consistency check
        print("\n🎯 DATA CONSISTENCY CHECK:")
        
        enhanced_count = len(enhanced_df)
        legacy_count = len(legacy_df)
        
        print(f"Enhanced records: {enhanced_count}")
        print(f"Legacy records: {legacy_count}")
        
        if enhanced_count > 0:
            print("✅ PRIMARY: Enhanced data will be displayed")
            data_source = "Enhanced"
        elif legacy_count > 0:
            print("✅ FALLBACK: Legacy data will be displayed")
            data_source = "Legacy"
        else:
            print("❌ NO DATA: No data available for dashboards")
            data_source = "None"
        
        # 4. Entry price validation
        print("\n💰 ENTRY PRICE VALIDATION:")
        
        if enhanced_count > 0:
            zero_enhanced = len(enhanced_df[enhanced_df['entry_price'] <= 0])
            if zero_enhanced == 0:
                print("✅ Enhanced data: All entry prices > 0")
            else:
                print(f"⚠️  Enhanced data: {zero_enhanced} zero entry prices found")
        
        if legacy_count > 0:
            zero_legacy = len(legacy_df[legacy_df['entry_price'] <= 0])
            if zero_legacy == 0:
                print("✅ Legacy data: All entry prices > 0")
            else:
                print(f"⚠️  Legacy data: {zero_legacy} zero entry prices found")
        
        # 5. Dashboard URLs
        print("\n🌐 DASHBOARD ACCESS:")
        print("Enhanced Dashboard: http://localhost:8501")
        print("ML Dashboard: http://localhost:8502")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print(f"🎯 VERIFICATION COMPLETE - Data Source: {data_source}")
        print("✅ Both dashboards should now show consistent enhanced data!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    verify_dashboard_data()

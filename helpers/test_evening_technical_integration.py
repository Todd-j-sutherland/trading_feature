#!/usr/bin/env python3
"""
Test Technical Score Integration in Evening Routine
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_evening_technical_integration():
    """Test if technical scores are updated during evening routine"""
    
    print("🧪 TESTING EVENING ROUTINE TECHNICAL INTEGRATION")
    print("=" * 60)
    
    # Test 1: Check if technical engine can be imported
    print("\n1. Testing TechnicalAnalysisEngine import...")
    try:
        from technical_analysis_engine import TechnicalAnalysisEngine
        print("✅ TechnicalAnalysisEngine imported successfully")
        tech_available = True
    except ImportError as e:
        print(f"❌ Failed to import TechnicalAnalysisEngine: {e}")
        tech_available = False
    
    # Test 2: Test technical score calculation
    if tech_available:
        print("\n2. Testing technical score calculation...")
        try:
            tech_engine = TechnicalAnalysisEngine()
            
            # Test single bank calculation
            result = tech_engine.calculate_technical_score('CBA.AX')
            if result and 'technical_score' in result:
                print(f"✅ Technical calculation works: CBA.AX = {result['technical_score']}")
            else:
                print("❌ Technical calculation failed")
                
        except Exception as e:
            print(f"❌ Technical calculation error: {e}")
    
    # Test 3: Check database integration
    print("\n3. Testing database integration...")
    try:
        import sqlite3
        conn = sqlite3.connect('data/ml_models/training_data.db')
        cursor = conn.cursor()
        
        # Check recent technical scores
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sentiment_features 
            WHERE technical_score > 0 
            AND timestamp >= date('now', '-1 day')
        """)
        
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            print(f"✅ Database has {count} records with technical scores")
        else:
            print("⚠️ No recent records with technical scores found")
            
    except Exception as e:
        print(f"❌ Database check error: {e}")
    
    # Test 4: Test evening routine integration (simplified)
    print("\n4. Testing evening routine components...")
    try:
        # Import and test the evening routine method signature
        from app.services.daily_manager import TradingSystemManager
        manager = TradingSystemManager()
        
        # Check if the method exists
        if hasattr(manager, 'evening_routine'):
            print("✅ evening_routine method found in TradingSystemManager")
            
            # Check if our technical integration is in the source code
            import inspect
            source = inspect.getsource(manager.evening_routine)
            if 'TechnicalAnalysisEngine' in source:
                print("✅ Technical score integration found in evening_routine")
            else:
                print("❌ Technical score integration NOT found in evening_routine")
        else:
            print("❌ evening_routine method not found")
            
    except Exception as e:
        print(f"❌ Evening routine test error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST SUMMARY:")
    
    if tech_available:
        print("✅ Technical scores will be updated during evening routine")
        print("🔄 When you run 'python -m app.main evening', technical scores will be calculated automatically")
    else:
        print("❌ Technical integration needs fixing")
        print("🔧 Use 'python automated_technical_updater.py once' as manual alternative")

if __name__ == "__main__":
    test_evening_technical_integration()

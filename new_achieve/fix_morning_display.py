#!/usr/bin/env python3
"""
Quick fix for remote morning analysis display issue
"""

import os
import sys

def fix_daily_manager():
    """Fix the daily manager display logic"""
    
    daily_manager_path = "app/services/daily_manager.py"
    
    if not os.path.exists(daily_manager_path):
        print("❌ daily_manager.py not found")
        return False
    
    print("🔧 Fixing daily manager display logic...")
    
    # Read the file
    with open(daily_manager_path, 'r') as f:
        content = f.read()
    
    # Replace the incorrect display logic
    old_logic = '''                    # Display key results
                    predictions = enhanced_result.get('bank_predictions', {})
                    market_overview = enhanced_result.get('market_overview', {})
                    
                    print(f"\\n📊 Enhanced Analysis Summary:")
                    print(f"   Banks Analyzed: {len(predictions)}")
                    print(f"   Market Sentiment: {market_overview.get('overall_sentiment', 'UNKNOWN')}")
                    print(f"   Feature Pipeline: {enhanced_result.get('data_collection_summary', {}).get('total_features_collected', 0)} features")
                    
                    # Show top predictions
                    if predictions:
                        print(f"\\n🎯 Top Trading Signals:")
                        for symbol, pred in list(predictions.items())[:3]:
                            action = pred.get('optimal_action', 'UNKNOWN')
                            confidence = pred.get('confidence', 0)
                            print(f"   {symbol}: {action} (confidence: {confidence:.3f})")'''
    
    new_logic = '''                    # Display key results using correct structure
                    banks_analyzed = enhanced_result.get('banks_analyzed', [])
                    ml_predictions = enhanced_result.get('ml_predictions', {})
                    overall_sentiment = enhanced_result.get('overall_market_sentiment', 0)
                    feature_counts = enhanced_result.get('feature_counts', {})
                    total_features = sum(feature_counts.values()) if feature_counts else 0
                    
                    print(f"\\n📊 Enhanced Analysis Summary:")
                    print(f"   Banks Analyzed: {len(banks_analyzed)}")
                    print(f"   Market Sentiment: {'BULLISH' if overall_sentiment > 0.1 else 'BEARISH' if overall_sentiment < -0.1 else 'NEUTRAL'}")
                    print(f"   Feature Pipeline: {total_features} features")
                    
                    # Show top predictions
                    if ml_predictions:
                        print(f"\\n🎯 Top Trading Signals:")
                        for symbol, pred in list(ml_predictions.items())[:3]:
                            action = pred.get('optimal_action', 'UNKNOWN')
                            confidence = pred.get('confidence_scores', {}).get('average', 0)
                            print(f"   {symbol}: {action} (confidence: {confidence:.3f})")'''
    
    if old_logic in content:
        content = content.replace(old_logic, new_logic)
        
        # Write back the file
        with open(daily_manager_path, 'w') as f:
            f.write(content)
        
        print("✅ Daily manager display logic fixed!")
        print("📊 Now shows: banks_analyzed, ml_predictions, overall_market_sentiment")
        return True
    else:
        print("⚠️ Display logic already appears to be correct or pattern not found")
        return False

def verify_fix():
    """Verify the fix by checking the file content"""
    daily_manager_path = "app/services/daily_manager.py"
    
    with open(daily_manager_path, 'r') as f:
        content = f.read()
    
    if 'banks_analyzed = enhanced_result.get(\'banks_analyzed\', [])' in content:
        print("✅ Fix verification: Correct logic found in file")
        return True
    else:
        print("❌ Fix verification: Correct logic not found")
        return False

if __name__ == "__main__":
    print("🔧 REMOTE MORNING ANALYSIS FIX")
    print("=" * 40)
    
    if fix_daily_manager():
        if verify_fix():
            print("\n🎉 Fix complete! The remote morning analysis should now display correctly.")
            print("💡 Next time you run the morning routine, it should show:")
            print("   Banks Analyzed: 7 (instead of 0)")
            print("   Market Sentiment: NEUTRAL/BULLISH/BEARISH")
            print("   Feature Pipeline: 371 features (53 per bank)")
        else:
            print("\n❌ Fix verification failed")
    else:
        print("\n❌ Fix failed - file may already be correct")

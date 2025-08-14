#!/usr/bin/env python3
"""
Integration Patch: Add Technical Score Updates to Evening Routine
This script integrates technical score calculation into the evening workflow
"""

import os
import sys
from datetime import datetime

def integrate_technical_scores_into_evening():
    """
    Add technical score updates to the enhanced evening analyzer
    """
    analyzer_file = "enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py"
    
    if not os.path.exists(analyzer_file):
        print(f"❌ {analyzer_file} not found")
        return False
    
    # Read the current file
    with open(analyzer_file, 'r') as f:
        content = f.read()
    
    # Check if technical analysis is already integrated
    if "TechnicalAnalysisEngine" in content and "update_database_technical_scores" in content:
        print("✅ Technical score updates already integrated in evening analyzer")
        return True
    
    # Add import for TechnicalAnalysisEngine
    if "from technical_analysis_engine import TechnicalAnalysisEngine" not in content:
        # Find the import section and add the technical analysis import
        import_line = "from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer"
        if import_line in content:
            new_import = f"{import_line}\nfrom technical_analysis_engine import TechnicalAnalysisEngine"
            content = content.replace(import_line, new_import)
    
    # Add technical engine to __init__ method
    init_pattern = "self.ml_training_pipeline = None"
    if init_pattern in content and "self.technical_engine" not in content:
        new_init = f"{init_pattern}\n        self.technical_engine = TechnicalAnalysisEngine()"
        content = content.replace(init_pattern, new_init)
    
    # Add technical score update method
    if "def update_technical_scores" not in content:
        # Find a good place to add the method (before the main run method)
        run_method_pattern = "def run_enhanced_evening_analysis(self):"
        if run_method_pattern in content:
            new_method = '''    def update_technical_scores(self) -> bool:
        """
        Update technical scores for all banks
        """
        try:
            print("📊 Updating technical scores...")
            success = self.technical_engine.update_database_technical_scores()
            
            if success:
                print("✅ Technical scores updated successfully")
                
                # Get summary for logging
                summary = self.technical_engine.get_technical_summary()
                print(f"📈 Technical Analysis Summary:")
                print(f"   Banks analyzed: {summary['total_banks_analyzed']}")
                print(f"   BUY signals: {summary['signals']['BUY']}")
                print(f"   HOLD signals: {summary['signals']['HOLD']}")
                print(f"   SELL signals: {summary['signals']['SELL']}")
                print(f"   Average score: {summary['average_technical_score']}")
                
            return success
            
        except Exception as e:
            print(f"❌ Error updating technical scores: {e}")
            return False

    '''
            content = content.replace(run_method_pattern, f"{new_method}\n    {run_method_pattern}")
    
    # Add technical score update call to the main run method
    # Find the run method and add technical score update at the beginning
    if "# Step 1: Enhanced analysis with validation" in content:
        step1_pattern = "        # Step 1: Enhanced analysis with validation"
        new_step = '''        # Step 0: Update technical scores first
        print("🔧 Updating technical scores...")
        tech_success = self.update_technical_scores()
        if not tech_success:
            print("⚠️ Technical score update failed, continuing with analysis...")
        
        # Step 1: Enhanced analysis with validation'''
        content = content.replace(step1_pattern, new_step)
    
    # Create backup
    backup_path = f"{analyzer_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_path, 'w') as f:
        with open(analyzer_file, 'r') as original:
            f.write(original.read())
    
    # Write modified content
    with open(analyzer_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Integrated technical score updates into {analyzer_file}")
    print(f"📄 Backup created: {backup_path}")
    return True

def test_evening_integration():
    """
    Test if the evening routine now includes technical score updates
    """
    print("🧪 Testing evening integration...")
    
    try:
        # Skip transformers to avoid torch issues
        os.environ['SKIP_TRANSFORMERS'] = '1'
        
        from enhanced_ml_system.analyzers.enhanced_evening_analyzer_with_ml import EnhancedEveningAnalyzer
        
        analyzer = EnhancedEveningAnalyzer()
        
        # Check if technical engine is available
        if hasattr(analyzer, 'technical_engine'):
            print("✅ Technical engine found in evening analyzer")
            
            # Check if update method exists
            if hasattr(analyzer, 'update_technical_scores'):
                print("✅ Technical score update method found")
                
                # Test the method
                print("🔧 Testing technical score update...")
                success = analyzer.update_technical_scores()
                
                if success:
                    print("✅ Technical score update test successful")
                    return True
                else:
                    print("❌ Technical score update test failed")
                    return False
            else:
                print("❌ Technical score update method not found")
                return False
        else:
            print("❌ Technical engine not found in evening analyzer")
            return False
            
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        return False

def main():
    print("🔧 INTEGRATING TECHNICAL SCORES INTO EVENING ROUTINE")
    print("=" * 60)
    
    # Step 1: Integrate technical scores into evening analyzer
    print("\n1. Integration:")
    integration_success = integrate_technical_scores_into_evening()
    
    # Step 2: Test the integration
    print("\n2. Testing Integration:")
    test_success = test_evening_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION SUMMARY:")
    print(f"   ✅ File Integration: {'SUCCESS' if integration_success else 'FAILED'}")
    print(f"   ✅ Functionality Test: {'SUCCESS' if test_success else 'FAILED'}")
    
    if integration_success and test_success:
        print("\n🎉 TECHNICAL SCORES INTEGRATED!")
        print("   The evening routine will now automatically update technical scores.")
        print("   Run 'python -m app.main evening' to test the complete workflow.")
    else:
        print("\n❌ INTEGRATION ISSUES")
        print("   Please check the error messages above.")
        
    print(f"\n📋 Next Steps:")
    print(f"   1. Run: source dashboard_env/bin/activate")
    print(f"   2. Run: SKIP_TRANSFORMERS=1 python -m app.main evening")
    print(f"   3. Check that technical scores are updated automatically")

if __name__ == "__main__":
    main()

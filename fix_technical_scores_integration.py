#!/usr/bin/env python3
"""
Fix Technical Scores Integration
This script integrates technical score calculation into the data collection process
"""

import sqlite3
import sys
import os
from datetime import datetime
from technical_analysis_engine import TechnicalAnalysisEngine

def modify_collect_reliable_data():
    """
    Modify collect_reliable_data.py to include technical score calculation
    """
    file_path = "collect_reliable_data.py"
    
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return False
    
    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if technical analysis is already integrated
    if "TechnicalAnalysisEngine" in content:
        print("✅ Technical analysis already integrated in collect_reliable_data.py")
        return True
    
    # Add import for TechnicalAnalysisEngine at the top
    import_section = "import sqlite3\nimport pandas as pd\nimport numpy as np"
    new_import = "import sqlite3\nimport pandas as pd\nimport numpy as np\nfrom technical_analysis_engine import TechnicalAnalysisEngine"
    
    content = content.replace(import_section, new_import)
    
    # Modify the __init__ method to include technical engine
    init_pattern = "def __init__(self, db_path: str = \"data/ml_models/training_data.db\"):"
    if init_pattern in content:
        init_replacement = """def __init__(self, db_path: str = "data/ml_models/training_data.db"):
        self.db_path = db_path
        self.technical_engine = TechnicalAnalysisEngine(db_path)"""
        
        # Find and replace the init method
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if init_pattern in line:
                # Replace the init line and add technical engine
                lines[i] = "    def __init__(self, db_path: str = \"data/ml_models/training_data.db\"):"
                # Add technical engine initialization after the db_path line
                for j in range(i+1, len(lines)):
                    if "self.db_path = db_path" in lines[j]:
                        lines.insert(j+1, "        self.technical_engine = TechnicalAnalysisEngine(db_path)")
                        break
                break
        content = '\n'.join(lines)
    
    # Modify the insert_data method to calculate technical scores
    old_technical_line = "data.get('technical_score', 0.0)"
    new_technical_section = """# Calculate real-time technical score
                symbol = data['symbol']
                try:
                    tech_result = self.technical_engine.calculate_technical_score(symbol)
                    technical_score = tech_result.get('technical_score', 0.0)
                    print(f"📊 Calculated technical score for {symbol}: {technical_score}")
                except Exception as e:
                    print(f"⚠️ Failed to calculate technical score for {symbol}: {e}")
                    technical_score = 0.0
                
                technical_score"""
    
    content = content.replace(old_technical_line, new_technical_section)
    
    # Write the modified file
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create backup
    with open(backup_path, 'w') as f:
        with open(file_path, 'r') as original:
            f.write(original.read())
    
    # Write modified content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Modified {file_path} to include technical score calculation")
    print(f"📄 Backup created: {backup_path}")
    return True

def run_immediate_technical_update():
    """
    Run immediate technical score update for existing data
    """
    print("🔧 Running immediate technical score update...")
    
    tech_engine = TechnicalAnalysisEngine()
    success = tech_engine.update_database_technical_scores()
    
    if success:
        print("✅ Technical scores updated successfully")
        return True
    else:
        print("❌ Failed to update technical scores")
        return False

def verify_dashboard_data():
    """
    Verify that dashboard will now show technical scores
    """
    print("🔍 Verifying dashboard data...")
    
    try:
        conn = sqlite3.connect("data/ml_models/training_data.db")
        cursor = conn.cursor()
        
        # Check for non-zero technical scores
        cursor.execute("""
            SELECT symbol, technical_score 
            FROM sentiment_features 
            WHERE technical_score > 0 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            print(f"✅ Found {len(results)} records with technical scores > 0")
            for symbol, score in results:
                print(f"   {symbol}: {score}")
            return True
        else:
            print("❌ No records with technical scores > 0 found")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return False

def main():
    print("🚀 FIXING TECHNICAL SCORES INTEGRATION")
    print("=" * 50)
    
    # Step 1: Run immediate update to fix current dashboard
    print("\n1. Immediate Technical Score Update:")
    immediate_success = run_immediate_technical_update()
    
    # Step 2: Verify dashboard data
    print("\n2. Verify Dashboard Data:")
    verify_success = verify_dashboard_data()
    
    # Step 3: Integrate into data collection (optional enhancement)
    print("\n3. Integration Enhancement:")
    print("   To automatically calculate technical scores during data collection,")
    print("   consider modifying collect_reliable_data.py or enhanced_ml_system/")
    print("   to include technical score calculation.")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"   ✅ Immediate Fix: {'SUCCESS' if immediate_success else 'FAILED'}")
    print(f"   ✅ Data Verification: {'SUCCESS' if verify_success else 'FAILED'}")
    
    if immediate_success and verify_success:
        print("\n🎉 TECHNICAL SCORES FIXED!")
        print("   Your dashboard.py should now show technical scores instead of zeros.")
        print("   Run 'streamlit run dashboard.py' to see the updated data.")
    else:
        print("\n❌ ISSUES REMAIN")
        print("   Please check the error messages above.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Quick Diagnostic Script
Find the source of return calculation bugs in the codebase
"""

import os
import re
import subprocess

def search_for_calculation_code():
    """Search for return calculation related code"""
    
    print("🔍 RETURN CALCULATION CODE SEARCH")
    print("=" * 40)
    
    # Patterns to search for
    patterns = [
        r"return_pct.*=",
        r"exit_price.*entry_price",
        r"enhanced_outcomes.*INSERT",
        r"enhanced_outcomes.*UPDATE",
        r"((.*exit.*-.*entry.*)/.*entry.*)",
        r"exit.*price.*-.*entry.*price"
    ]
    
    for pattern in patterns:
        print(f"\n🔎 Searching for pattern: {pattern}")
        print("-" * 50)
        
        try:
            result = subprocess.run([
                'grep', '-r', '-n', '--include=*.py', pattern, '.'
            ], capture_output=True, text=True, cwd='/Users/toddsutherland/Repos/trading_feature')
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines[:10]:  # Show first 10 matches
                    print(f"  {line}")
                if len(lines) > 10:
                    print(f"  ... and {len(lines) - 10} more matches")
            else:
                print("  No matches found")
                
        except Exception as e:
            print(f"  Error searching: {e}")

def find_evening_analysis_files():
    """Find files related to evening analysis"""
    
    print(f"\n📁 EVENING ANALYSIS FILES")
    print("-" * 30)
    
    evening_patterns = [
        "*evening*",
        "*outcome*", 
        "*analyzer*",
        "*trading*"
    ]
    
    for pattern in evening_patterns:
        print(f"\n📂 Files matching '{pattern}':")
        try:
            result = subprocess.run([
                'find', '.', '-name', pattern, '-type', 'f'
            ], capture_output=True, text=True, cwd='/Users/toddsutherland/Repos/trading_feature')
            
            if result.stdout:
                files = result.stdout.strip().split('\n')
                for file in files:
                    if file.endswith('.py'):
                        print(f"  🐍 {file}")
                    else:
                        print(f"  📄 {file}")
            else:
                print("  No files found")
                
        except Exception as e:
            print(f"  Error: {e}")

def check_app_main_structure():
    """Check the app.main structure for evening analysis entry point"""
    
    print(f"\n⚙️ APP.MAIN STRUCTURE")
    print("-" * 25)
    
    main_files = [
        'app/main.py',
        'main.py', 
        'app/__init__.py',
        'app.py'
    ]
    
    for main_file in main_files:
        full_path = f'/Users/toddsutherland/Repos/trading_feature/{main_file}'
        if os.path.exists(full_path):
            print(f"\n📜 Found: {main_file}")
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                    
                # Look for evening-related code
                if 'evening' in content.lower():
                    print("  Contains 'evening' references ✅")
                    
                    # Extract evening-related lines
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'evening' in line.lower():
                            print(f"    Line {i}: {line.strip()}")
                else:
                    print("  No 'evening' references found")
                    
            except Exception as e:
                print(f"  Error reading: {e}")
        else:
            print(f"❌ Not found: {main_file}")

def analyze_database_schema():
    """Analyze database schema for return calculation fields"""
    
    print(f"\n🗄️ DATABASE SCHEMA ANALYSIS")
    print("-" * 35)
    
    try:
        result = subprocess.run([
            'sqlite3', 'data/trading_unified.db', '.schema enhanced_outcomes'
        ], capture_output=True, text=True, cwd='/Users/toddsutherland/Repos/trading_feature')
        
        if result.stdout:
            print("📋 enhanced_outcomes schema:")
            schema_lines = result.stdout.split('\n')
            for line in schema_lines:
                if any(field in line.lower() for field in ['return', 'entry', 'exit', 'price']):
                    print(f"  🎯 {line.strip()}")
                elif line.strip():
                    print(f"     {line.strip()}")
        else:
            print("❌ Could not read schema")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

def priority_investigation_list():
    """Generate priority list for investigation"""
    
    print(f"\n📋 PRIORITY INVESTIGATION LIST")
    print("-" * 35)
    
    priorities = [
        "1. HIGH: Search for 'evening' in app/main.py or main.py",
        "2. HIGH: Find evening_analyzer.py or similar files",
        "3. MEDIUM: Check files with 'enhanced_outcomes' INSERT/UPDATE",
        "4. MEDIUM: Look for return_pct calculation functions",
        "5. LOW: Review Yahoo Finance integration code"
    ]
    
    for priority in priorities:
        print(f"  {priority}")
    
    print(f"\n🔧 INVESTIGATION COMMANDS")
    print("-" * 25)
    
    commands = [
        "grep -r 'def.*evening' --include='*.py' .",
        "grep -r 'enhanced_outcomes.*INSERT' --include='*.py' .",
        "grep -r 'return_pct.*=' --include='*.py' .",
        "find . -name '*evening*' -o -name '*outcome*' | grep '.py$'"
    ]
    
    for cmd in commands:
        print(f"  {cmd}")

if __name__ == "__main__":
    search_for_calculation_code()
    find_evening_analysis_files()
    check_app_main_structure()
    analyze_database_schema()
    priority_investigation_list()
    
    print(f"\n🎯 NEXT STEPS")
    print("-" * 15)
    print("1. Run the investigation commands above")
    print("2. Focus on files containing 'evening' and 'return_pct'")
    print("3. Look for the specific calculation that's producing wrong values")
    print("4. Use DEBUGGING_GUIDE.md for detailed fix instructions")

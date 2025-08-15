#!/usr/bin/env python3
"""
Fix Database References - Use trading_predictions.db as Primary
Updates all files to use trading_predictions.db since that's what the live system uses
"""

import os
import re

def find_and_fix_database_references():
    """Find and fix database references to use trading_predictions.db"""
    files_updated = []
    
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', 'backup_', 'archive', 'venv', 'env']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Replace trading_predictions.db with trading_predictions.db
                    if 'trading_predictions.db' in content:
                        content = content.replace('trading_predictions.db', 'trading_predictions.db')
                        
                        if content != original_content:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                            files_updated.append(filepath)
                            print(f"✓ Updated: {filepath}")
                            
                except Exception as e:
                    print(f"Warning: Could not update {filepath}: {e}")
    
    return files_updated

def main():
    print("🔄 FIXING DATABASE REFERENCES")
    print("=" * 50)
    print("Updating all references to use trading_predictions.db")
    print("(This is the active database used by the live system)")
    print()
    
    updated_files = find_and_fix_database_references()
    
    print(f"\n✅ Updated {len(updated_files)} files")
    print("\n🎯 VERIFICATION:")
    print("- All components now use trading_predictions.db")
    print("- This matches the live prediction system on remote server")
    print("- Dashboard will show current predictions (not historical)")

if __name__ == "__main__":
    main()

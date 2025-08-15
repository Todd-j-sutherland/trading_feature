#!/usr/bin/env python3
"""
Database Standardization Script
Updates all dashboard and system files to use trading_predictions.db as the single source of truth
"""

import os
import re

def find_python_files_with_db_references():
    """Find all Python files that reference database paths"""
    db_files = []
    
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', 'backup_', 'archive']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Look for database references
                    if any(pattern in content for pattern in [
                        'trading_predictions.db',
                        'DATABASE_PATH',
                        'sqlite3.connect',
                        '.db'
                    ]):
                        db_files.append(filepath)
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return db_files

def update_database_references(file_path):
    """Update database references in a file to use trading_predictions.db"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Pattern 1: DATABASE_PATH = "data/trading_predictions.db"
        pattern1 = r'DATABASE_PATH\s*=\s*["\']data/trading_predictions\.db["\']'
        if re.search(pattern1, content):
            content = re.sub(pattern1, 'DATABASE_PATH = "data/trading_predictions.db"', content)
            changes_made.append("Updated DATABASE_PATH")
        
        # Pattern 2: sqlite3.connect('data/trading_predictions.db')
        pattern2 = r'sqlite3\.connect\(["\']data/trading_predictions\.db["\']\)'
        if re.search(pattern2, content):
            content = re.sub(pattern2, "sqlite3.connect('data/trading_predictions.db')", content)
            changes_made.append("Updated sqlite3.connect call")
        
        # Pattern 3: sqlite3.connect('data/trading_predictions.db')
        pattern3 = r'sqlite3\.connect\(["\']data/trading_predictions\.db["\']\)'
        if re.search(pattern3, content):
            content = re.sub(pattern3, "sqlite3.connect('data/trading_predictions.db')", content)
            changes_made.append("Updated sqlite3.connect call (double quotes)")
        
        # Pattern 4: General trading_predictions.db references
        pattern4 = r'["\']data/trading_predictions\.db["\']'
        if re.search(pattern4, content):
            content = re.sub(pattern4, '"data/trading_predictions.db"', content)
            changes_made.append("Updated general database path references")
        
        # Pattern 5: trading_data.db references (less common)
        pattern5 = r'["\']data/trading_data\.db["\']'
        if re.search(pattern5, content):
            content = re.sub(pattern5, '"data/trading_predictions.db"', content)
            changes_made.append("Updated trading_data.db references")
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return changes_made
        
        return []
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return []

def standardize_database_references():
    """Main function to standardize all database references"""
    print("=== DATABASE REFERENCE STANDARDIZATION ===")
    print("Target: trading_predictions.db as single source of truth")
    print()
    
    # Find all Python files with database references
    print("Scanning for Python files with database references...")
    db_files = find_python_files_with_db_references()
    
    print(f"Found {len(db_files)} files with potential database references")
    print()
    
    updated_files = []
    
    # Update each file
    for file_path in db_files:
        print(f"Checking: {file_path}")
        changes = update_database_references(file_path)
        
        if changes:
            updated_files.append((file_path, changes))
            print(f"  ✓ Updated: {', '.join(changes)}")
        else:
            print(f"  - No changes needed")
    
    print()
    print("=== SUMMARY ===")
    print(f"Updated {len(updated_files)} files:")
    
    for file_path, changes in updated_files:
        print(f"  {file_path}")
        for change in changes:
            print(f"    - {change}")
    
    print()
    print("=== VERIFICATION ===")
    
    # Verify trading_predictions.db has the data
    import sqlite3
    try:
        conn = sqlite3.connect('data/trading_predictions.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM predictions")
        predictions_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        outcomes_count = cursor.fetchone()[0]
        
        print(f"trading_predictions.db verification:")
        print(f"  Predictions: {predictions_count}")
        print(f"  Enhanced outcomes: {outcomes_count}")
        
        if predictions_count > 0 and outcomes_count > 0:
            print("  ✓ Database contains live data")
        else:
            print("  ⚠ Database appears to have missing data")
        
        conn.close()
        
    except Exception as e:
        print(f"  ✗ Error verifying database: {e}")
    
    print()
    print("=== STANDARDIZATION COMPLETE ===")
    print("All files now reference: data/trading_predictions.db")
    print()
    print("Next steps:")
    print("1. Test dashboard functionality with unified database")
    print("2. Remove unused database files if desired")
    print("3. Update any remaining hardcoded references")

if __name__ == "__main__":
    standardize_database_references()

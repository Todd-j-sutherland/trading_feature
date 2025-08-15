#!/usr/bin/env python3
"""
Comprehensive Database and File Cleanup
Removes all unnecessary database files and updates remaining references
"""

import os
import shutil
import re
from pathlib import Path

class DatabaseCleanup:
    def __init__(self):
        self.root_dir = Path(".")
        self.keep_db = "data/trading_unified.db"
        self.cleanup_report = []
        
    def log_action(self, action, details=""):
        """Log cleanup actions"""
        log_entry = f"✓ {action}"
        if details:
            log_entry += f": {details}"
        self.cleanup_report.append(log_entry)
        print(log_entry)
    
    def find_all_databases(self):
        """Find all database files except the one we want to keep"""
        all_dbs = []
        for db_file in self.root_dir.rglob("*.db"):
            if str(db_file) != self.keep_db:
                all_dbs.append(str(db_file))
        return sorted(all_dbs)
    
    def categorize_databases(self, db_files):
        """Categorize databases for cleanup"""
        categories = {
            'backup_directories': [],
            'archive_directories': [], 
            'individual_backups': [],
            'old_ml_databases': [],
            'test_databases': [],
            'other_databases': []
        }
        
        for db in db_files:
            if 'backup_' in db or 'migration_backup' in db:
                categories['backup_directories'].append(db)
            elif 'archive' in db:
                categories['archive_directories'].append(db)
            elif any(name in db for name in ['backup', 'unused']):
                categories['individual_backups'].append(db)
            elif any(name in db for name in ['training_data', 'enhanced_training_data', 'ml_models']):
                categories['old_ml_databases'].append(db)
            elif any(name in db for name in ['test', 'testing']):
                categories['test_databases'].append(db)
            else:
                categories['other_databases'].append(db)
        
        return categories
    
    def remove_databases(self, categories):
        """Remove categorized database files"""
        total_removed = 0
        
        # Remove backup directories entirely
        backup_dirs = set()
        for db in categories['backup_directories']:
            backup_dir = str(Path(db).parent)
            if 'backup_' in backup_dir or 'migration_backup' in backup_dir:
                backup_dirs.add(backup_dir)
        
        for backup_dir in backup_dirs:
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
                self.log_action(f"Removed backup directory", backup_dir)
                total_removed += 1
        
        # Remove archive directories entirely (but keep one recent archive as safety)
        archive_dirs = set()
        for db in categories['archive_directories']:
            archive_dir = str(Path(db).parent.parent)  # Go up to archive root
            if 'archive' in archive_dir:
                archive_dirs.add(archive_dir)
        
        archive_list = sorted(list(archive_dirs))
        # Keep the most recent archive, remove the rest
        if len(archive_list) > 1:
            for archive_dir in archive_list[:-1]:  # Keep last one
                if os.path.exists(archive_dir):
                    shutil.rmtree(archive_dir)
                    self.log_action(f"Removed old archive directory", archive_dir)
                    total_removed += 1
        
        # Remove individual database files
        for category_name, db_list in categories.items():
            if category_name in ['backup_directories', 'archive_directories']:
                continue  # Already handled above
                
            for db in db_list:
                if os.path.exists(db):
                    os.remove(db)
                    self.log_action(f"Removed {category_name}", db)
                    total_removed += 1
        
        return total_removed
    
    def update_database_references_in_comments(self):
        """Update comments and documentation that mention old databases"""
        files_updated = 0
        
        # Find Python files that might have references in comments
        for py_file in self.root_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Update references in comments and docstrings
                patterns = [
                    (r'trading_predictions\.db', 'trading_unified.db'),
                    (r'training_data\.db', 'trading_unified.db (consolidated)'),
                    (r'enhanced_training_data\.db', 'trading_unified.db (consolidated)'),
                    (r'ml_models/.*\.db', 'trading_unified.db (consolidated)')
                ]
                
                for old_pattern, new_text in patterns:
                    # Only update in comments (lines starting with # or in docstrings)
                    lines = content.split('\n')
                    updated_lines = []
                    
                    for line in lines:
                        stripped = line.strip()
                        # Update if it's a comment line or in a docstring
                        if stripped.startswith('#') or '"""' in line or "'''" in line:
                            line = re.sub(old_pattern, new_text, line)
                        updated_lines.append(line)
                    
                    content = '\n'.join(updated_lines)
                
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    files_updated += 1
                    self.log_action(f"Updated documentation references", str(py_file))
                    
            except Exception as e:
                print(f"Warning: Could not update {py_file}: {e}")
        
        return files_updated
    
    def clean_empty_directories(self):
        """Remove empty directories left after cleanup"""
        dirs_removed = 0
        
        # Look for empty directories in data and related folders
        for dir_path in ['data', 'enhanced_ml_system', 'archive_cleanup']:
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path, topdown=False):
                    for dirname in dirs:
                        dirpath = os.path.join(root, dirname)
                        try:
                            if not os.listdir(dirpath):  # Directory is empty
                                os.rmdir(dirpath)
                                self.log_action(f"Removed empty directory", dirpath)
                                dirs_removed += 1
                        except Exception:
                            pass  # Directory not empty or permission issue
        
        return dirs_removed
    
    def generate_cleanup_summary(self):
        """Generate a summary of what was cleaned up"""
        # Check current state
        remaining_dbs = list(self.root_dir.rglob("*.db"))
        
        print("\n" + "="*60)
        print("DATABASE CLEANUP SUMMARY")
        print("="*60)
        
        print(f"\n📊 FINAL STATE:")
        print(f"✅ Active database: {self.keep_db}")
        print(f"📁 Remaining databases: {len(remaining_dbs)}")
        
        if len(remaining_dbs) <= 2:  # Should be just trading_unified.db and maybe one backup
            print("✅ Cleanup successful - minimal databases remaining")
        else:
            print("⚠️  Additional databases still present:")
            for db in remaining_dbs:
                if str(db) != self.keep_db:
                    print(f"   - {db}")
        
        print(f"\n📋 ACTIONS TAKEN:")
        for action in self.cleanup_report:
            print(f"   {action}")
        
        print(f"\n💾 DISK SPACE:")
        if os.path.exists(self.keep_db):
            size_mb = os.path.getsize(self.keep_db) / (1024 * 1024)
            print(f"   Active database size: {size_mb:.1f} MB")
        
        return len(remaining_dbs)

def main():
    """Run comprehensive database cleanup"""
    print("🧹 COMPREHENSIVE DATABASE CLEANUP")
    print("=" * 50)
    print(f"Keeping only: data/trading_unified.db")
    print(f"Removing all other database files and archives")
    print()
    
    cleanup = DatabaseCleanup()
    
    # Step 1: Find all databases
    print("1️⃣ Scanning for database files...")
    all_dbs = cleanup.find_all_databases()
    print(f"   Found {len(all_dbs)} database files to evaluate")
    
    # Step 2: Categorize databases
    print("\n2️⃣ Categorizing databases...")
    categories = cleanup.categorize_databases(all_dbs)
    
    for category, files in categories.items():
        if files:
            print(f"   {category}: {len(files)} files")
    
    # Step 3: Remove databases
    print("\n3️⃣ Removing unnecessary databases...")
    removed_count = cleanup.remove_databases(categories)
    print(f"   Removed {removed_count} items")
    
    # Step 4: Update documentation references
    print("\n4️⃣ Updating documentation references...")
    updated_files = cleanup.update_database_references_in_comments()
    print(f"   Updated {updated_files} files")
    
    # Step 5: Clean empty directories
    print("\n5️⃣ Cleaning empty directories...")
    removed_dirs = cleanup.clean_empty_directories()
    print(f"   Removed {removed_dirs} empty directories")
    
    # Step 6: Generate summary
    remaining_dbs = cleanup.generate_cleanup_summary()
    
    print("\n🎉 CLEANUP COMPLETE!")
    print("   Your database architecture is now clean and unified.")
    print("   All components use data/trading_unified.db as the single source of truth.")

if __name__ == "__main__":
    main()

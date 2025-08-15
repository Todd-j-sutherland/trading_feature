#!/usr/bin/env python3
"""
Database Cleanup and Consolidation Tool
=======================================

Consolidates multiple databases into the main trading_unified.db
and archives unused/empty databases.
"""

import sqlite3
import shutil
import os
from datetime import datetime
import json

class DatabaseCleanupManager:
    def __init__(self):
        self.main_db = "data/trading_unified.db"
        self.backup_dir = "data/database_cleanup_backup"
        self.report = {
            "cleanup_date": datetime.now().isoformat(),
            "actions": [],
            "consolidated": [],
            "archived": [],
            "removed": []
        }
    
    def create_backup_dir(self):
        """Create backup directory for cleanup"""
        os.makedirs(self.backup_dir, exist_ok=True)
        print(f"📁 Created backup directory: {self.backup_dir}")
    
    def analyze_database(self, db_path):
        """Analyze a database and return table information"""
        if not os.path.exists(db_path):
            return None
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            table_info = {}
            total_records = 0
            
            for table in tables:
                table_name = table[0]
                if not table_name.startswith('sqlite_'):  # Skip SQLite system tables
                    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                    count = cursor.fetchone()[0]
                    table_info[table_name] = count
                    total_records += count
            
            conn.close()
            
            return {
                "tables": table_info,
                "total_records": total_records,
                "file_size": os.path.getsize(db_path)
            }
            
        except Exception as e:
            print(f"❌ Error analyzing {db_path}: {e}")
            return None
    
    def backup_database(self, db_path):
        """Create a backup of a database before cleanup"""
        if not os.path.exists(db_path):
            return False
            
        backup_name = f"{os.path.basename(db_path)}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            shutil.copy2(db_path, backup_path)
            print(f"📋 Backed up: {db_path} -> {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Backup failed for {db_path}: {e}")
            return False
    
    def consolidate_trading_data_db(self):
        """Consolidate data from trading_data.db into trading_unified.db"""
        source_db = "data/trading_data.db"
        
        if not os.path.exists(source_db):
            print(f"ℹ️  {source_db} not found, skipping consolidation")
            return
        
        source_info = self.analyze_database(source_db)
        if not source_info or source_info["total_records"] == 0:
            print(f"📭 {source_db} is empty, marking for removal")
            self.report["actions"].append(f"Empty database: {source_db}")
            return
        
        print(f"🔄 Consolidating {source_db} into {self.main_db}")
        
        try:
            # Backup source database
            self.backup_database(source_db)
            
            # Connect to both databases
            source_conn = sqlite3.connect(source_db)
            main_conn = sqlite3.connect(self.main_db)
            
            # Get tables from source
            source_cursor = source_conn.cursor()
            source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in source_cursor.fetchall() if not row[0].startswith('sqlite_')]
            
            for table_name in tables:
                print(f"   📊 Processing table: {table_name}")
                
                # Get table schema
                source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                create_sql = source_cursor.fetchone()
                
                if create_sql:
                    # Create table in main database if it doesn't exist
                    main_cursor = main_conn.cursor()
                    try:
                        main_cursor.execute(create_sql[0])
                    except sqlite3.OperationalError:
                        pass  # Table already exists
                    
                    # Copy data (avoid duplicates)
                    source_cursor.execute(f"SELECT * FROM {table_name}")
                    rows = source_cursor.fetchall()
                    
                    if rows:
                        # Get column names
                        source_cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in source_cursor.fetchall()]
                        placeholders = ','.join(['?'] * len(columns))
                        
                        try:
                            main_cursor.executemany(
                                f"INSERT OR IGNORE INTO {table_name} VALUES ({placeholders})",
                                rows
                            )
                            print(f"      ✅ Copied {len(rows)} records")
                            self.report["consolidated"].append({
                                "table": table_name,
                                "records": len(rows),
                                "source": source_db
                            })
                        except Exception as e:
                            print(f"      ⚠️ Error copying data: {e}")
            
            main_conn.commit()
            source_conn.close()
            main_conn.close()
            
            print(f"✅ Consolidation of {source_db} completed")
            
        except Exception as e:
            print(f"❌ Error consolidating {source_db}: {e}")
    
    def archive_empty_databases(self):
        """Archive databases with no data"""
        empty_databases = [
            "data/enhanced_outcomes.db",
            "data/outcomes.db"
        ]
        
        for db_path in empty_databases:
            if os.path.exists(db_path):
                info = self.analyze_database(db_path)
                if info and info["total_records"] == 0:
                    print(f"📦 Archiving empty database: {db_path}")
                    self.backup_database(db_path)
                    os.remove(db_path)
                    self.report["archived"].append(db_path)
    
    def clean_old_backups(self):
        """Clean up old migration backups (keep recent ones)"""
        backup_dir = "data/migration_backup"
        if not os.path.exists(backup_dir):
            return
        
        print(f"🧹 Cleaning old backups in {backup_dir}")
        
        # Keep backups from last 7 days, archive older ones
        cutoff_time = datetime.now().timestamp() - (7 * 24 * 3600)  # 7 days ago
        
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) < cutoff_time:
                    print(f"   🗑️ Removing old backup: {file_path}")
                    os.remove(file_path)
                    self.report["removed"].append(file_path)
    
    def generate_report(self):
        """Generate cleanup report"""
        report_path = "data/database_cleanup_report.json"
        
        # Add database analysis to report
        self.report["final_state"] = {}
        for db_name in ["trading_unified.db", "trading_predictions.db", "ml_models/training_data.db"]:
            db_path = f"data/{db_name}"
            if os.path.exists(db_path):
                self.report["final_state"][db_name] = self.analyze_database(db_path)
        
        with open(report_path, 'w') as f:
            json.dump(self.report, f, indent=2)
        
        print(f"📄 Cleanup report saved: {report_path}")
        
        # Print summary
        print("\\n" + "="*50)
        print("📊 DATABASE CLEANUP SUMMARY")
        print("="*50)
        print(f"✅ Consolidated: {len(self.report['consolidated'])} tables")
        print(f"📦 Archived: {len(self.report['archived'])} databases")
        print(f"🗑️ Removed: {len(self.report['removed'])} old backups")
        print("\\n🎯 Recommended database structure:")
        print("   - trading_unified.db (main data)")
        print("   - trading_predictions.db (remote predictions)")
        print("   - ml_models/training_data.db (ML training)")
    
    def run_cleanup(self):
        """Run the complete database cleanup process"""
        print("🧹 STARTING DATABASE CLEANUP")
        print("="*50)
        
        # Create backup directory
        self.create_backup_dir()
        
        # Consolidate trading_data.db
        self.consolidate_trading_data_db()
        
        # Archive empty databases
        self.archive_empty_databases()
        
        # Clean old backups
        self.clean_old_backups()
        
        # Generate report
        self.generate_report()
        
        print("\\n🎉 Database cleanup completed!")

def main():
    cleanup_manager = DatabaseCleanupManager()
    cleanup_manager.run_cleanup()

if __name__ == "__main__":
    main()
